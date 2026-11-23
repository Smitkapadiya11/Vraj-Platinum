import './styles.css';
import * as THREE from 'three';
import gsap from 'gsap';
import { World, IS_MOBILE } from './scene/World';
import { Campus, toV, STATUS_COLOR } from './scene/Campus';
import { Ground } from './scene/Ground';
import { Context } from './scene/Context';
import { Trees } from './scene/Trees';
import { Interior } from './scene/Interior';
import { BalconyView } from './scene/BalconyView';
import { RealView } from './scene/RealView';
import { SITE, PROJECT, PLANS, GALLERY, SAMPLE_FLAT, PLAN_IMG } from './data/project';
import { UNITS, UNIT_BY_ID, TOWERS, DIR_NAME, unitsOf, type Unit } from './data/units';
import { t, setLang, getLang, onLang, type Lang } from './ui/i18n';
import { L, DIR3, TAG3, VIEW3, room, ABOUT, HIGHLIGHTS3, AMENITIES3, SPECS_EXT3, SPECS_INT3, NEARBY3, TOUR3 } from './data/i18nContent';
import { SITE_PHOTOS, SET_INFO, photoSrc, photosForView, realViewsFor, type SitePhoto } from './data/sitePhotos';
import { icon } from './ui/icons';

// ------------------------------------------------------------------ setup
const $ = <T extends HTMLElement = HTMLElement>(s: string) => document.querySelector(s) as T;
const canvas = $<HTMLCanvasElement>('#c');
const world = new World(canvas);
const campus = new Campus(world);
const ground = new Ground(world.renderer.capabilities.getMaxAnisotropy(), IS_MOBILE);
world.scene.add(ground.group);
const context = new Context();
world.scene.add(context.group);
const trees = new Trees(IS_MOBILE);
world.scene.add(trees.group);
const interior = new Interior(world, $('#roomLabels'));
const balcony = new BalconyView(world);
const realView = new RealView(world);

type Mode = 'campus' | 'tower' | 'unit' | 'balcony' | 'interior';
const S = { real: true, realIdx: 0, mode: 'campus' as Mode, tower: null as string | null, floor: null as number | null, unit: null as string | null, view: 0, hover: null as string | null };
const shortlist = new Set<string>(JSON.parse(safeGet('vp-short') || '[]'));
function safeGet(k: string) { try { return localStorage.getItem(k); } catch { return null; } }
function safeSet(k: string, v: string) { try { localStorage.setItem(k, v); } catch { /* ignore */ } }

const CAMPUS_POS = toV(165, -205, 125), CAMPUS_TARGET = new THREE.Vector3(0, 18, 0);
const GH = SITE.groundH, FH = SITE.floorH, NF = SITE.floors;
const fmtINR = (n: number) => '₹' + Math.round(n).toLocaleString('en-IN');
const lakh = (n: number) => '₹' + (n / 1e5).toFixed(2) + ' L';
const fmtHour = (h: number) => { const H = Math.floor(h), m = Math.round((h - H) * 60); const hh = ((H + 11) % 12) + 1; return `${hh}:${String(m).padStart(2, '0')} ${H < 12 ? 'AM' : 'PM'}`; };

// ------------------------------------------------------------------ loader / intro
const ldBar = $('#ldBar'), ldText = $('#ldText'), enterBtn = $('#enterBtn');
ldText.textContent = t('loading');
enterBtn.textContent = t('enter');
world.camera.position.copy(toV(600, -700, 420));
world.controls.target.copy(CAMPUS_TARGET);

campus.load((p) => (ldBar.style.width = `${Math.round(p * 92)}%`)).then(() => {
  ldBar.style.width = '100%';
  campus.setNight(world.night);
  buildTowerLabels();
  enterBtn.classList.add('on');
  ldText.textContent = '6 towers · 336 homes · G+14';
  if (IS_MOBILE) enterBtn.focus();
  // deep link
  const startFromHash = location.hash.length > 2;
  enterBtn.onclick = () => enter(startFromHash);
  setTimeout(() => { if (!entered) enter(startFromHash); }, 6000);
}).catch((e) => {
  console.error(e);
  ldText.textContent = 'Could not load 3D models. Please refresh.';
});

let entered = false;
async function enter(fromHash: boolean) {
  if (entered) return;
  entered = true;
  $('#loader').classList.add('done');
  if (fromHash) { route(); return; }
  await world.flyTo(CAMPUS_POS, CAMPUS_TARGET, 3.6, 'power2.inOut');
  hint(t('tapTower'));
}

// ------------------------------------------------------------------ chrome
function renderNav() {
  const items: [string, string, () => void][] = [
    ['explore', t('explore'), () => goCampus()],
    ['res', t('residences'), () => openResidences()],
    ['sample', t('sampleFlat'), () => openSampleFlat()],
    ['gallery', t('gallery'), () => openGallery()],
    ['loc', t('location'), () => openLocation()],
    ['specs', t('specs'), () => openSpecs()],
  ];
  const nav = $('#nav');
  nav.innerHTML = '';
  for (const [, label, fn] of items) {
    const b = document.createElement('button');
    b.textContent = label;
    b.onclick = () => { nav.classList.remove('open'); fn(); };
    nav.appendChild(b);
  }
  const enq = document.createElement('button');
  enq.textContent = t('enquire');
  enq.className = 'only-m';
  enq.onclick = () => { nav.classList.remove('open'); openEnquiry(); };
  if (IS_MOBILE) nav.appendChild(enq);
  $('#enqTop').textContent = t('enquire');
}
$('#enqTop').onclick = () => openEnquiry();
$('#menuBtn').onclick = () => $('#nav').classList.toggle('open');
const langSel = $<HTMLSelectElement>('#lang');
langSel.value = getLang();
langSel.onchange = () => setLang(langSel.value as Lang);
onLang(() => { renderAll(); });

function renderDock() {
  const d = $('#dock');
  d.innerHTML = `
    <div class="compass" title="North"><i></i><b id="cmpN">N</b></div>
    <div class="sep"></div>
    <div class="time" title="${t('timeOfDay')}">${icon(world.night > 0.5 ? 'moon' : 'sun')}<span class="lbl">${t('timeOfDay')}</span>
      <input id="hour" type="range" min="5.5" max="20.5" step="0.05" value="${world.hour}" aria-label="${t('timeOfDay')}"><b id="hourTxt">${fmtHour(world.hour)}</b></div>
    <div class="sep"></div>
    <button class="btn sm" id="dayNight">${world.night > 0.5 ? icon('sun') + t('day') : icon('moon') + t('night')}</button>
    <button class="btn sm hide-m" id="mapMode">${ground.mode === 'map' ? '🛰 ' + t('satView') : '🗺 ' + t('mapView')}</button>
    <button class="btn sm" id="tourBtn">${touring ? '■ ' + t('stopTour') : '▶ ' + t('droneTour')}</button>
    <button class="btn icon sm hide-m" id="zIn" title="Zoom in">+</button>
    <button class="btn icon sm hide-m" id="zOut" title="Zoom out">−</button>
    <button class="btn icon sm" id="resetCam" title="Reset view">${icon('reset')}</button>`;
  const dolly = (k: number) => {
    if (S.mode === 'balcony' || S.mode === 'interior') return;
    const c = world.controls, cam = world.camera;
    const off = cam.position.clone().sub(c.target).multiplyScalar(k);
    const len = THREE.MathUtils.clamp(off.length(), c.minDistance, c.maxDistance);
    off.setLength(len);
    gsap.to(cam.position, { x: c.target.x + off.x, y: c.target.y + off.y, z: c.target.z + off.z, duration: 0.6, ease: 'power2.out' });
  };
  $('#tourBtn').onclick = () => droneTour();
  $('#mapMode').onclick = () => { ground.setMode(ground.mode === 'map' ? 'sat' : 'map'); renderDock(); };
  $('#zIn').onclick = () => dolly(0.75);
  $('#zOut').onclick = () => dolly(1.33);
  (d.querySelector('.compass') as HTMLElement).onclick = () => {
    if (S.mode === 'balcony' || S.mode === 'interior') return;
    const c = world.controls, cam = world.camera;
    const off = cam.position.clone().sub(c.target);
    const h = Math.hypot(off.x, off.z);
    gsap.to(cam.position, { x: c.target.x, z: c.target.z + h, duration: 1, ease: 'power2.inOut' });
  };
  const hr = $<HTMLInputElement>('#hour');
  hr.oninput = () => setHour(+hr.value);
  $('#dayNight').onclick = () => {
    const target = world.night > 0.5 ? 10 : 19.6;
    const o = { h: world.hour };
    gsap.to(o, { h: target, duration: 1.8, ease: 'power2.inOut', onUpdate: () => setHour(o.h, false), onComplete: () => renderDock() });
  };
  $('#resetCam').onclick = () => { if (S.mode === 'interior') interior.overview(); else if (S.mode === 'balcony') balcony.enter(campus.balconyPose(UNIT_BY_ID.get(S.unit!)!, S.view).pos, campus.balconyPose(UNIT_BY_ID.get(S.unit!)!, S.view).look); else goCampus(); };
}
function setHour(h: number, rerender = true) {
  world.setHour(h);
  campus.setNight(world.night);
  context.setNight(world.night);
  const ht = document.getElementById('hourTxt');
  if (ht) ht.textContent = fmtHour(h);
  const hr = document.getElementById('hour') as HTMLInputElement | null;
  if (hr && Math.abs(+hr.value - h) > 0.01) hr.value = String(h);
  if (rerender && (world.night > 0.5) !== nightShown) renderDock();
  nightShown = world.night > 0.5;
}
let nightShown = false;

