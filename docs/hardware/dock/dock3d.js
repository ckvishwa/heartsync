import * as THREE from 'three';
import { RoundedBoxGeometry } from './RoundedBoxGeometry.js';

// Dock rev E. Model mm: X across (+right), Y depth (front 0 -> back 95), Z up (deck top 18).
// three: x = X, y = Z, z = -(Y - 47.5)
export const D = {
  L: 195, W: 124, H: 14, R: 20, RF: 8,
  col: [-35, 102], colW: 62, colD: 40, colH: 146,
  puckZ: 132, bay: [36, 111], bayW: 50, bayD: 24, bayH: 26,
  buds: [38, 72], ports: [['A', 60, 13.7, 6.3], ['C', 74, 10.8, 4.2], ['C', 88, 10.8, 4.2]], usbIn: 70, led: 0,
  dev: { back: 40, ring: 1.5, T: 32.8, L: 185, Hh: 72.5 }, pogoX: [-12, -4, 4, 12], magX: [-70, -32, 32, 70],
};
const P = (x, y, z) => new THREE.Vector3(x, z, -(y - D.W / 2));
const mat = (color, rough = 0.85, metal = 0, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
function rrShape(w, d, r, rf) {
  rf = rf === undefined ? r : rf;   // rf: front corners (shape -y), r: back corners
  const s = new THREE.Shape(), x = -w / 2, y = -d / 2;
  s.moveTo(x + rf, y); s.lineTo(x + w - rf, y); s.absarc(x + w - rf, y + rf, rf, -Math.PI / 2, 0); s.lineTo(x + w, y + d - r);
  s.absarc(x + w - r, y + d - r, r, 0, Math.PI / 2); s.lineTo(x + r, y + d); s.absarc(x + r, y + d - r, r, Math.PI / 2, Math.PI);
  s.lineTo(x, y + rf); s.absarc(x + rf, y + rf, rf, Math.PI, Math.PI * 1.5); return s;
}
// extruded rounded rect: footprint w (X) x d (Y), from z0 to z0 + h, centred at model (cx, cy)
function slab(g, cx, cy, w, d, r, z0, h, m, bevel = 1.5, rf) {
  const geo = new THREE.ExtrudeGeometry(rrShape(w - 2 * bevel, d - 2 * bevel, Math.max(r - bevel, 0.5), rf === undefined ? undefined : Math.max(rf - bevel, 0.5)), { depth: h - 2 * bevel, bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 3, curveSegments: 32 });
  geo.rotateX(-Math.PI / 2); geo.translate(0, bevel, 0);
  const mesh = new THREE.Mesh(geo, m); const p = P(cx, cy, z0); mesh.position.copy(p); g.add(mesh); return mesh;
}
const shadowAll = o => o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });

