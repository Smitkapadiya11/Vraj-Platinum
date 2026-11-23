import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import gsap from 'gsap';
import { sunPosition, istDate } from './sun';
import { SITE } from '../data/project';

export const LITE = new URLSearchParams(location.search).has('lite');
if (LITE) gsap.ticker.lagSmoothing(0);
export const IS_MOBILE = matchMedia('(pointer: coarse)').matches || Math.min(innerWidth, innerHeight) < 700;

export class World {
  renderer: THREE.WebGLRenderer;
  scene = new THREE.Scene();
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  composer: EffectComposer;
  bloom: UnrealBloomPass;
  ao?: GTAOPass;
  sky = new Sky();
  sun = new THREE.DirectionalLight(0xfff1dc, 3.2);
  hemi = new THREE.HemisphereLight(0xcfe3ff, 0x6b5a46, 0.9);
  night = 0; // 0 day .. 1 night
  hour = 16.5;
  private pmrem: THREE.PMREMGenerator;
  private envRT?: THREE.WebGLRenderTarget;
  private skyScene = new THREE.Scene();
  private tickers: ((dt: number, t: number) => void)[] = [];
  private clock = new THREE.Clock();
  quality: 'high' | 'balanced' = IS_MOBILE ? 'balanced' : 'high';
  overrideScene?: { scene: THREE.Scene; camera: THREE.Camera };
  private fpsAcc = 0; private fpsN = 0; private dprScale = 1;
  onSunChange: (() => void)[] = [];