let hintTimer = 0;
function hint(msg: string, ms = 5000) {
  const h = $('#hint');
  h.textContent = msg;
  h.style.opacity = '1';
  clearTimeout(hintTimer);
  hintTimer = window.setTimeout(() => (h.style.opacity = '0'), ms);
}
function toast(msg: string) {
  const d = document.createElement('div');
  d.className = 'toast';
  d.textContent = msg;
  document.body.appendChild(d);
  gsap.fromTo(d, { y: -10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3 });
  setTimeout(() => gsap.to(d, { opacity: 0, duration: 0.4, onComplete: () => d.remove() }), 1800);
}

// ------------------------------------------------------------------ context panel
const towerInfo = (tw: string) => {
  const us = unitsOf(tw);
  const types = [...new Set(us.map((u) => u.type))].join(' · ');
  return { avail: us.filter((u) => u.status === 'available').length, total: us.length, types };
};
function renderCtx() {
  const c = $('#ctx');
  c.classList.remove('hidden');
  if (S.mode === 'balcony' || S.mode === 'interior') { c.classList.add('hidden'); return; }
  if (!S.tower) {
    const av = UNITS.filter((u) => u.status === 'available').length;
    c.innerHTML = `
      <div class="eyebrow">${PROJECT.tagline}</div>
      <h2>Vraj Platinum</h2>
      <div class="muted sub-m" style="font-size:13px">${PROJECT.subline} · Sarthana, Surat</div>
      <div class="stat-row"><span><b>6</b> towers</span><span><b>G+14</b></span><span><b>336</b> homes</span><span><b>${av}</b> ${t('available').toLowerCase()}</span></div>
      <div id="ctx-body">
        <div class="tower-grid">${TOWERS.map((tw) => { const i = towerInfo(tw); return `<button class="tower-card" data-t="${tw}"><b>${tw}</b><span>Type ${i.types}</span><br><span><span class="dot available"></span> ${i.avail}/${i.total}</span></button>`; }).join('')}</div>
        <div class="legend"><span><i class="dot available"></i>${t('available')}</span><span><i class="dot hold"></i>${t('hold')}</span><span><i class="dot sold"></i>${t('sold')}</span>${PROJECT.commercial.demoInventory ? '<span style="opacity:.7">· demo availability</span>' : ''}</div>
        <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap">
          <button class="btn sm primary" id="tourCtx">▶ ${t('droneTour')}</button>
          <button class="btn sm" id="findBtn">${t('filters')}</button>
          <button class="btn sm" id="sfBtn">${t('sampleFlat')}</button>
          <a class="btn sm" href="${PROJECT.brochure}" target="_blank" rel="noopener">${t('brochure')} ↗</a>
        </div>
      </div>`;
    c.querySelectorAll<HTMLElement>('.tower-card').forEach((b) => (b.onclick = () => selectTower(b.dataset.t!)));
    $('#findBtn').onclick = () => openResidences();
    $('#tourCtx').onclick = () => droneTour();
    $('#sfBtn').onclick = () => openSampleFlat();
    return;
  }
  const tw = S.tower;
  const i = towerInfo(tw);
  const floors = Array.from({ length: NF }, (_, k) => NF - k);
  c.innerHTML = `
    <div class="crumbs"><button id="crCampus">${t('campus')}</button> › <span>${t('tower')} ${tw}</span>${S.floor ? ` › <span>${t('floor')} ${S.floor}</span>` : ''}</div>
    <h2>${t('tower')} ${tw}</h2>
    <div class="stat-row"><span><b>G+14</b></span><span>Type <b>${i.types}</b></span><span><b>${i.avail}</b>/${i.total} ${t('available').toLowerCase()}</span></div>
    <div id="ctx-body">
    ${S.floor ? `<div class="eyebrow" style="margin-top:12px">${t('units')} · ${t('floor')} ${S.floor}</div>
      <div class="unit-list">${unitsOf(tw, S.floor).map((u) => `
        <button class="unit-item ${u.id === S.unit ? 'on' : ''}" data-u="${u.id}">
          <i class="dot ${u.status}"></i>
          <div><b>${u.id}</b><small>Type ${u.type} · ${u.roomArea} sq ft · ${L(DIR3[u.facing])} · ${L(TAG3[u.tag])}</small></div>
          <span class="muted" style="font-size:12px">${t(u.status)}</span>
        </button>`).join('')}</div>` : ''}
    <div class="eyebrow" style="margin-top:16px">${t('floor')}</div>
    <div class="floor-list">${floors.map((f) => `<button class="floor-row ${f === S.floor ? 'on' : ''}" data-f="${f}"><span class="n">${f}</span><span class="u">${unitsOf(tw, f).map((u) => `<i style="background:${'#' + STATUS_COLOR[u.status].toString(16).padStart(6, '0')}"></i>`).join('')}</span></button>`).join('')}</div>
    <div class="legend"><span><i class="dot available"></i>${t('available')}</span><span><i class="dot hold"></i>${t('hold')}</span><span><i class="dot sold"></i>${t('sold')}</span></div>
    </div>`;
  $('#crCampus').onclick = () => goCampus();
  c.querySelectorAll<HTMLElement>('.floor-row').forEach((b) => (b.onclick = () => selectFloor(+b.dataset.f!)));
  c.querySelectorAll<HTMLElement>('.unit-item').forEach((b) => (b.onclick = () => selectUnit(b.dataset.u!)));
  const on = c.querySelector('.unit-item.on') || c.querySelector('.floor-row.on');
  if (on && !IS_MOBILE) on.scrollIntoView({ block: 'nearest' });
}