export function buildDock(opts = {}) {
  const g = new THREE.Group();
  const shell = mat('#D9CFC1', 0.75), shellD = mat('#CFC4B5', 0.8), trayTop = mat('#C9BEAE', 0.95);
  const { L, W, H, R } = D;
  slab(g, 0, W / 2, L, W, R, 0, H, shell, 2, D.RF);
  slab(g, 0, W / 2, L - 3, W - 3, R - 1.5, H - 0.8, 1.2, trayTop, 0.4, D.RF - 1.5);
  // buds oval
  const pad = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1.2, 48), mat('#BDB2A2', 0.95));
  pad.scale.set(33, 1, 25.5); pad.position.copy(P(D.buds[0], D.buds[1], H + 0.2)); g.add(pad);
  // front light + ports + power in
  const led = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 16), mat('#F5B041', 0.3, 0, { emissive: '#F5A623', emissiveIntensity: 1.2 }));
  led.rotation.x = Math.PI / 2; led.position.copy(P(D.led, -0.2, 7)); g.add(led);
  for (const [, y, w, h] of D.ports) {
    const pm = new THREE.Mesh(new RoundedBoxGeometry(1, h, w, 2, Math.min(1.8, h / 2 - 0.1)), mat('#2a2a2a', 0.4, 0.3));
    pm.position.copy(P(L / 2 + 0.05, y, 7)); g.add(pm);
  }
  const pin = new THREE.Mesh(new RoundedBoxGeometry(10.8, 4.2, 1, 2, 1.8), mat('#2a2a2a', 0.4, 0.3)); pin.position.copy(P(D.usbIn, W + 0.05, 7)); g.add(pin);
  // column (stadium 62 x 40)
  slab(g, D.col[0], D.col[1], D.colW, D.colD, D.colD / 2, H, D.colH, shellD, 2.5);
  // phone puck on the front
  const front = D.col[1] - D.colD / 2;
  const pk = new THREE.Mesh(new THREE.CylinderGeometry(31, 31, 8, 64), shell); pk.rotation.x = Math.PI / 2; pk.position.copy(P(D.col[0], front - 4, D.puckZ)); g.add(pk);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(27.5, 0.6, 8, 64), mat('#B8AB97', 0.9)); ring.position.copy(P(D.col[0], front - 8.1, D.puckZ)); g.add(ring);
  if (opts.phone !== false) {
    const portrait = !!opts.portrait, pw = portrait ? 78 : 163, ph = portrait ? 163 : 78;
    const phone = new THREE.Mesh(new RoundedBoxGeometry(pw, ph, 8.3, 6, 8), mat('#D8D8DC', 0.3, 0.7)); phone.position.copy(P(D.col[0], front - 12.2, D.puckZ)); g.add(phone);
    const tex = canvasTex(portrait ? 780 : 1630, portrait ? 1630 : 780, (c, w, h) => {
      c.fillStyle = '#000'; c.fillRect(0, 0, w, h); c.textAlign = 'center'; c.textBaseline = 'middle';
      if (portrait) {
        c.fillStyle = '#E8DCC8'; c.font = '600 230px IBM Plex Sans, Arial'; c.fillText('9:41', w / 2, h * 0.22);
        c.font = '500 56px IBM Plex Sans, Arial'; c.fillStyle = '#ccc'; c.fillText('Friday 20 November', w / 2, h * 0.12);
        c.fillStyle = '#7CD67C'; c.font = '600 60px IBM Plex Sans, Arial'; c.fillText('Charging · 86 %', w / 2, h * 0.9);
      } else {
        c.fillStyle = '#E8DCC8'; c.font = '700 470px IBM Plex Sans, Arial'; c.fillText('9:41', w * 0.4, h * 0.53);
        c.textAlign = 'left'; c.font = '500 70px IBM Plex Sans, Arial'; c.fillText('FRI 20', w * 0.74, h * 0.25); c.fillText('6:30AM', w * 0.74, h * 0.72);
      }
    });
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(pw - 7, ph - 7), new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: '#fff', emissiveIntensity: 0.8, roughness: 0.15 }));
    scr.position.copy(P(D.col[0], front - 16.4, D.puckZ)); g.add(scr);
  }
  // band bay (WHOOP PowerPack / Basic Charger, Fitbit clip) on the tray, back-right
  const [bx, by] = D.bay, bw = D.bayW, bd = D.bayD, bh = D.bayH, t = 2;
  const bayM = shellD;
  slab(g, bx, by + bd / 2 - t / 2, bw, t, 1, H, bh, bayM, 0.6);
  slab(g, bx, by - bd / 2 + t / 2, bw, t, 1, H, bh - 8, bayM, 0.6);
  slab(g, bx - bw / 2 + t / 2, by, t, bd, 1, H, bh, bayM, 0.6);
  slab(g, bx + bw / 2 - t / 2, by, t, bd, 1, H, bh, bayM, 0.6);
  const floor = new THREE.Mesh(new THREE.BoxGeometry(bw - 2 * t, 1.5, bd - 2 * t), mat('#3a3a3a', 0.9)); floor.position.copy(P(bx, by, H + 0.75)); g.add(floor);
  if (opts.band !== false) {
    const pp = new THREE.Mesh(new RoundedBoxGeometry(43, 36, 17, 5, 6), mat('#1c1c1e', 0.45, 0.2)); pp.position.copy(P(bx, by, H + 1.5 + 18)); g.add(pp);
    const led2 = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 0.6, 12), mat('#4CD964', 0.3, 0, { emissive: '#4CD964', emissiveIntensity: 1.5 }));
    led2.rotation.x = Math.PI / 2; led2.position.copy(P(bx + 14, by - 8.6, H + 1.5 + 26)); g.add(led2);
    const strap = new THREE.Mesh(new THREE.TorusGeometry(1, 0.09, 10, 64), mat('#7A8B6E', 0.85));
    strap.scale.set(30, 30, 30); strap.rotation.x = Math.PI / 2; strap.position.copy(P(bx - 2, by + 2, H + bh + 1)); g.add(strap);
  }
  // ---- HeartSync landing strip (no walls): 0.8 mm recess, 4 pogo pins, 4 magnets under the skin ----
  const dv = D.dev, back = dv.back, pogoY = back - dv.ring - 16.8, magY = back - dv.ring - 10;
  const strip = new THREE.Mesh(new RoundedBoxGeometry(187, 0.6, back - 3, 2, 0.25), mat('#BFB3A3', 0.95)); strip.position.copy(P(0, (back + 3) / 2, H + 0.05)); g.add(strip);
  for (const x of D.pogoX) { const pp = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 1.2, 16), mat('#C9A227', 0.3, 0.9)); pp.position.copy(P(x, pogoY, H + 0.6)); g.add(pp); }
  for (const x of D.magX) { const mm = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 0.2, 24), mat('#A39B8E', 0.9)); mm.position.copy(P(x, magY, H + 0.4)); g.add(mm); }
  if (opts.device !== false) {
    const dev = new THREE.Group(); g.add(dev);
    const y1 = back - dv.ring, y0 = y1 - dv.T, z0 = H + 0.1, z1 = z0 + dv.Hh;
    const shellM = mat('#1D1D1D', 0.5), fab = mat('#CBBFAE', 0.95);
    const b = new THREE.Mesh(new RoundedBoxGeometry(dv.L, dv.Hh, dv.T, 4, 5), shellM); b.position.copy(P(0, (y0 + y1) / 2, (z0 + z1) / 2)); dev.add(b);
    const f = new THREE.Mesh(new RoundedBoxGeometry(dv.L - 0.6, dv.Hh - 0.6, 1, 2, 0.4), fab); f.position.copy(P(0, y0 + 0.2, (z0 + z1) / 2)); dev.add(f);
    const rg = new THREE.Mesh(new RoundedBoxGeometry(dv.L - 6, dv.Hh - 6, dv.ring, 2, 0.6), mat('#3a3a3a', 0.9)); rg.position.copy(P(0, y1 + dv.ring / 2, (z0 + z1) / 2)); dev.add(rg);
    const disp = canvasTex(1024, 288, (c, w, h) => {
      c.fillStyle = '#040404'; c.fillRect(0, 0, w, h); c.fillStyle = '#F5A623'; c.font = '600 120px IBM Plex Sans, Arial';
      c.textAlign = 'center'; c.textBaseline = 'middle'; c.shadowColor = '#F5A623'; c.shadowBlur = 18; c.fillText('I miss you ♥', w / 2, h / 2);
    });
    const win = new THREE.Mesh(new THREE.PlaneGeometry(79.8, 22.2), new THREE.MeshStandardMaterial({ map: disp, emissiveMap: disp, emissive: '#fff', emissiveIntensity: 0.9, roughness: 0.2 }));
    win.position.copy(P(-46, y0 - 0.35, z0 + 36.25 + 4)); dev.add(win);
    const qr = new THREE.Mesh(new THREE.TorusGeometry(27.5, 0.5, 8, 64), mat('#B8AB97', 0.9)); qr.position.copy(P(45, y0 - 0.35, z0 + 36.25)); dev.add(qr);
    for (let i = 0; i < 5; i++) { const bt = new THREE.Mesh(new RoundedBoxGeometry(5.2, 1, 4.6, 2, 0.4), mat('#CBBFAE', 0.8)); bt.position.copy(P(-68 + 9.8 * i, y0 + 16, z1 + 0.4)); dev.add(bt); }
    for (const [xc, w] of [[38.5, 13.7], [52.75, 10.8], [66.05, 10.8]]) { const pt = new THREE.Mesh(new THREE.BoxGeometry(w, 0.6, 4.5), mat('#555', 0.4, 0.6)); pt.position.copy(P(xc, y0 + 16, z1 + 0.2)); dev.add(pt); }
  }
  if (opts.buds !== false) {
    const bc = new THREE.Mesh(new RoundedBoxGeometry(60.6, 21.7, 45.2, 6, 10), mat('#F4F4F2', 0.35));
    bc.position.copy(P(D.buds[0], D.buds[1], H + 0.2 + 10.85)); g.add(bc);
  }
  shadowAll(g);
  return g;
}

export function makeScene(canvas, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(opts.bg || '#ECEAE3');
  const cam = new THREE.PerspectiveCamera(32, 1, 1, 5000); cam.position.set(260, 230, 420);
  scene.add(new THREE.HemisphereLight('#ffffff', '#8a8578', 1.2));
  const key = new THREE.DirectionalLight('#ffffff', 2.4); key.position.set(200, 400, 300); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -250, right: 250, top: 250, bottom: -250, near: 10, far: 1200 });
  key.shadow.camera.updateProjectionMatrix(); scene.add(key);
  const fill = new THREE.DirectionalLight('#ffe9d0', 0.6); fill.position.set(-300, 150, 200); scene.add(fill);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), new THREE.ShadowMaterial({ opacity: 0.18 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const dock = buildDock(opts); scene.add(dock);
  return { renderer, scene, cam, dock, THREE };
}
