/**
 * Photoreal orbit: pre-rendered Cycles frames (48 around the project, day / sunset / night) shown as a
 * draggable 360° spin. Every frame has a matching flat-ID map, so any flat can be tapped and the
 * flats are tinted by status (available / on hold / sold), like a sales-gallery touch table.
 */
export type Kind = 'day' | 'sunset' | 'night';
export interface Manifest { frames: number; kinds: Kind[]; ids: string[]; w: number; h: number; idw: number; idh: number; base: string; mobileBase?: string }
type Status = 'available' | 'hold' | 'sold';

const COL: Record<Status, [number, number, number]> = { available: [40, 200, 110], hold: [255, 190, 40], sold: [235, 64, 64] };

export class PhotoOrbit {
  el: HTMLDivElement;
  private cv: HTMLCanvasElement;
  private ov: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private octx: CanvasRenderingContext2D;
  private m!: Manifest;
  private imgs = new Map<string, HTMLImageElement>();
  private ids = new Map<number, Uint16Array>();
  private idLoading = new Set<number>();
  kind: Kind = 'day';
  private pos = 0;           // continuous frame position
  private zoom = 1; private tZoom = 1;
  private cx = 0.5; private cy = 0.5; private tcx = 0.5; private tcy = 0.5;
  private pinch?: number;
  private target = 0;
  private vel = 0;
  private drag?: { x: number; pos: number; t: number; moved: number };
  private raf = 0;
  active = false;
  private lastDrawn = '';
  /** tower to tint (null = all towers), selected flat, hovered flat */
  tintTower: string | null = null;
  tintFloor: number | null = null;
  tintAll = true;
  floorOf: (id: string) => number = (id) => parseInt(id.split('-')[1].slice(0, -2), 10);
  selected: string | null = null;
  hover: string | null = null;
  statusOf: (id: string) => Status = () => 'available';
  towerOf: (id: string) => string = (id) => id.split('-')[0];
  onPick?: (id: string | null) => void;
  onFrame?: (f: number) => void;
  onHover?: (id: string | null, x: number, y: number) => void;
  best: Record<string, number> = {};
  mobile = matchMedia('(max-width: 860px)').matches;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'porbit hidden';
    this.cv = document.createElement('canvas');
    this.ov = document.createElement('canvas');
    this.ov.className = 'pov';
    this.el.append(this.cv, this.ov);
    parent.appendChild(this.el);
    this.ctx = this.cv.getContext('2d')!;
    this.octx = this.ov.getContext('2d')!;
    addEventListener('resize', () => this.resize());
    this.bind();
  }

  async load(url: string) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('no photoreal renders');
    this.m = await r.json();
    this.best = (this.m as unknown as { best?: Record<string, number> }).best || {};
    this.resize();
  }
  get ready() { return !!this.m; }
  get frames() { return this.m?.frames ?? 48; }

  private src(kind: Kind, f: number) {
    const base = this.mobile && this.m.mobileBase ? this.m.mobileBase : this.m.base;
    return `${base}/${kind}/f_${String(f).padStart(4, '0')}.webp`;
  }
  private img(kind: Kind, f: number): HTMLImageElement {
    const k = `${kind}${f}`;
    let im = this.imgs.get(k);
    if (!im) {
      im = new Image();
      im.decoding = 'async';
      im.src = this.src(kind, f);
      im.onload = () => { this.lastDrawn = ''; };
      this.imgs.set(k, im);
    }
    return im;
  }
  private loadIds(f: number) {
    if (this.ids.has(f) || this.idLoading.has(f)) return;
    this.idLoading.add(f);
    const im = new Image();
    im.src = `${this.m.base}/ids/id_${String(f).padStart(4, '0')}.png`;
    im.onload = () => {
      const c = document.createElement('canvas');
      c.width = this.m.idw; c.height = this.m.idh;
      const x = c.getContext('2d', { willReadFrequently: true })!;
      x.drawImage(im, 0, 0);
      const d = x.getImageData(0, 0, c.width, c.height).data;
      const a = new Uint16Array(c.width * c.height);
      for (let i = 0, j = 0; j < a.length; i += 4, j++) a[j] = d[i] + d[i + 1] * 256;
      this.ids.set(f, a);
      this.idLoading.delete(f);
      this.lastDrawn = '';
    };
  }
  /** progressive preload: coarse ring first, then everything */
  preload(kind: Kind) {
    const n = this.frames;
    const order: number[] = [];
    for (const step of [12, 6, 3, 1]) for (let f = 0; f < n; f += step) if (!order.includes(f)) order.push(f);
    let i = 0;
    const next = () => {
      if (i >= order.length) return;
      const im = this.img(kind, order[i++]);
      if (im.complete) next(); else { im.addEventListener('load', next, { once: true }); im.addEventListener('error', next, { once: true }); }
    };
    for (let k = 0; k < 4; k++) next();
  }

  open(kind?: Kind) {
    if (kind) this.kind = kind;
    this.active = true;
    this.el.classList.remove('hidden');
    this.resize();
    this.preload(this.kind);
    cancelAnimationFrame(this.raf);
    const loop = () => { this.raf = requestAnimationFrame(loop); this.tick(); };
    loop();
  }
  close() {
    this.active = false;
    this.el.classList.add('hidden');
    cancelAnimationFrame(this.raf);
  }
  setKind(k: Kind) {
    this.kind = k;
    this.preload(k);
    this.lastDrawn = '';
  }
  spinTo(f: number) { this.target = this.nearest(f); }
  private nearest(f: number) {
    const n = this.frames;
    let d = ((f - this.pos) % n + n) % n;
    if (d > n / 2) d -= n;
    return this.pos + d;
  }
  frameIndex() { const n = this.frames; return ((Math.round(this.pos) % n) + n) % n; }

  private resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    for (const c of [this.cv, this.ov]) {
      c.width = Math.round(innerWidth * dpr);
      c.height = Math.round(innerHeight * dpr);
    }
    this.lastDrawn = '';
  }

  /** image rect: cover fit, zoomed about (cx, cy) and clamped so the picture always fills the screen */
  private fit() {
    const W = this.cv.width, H = this.cv.height;
    const iw = this.m.w, ih = this.m.h;
    // portrait phones: don't crop the 16:10 frame to a sliver — fill ~64 % of the height and
    // let a blurred copy fill the rest (drawn in tick)
    const portrait = H > W * 1.15;
    const base = portrait ? Math.max(W / iw, (H * 0.64) / ih) : Math.max(W / iw, H / ih);
    const s = base * this.zoom;
    const dw = iw * s, dh = ih * s;
    const ay = portrait ? (this.zoom > 1.05 ? 0.3 : 0.4) : 0.5;
    let x = W / 2 - this.cx * dw, y = H * ay - this.cy * dh;
    x = Math.min(0, Math.max(W - dw, x));
    if (dh >= H) y = Math.min(0, Math.max(H - dh, y)); else y = Math.min(Math.max(y, Math.min(0, H * 0.06)), H - dh);
    return { x, y, s, dw, dh, portrait };
  }
  /** zoom towards a flat (centroid of its pixels in the current frame's ID map) */
  focus(uid: string | null, z = this.mobile ? 2.1 : 1.8) {
    if (!uid) { this.tZoom = 1; this.tcx = 0.5; this.tcy = 0.5; return; }
    const f = this.best[uid] ?? this.frameIndex();
    const go = () => {
      const a = this.ids.get(f);
      if (!a) return;
      const i = this.m.ids.indexOf(uid) + 1;
      let sx = 0, sy = 0, n = 0;
      for (let j = 0; j < a.length; j++) if (a[j] === i) { sx += j % this.m.idw; sy += (j / this.m.idw) | 0; n++; }
      if (!n) return;
      this.tcx = sx / n / this.m.idw; this.tcy = sy / n / this.m.idh; this.tZoom = z;
    };
    if (this.ids.has(f)) go(); else { this.loadIds(f); const iv = setInterval(() => { if (this.ids.has(f)) { clearInterval(iv); go(); } }, 60); setTimeout(() => clearInterval(iv), 4000); }
  }

  private tick() {
    if (!this.m) return;
    if (!this.drag) {
      if (Math.abs(this.vel) > 0.002) { this.target += this.vel; this.vel *= 0.92; }
      this.pos += (this.target - this.pos) * 0.18;
    }
    const pz = this.zoom;
    this.zoom += (this.tZoom - this.zoom) * 0.12; this.cx += (this.tcx - this.cx) * 0.12; this.cy += (this.tcy - this.cy) * 0.12;
    const moving = Math.abs(this.zoom - pz) > 1e-4 || Math.abs(this.tcx - this.cx) > 1e-4 || Math.abs(this.tcy - this.cy) > 1e-4;
    if (moving) this.lastDrawn = '';
    const f = this.frameIndex();
    this.loadIds(f);
    const key = `${this.kind}${f}|${this.zoom.toFixed(4)}|${this.cx.toFixed(4)}|${this.cy.toFixed(4)}|${this.cv.width}|${this.tintTower}|${this.tintFloor}|${this.tintAll}|${this.selected}|${this.hover}|${this.ids.has(f)}`;
    if (key === this.lastDrawn) return;
    let im = this.img(this.kind, f);
    if (!im.complete || !im.naturalWidth) {
      // fall back to the nearest loaded frame so the spin never shows a blank
      for (let d = 1; d < this.frames / 2; d++) {
        for (const g of [f - d, f + d]) {
          const k = `${this.kind}${((g % this.frames) + this.frames) % this.frames}`;
          const c = this.imgs.get(k);
          if (c?.complete && c.naturalWidth) { im = c; d = this.frames; break; }
        }
      }
      if (!im.complete || !im.naturalWidth) return;
    } else this.lastDrawn = key;
    const r = this.fit();
    if (r.dh < this.cv.height) {
      // soft blurred backdrop from the same frame
      const W = this.cv.width, H = this.cv.height, cs = Math.max(W / this.m.w, H / this.m.h);
      this.ctx.filter = 'blur(18px) brightness(0.8)';
      this.ctx.drawImage(im, (W - this.m.w * cs) / 2, (H - this.m.h * cs) / 2, this.m.w * cs, this.m.h * cs);
      this.ctx.filter = 'none';
    }
    this.ctx.drawImage(im, r.x, r.y, r.dw, r.dh);
    this.drawOverlay(f, r);
    this.onFrame?.(f);
  }

  private drawOverlay(f: number, r: { x: number; y: number; dw: number; dh: number }) {
    const o = this.octx;
    o.clearRect(0, 0, this.ov.width, this.ov.height);
    const a = this.ids.get(f);
    if (!a || (!this.tintAll && !this.tintTower && !this.selected && !this.hover)) return;
    const w = this.m.idw, h = this.m.idh;
    const img = new ImageData(w, h);
    const d = img.data;
    const ids = this.m.ids;
    const cache = new Map<number, [number, number, number, number]>();
    for (let j = 0; j < a.length; j++) {
      const v = a[j];
      if (!v) continue;
      let c = cache.get(v);
      if (!c) {
        const uid = ids[v - 1];
        const st = this.statusOf(uid);
        const inTower = this.tintAll || (this.towerOf(uid) === this.tintTower && (this.tintFloor == null || this.floorOf(uid) === this.tintFloor));
        const sel = uid === this.selected, hov = uid === this.hover;
        const base = COL[st];
        c = sel ? [255, 255, 255, 170] : hov ? [base[0], base[1], base[2], 200] : inTower ? [base[0], base[1], base[2], this.kind === 'night' ? 120 : 105] : [0, 0, 0, 0];
        cache.set(v, c);
      }
      if (!c[3]) continue;
      // thin dark edge between flats for a crisp, tiled look
      const x = j % w;
      const edge = (x > 0 && a[j - 1] !== v) || (j >= w && a[j - w] !== v);
      const k = j * 4;
      d[k] = edge ? c[0] * 0.55 : c[0]; d[k + 1] = edge ? c[1] * 0.55 : c[1]; d[k + 2] = edge ? c[2] * 0.55 : c[2]; d[k + 3] = edge ? Math.min(255, c[3] + 60) : c[3];
    }
    const tmp = document.createElement('canvas');
    tmp.width = w; tmp.height = h;
    tmp.getContext('2d')!.putImageData(img, 0, 0);
    o.imageSmoothingEnabled = true;
    o.drawImage(tmp, r.x, r.y, r.dw, r.dh);
  }

  /** flat id under a client point */
  pick(cx: number, cy: number): string | null {
    const f = this.frameIndex();
    const a = this.ids.get(f);
    if (!a || !this.m) return null;
    const dpr = this.cv.width / innerWidth;
    const r = this.fit();
    const u = (cx * dpr - r.x) / r.dw, v = (cy * dpr - r.y) / r.dh;
    if (u < 0 || v < 0 || u >= 1 || v >= 1) return null;
    const px = Math.floor(u * this.m.idw), py = Math.floor(v * this.m.idh);
    const id = a[py * this.m.idw + px];
    return id ? this.m.ids[id - 1] : null;
  }

  private bind() {
    const el = this.el;
    el.addEventListener('pointerdown', (e) => {
      this.drag = { x: e.clientX, pos: this.pos, t: performance.now(), moved: 0 };
      this.vel = 0;
      el.setPointerCapture(e.pointerId);
    });
    el.addEventListener('pointermove', (e) => {
      if (this.drag) {
        const dx = e.clientX - this.drag.x;
        this.drag.moved = Math.max(this.drag.moved, Math.abs(dx));
        // a full-width drag turns the project ~half way round
        const k = (this.frames / 2) / Math.max(320, innerWidth);
        const np = this.drag.pos - dx * k;
        const now = performance.now();
        this.vel = (np - this.pos) / Math.max(1, (now - this.drag.t) / 16.7) * 0.9;
        this.drag.t = now;
        this.pos = this.target = np;
      } else if (e.pointerType === 'mouse') {
        const id = this.pick(e.clientX, e.clientY);
        if (id !== this.hover) { this.hover = id; el.style.cursor = id ? 'pointer' : 'grab'; this.onHover?.(id, e.clientX, e.clientY); }
        else if (id) this.onHover?.(id, e.clientX, e.clientY);
      }
    });
    const up = (e: PointerEvent) => {
      if (!this.drag) return;
      const tap = this.drag.moved < 6;
      this.drag = undefined;
      if (tap) { this.vel = 0; this.onPick?.(this.pick(e.clientX, e.clientY)); }
    };
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', () => (this.drag = undefined));
    el.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) { this.target += Math.sign(e.deltaX); return; }
      const r = this.fit(), dpr = this.cv.width / innerWidth;
      if (this.tZoom <= 1.01) { this.tcx = (e.clientX * dpr - r.x) / r.dw; this.tcy = (e.clientY * dpr - r.y) / r.dh; }
      this.tZoom = Math.min(3, Math.max(1, this.tZoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15)));
      if (this.tZoom <= 1.01) { this.tcx = 0.5; this.tcy = 0.5; }
    }, { passive: false });
    el.addEventListener('touchmove', (e) => {
      if (e.touches.length !== 2) return;
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      if (this.pinch) {
        const mx = (e.touches[0].clientX + e.touches[1].clientX) / 2, my = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        const r = this.fit(), dpr = this.cv.width / innerWidth;
        if (this.tZoom <= 1.01) { this.tcx = (mx * dpr - r.x) / r.dw; this.tcy = (my * dpr - r.y) / r.dh; }
        this.tZoom = Math.min(3, Math.max(1, this.tZoom * d / this.pinch));
      }
      this.pinch = d;
      this.drag = undefined;
    }, { passive: true });
    el.addEventListener('touchend', () => (this.pinch = undefined));
    addEventListener('keydown', (e) => {
      if (!this.active) return;
      if (e.key === 'ArrowLeft') this.target -= 1;
      if (e.key === 'ArrowRight') this.target += 1;
    });
  }
}