// ------------------------------------------------------------------ unit card
function renderCard() {
  const c = $('#card');
  const u = S.unit ? UNIT_BY_ID.get(S.unit) : null;
  if (!u || S.mode === 'balcony' || S.mode === 'interior') { c.classList.add('hidden'); return; }
  c.classList.remove('hidden');
  if (IS_MOBILE) $('#ctx').classList.add('hidden');
  const isShort = shortlist.has(u.id);
  c.innerHTML = `
    <button class="x" id="cardX" aria-label="${t('close')}">×</button>
    <div class="hero" style="background-image:url(${PLAN_IMG[u.type]})"><span class="badge"><i class="dot ${u.status}"></i>${t(u.status)}</span></div>
    <div class="body">
      <div class="eyebrow">${t('tower')} ${u.tower} · ${t('floor')} ${u.floor}</div>
      <h3>${u.id} <span class="badge" style="font-family:var(--sans);font-size:11.5px;vertical-align:middle"><i class="dot ${u.status}"></i>${t(u.status)}</span></h3>
      <div class="muted" style="font-size:13px;margin-top:4px">${t('bhk')} · ${PLANS[u.type].label} · ${L(TAG3[u.tag])}</div>
      <div class="kv">
        <div><small>${t('roomArea')}</small><b>${u.roomArea} sq ft</b><small>${u.roomAreaM2} m²</small></div>
        <div><small>${t('facing')}</small><b>${L(DIR3[u.facing])}</b><small>${u.flat.views.map((v) => L(DIR3[v.dir])).join(' + ')} ${t('views')}</small></div>
        <div><small>${t('height')}</small><b>${u.heightM.toFixed(1)} m</b><small>${t('floor')} ${u.floor} of 14</small></div>
        <div><small>${t('type')}</small><b>2 BHK · ${u.type}</b><small>${PLANS[u.type].rooms.filter((r) => r.kind === 'toilet').length} toilets${PLANS[u.type].rooms.some((r) => r.kind === 'balcony') ? ' · balcony' : ''}</small></div>
      </div>
      <div class="actions">
        <button class="btn primary wide" id="aBal">${icon('eye')}${t('balconyView')}</button>
        <button class="btn" id="a3d">${icon('cube')}${t('interior3d')}</button>
        <button class="btn" id="aPlan">${icon('plan')}${t('floorPlan')}</button>
        <button class="btn" id="aCost">${icon('calc')}${t('costSheet')}</button>
        <button class="btn" id="aShort">${icon('heart')}${isShort ? t('shortlisted') : t('shortlist')}</button>
        <a class="btn wide" id="aWa" href="${waLink(u)}" target="_blank" rel="noopener">${icon('wa')}${t('whatsapp')}</a>
        <button class="btn sm wide ghost" id="aShare">${icon('share')}${t('share')}</button>
      </div>
      <div class="sunrow" id="sunRow">${icon('sun')}<span>${t('sunToday')}…</span></div>
    </div>`;
  setTimeout(() => {
    const blockers = [...campus.towerPick, context.group];
    const y = new Date().getUTCFullYear();
    const fmt = (h: number) => (h >= 1 ? `${h.toFixed(1)} h` : h > 0 ? `${Math.round(h * 60)} min` : '—');
    const today = campus.sunHours(u, 0, new Date(), blockers);
    const jun = campus.sunHours(u, 0, new Date(Date.UTC(y, 5, 21)), blockers);
    const dec = campus.sunHours(u, 0, new Date(Date.UTC(y, 11, 21)), blockers);
    const el = document.getElementById('sunRow');
    if (el && S.unit === u.id) el.innerHTML = `${icon('sun')}<span>${t('sunToday')}: <b>${fmt(today)}</b> ${t('hrsToday')} · ${t('june')} ${fmt(jun)} · ${t('dec')} ${fmt(dec)}</span>`;
  }, 60);
  $('#cardX').onclick = () => { S.unit = null; S.mode = 'tower'; refreshFloor(); renderCard(); renderCtx(); syncHash(); };
  $('#aBal').onclick = () => openBalcony(u.id, 0);
  $('#a3d').onclick = () => openInterior(u.type);
  $('#aPlan').onclick = () => openPlan(u);
  $('#aCost').onclick = () => openCost(u);
  $('#aShort').onclick = () => { if (shortlist.has(u.id)) shortlist.delete(u.id); else shortlist.add(u.id); safeSet('vp-short', JSON.stringify([...shortlist])); renderCard(); };
  $('#aShare').onclick = async () => {
    const url = location.href;
    try { if (navigator.share) await navigator.share({ title: `Vraj Platinum ${u.id}`, url }); else { await navigator.clipboard.writeText(url); toast(t('copied')); } } catch { /* cancelled */ }
  };
}
function waLink(u?: Unit, extra = '') {
  const msg = u
    ? `Hello, I am interested in Vraj Platinum flat ${u.id} (Tower ${u.tower}, Floor ${u.floor}, 2 BHK Type ${u.type}). Please share price & availability.${extra}`
    : `Hello, I would like details of Vraj Platinum, Sarthana (2 BHK).${extra}`;
  return `https://wa.me/${PROJECT.phone.replace('+', '')}?text=${encodeURIComponent(msg)}`;
}

// ------------------------------------------------------------------ navigation in 3D
function towerCam(tw: string, floor?: number | null) {
  const c = campus.towerCenter(tw);
  const out = new THREE.Vector3(c.x, 0, c.z).normalize();
  if (out.lengthSq() < 0.01) out.set(1, 0, 0);
  const side = new THREE.Vector3(-out.z, 0, out.x);
  const fy = floor ? GH + floor * FH : 26;
  const dist = floor ? (IS_MOBILE ? 52 : 40) : (IS_MOBILE ? 120 : 92);
  const pos = new THREE.Vector3(c.x, 0, c.z).addScaledVector(out, dist).addScaledVector(side, dist * 0.45);
  pos.y = floor ? fy + (IS_MOBILE ? 34 : 26) : 58;
  const target = new THREE.Vector3(c.x, floor ? fy - 2 : 22, c.z);
  if (IS_MOBILE) target.y -= floor ? 6 : 10; // leave room for bottom sheet
  return { pos, target };
}
function goCampus() {
  realView.close();
  context.clear.value = 40;
  if (S.mode === 'balcony') balcony.exit();
  if (S.mode === 'interior') interior.close();
  Object.assign(S, { mode: 'campus', tower: null, floor: null, unit: null });
  campus.slice(null, null);
  campus.showFloorUnits(null, null);
  world.flyTo(CAMPUS_POS, CAMPUS_TARGET, 2.2);
  renderAll();
  syncHash();
}
function selectTower(tw: string, floor: number | null = null) {
  stopTour();
  realView.close();
  context.clear.value = 40;
  if (S.mode === 'balcony') balcony.exit();
  if (S.mode === 'interior') interior.close();
  Object.assign(S, { mode: 'tower', tower: tw, floor, unit: null });
  const best = floor ?? null;
  campus.slice(best ? tw : null, best);
  refreshFloor();
  const { pos, target } = towerCam(tw, floor);
  world.flyTo(pos, target, 2.0);
  renderAll();
  syncHash();
  if (!floor) hint(`${t('floor')} → ${t('units')}`);
}
function selectFloor(f: number) {
  if (!S.tower) return;
  S.floor = f; S.unit = null; S.mode = 'tower';
  campus.slice(S.tower, f);
  refreshFloor();
  const { pos, target } = towerCam(S.tower, f);
  world.flyTo(pos, target, 1.4, 'power2.inOut');
  renderCtx(); renderCard(); rebuildUnitLabels(); syncHash();
}
function selectUnit(id: string) {
  stopTour();
  realView.close();
  const u = UNIT_BY_ID.get(id);
  if (!u) return;
  if (S.tower !== u.tower || S.floor !== u.floor) {
    S.tower = u.tower; S.floor = u.floor;
    campus.slice(u.tower, u.floor);
  }
  S.unit = id; S.mode = 'unit';
  refreshFloor();
  const [x0, x1, y0, y1] = u.flat.rect;
  const c = toV((x0 + x1) / 2, (y0 + y1) / 2, GH + u.floor * FH);
  const { pos } = towerCam(u.tower, u.floor);
  const dir = pos.clone().sub(c).setY(0).normalize();
  const p = c.clone().addScaledVector(dir, IS_MOBILE ? 50 : 42).setY(c.y + (IS_MOBILE ? 44 : 30));
  const tg = c.clone();
  if (!IS_MOBILE) { const side = new THREE.Vector3(-dir.z, 0, dir.x); tg.addScaledVector(side, -8); } else tg.y -= 10;
  world.flyTo(p, tg, 1.4);
  renderCtx(); renderCard(); rebuildUnitLabels(); syncHash();
}
function refreshFloor() {
  campus.showFloorUnits(S.tower, S.floor, S.unit ?? undefined, S.hover ?? undefined);
}