  constructor(public canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: !IS_MOBILE, powerPreference: 'high-performance', alpha: false });
    this.renderer.setPixelRatio(LITE ? 0.5 : Math.min(devicePixelRatio, IS_MOBILE ? 1.6 : 2));
    this.renderer.setSize(innerWidth, innerHeight, false);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.95;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.shadowMap.enabled = !LITE;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.camera = new THREE.PerspectiveCamera(IS_MOBILE ? 50 : 38, innerWidth / innerHeight, 0.05, 9000);
    this.camera.position.set(260, 150, 300);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.maxPolarAngle = Math.PI * 0.495;
    this.controls.minDistance = 8;
    this.controls.maxDistance = 900;
    this.controls.rotateSpeed = 0.6;
    this.controls.zoomSpeed = 0.9;
    this.controls.screenSpacePanning = false;

    // sky + sun
    this.sky.scale.setScalar(8000);
    const u = this.sky.material.uniforms;
    u.turbidity.value = 6.5; u.rayleigh.value = 1.6; u.mieCoefficient.value = 0.004; u.mieDirectionalG.value = 0.82;
    this.scene.add(this.sky);
    this.skyScene.add(new Sky());
    (this.skyScene.children[0] as Sky).scale.setScalar(1000);
    this.pmrem = new THREE.PMREMGenerator(this.renderer);

    this.sun.castShadow = true;
    const sm = IS_MOBILE ? 1024 : 2048;
    this.sun.shadow.mapSize.set(sm, sm);
    const sc = this.sun.shadow.camera as THREE.OrthographicCamera;
    sc.left = -80; sc.right = 80; sc.top = 80; sc.bottom = -80; sc.near = 10; sc.far = 600;
    this.sun.shadow.bias = -0.0004;
    this.sun.shadow.normalBias = 0.04;
    this.scene.add(this.sun, this.sun.target, this.hemi);
    this.scene.fog = new THREE.Fog(0xdfe6ee, 600, 4200);

    // post
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    if (!IS_MOBILE && !LITE) {
      this.ao = new GTAOPass(this.scene, this.camera, innerWidth, innerHeight);
      this.ao.updateGtaoMaterial({ radius: 1.4, distanceExponent: 1.4, thickness: 1.5, scale: 1.0, samples: 8 });
      this.ao.updatePdMaterial({ samples: 6, rings: 2, radius: 6 });
      this.ao.blendIntensity = 0.85;
      this.composer.addPass(this.ao);
    }
    this.bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.35, 0.5, 0.92);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());

    addEventListener('resize', () => this.resize());
    this.setHour(this.hour);
    this.loop();
  }

  resize() {
    const w = innerWidth, h = innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.composer.setSize(w, h);
    this.overrideResize?.(w, h);
  }
  overrideResize?: (w: number, h: number) => void;

  onTick(f: (dt: number, t: number) => void) { this.tickers.push(f); }

  setQuality(q: 'high' | 'balanced') {
    this.quality = q;
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, q === 'high' ? 2 : 1.25) * this.dprScale);
    this.resize();
  }

  /** hour in IST (0-24). Updates sky, sun light, env map, night factor */
  setHour(hour: number) {
    this.hour = hour;
    const p = sunPosition(istDate(hour), SITE.geo.lat, SITE.geo.lng);
    const alt = p.altitude, az = p.azimuth;
    // three: x = East, z = South, y = up
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(alt), Math.sin(alt), -Math.cos(az) * Math.cos(alt));
    const u = this.sky.material.uniforms;
    u.sunPosition.value.copy(dir);
    const sk = this.skyScene.children[0] as Sky;
    sk.material.uniforms.sunPosition.value.copy(dir);
    for (const k of ['turbidity', 'rayleigh', 'mieCoefficient', 'mieDirectionalG'] as const) sk.material.uniforms[k].value = u[k].value;

    const elev = THREE.MathUtils.radToDeg(alt);
    this.night = THREE.MathUtils.clamp((2 - elev) / 10, 0, 1);
    const day = 1 - this.night;
    const warm = THREE.MathUtils.clamp(1 - elev / 25, 0, 1);
    this.sunDir.copy(dir);
    this.sun.intensity = 3.4 * THREE.MathUtils.clamp(elev / 8, 0, 1);
    this.sun.color.setRGB(1, 0.93 - 0.22 * warm, 0.84 - 0.42 * warm);
    this.hemi.intensity = 0.25 + 0.75 * day;
    this.hemi.color.setRGB(0.8 - 0.55 * this.night, 0.88 - 0.6 * this.night, 1.0 - 0.55 * this.night);
    this.hemi.groundColor.setRGB(0.42 * day + 0.05, 0.36 * day + 0.04, 0.3 * day + 0.06);
    this.renderer.toneMappingExposure = 0.84 + 0.5 * this.night;
    const fog = this.scene.fog as THREE.Fog;
    fog.color.setRGB(0.86 * day + 0.04, 0.89 * day + 0.06, 0.93 * day + 0.12);
    this.scene.background = null;
    this.sky.visible = true;
    if (this.night > 0.85) {
      this.sky.visible = false;
      this.scene.background = new THREE.Color().setRGB(0.012, 0.025, 0.06);
    }
    // bloom only for lit windows/lamps at dusk & night (HDR sky would wash out the day image)
    this.bloom.strength = 0.55 * this.night;
    this.bloom.threshold = 1.15;
    this.bloom.radius = 0.45;
    this.bloom.enabled = this.night > 0.05;
    this.updateEnv();
    this.onSunChange.forEach((f) => f());
  }

  private envPending = false;
  private updateEnv() {
    if (this.envPending) return;
    this.envPending = true;
    requestAnimationFrame(() => {
      this.envPending = false;
      this.envRT?.dispose();
      if (this.night > 0.6) {
        const s = new THREE.Scene();
        s.background = new THREE.Color(0x0b1424);
        this.envRT = this.pmrem.fromScene(s, 0.02);
      } else {
        this.envRT = this.pmrem.fromScene(this.skyScene, 0.02);
      }
      this.scene.environment = this.envRT.texture;
      this.scene.environmentIntensity = 0.55 * (1 - this.night) + 0.08;
    });
  }

  /** Smooth camera flight. Long moves arc up and over (drone-like) instead of cutting through towers. */
  flyTo(pos: THREE.Vector3, target: THREE.Vector3, dur = 2.2, ease = 'power3.inOut') {
    gsap.killTweensOf(this.flight);
    const p0 = this.camera.position.clone(), t0 = this.controls.target.clone();
    const dist = p0.distanceTo(pos);
    const lift = Math.min(90, dist * 0.32);
    const ctrl = p0.clone().lerp(pos, 0.5);
    ctrl.y = Math.max(ctrl.y, Math.max(p0.y, pos.y) + lift * (dist > 40 ? 1 : 0.2));
    this.flight.t = 0;
    return new Promise<void>((res) => {
      gsap.to(this.flight, {
        t: 1, duration: dur, ease,
        onUpdate: () => {
          const k = this.flight.t, a = (1 - k) * (1 - k), b = 2 * (1 - k) * k, c = k * k;
          this.camera.position.set(a * p0.x + b * ctrl.x + c * pos.x, a * p0.y + b * ctrl.y + c * pos.y, a * p0.z + b * ctrl.z + c * pos.z);
          this.controls.target.lerpVectors(t0, target, k);
        },
        onComplete: () => res(),
      });
    });
  }
  flight = { t: 0 };
  stopFlight() { gsap.killTweensOf(this.flight); }

  private loop = () => {
    requestAnimationFrame(this.loop);
    const raw = this.clock.getDelta();
    const dt = Math.min(raw, 0.1);
    const t = this.clock.elapsedTime;
    if (this.controls.enabled) this.controls.update();
    this.tickers.forEach((f) => f(dt, t));
    if (this.overrideScene) {
      this.renderer.render(this.overrideScene.scene, this.overrideScene.camera);
    } else {
      // keep the shadow frustum around what we look at
      const tg = this.controls.target;
      this.sun.target.position.set(tg.x, 0, tg.z);
      this.sun.position.copy(this.sun.target.position).addScaledVector(this.sunDir, 300);
      this.composer.render(dt);
    }
    // adaptive resolution
    if (LITE) return;
    if (raw > 0.25 || document.hidden) { this.fpsAcc = 0; this.fpsN = 0; return; } // throttled/background tab
    this.fpsAcc += dt; this.fpsN++;
    if (this.fpsAcc > 2.5) {
      const fps = this.fpsN / this.fpsAcc;
      this.fpsAcc = 0; this.fpsN = 0;
      if (fps < 45 && this.ao?.enabled) { this.ao.enabled = false; } // drop AO first
      else if (fps < 32 && this.dprScale > 0.6) { this.dprScale -= 0.15; this.setQuality(this.quality); }
      else if (fps > 55 && this.dprScale < 1) { this.dprScale = Math.min(1, this.dprScale + 0.1); this.setQuality(this.quality); }
    }
  };
  sunDir = new THREE.Vector3(0, 1, 0);
}