async function openBalcony(id: string, view: number) {
  stopTour();
  const u = UNIT_BY_ID.get(id)!;
  if (S.mode === 'interior') interior.close();
  S.unit = id; S.tower = u.tower; S.floor = u.floor; S.view = view; S.mode = 'balcony';
  campus.slice(null, null);
  campus.showFloorUnits(null, null);
  renderAll();
  syncHash();
  const pose = campus.balconyPose(u, view);
  renderHud();
  context.clear.value = 0;
  realView.close();
  const srcs = realViewsFor(u.tower, u.floor, pose.dir as 'N' | 'S' | 'E' | 'W', u.tag.startsWith('Garden'));
  if (S.realIdx >= srcs.length) S.realIdx = 0;
  await balcony.enter(pose.pos, pose.look);
  if (S.mode !== 'balcony' || S.unit !== id) return;
  if (S.real && srcs.length && !srcs[0].nearest) await showReal();
  else { renderHud(); hint(t('lookAround')); }
}
async function showReal() {
  if (S.mode !== 'balcony' || !S.unit) return;
  const u = UNIT_BY_ID.get(S.unit)!;
  const pose = campus.balconyPose(u, S.view);
  const srcs = realViewsFor(u.tower, u.floor, pose.dir as 'N' | 'S' | 'E' | 'W', u.tag.startsWith('Garden'));
  if (!srcs.length) { renderHud(); return; }
  const cur = srcs[Math.min(S.realIdx, srcs.length - 1)];
  await realView.open(cur.src, cur.kind);
  renderHud();
  hint(t('lookAround'));
}
async function openInterior(type: 'A' | 'B' | 'C') {
  stopTour();
  realView.close();
  if (S.mode === 'balcony') balcony.exit();
  const prev = S.mode;
  S.mode = 'interior';
  renderAll();
  renderHud(type);
  await interior.open(type);
  if (S.mode !== 'interior') return;
  hint(t('dragHint'));
  void prev;
}
function closeOverlayMode() {
  realView.close();
  context.clear.value = 40;
  if (S.mode === 'balcony') balcony.exit();
  if (S.mode === 'interior') interior.close();
  S.mode = S.unit ? 'unit' : S.tower ? 'tower' : 'campus';
  if (S.tower && S.floor) campus.slice(S.tower, S.floor);
  refreshFloor();
  if (S.mode === 'unit' && S.unit) selectUnit(S.unit);
  renderAll();
  syncHash();
}

function renderHud(type?: string) {
  const h = $('#hud'), chips = $('#chips');
  if (S.mode === 'balcony' && S.unit) {
    const u = UNIT_BY_ID.get(S.unit)!;
    const pose = campus.balconyPose(u, S.view);
    const srcs = realViewsFor(u.tower, u.floor, pose.dir as 'N' | 'S' | 'E' | 'W', u.tag.startsWith('Garden'));
    const cur = srcs[Math.min(S.realIdx, srcs.length - 1)];
    const showingReal = realView.active && !!cur;
    h.classList.remove('hidden');
    chips.classList.remove('hidden');
    const diff = cur ? u.floor - cur.capFloor : 0;
    const note = !cur ? '' : cur.nearest ? t('nearestNote')
      : cur.capFloor === 0 ? t('groundNote')
      : Math.abs(diff) >= 3 ? `${t('capturedOn')} ${cur.capFloor} · ${Math.abs(diff * SITE.floorH).toFixed(0)} m ${diff < 0 ? t('lowerHere') : t('higherHere')}` : t('sameHeight');
    h.innerHTML = `<div><div class="eyebrow">${showingReal ? '📷 ' + t('realPhotoView') : t('realView')}</div><h3>${u.id} · ${L(VIEW3[pose.label] || pose.label)}</h3>
      <small>${t('floor')} ${u.floor} · ${u.heightM.toFixed(1)} m · ${t('facing')} <span class="heading" id="hdg">${L(DIR3[pose.dir])}</span></small>
      ${showingReal ? `<small class="capnote">${t('captured')}: ${cur.capTower === 'garden' ? t('gardenLevel') : `${t('tower')} ${cur.capTower}, ${t('floor')} ${cur.capFloor || 'G'}`} · 23 Nov 2026${note ? ' — ' + note : ''}</small>` : ''}</div>
      <button class="btn sm" id="hudX">${t('exitView')}</button>`;
    chips.innerHTML = (srcs.length ? `<button class="chip ${showingReal ? 'on' : ''}" id="toReal">📷 ${t('realPhotoView')}</button><button class="chip ${showingReal ? '' : 'on'}" id="to3d">3D · ${t('floor')} ${u.floor}</button>` : '') +
      u.flat.views.map((v, i) => `<button class="chip ${i === S.view ? 'on' : ''}" data-v="${i}">${L(VIEW3[v.label] || v.label)} · ${L(DIR3[v.dir])}</button>`).join('') +
      `<button class="chip" data-f="-1">▼ ${t('floor')}</button><button class="chip" data-f="1">▲ ${t('floor')}</button>` +
      (IS_MOBILE && showingReal ? `<button class="chip" id="gyro">📱 ${t('movePhone')}</button>` : '') +
      `<button class="chip" id="hud3d">${t('interior3d')}</button>`;
    chips.querySelectorAll<HTMLElement>('[data-v]').forEach((b) => (b.onclick = () => openBalcony(u.id, +b.dataset.v!)));
    chips.querySelectorAll<HTMLElement>('[data-f]').forEach((b) => (b.onclick = () => {
      const nf = THREE.MathUtils.clamp(u.floor + +b.dataset.f!, 1, NF);
      const nu = UNITS.find((x) => x.tower === u.tower && x.no === u.no && x.floor === nf)!;
      openBalcony(nu.id, Math.min(S.view, nu.flat.views.length - 1));
    }));
    const tr = document.getElementById('toReal'), t3 = document.getElementById('to3d'), gy = document.getElementById('gyro');
    if (tr) tr.onclick = () => { S.real = true; showReal(); };
    if (t3) t3.onclick = () => { S.real = false; realView.close(); renderHud(); };
    if (gy) gy.onclick = async () => { const ok = await realView.enableGyro(); toast(ok ? t('movePhone') : t('gyroNo')); };
    $('#hud3d').onclick = () => openInterior(u.type);
    $('#hudX').onclick = () => closeOverlayMode();
    $('#realPh').classList.add('hidden');
    const clip = photosForView(u.tower, u.floor, pose.dir as 'N' | 'S' | 'E' | 'W', u.tag.startsWith('Garden')).find((p) => p.video) || (srcs[0] && SITE_PHOTOS.find((p) => p.video && p.set === srcs[0].set));
    if (clip) {
      const vb = document.createElement('button');
      vb.className = 'chip';
      vb.textContent = '▶ ' + t('playClip');
      vb.onclick = () => lightbox(photoSrc(clip), photoCaption(clip));
      chips.insertBefore(vb, chips.children[2] || null);
    }
    balcony.onHeading = (deg) => {
      const el = document.getElementById('hdg');
      const names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
      if (el) el.textContent = `${names[Math.round(deg / 45) % 8]} · ${Math.round(deg)}°`;
      const cmp = document.getElementById('cmpN');
      if (cmp) cmp.parentElement!.style.transform = `rotate(${-deg}deg)`;
    };
    return;
  }
  $('#realPh').classList.add('hidden');
  if (S.mode === 'interior') {
    const ty = (type || UNIT_BY_ID.get(S.unit || '')?.type || 'A') as 'A' | 'B' | 'C';
    const P = PLANS[ty];
    h.classList.remove('hidden');
    chips.classList.remove('hidden');
    h.innerHTML = `<div><div class="eyebrow">${t('interior3d')} · ${P.label}</div><h3>2 BHK · ${Math.round(P.rooms.reduce((s, r) => s + (r.ft ? r.ft[0] * r.ft[1] : 0), 0))} sq ft</h3>
      <small>Furnished in the palette of the actual Vraj Platinum sample flat</small></div>
      <button class="btn sm" id="hudX">${t('close')}</button>`;
    chips.innerHTML = `<button class="chip on" id="ov">${t('overview')}</button>` + P.rooms.filter((r) => r.dim).map((r) => `<button class="chip" data-r="${r.id}">${room(r.name)}</button>`).join('') +
      (S.unit ? `<button class="chip" id="toBal">${t('balconyView')}</button>` : '');
    chips.querySelectorAll<HTMLElement>('[data-r]').forEach((b) => (b.onclick = () => {
      chips.querySelectorAll('.chip').forEach((x) => x.classList.remove('on'));
      b.classList.add('on');
      interior.focusRoom(b.dataset.r!);
    }));
    $('#ov').onclick = () => interior.overview();
    const tb = document.getElementById('toBal');
    if (tb) tb.onclick = () => { interior.close(); openBalcony(S.unit!, 0); };
    $('#hudX').onclick = () => closeOverlayMode();
    return;
  }
  h.classList.add('hidden');
  chips.classList.add('hidden');
  $('#realPh').classList.add('hidden');
  const cmp = document.getElementById('cmpN');
  if (cmp) cmp.parentElement!.style.transform = '';
}

// ------------------------------------------------------------------ drone tour
let touring = false;
const TOUR: { p: [number, number, number]; t: [number, number, number]; d: number; c: number }[] = [
  { p: [230, 170, 250], t: [0, 12, 0], d: 4.5, c: 0 },
  { p: [78, 7, 16], t: [40, 3.5, 0], d: 5, c: 1 },
  { p: [92, 38, -58], t: [27, 24, 0], d: 4.5, c: 2 },
  { p: [16, 10, 0], t: [-30, 7, 0], d: 5, c: 3 },
  { p: [-26, 13, 0], t: [-48, 9, 0], d: 4, c: 3 },
  { p: [-12, 74, 46], t: [-13, 47, 20], d: 5, c: 4 },
  { p: [-230, 130, -190], t: [0, 18, 0], d: 6, c: 5 },
];
async function droneTour() {
  if (touring) { stopTour(); return; }
  goCampus();
  touring = true;
  world.controls.enabled = false;
  renderDock();
  const cap = $('#tourCap');
  cap.classList.remove('hidden');
  for (const k of TOUR) {
    if (!touring) break;
    cap.textContent = L(TOUR3[k.c]);
    await world.flyTo(new THREE.Vector3(...k.p), new THREE.Vector3(...k.t), k.d, 'sine.inOut');
    if (!touring) break;
    await new Promise((r) => setTimeout(r, 900));
  }
  if (touring) { await world.flyTo(CAMPUS_POS, CAMPUS_TARGET, 4, 'sine.inOut'); stopTour(); }
}
function stopTour() {
  if (!touring) return;
  touring = false;
  world.stopFlight();
  world.controls.enabled = true;
  $('#tourCap').classList.add('hidden');
  renderDock();
}
canvas.addEventListener('pointerdown', () => { if (touring) stopTour(); });

// ------------------------------------------------------------------ 3D labels & picking
const labelLayer = $('#labels');
const towerLabels: { el: HTMLElement; tw: string; pos: THREE.Vector3 }[] = [];
function buildTowerLabels() {
  for (const tw of TOWERS) {
    const el = document.createElement('button');
    el.className = 'tlabel';
    el.innerHTML = `<span class="pin">${tw}</span><small></small>`;
    el.onclick = () => selectTower(tw);
    labelLayer.appendChild(el);
    const p = campus.towerCenter(tw);
    towerLabels.push({ el, tw, pos: new THREE.Vector3(p.x, GH + NF * FH + 9, p.z) });
  }
  updateTowerLabelText();
}
function updateTowerLabelText() {
  for (const l of towerLabels) {
    const i = towerInfo(l.tw);
    (l.el.querySelector('small') as HTMLElement).textContent = `Type ${i.types} · ${i.avail} ${t('available').toLowerCase()}`;
  }
}
const unitLabelEls: { el: HTMLElement; pos: THREE.Vector3 }[] = [];
function rebuildUnitLabels() {
  unitLabelEls.forEach((u) => u.el.remove());
  unitLabelEls.length = 0;
  if (!S.tower || !S.floor || S.mode === 'balcony' || S.mode === 'interior') return;
  for (const u of unitsOf(S.tower, S.floor)) {
    const el = document.createElement('button');
    el.className = 'ulabel';
    el.innerHTML = `<i class="dot ${u.status}"></i>${u.id.split('-')[1]} · ${u.type}`;
    el.onclick = () => selectUnit(u.id);
    labelLayer.appendChild(el);
    const [x0, x1, y0, y1] = u.flat.rect;
    unitLabelEls.push({ el, pos: toV((x0 + x1) / 2, (y0 + y1) / 2, GH + u.floor * FH + 0.6) });
  }
}
const pv = new THREE.Vector3();
world.onTick(() => {
  const w = innerWidth, h = innerHeight;
  const showT = S.mode === 'campus' && entered;
  for (const l of towerLabels) {
    pv.copy(l.pos).project(world.camera);
    const on = showT && pv.z < 1;
    l.el.style.display = on ? '' : 'none';
    if (on) l.el.style.transform = `translate(-50%,-100%) translate(${(pv.x * 0.5 + 0.5) * w}px, ${(-pv.y * 0.5 + 0.5) * h}px)`;
  }
  for (const l of unitLabelEls) {
    pv.copy(l.pos).project(world.camera);
    l.el.style.transform = `translate(-50%,-50%) translate(${(pv.x * 0.5 + 0.5) * w}px, ${(-pv.y * 0.5 + 0.5) * h}px)`;
    l.el.style.display = pv.z < 1 ? '' : 'none';
  }
  if (S.mode !== 'balcony') {
    const cmp = document.getElementById('cmpN')?.parentElement;
    if (cmp) {
      const off = world.camera.position.clone().sub(world.controls.target);
      const az = Math.atan2(off.x, off.z); // 0 when camera is south of target (looking north)
      cmp.style.transform = `rotate(${THREE.MathUtils.radToDeg(az)}deg)`;
    }
  }
  // gentle idle drift on campus overview
  if (S.mode === 'campus' && entered && Date.now() - lastInteract > 9000) {
    world.controls.autoRotate = true;
    world.controls.autoRotateSpeed = 0.35;
  } else world.controls.autoRotate = false;
});
let lastInteract = Date.now();
['pointerdown', 'wheel', 'keydown'].forEach((e) => addEventListener(e, () => (lastInteract = Date.now()), { passive: true }));

const ray = new THREE.Raycaster();
const ndc = new THREE.Vector2();
let downAt: { x: number; y: number; t: number } | null = null;
canvas.addEventListener('pointerdown', (e) => (downAt = { x: e.clientX, y: e.clientY, t: performance.now() }));
canvas.addEventListener('pointerup', (e) => {
  if (!downAt || S.mode === 'balcony' || S.mode === 'interior') return;
  const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
  if (moved > 6 || performance.now() - downAt.t > 600) return;
  const hit = pick(e.clientX, e.clientY);
  if (hit?.unit) selectUnit(hit.unit);
  else if (hit?.tower && hit.tower !== S.tower) selectTower(hit.tower);
  else if (hit?.tower && !S.floor) selectFloor(8);
});
canvas.addEventListener('pointermove', (e) => {
  if (IS_MOBILE || S.mode === 'balcony' || S.mode === 'interior' || e.buttons) return;
  const hit = pick(e.clientX, e.clientY);
  canvas.style.cursor = hit ? 'pointer' : 'grab';
  const hv = hit?.unit ?? null;
  if (hv !== S.hover) { S.hover = hv; refreshFloor(); }
  towerLabels.forEach((l) => l.el.classList.toggle('on', hit?.tower === l.tw));
});
function pick(x: number, y: number): { unit?: string; tower?: string } | null {
  ndc.set((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1);
  ray.setFromCamera(ndc, world.camera);
  if (campus.unitPick.length) {
    const h = ray.intersectObjects(campus.unitPick, false)[0];
    if (h) return { unit: h.object.userData.unit };
  }
  const h = ray.intersectObjects(campus.towerPick, false)[0];
  return h ? { tower: h.object.userData.tower } : null;
}
addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if ($('#modal').classList.contains('on')) closeModal();
    else if (S.mode === 'balcony' || S.mode === 'interior') closeOverlayMode();
    else if (S.unit) { S.unit = null; S.mode = 'tower'; refreshFloor(); renderAll(); }
    else if (S.tower) goCampus();
  }
  if (S.tower && S.floor && (e.key === 'ArrowUp' || e.key === 'ArrowDown') && S.mode !== 'balcony') {
    selectFloor(THREE.MathUtils.clamp(S.floor + (e.key === 'ArrowUp' ? 1 : -1), 1, NF));
  }
});

// ------------------------------------------------------------------ modals
function openModal(html: string) {
  $('#sheet').innerHTML = `<button class="x" id="mX" aria-label="${t('close')}">×</button>` + html;
  $('#modal').classList.add('on');
  $('#mX').onclick = closeModal;
  gsap.fromTo('#sheet', { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: 'power3.out' });
}
function closeModal() {
  $('#modal').classList.remove('on');
  $('#sheet').querySelectorAll('video').forEach((v) => v.pause());
}
$('#modal').addEventListener('click', (e) => { if (e.target === $('#modal')) closeModal(); });
function lightbox(src: string, cap = '') {
  const d = document.createElement('div');
  d.className = 'lightbox';
  d.innerHTML = src.endsWith('.mp4')
    ? `<video src="${src}" autoplay muted loop playsinline controls></video><p>${cap}</p>`
    : `<img src="${src}" alt=""><p>${cap}</p>`;
  d.onclick = (e) => { if ((e.target as HTMLElement).tagName !== 'VIDEO') d.remove(); };
  document.body.appendChild(d);
}
function photoCaption(p: SitePhoto) { return `${L(SET_INFO[p.set])} · 23 Nov 2026`; }

function openGallery(cat = 'site') {
  const siteLbl = t('siteToday');
  const cats = ['site', 'All', ...new Set(GALLERY.map((g) => g.cat))];
  const items = cat === 'site'
    ? SITE_PHOTOS.map((p) => ({ src: photoSrc(p), thumb: photoSrc(p, true), title: photoCaption(p), video: !!p.video }))
    : GALLERY.filter((g) => cat === 'All' || g.cat === cat).map((g) => ({ src: g.src, thumb: g.src, title: g.title, video: false }));
  openModal(`<div class="eyebrow">Vraj Platinum</div><h2>${t('gallery')}</h2>
    <div class="tabs">${cats.map((c) => `<button class="chip ${c === cat ? 'on' : ''}" data-c="${c}">${c === 'site' ? '📷 ' + siteLbl : c}</button>`).join('')}</div>
    <div class="grid-g">${items.map((g) => `<figure data-s="${g.src}" data-t="${g.title}"><img loading="lazy" src="${g.thumb}" alt="${g.title}">${g.video ? '<span class="play">▶</span>' : ''}<figcaption>${g.title}</figcaption></figure>`).join('')}</div>
    <p class="note">${cat === 'site' ? 'Actual photographs and clips taken on site, 23 November 2026.' : 'Artist’s impressions from the official Vraj Platinum brochure.'}</p>`);
  $('#sheet').querySelectorAll<HTMLElement>('[data-c]').forEach((b) => (b.onclick = () => openGallery(b.dataset.c!)));
  $('#sheet').querySelectorAll<HTMLElement>('figure').forEach((f) => (f.onclick = () => lightbox(f.dataset.s!, f.dataset.t)));
}

function openSampleFlat() {
  openModal(`<div class="eyebrow">${t('actualPhotos')}</div><h2>${t('sampleFlat')}</h2>
    <div class="sf">
      <video src="${SAMPLE_FLAT.video}" poster="${SAMPLE_FLAT.poster}" controls playsinline autoplay muted loop preload="metadata"></video>
      <div class="thumbs">${SAMPLE_FLAT.stills.map((s) => `<img loading="lazy" src="${s}" alt="Sample flat">`).join('')}</div>
    </div>
    <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap">
      <button class="btn primary" id="sf3d">${icon('cube')}${t('interior3d')} · Type A</button>
      <button class="btn" data-ty="B">${t('interior3d')} · Type B</button>
      <button class="btn" data-ty="C">${t('interior3d')} · Type C</button>
      <a class="btn" href="${waLink(undefined, ' I would like to visit the sample flat.')}" target="_blank" rel="noopener">${icon('wa')}Book a site visit</a>
    </div>
    <p class="note">Video recorded at the Vraj Platinum sample flat, Sarthana. The 3D interiors use the same finishes: white large-format tiles, burnt-orange upholstery, oak slat TV wall, black granite kitchen.</p>`);
  $('#sheet').querySelectorAll<HTMLImageElement>('.thumbs img').forEach((i) => (i.onclick = () => lightbox(i.src, t('sampleFlat'))));
  $('#sf3d').onclick = () => { closeModal(); openInterior('A'); };
  $('#sheet').querySelectorAll<HTMLElement>('[data-ty]').forEach((b) => (b.onclick = () => { closeModal(); openInterior(b.dataset.ty as 'A' | 'B' | 'C'); }));
}

function openLocation() {
  openModal(`<div class="eyebrow">${t('location')}</div><h2>Sarthana, Surat</h2>
    <div class="loc">
      <div><img src="/img/location-map.jpg" alt="Location map" style="cursor:zoom-in" id="locImg">
        <p class="note">${PROJECT.address}<br>${PROJECT.addressGu}</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <a class="btn primary" href="${PROJECT.mapsUrl}" target="_blank" rel="noopener">${icon('pin')}${t('directions')}</a>
          <a class="btn" href="tel:${PROJECT.phone}">${icon('phone')}${PROJECT.phoneDisplay}</a>
          <button class="btn" id="locAerial">${icon('eye')}Aerial view in 3D</button>
          <button class="btn" id="locGps">${icon('pin')}How far am I?</button>
        </div><p class="note" id="gpsOut"></p></div>
      <div><div class="eyebrow" style="margin-bottom:10px">${t('nearby')}</div>
        <div class="nearby">${NEARBY3.map((n) => `<div><span>${L(n.t)}</span><small>${L(n.note)}</small></div>`).join('')}</div>
        <p class="note">Landmarks as marked on the brochure’s location map. The 3D scene sits on live satellite imagery of the actual plot (21.2318° N, 72.9137° E).</p></div>
    </div>`);
  $('#locImg').onclick = () => lightbox('/img/location-map.jpg', 'Location map · Vraj Platinum');
  $('#locGps').onclick = () => {
    const out = $('#gpsOut');
    if (!navigator.geolocation) { out.textContent = 'Location is not available in this browser.'; return; }
    out.textContent = 'Finding you…';
    navigator.geolocation.getCurrentPosition((p) => {
      const R = 6371, toR = Math.PI / 180, la1 = p.coords.latitude * toR, la2 = SITE.geo.lat * toR;
      const dla = la2 - la1, dlo = (SITE.geo.lng - p.coords.longitude) * toR;
      const a = Math.sin(dla / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dlo / 2) ** 2;
      const km = 2 * R * Math.asin(Math.sqrt(a));
      const brg = (Math.atan2(Math.sin(dlo) * Math.cos(la2), Math.cos(la1) * Math.sin(la2) - Math.sin(la1) * Math.cos(la2) * Math.cos(dlo)) / toR + 360) % 360;
      const names = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
      out.innerHTML = `Vraj Platinum is <b>${km < 1 ? Math.round(km * 1000) + ' m' : km.toFixed(1) + ' km'}</b> to the ${names[Math.round(brg / 45) % 8]} of you (straight line). <a href="https://www.google.com/maps/dir/?api=1&origin=${p.coords.latitude},${p.coords.longitude}&destination=${SITE.geo.lat},${SITE.geo.lng}" target="_blank" rel="noopener">Route in Google Maps ↗</a>`;
    }, () => { out.textContent = 'Location permission was not granted.'; }, { enableHighAccuracy: true, timeout: 10000 });
  };
  $('#locAerial').onclick = () => { closeModal(); goCampus(); world.flyTo(toV(-120, -260, 520), new THREE.Vector3(0, 0, 0), 3); };
}

function openSpecs() {
  openModal(`<div class="eyebrow">Vraj Platinum</div><h2>${t('specs')}</h2>
    <p style="max-width:70ch;line-height:1.6;margin:0 0 16px">${L(ABOUT)}</p>
    <div class="stat-row" style="margin-bottom:12px"><span><b>6</b> ${t('towersW')}</span><span><b>G+14</b></span><span><b>336</b> ${t('homesW')}</span><span><b>3</b> ${t('planTypes')}</span><span><b>650 · 655 · 641</b> sq ft</span></div>
    <div class="eyebrow" style="margin:6px 0 10px">${t('highlights')}</div>
    <div class="amen">${HIGHLIGHTS3.map((h) => `<div>${icon('sun')}${L(h)}</div>`).join('')}</div>
    <div class="eyebrow" style="margin:22px 0 10px">${t('amenities')}</div>
    <div class="amen">${AMENITIES3.map((a) => `<div>${icon(a.icon)}${L(a.t)}</div>`).join('')}</div>
    <div class="cols" style="margin-top:22px">
      <div><div class="eyebrow">${t('external')}</div>${SPECS_EXT3.map(([k, v]) => `<div class="spec"><b>${L(k)}</b><span>${L(v)}</span></div>`).join('')}</div>
      <div><div class="eyebrow">${t('internal')}</div>${SPECS_INT3.map(([k, v]) => `<div class="spec"><b>${L(k)}</b><span>${L(v)}</span></div>`).join('')}</div>
    </div>
    <div class="eyebrow" style="margin:22px 0 10px">Team</div>
    <div class="amen">${PROJECT.team.map((m) => `<div><span><small class="muted">${m.role}</small><br><b>${m.name}</b></span></div>`).join('')}</div>
    <p class="note">Specifications translated from the Gujarati brochure. The developer may change specifications, plans and amenities; the final agreement prevails.</p>`);
}

function openPlan(u: Unit) {
  const P = PLANS[u.type];
  openModal(`<div class="eyebrow">${u.id} · ${P.label}</div><h2>${t('floorPlan')}</h2>
    <div class="cols"><div><img src="${PLAN_IMG[u.type]}" style="width:100%;border-radius:14px;background:#fff;cursor:zoom-in" id="planImg" alt="Plan"></div>
    <div><div class="eyebrow" style="margin-bottom:8px">${t('rooms')}</div>
      ${P.rooms.filter((r) => r.dim).map((r) => `<div class="spec"><b>${room(r.name)}</b><span>${r.dim} · ${(r.ft![0] * r.ft![1]).toFixed(0)} sq ft</span></div>`).join('')}
      <div class="spec"><b>Total</b><span><b>${u.roomArea} sq ft</b> (${u.roomAreaM2} m²) of room area</span></div>
      <p class="note">Room sizes are clear internal dimensions printed in the brochure. RERA carpet / super built-up area as per the developer’s agreement.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px"><button class="btn primary" id="p3d">${icon('cube')}${t('interior3d')}</button><button class="btn" id="pBal">${icon('eye')}${t('balconyView')}</button></div>
    </div></div>`);
  $('#planImg').onclick = () => lightbox(PLAN_IMG[u.type], `${P.label} plan`);
  $('#p3d').onclick = () => { closeModal(); openInterior(u.type); };
  $('#pBal').onclick = () => { closeModal(); openBalcony(u.id, 0); };
}

function openCost(u: Unit) {
  const st = { val: PROJECT.commercial.defaultAgreementLakh * 1e5, woman: false, ready: !PROJECT.commercial.underConstruction, loanPct: 80, rate: 8.5, yrs: 20 };
  openModal(`<div class="eyebrow">${u.id} · Type ${u.type} · ${u.roomArea} sq ft room area</div><h2>${t('costSheet')}</h2>
    <div class="cols calc"><div>
      <label>${t('agreement')} <span class="val" id="vVal"></span></label><input type="range" id="iVal" min="2000000" max="7000000" step="25000" value="${st.val}">
      <div class="toggle"><input type="checkbox" id="iWoman"><label for="iWoman" style="margin:0">${t('womanBuyer')} (registration fee waived)</label></div>
      <div class="toggle"><input type="checkbox" id="iReady"><label for="iReady" style="margin:0">${t('ready')} (no GST)</label></div>
      <div id="rows" style="margin-top:14px"></div>
    </div><div>
      <label>${t('loan')} <span class="val" id="vLoan"></span></label><input type="range" id="iLoan" min="0" max="90" step="5" value="${st.loanPct}">
      <label>${t('rate')} <span class="val" id="vRate"></span></label><input type="range" id="iRate" min="6.5" max="12" step="0.05" value="${st.rate}">
      <label>${t('tenure')} <span class="val" id="vYrs"></span></label><input type="range" id="iYrs" min="5" max="30" step="1" value="${st.yrs}">
      <div id="emi" style="margin-top:16px"></div>
      <a class="btn primary" id="cWa" target="_blank" rel="noopener" style="margin-top:12px;width:100%">${icon('wa')}Request official price sheet</a>
    </div></div>
    <p class="note">Indicative calculator. The agreement value above is an example — prices are set by the developer. Gujarat stamp duty 4.9% and registration 1% (waived for a sole woman buyer). GST on under-construction homes: 1% when carpet area ≤ 90 m² and value ≤ ₹45 lakh (affordable housing), otherwise 5%; nil on ready possession with completion certificate. Not legal or financial advice.</p>`);
  const q = (id: string) => document.getElementById(id) as HTMLInputElement;
  const upd = () => {
    st.val = +q('iVal').value; st.woman = q('iWoman').checked; st.ready = q('iReady').checked;
    st.loanPct = +q('iLoan').value; st.rate = +q('iRate').value; st.yrs = +q('iYrs').value;
    const affordable = u.roomAreaM2 <= 90 && st.val <= 4500000;
    const gstPct = st.ready ? 0 : affordable ? 1 : 5;
    const gst = st.val * gstPct / 100, stamp = st.val * 0.049, reg = st.woman ? 0 : st.val * 0.01;
    const total = st.val + gst + stamp + reg;
    q('vVal').textContent = lakh(st.val);
    document.getElementById('rows')!.innerHTML = `
      <div class="row"><span>${t('agreement')}</span><b>${fmtINR(st.val)}</b></div>
      <div class="row"><span>${t('gst')} (${gstPct}%)</span><b>${fmtINR(gst)}</b></div>
      <div class="row"><span>${t('stamp')}</span><b>${fmtINR(stamp)}</b></div>
      <div class="row"><span>${t('registration')}</span><b>${fmtINR(reg)}</b></div>
      <div class="row total"><span>${t('total')}</span><span>${lakh(total)}</span></div>`;
    const P = st.val * st.loanPct / 100, r = st.rate / 1200, n = st.yrs * 12;
    const emi = r ? (P * r * (1 + r) ** n) / ((1 + r) ** n - 1) : P / n;
    q('vLoan').textContent = `${st.loanPct}% · ${lakh(P)}`;
    q('vRate').textContent = `${st.rate.toFixed(2)}%`;
    q('vYrs').textContent = `${st.yrs} ${t('years')}`;
    document.getElementById('emi')!.innerHTML = `
      <div class="row total"><span>${t('emi')}</span><span>${fmtINR(emi)}</span></div>
      <div class="row"><span>Down payment + charges</span><b>${lakh(total - P)}</b></div>
      <div class="row"><span>Total interest</span><b>${lakh(emi * n - P)}</b></div>`;
    (document.getElementById('cWa') as HTMLAnchorElement).href = waLink(u, ` My budget is around ${lakh(st.val)}.`);
  };
  ['iVal', 'iWoman', 'iReady', 'iLoan', 'iRate', 'iYrs'].forEach((i) => q(i).addEventListener('input', upd));
  q('iReady').checked = st.ready;
  upd();
}

function openResidences() {
  const f = { tower: 'all', type: 'all', facing: 'all', avail: true, minF: 1, maxF: 14 };
  const tags = [...new Set(UNITS.map((u) => u.tag))];
  openModal(`<div class="eyebrow">336 homes · 6 towers</div><h2>${t('filters')}</h2>
    <div class="res-filters">
      <select id="fT"><option value="all">${t('allTowers')}</option>${TOWERS.map((x) => `<option>${x}</option>`).join('')}</select>
      <select id="fY"><option value="all">${t('anyType')}</option><option value="A">Type A</option><option value="B">Type B</option><option value="C">Type C</option></select>
      <select id="fV"><option value="all">${t('anyFacing')}</option>${tags.map((x) => `<option value="${x}">${L(TAG3[x] || x)}</option>`).join('')}</select>
      <select id="fF"><option value="1-14">${t('floorsRange')} 1–14</option><option value="1-5">1–5</option><option value="6-10">6–10</option><option value="11-14">11–14</option></select>
      <label class="toggle" style="margin:0"><input type="checkbox" id="fA" checked>${t('onlyAvailable')}</label>
      <span class="muted" id="fCount" style="margin-left:auto;font-size:13px"></span>
    </div>
    <div style="max-height:58vh;overflow:auto"><table class="res-table"><thead><tr><th>Flat</th><th>${t('floor')}</th><th>${t('type')}</th><th class="hide-m">${t('roomArea')}</th><th class="hide-m">${t('facing')}</th><th>Status</th><th></th></tr></thead><tbody id="fBody"></tbody></table></div>
    ${shortlist.size ? `<p class="note">♥ ${t('shortlist')}: ${[...shortlist].join(', ')}</p>` : ''}`);
  const q = (id: string) => document.getElementById(id) as HTMLInputElement & HTMLSelectElement;
  const upd = () => {
    f.tower = q('fT').value; f.type = q('fY').value; f.facing = q('fV').value; f.avail = q('fA').checked;
    [f.minF, f.maxF] = q('fF').value.split('-').map(Number);
    const list = UNITS.filter((u) => (f.tower === 'all' || u.tower === f.tower) && (f.type === 'all' || u.type === f.type) &&
      (f.facing === 'all' || u.tag === f.facing) && (!f.avail || u.status === 'available') && u.floor >= f.minF && u.floor <= f.maxF)
      .sort((a, b) => a.tower.localeCompare(b.tower) || b.floor - a.floor || a.no.localeCompare(b.no));
    q('fCount').textContent = `${list.length} ${t('results')}`;
    document.getElementById('fBody')!.innerHTML = list.slice(0, 200).map((u) => `<tr>
      <td><b>${u.id}</b>${shortlist.has(u.id) ? ' ♥' : ''}</td><td>${u.floor}</td><td>${u.type}</td><td class="hide-m">${u.roomArea} sq ft</td><td class="hide-m">${L(DIR3[u.facing])} · ${L(TAG3[u.tag])}</td>
      <td><i class="dot ${u.status}"></i> ${t(u.status)}</td><td><button class="btn sm" data-u="${u.id}">${t('view')}</button></td></tr>`).join('');
    document.querySelectorAll<HTMLElement>('#fBody [data-u]').forEach((b) => (b.onclick = () => { closeModal(); if (S.mode === 'balcony' || S.mode === 'interior') closeOverlayMode(); selectUnit(b.dataset.u!); }));
  };
  ['fT', 'fY', 'fV', 'fF', 'fA'].forEach((i) => q(i).addEventListener('input', upd));
  upd();
}

function openEnquiry() {
  const u = S.unit ? UNIT_BY_ID.get(S.unit) : undefined;
  openModal(`<div class="eyebrow">Vraj Group · ${PROJECT.phoneDisplay}</div><h2>${t('enquire')}</h2>
    <div class="cols"><div>
      <div class="field"><label>${t('name')}</label><input id="eN" autocomplete="name"></div>
      <div class="field"><label>${t('phone')}</label><input id="eP" inputmode="tel" autocomplete="tel"></div>
      <div class="field"><label>Interested in</label><select id="eU"><option>${u ? u.id : 'Any 2 BHK'}</option>${[...shortlist].map((s) => `<option>${s}</option>`).join('')}<option>Site visit</option></select></div>
      <button class="btn primary" id="eGo" style="width:100%">${icon('wa')}${t('send')}</button>
      <p class="note">Opens WhatsApp with your message to the Vraj Platinum sales desk. Nothing is stored on this website.</p>
    </div><div>
      <img src="/img/entrance.jpg" style="width:100%;border-radius:14px" alt="">
      <p class="note">${PROJECT.address}</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><a class="btn" href="tel:${PROJECT.phone}">${icon('phone')}${t('call')}</a><a class="btn" href="${PROJECT.mapsUrl}" target="_blank" rel="noopener">${icon('pin')}${t('directions')}</a></div>
    </div></div>`);
  $('#eGo').onclick = () => {
    const n = (document.getElementById('eN') as HTMLInputElement).value.trim();
    const p = (document.getElementById('eP') as HTMLInputElement).value.trim();
    const which = (document.getElementById('eU') as HTMLSelectElement).value;
    const msg = `Hello, I am ${n || '—'} (${p || '—'}). I am interested in Vraj Platinum: ${which}. Please share details.`;
    window.open(`https://wa.me/${PROJECT.phone.replace('+', '')}?text=${encodeURIComponent(msg)}`, '_blank', 'noopener');
  };
}

// ------------------------------------------------------------------ routing (#/tower/D/7/D-703/balcony/0)
function syncHash() {
  let h = '#/';
  if (S.tower) h += `tower/${S.tower}`;
  if (S.floor) h += `/${S.floor}`;
  if (S.unit) h += `/${S.unit}`;
  if (S.mode === 'balcony') h += `/balcony/${S.view}`;
  if (S.mode === 'interior') h += '/interior';
  if (location.hash !== h) history.replaceState(null, '', h);
}
function route() {
  const p = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  if (p[0] === 'tower' && p[1] && TOWERS.includes(p[1])) {
    const f = p[2] ? +p[2] : null;
    if (p[3] && UNIT_BY_ID.has(p[3])) {
      selectUnit(p[3]);
      if (p[4] === 'balcony') openBalcony(p[3], +(p[5] || 0));
      if (p[4] === 'interior') openInterior(UNIT_BY_ID.get(p[3])!.type);
    } else selectTower(p[1], f && f >= 1 && f <= NF ? f : null);
  } else goCampus();
}

// ------------------------------------------------------------------ boot
function renderAll() {
  renderNav(); renderCtx(); renderCard(); renderDock(); renderHud();
  rebuildUnitLabels(); updateTowerLabelText();
  ldText.textContent = entered ? ldText.textContent : t('loading');
  enterBtn.textContent = t('enter');
  document.documentElement.lang = getLang();
}
document.documentElement.lang = getLang();
setHour(10); // morning sun on the road (east) and garden (south) faces the default views look at
renderAll();
world.renderer.domElement.addEventListener('webglcontextlost', (e) => { e.preventDefault(); toast('Graphics paused — tap to reload'); setTimeout(() => location.reload(), 1500); });
(window as unknown as { vp: unknown }).vp = { world, campus, ground, context, trees, S, droneTour, stopTour, selectUnit, openBalcony, openInterior, goCampus, setHour, selectTower, selectFloor };
