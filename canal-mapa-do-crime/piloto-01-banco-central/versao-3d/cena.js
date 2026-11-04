// =====================================================================
// Caso 01 — O Furto do Banco Central (Fortaleza, 2005) — versão 3D
// Maquete noturna da quadra + subsolo em "raio-X". 1 unidade = 1 metro.
// x = leste (casa -> banco), y = cima, z = sul (lado da câmera).
// Representação ilustrativa: geometria simplificada, fora de escala real.
// =====================================================================
import {
  THREE, scene, camera, C, W, H, g, clamp, lerp, seg, eio, eout, rng, v3, lerpV,
  sceneAt, P, TL, setCam, camPath, toScreen, mat, canvasTex, signMesh, makeGuy, poseGuy,
  txt, tag, tag3D, counter, dim3D, brl, hud, caption, vignette, run,
} from 'engine';

/* ---------- luz e atmosfera ---------- */
const hemi = new THREE.HemisphereLight('#9fb4e8', '#2a1d14', 1.15); scene.add(hemi);
const moon = new THREE.DirectionalLight('#c4d2ff', 1.5); moon.position.set(-90, 140, 110); scene.add(moon);
const fill = new THREE.DirectionalLight('#ffb070', .35); fill.position.set(120, 40, -60); scene.add(fill);
scene.fog = new THREE.Fog('#070a12', 220, 560);

/* ---------- materiais "da frente" (ficam transparentes no raio-X) ---------- */
const ZC = -0.8;                 // plano de corte: tudo com z > ZC some no raio-X
const FADE = [];
function fmat(color, o = {}) { const m = mat(color, { transparent: true, opacity: 1, ...o }); FADE.push(m); return m; }
function setFade(a) { for (const m of FADE) { m.opacity = a * (m.userData.base ?? 1); m.depthWrite = a > .98; } }

/* ---------- solo (bloco da maquete) ---------- */
const strata = canvasTex(1024, 256, (x, w, h) => {
  const gr = x.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#6b4a30'); gr.addColorStop(.25, '#5a3d27'); gr.addColorStop(.7, '#3f2b1d'); gr.addColorStop(1, '#2a1d14');
  x.fillStyle = gr; x.fillRect(0, 0, w, h); const r = rng(4);
  for (let i = 0; i < 9; i++) { x.strokeStyle = 'rgba(0,0,0,.18)'; x.lineWidth = 2; x.beginPath(); for (let px = 0; px <= w; px += 16) { const py = 20 + i * 26 + Math.sin(px * .02 + i) * 4; px ? x.lineTo(px, py) : x.moveTo(px, py); } x.stroke(); }
  for (let i = 0; i < 900; i++) { x.fillStyle = r() > .5 ? 'rgba(255,220,180,.10)' : 'rgba(0,0,0,.18)'; x.fillRect(r() * w, r() * h, 2 + r() * 3, 2 + r() * 3); }
}, [6, 1]);
const soilSide = mat('#4a3322');
const soilCut = mat('#ffffff', { map: strata });
const X0 = -200, X1 = 220, Z0 = -160, Z1 = 140, DEPTH = 14;
{ // bloco de trás: a face +z é o "corte" com estratos
  const geo = new THREE.BoxGeometry(X1 - X0, DEPTH, ZC - Z0);
  const m = new THREE.Mesh(geo, [soilSide, soilSide, soilSide, soilSide, soilCut, soilSide]);
  m.position.set((X0 + X1) / 2, -DEPTH / 2, (Z0 + ZC) / 2); scene.add(m);
  const front = new THREE.Mesh(new THREE.BoxGeometry(X1 - X0, DEPTH, Z1 - ZC), fmat('#4a3322'));
  front.position.set((X0 + X1) / 2, -DEPTH / 2 - .01, (ZC + Z1) / 2); scene.add(front);
}

/* ---------- ruas e quadras ---------- */
const asphaltB = mat('#252a33'), asphaltF = fmat('#252a33');
const walkB = mat('#3b424e'), walkF = fmat('#3b424e');
function slab(x0, x1, z0, z1, y, h, mb, mf) { // divide no plano de corte
  const parts = z1 <= ZC ? [[z0, z1, mb]] : z0 >= ZC ? [[z0, z1, mf]] : [[z0, ZC, mb], [ZC, z1, mf]];
  for (const [a, b2, m] of parts) { const me = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, h, b2 - a), m); me.position.set((x0 + x1) / 2, y + h / 2, (a + b2) / 2); scene.add(me); }
}
slab(X0, X1, Z0, Z1, -.02, .04, asphaltB, asphaltF);
const XS = [[X0, -78], [-64, 30], [46, 150], [162, X1]], ZS = [[Z0, -72], [-58, 60], [72, Z1]];
for (const [a, b2] of XS) for (const [c, d] of ZS) slab(a, b2, c, d, 0, .18, walkB, walkF);
// faixas da avenida
const lineM = fmat('#c9a227', { emissive: '#c9a227', emissiveIntensity: .4 });
for (let z = Z0; z < Z1; z += 9) { const l = new THREE.Mesh(new THREE.BoxGeometry(.25, .03, 4), lineM); l.position.set(38, .03, z); scene.add(l); }

/* ---------- prédios genéricos (com janelas acesas) ---------- */
const winTex = [0, 1, 2].map(k => canvasTex(256, 256, (x, w, h) => {
  x.fillStyle = '#000'; x.fillRect(0, 0, w, h); const r = rng(10 + k);
  for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) { x.fillStyle = r() > .7 ? (r() > .5 ? '#ffcf7a' : '#ffe3a8') : '#0b0e14'; x.fillRect(i * 64 + 20, j * 64 + 16, 24, 32); }
}, [1, 1]));
const OCC = [[-64, -6, -9, 9], [44, 132, -48, 44], [-135, -60, -12, 48], [-20, 30, 0, 60]]; // casa e banco: não colocar prédios aqui
{
  const r = rng(21); const cols = ['#5d6577', '#6a7186', '#6b6577', '#5f5a55', '#707a8c'];
  for (const [a, b2] of XS) for (const [c, d] of ZS) {
    let x = a + 3; while (x < b2 - 8) {
      const w = 9 + r() * 14; let z = c + 3;
      while (z < d - 8) {
        const dz = 9 + r() * 14, hgt = 5 + r() * 26, x0 = x, x1 = Math.min(x + w, b2 - 3), z0 = z, z1 = Math.min(z + dz, d - 3);
        const hit = OCC.some(([ox0, ox1, oz0, oz1]) => x1 > ox0 && x0 < ox1 && z1 > oz0 && z0 < oz1);
        if (!hit && r() > .12) {
          const col = cols[Math.floor(r() * cols.length)], wt = winTex[Math.floor(r() * 3)].clone(); wt.repeat.set(Math.max(1, Math.round((x1 - x0) / 14)), Math.max(1, Math.round(hgt / 12))); wt.needsUpdate = true;
          const front = z1 > ZC; const m = (front ? fmat : mat)(col, { emissive: '#ffffff', emissiveMap: wt, emissiveIntensity: .55 });
          const b3 = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, hgt, z1 - z0), m); b3.position.set((x0 + x1) / 2, hgt / 2 + .18, (z0 + z1) / 2); scene.add(b3);
        }
        z += dz + 2;
      }
      x += w + 2;
    }
  }
}

/* ---------- postes ---------- */
{ const pm = fmat('#6b7280'), lm = fmat('#ffe2a0', { emissive: '#ffd27a', emissiveIntensity: 2.2 });
  for (let z = -141; z < 130; z += 22) for (const x of [29, 47, -79, -63]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.12, .12, 6), pm); p.position.set(x, 3, z); scene.add(p); const l = new THREE.Mesh(new THREE.SphereGeometry(.4, 10, 8), lm); l.position.set(x, 6.2, z); scene.add(l); } }

/* ---------- CASA ALUGADA (Rua 25 de Março) + edícula ---------- */
const houseG = new THREE.Group(); scene.add(houseG);
{
  const wall = fmat('#a9a39a'), roofM = fmat('#9b4434'), doorM = fmat('#5a3a22'), winM = fmat('#ffd27a', { emissive: '#ffcc66', emissiveIntensity: 1.6 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(38, 4.5, 14), wall); body.position.set(-43, 2.25 + .18, 0); houseG.add(body);
  const sh = new THREE.Shape(); sh.moveTo(-7.6, 0); sh.lineTo(0, 2.8); sh.lineTo(7.6, 0); sh.lineTo(-7.6, 0);
  const roof = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 39, bevelEnabled: false }), roofM); roof.rotation.y = Math.PI / 2; roof.position.set(-62.5, 4.68, 0); houseG.add(roof);
  const door = new THREE.Mesh(new THREE.BoxGeometry(.2, 2.6, 1.6), doorM); door.position.set(-62.05, 1.5, 2.5); houseG.add(door);
  for (const z of [-3.5, 5.5]) { const w = new THREE.Mesh(new THREE.BoxGeometry(.2, 1.4, 2), winM); w.position.set(-62.05, 2.6, z); houseG.add(w); }
  const edi = new THREE.Mesh(new THREE.BoxGeometry(12, 3, 10), wall); edi.position.set(-14, 1.68, 0); houseG.add(edi);
  const ediR = new THREE.Mesh(new THREE.BoxGeometry(12.6, .3, 10.6), roofM); ediR.position.set(-14, 3.3, 0); houseG.add(ediR);
}
const sign = signMesh('GRAMA SINTÉTICA', { w: 13, h: 2.6 }); sign.rotation.y = -Math.PI / 2; sign.position.set(-62.7, 6.6, 0); scene.add(sign);
{ const pm = fmat('#6b7280'); for (const z of [-4.5, 4.5]) { const p = new THREE.Mesh(new THREE.BoxGeometry(.2, 2.2, .2), pm); p.position.set(-62.6, 5.2, z); scene.add(p); } }

/* caminhonete */
const truck = new THREE.Group(); scene.add(truck);
{ const red = fmat('#c94f3d'), dark = fmat('#15171c'), load = fmat('#8a6a44'), glass = fmat('#9fd3ff', { emissive: '#3a6a8a', emissiveIntensity: .6 });
  const ch = new THREE.Mesh(new THREE.BoxGeometry(2.2, .9, 6), red); ch.position.y = 1; truck.add(ch);
  const cab = new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.1, 1.8), red); cab.position.set(0, 1.95, -2); truck.add(cab);
  const gl = new THREE.Mesh(new THREE.BoxGeometry(2.12, .6, .1), glass); gl.position.set(0, 2.1, -2.92); truck.add(gl);
  const ld = new THREE.Mesh(new THREE.BoxGeometry(1.9, .7, 3.6), load); ld.position.set(0, 1.75, .9); truck.add(ld);
  for (const [x, z] of [[-1.1, -2], [1.1, -2], [-1.1, 2], [1.1, 2]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(.45, .45, .3, 14), dark); w.rotation.z = Math.PI / 2; w.position.set(x, .45, z); truck.add(w); }
  truck.position.set(-71, 0, 7); }

/* ---------- BANCO CENTRAL + caixa-forte + laje ---------- */
const bankG = new THREE.Group(); scene.add(bankG);
{
  const bw = canvasTex(512, 128, (x, w, h) => { x.fillStyle = '#c7ced8'; x.fillRect(0, 0, w, h); for (let j = 0; j < 2; j++) for (let i = 0; i < 8; i++) { x.fillStyle = (i + j) % 3 ? '#39414f' : '#e9c77a'; x.fillRect(i * 64 + 18, j * 64 + 18, 28, 34); } }, [6, 1]);
  const stone = fmat('#ffffff', { map: bw });
  const body = new THREE.Mesh(new THREE.BoxGeometry(80, 14, 88), stone); body.position.set(88, 7.18, -2); bankG.add(body);
  const colM = fmat('#e3e8ee');
  for (let z = -18; z <= 18; z += 4) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.55, .6, 11, 14), colM); c.position.set(46.5, 5.7, z); bankG.add(c); }
  const sh = new THREE.Shape(); sh.moveTo(-21, 0); sh.lineTo(0, 3.5); sh.lineTo(21, 0); sh.lineTo(-21, 0);
  const ped = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 3, bevelEnabled: false }), colM); ped.rotation.y = Math.PI / 2; ped.position.set(45, 11.2, 0); bankG.add(ped);
  const beam = new THREE.Mesh(new THREE.BoxGeometry(3, .8, 42), colM); beam.position.set(46.5, 11.6, 0); bankG.add(beam);
  for (let i = 0; i < 4; i++) { const st = new THREE.Mesh(new THREE.BoxGeometry(1 + i * .8, .25, 42), colM); st.position.set(47.5 - i * .4, .3 + (3 - i) * .25, 0); bankG.add(st); }
}
// laje de concreto (1,10 m) sob a caixa-forte — dividida no corte p/ aparecer em seção
const hatch = canvasTex(256, 64, (x, w, h) => { x.fillStyle = '#a3a9b2'; x.fillRect(0, 0, w, h); x.strokeStyle = 'rgba(40,44,52,.55)'; x.lineWidth = 5; for (let i = -h; i < w; i += 22) { x.beginPath(); x.moveTo(i, h); x.lineTo(i + h, 0); x.stroke(); } }, [6, 1]);
const concB = mat('#ffffff', { map: hatch }), concF = fmat('#a3a9b2');
slab(54, 76, -11, 11, -1.1, 1.1, concB, concF);
// caixa-forte (interior), visível só quando o prédio é "aberto"
const vaultG = new THREE.Group(); scene.add(vaultG);
const PALLETS = [], NEWP = [];
{
  const floor = new THREE.Mesh(new THREE.BoxGeometry(18, .2, 18), mat('#3a404c')); floor.position.set(65, .1, 0); vaultG.add(floor);
  const wallM = mat('#59606e'), trim = mat('#f2a93b', { emissive: '#f2a93b', emissiveIntensity: .6 });
  for (const [x, z, w, d, h] of [[65, -9, 18, .4, 3], [56, 0, .4, 18, 3], [74, 0, .4, 18, 3], [65, 9, 18, .4, .8]]) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), wallM); m.position.set(x, h / 2 + .2, z); vaultG.add(m);
    const t = new THREE.Mesh(new THREE.BoxGeometry(w + .05, .12, d + .05), trim); t.position.set(x, h + .2, z); vaultG.add(t);
  }
  const money = mat('#4fa857'), band = mat('#f2a93b', { emissive: '#f2a93b', emissiveIntensity: .3 }), grey = mat('#7d8696');
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { // notas usadas (alvo)
    const gp = new THREE.Group(); const m = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.1, 1.6), money); m.position.y = .75; gp.add(m);
    const b2 = new THREE.Mesh(new THREE.BoxGeometry(1.62, 1.12, .3), band); b2.position.y = .75; gp.add(b2);
    gp.position.set(66 + i * 2.1, 0, -6.5 + j * 2.6); vaultG.add(gp); PALLETS.push(gp);
  }
  for (let i = 0; i < 2; i++) for (let j = 0; j < 4; j++) { const m = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.1, 1.6), grey); m.position.set(58.5 + i * 2.1, .75, -6.5 + j * 2.6); vaultG.add(m); NEWP.push(m); }
}
const hole = new THREE.Mesh(new THREE.CircleGeometry(.75, 24), new THREE.MeshBasicMaterial({ color: '#020203' })); hole.rotation.x = -Math.PI / 2; hole.position.set(63, .22, 0); vaultG.add(hole);
const holeRing = new THREE.Mesh(new THREE.RingGeometry(.75, .95, 24), new THREE.MeshBasicMaterial({ color: C.red })); holeRing.rotation.x = -Math.PI / 2; holeRing.position.set(63, .23, 0); vaultG.add(holeRing);
const sensor = new THREE.Mesh(new THREE.ConeGeometry(2.6, 3.4, 24, 1, true), new THREE.MeshBasicMaterial({ color: C.red, transparent: true, opacity: .22, side: THREE.DoubleSide, depthWrite: false }));
sensor.geometry.translate(0, -1.7, 0); sensor.position.set(64, 3.6, 0); vaultG.add(sensor);
const door = new THREE.Mesh(new THREE.BoxGeometry(2.4, 2.6, .25), mat('#b8bfcc', { metalness: .6, roughness: .4 })); door.geometry.translate(1.2, 0, 0); door.position.set(63.8, 1.5, -9); vaultG.add(door);

/* ---------- TÚNEL (75,4 m) ---------- */
const TX0 = -12, TX1 = 63, SEWX = 48, TH = 1.2;
const topAt = x => x < SEWX ? -3.0 : -2.3;    // topo do túnel; sobe ~70 cm depois do esgoto
const voidM = mat('#3a281a', { side: THREE.BackSide, roughness: 1 });
const tunA = new THREE.Mesh(new THREE.BoxGeometry(1, TH, TH), voidM); scene.add(tunA);
const tunB = new THREE.Mesh(new THREE.BoxGeometry(1, TH, TH), voidM); scene.add(tunB);
const shaft = new THREE.Mesh(new THREE.BoxGeometry(TH, 1, TH), voidM); scene.add(shaft);
const riser = new THREE.Mesh(new THREE.BoxGeometry(TH, 1, TH), voidM); scene.add(riser);
const cutBox = new THREE.Mesh(new THREE.BoxGeometry(TH, 1, TH), voidM); scene.add(cutBox);
// escoras (≈900 tábuas) — instanciadas, ordenadas por x
const FR = []; for (let x = TX0 + .5; x < TX1; x += 1.5) FR.push(x);
const woodM = mat('#a5703f');
const posts = new THREE.InstancedMesh(new THREE.BoxGeometry(.14, TH, .14), woodM, FR.length * 2);
const beams = new THREE.InstancedMesh(new THREE.BoxGeometry(.14, .14, TH + .1), woodM, FR.length);
{ const o = new THREE.Object3D(); FR.forEach((x, i) => { const y = topAt(x) - TH / 2; for (const s of [0, 1]) { o.position.set(x, y, s ? .6 : -.6); o.updateMatrix(); posts.setMatrixAt(i * 2 + s, o.matrix); } o.position.set(x, topAt(x), 0); o.updateMatrix(); beams.setMatrixAt(i, o.matrix); }); }
scene.add(posts, beams);
const LAMPX = []; for (let x = TX0 + 3; x < TX1; x += 6) LAMPX.push(x);
const lamps = new THREE.InstancedMesh(new THREE.SphereGeometry(.13, 10, 8), new THREE.MeshBasicMaterial({ color: '#ffe08a' }), LAMPX.length);
{ const o = new THREE.Object3D(); LAMPX.forEach((x, i) => { o.position.set(x, topAt(x) - .2, .45); o.updateMatrix(); lamps.setMatrixAt(i, o.matrix); }); }
scene.add(lamps);
const tunLight = new THREE.PointLight('#ffcf80', 12, 9, 1.6); scene.add(tunLight);
// esgoto
const sewer = new THREE.Mesh(new THREE.CylinderGeometry(.6, .6, 20, 20), mat('#3d7f7a', { emissive: '#1d4a46', emissiveIntensity: .8 }));
sewer.geometry = new THREE.CylinderGeometry(.6, .6, 16, 20); sewer.rotation.x = Math.PI / 2; sewer.position.set(SEWX, -3.6, -7.3); scene.add(sewer);
// tambor (leva a terra) e partículas
const drum = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .35, 16), mat('#3d6fb0')); drum.rotation.z = Math.PI / 2; scene.add(drum);
const sparkGeo = new THREE.BufferGeometry(); sparkGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(80 * 3), 3));
const sparks = new THREE.Points(sparkGeo, new THREE.PointsMaterial({ color: '#ffc861', size: .09 })); scene.add(sparks);
const saw = new THREE.Mesh(new THREE.CylinderGeometry(.42, .42, .05, 24), mat('#d0d6de', { metalness: .8, roughness: .3 })); scene.add(saw);
const breakLight = new THREE.PointLight('#ffe2a8', 0, 14, 1.2); breakLight.position.set(63, -.5, .8); scene.add(breakLight);

function setTunnel(len, { shaftK = 1, riserK = 0, cutK = 0, lightsK = 1 } = {}) {
  const fx = TX0 + len;
  shaft.visible = shaftK > 0; const sh = 3.0 + TH; shaft.scale.y = sh * shaftK; shaft.position.set(TX0, -shaft.scale.y / 2, 0);
  const aEnd = Math.min(fx, SEWX); tunA.visible = aEnd > TX0 + .05; tunA.scale.x = Math.max(.01, aEnd - TX0 + TH / 2); tunA.position.set(TX0 - TH / 2 + tunA.scale.x / 2, -3 - TH / 2, 0);
  tunB.visible = fx > SEWX; tunB.scale.x = Math.max(.01, fx - SEWX); tunB.position.set(SEWX + tunB.scale.x / 2, -2.3 - TH / 2, 0);
  const n = FR.filter(x => x < fx - .3).length; beams.count = n; posts.count = n * 2;
  lamps.count = Math.floor(LAMPX.filter(x => x < fx).length * lightsK);
  riser.visible = riserK > 0; riser.scale.y = 1.2 * riserK + .01; riser.position.set(TX1 - .2, -2.3 + riser.scale.y / 2, 0);
  cutBox.visible = cutK > 0; cutBox.scale.y = 1.1 * cutK + .01; cutBox.position.set(TX1 - .2, -1.1 + cutBox.scale.y / 2, 0);
  tunLight.position.set(fx - 1.5, topAt(fx) - .4, 1.2); tunLight.intensity = len > 1 ? 12 : 0;
  return fx;
}

/* ---------- personagens (genéricos) ---------- */
const crew = [makeGuy('#3fa34d', 0), makeGuy('#3fa34d', 1, '#111'), makeGuy('#3fa34d', 2, '#b8913f'), makeGuy('#3fa34d', 3, '#5a3a22')];
crew.forEach(c => scene.add(c));
const clerk = makeGuy('#e8ecf2', 1, '#222'); scene.add(clerk);
const sacks = crew.map(() => { const s = new THREE.Mesh(new THREE.BoxGeometry(.55, .4, .45), mat('#9a7650')); scene.add(s); return s; });
const bundles = crew.map(() => { const s = new THREE.Mesh(new THREE.BoxGeometry(.7, .4, .5), mat('#4fa857')); scene.add(s); return s; });
function hideActors() { crew.forEach(c => c.visible = false); clerk.visible = false; sacks.forEach(s => s.visible = false); bundles.forEach(s => s.visible = false); }
function place(gr, x, y, z, rotY = 0, scale = 1) { gr.visible = true; gr.position.set(x, y, z); gr.rotation.set(0, rotY, 0); gr.scale.setScalar(scale); }

/* ---------- carros na avenida ---------- */
const cars = [];
{ const cols = ['#4f7ac9', '#d0d4dc', '#c9a227', '#b0413e'];
  for (let i = 0; i < 6; i++) { const gp = new THREE.Group(); const body = new THREE.Mesh(new THREE.BoxGeometry(1.9, .8, 4.2), fmat(cols[i % 4])); body.position.y = .65; gp.add(body);
    const cab = new THREE.Mesh(new THREE.BoxGeometry(1.7, .6, 2.2), fmat('#22262e')); cab.position.set(0, 1.3, .2); gp.add(cab);
    const hl = new THREE.Mesh(new THREE.BoxGeometry(1.6, .2, .1), fmat('#fff3c4', { emissive: '#fff3c4', emissiveIntensity: 2 })); hl.position.set(0, .7, -2.12); gp.add(hl);
    scene.add(gp); cars.push(gp); } }
function moveCars(t) { cars.forEach((c, i) => { const dir = i % 2 ? 1 : -1, sp = 9 + i * 2; const z = ((t * sp + i * 47) % 260) - 130; c.position.set(i % 2 ? 41.5 : 34.5, 0, dir * z); c.rotation.y = dir > 0 ? Math.PI : 0; }); }

/* =====================================================================
   CENAS
   ===================================================================== */
const CH = { gancho: '01 · O ALVO', terreno: '02 · O TERRENO', fachada: '03 · O DISFARCE', tunel: '04 · O TÚNEL', esgoto: '05 · O IMPREVISTO', laje: '06 · A LAJE', cofre: '07 · O COFRE', fecho: '08 · A FUGA' };
function clock(t) {
  const id = sceneAt(t).s.id;
  if (id === 'fachada' || id === 'tunel' || id === 'esgoto') return ['MAI — AGO 2005', 'ESCAVAÇÃO: 20h ÀS 4h'];
  if (id === 'cofre') { const k = eio(P('cofre', t)); const m = Math.round(lerp(22 * 60, 30 * 60, k)); const hh = Math.floor(m / 60) % 24, mm = m % 60; return [hh < 22 ? 'SÁB 06.08.2005' : 'SEX 05.08.2005', `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`]; }
  if (id === 'fecho') return ['SEG 08.08.2005', 'DESCOBERTA DO FURTO'];
  return ['SEX 05.08.2005', '21:00'];
}
const AERIAL = { pos: v3(-15, 105, 128), look: v3(8, 0, -6) };
let O = {}; // estado do overlay por quadro

function draw(t) {
  const { s } = sceneAt(t); const id = s.id; const p = P(id, t);
  hideActors(); moveCars(t); O = { id, p };
  bankG.visible = true; vaultG.visible = false; sparks.visible = false; saw.visible = false; drum.visible = false; breakLight.intensity = 0;
  hemi.color.set('#9fb4e8'); scene.background.set(C.bg);
  let fade = 1, len = 75.4, tun = { riserK: 1 }, cam;

  if (id === 'gancho') {
    cam = camPath([{ p: 0, pos: v3(66.5, -2.0, 9.5), look: v3(60.5, -2.4, 0) }, { p: .45, pos: v3(65.5, -1.9, 8.6), look: v3(61, -2.0, 0) },
      { p: .92, pos: v3(18, 30, 92), look: v3(55, 3, 0) }, { p: 1, pos: v3(14, 34, 98), look: v3(50, 2, -2) }], p);
    fade = lerp(.06, 1, eio(seg(p, .5, .82)));
    [[58.6, 0], [60.2, 1], [61.7, 2]].forEach(([x, i]) => { place(crew[i], x, -4.2, .05, 0, .8); poseGuy(crew[i], { crouch: .9, arms: i === 2 ? -1.2 : 0 }); });
    O.vault = v3(63, -1.1, 0);
  } else if (id === 'terreno') {
    cam = camPath([{ p: 0, pos: v3(14, 34, 98), look: v3(50, 2, -2) }, { p: .55, pos: AERIAL.pos, look: AERIAL.look }, { p: 1, pos: v3(-20, 112, 122), look: v3(6, 0, -6) }], p);
  } else if (id === 'fachada') {
    cam = camPath([{ p: 0, pos: v3(-110, 8, 14), look: v3(-62, 4, 1) }, { p: 1, pos: v3(-97, 5.4, 10), look: v3(-62, 3.2, 1) }], p);
    for (let i = 0; i < 3; i++) { // ida (com saco) e volta
      const ph = (t * .17 + i / 3) % 1, go = ph < .5, k = go ? ph * 2 : (ph - .5) * 2;
      const a = v3(-62.6, .18, 2.5), b = v3(-70, .18, 4.6); const pos = go ? lerpV(a, b, k) : lerpV(b, a, k);
      place(crew[i], pos.x, pos.y, pos.z + i * .5, go ? Math.PI * .58 : -Math.PI * .42, 1); poseGuy(crew[i], { walk: t * 9 + i, arms: go ? -1.3 : 0 });
      if (go) { sacks[i].visible = true; sacks[i].position.set(pos.x - .45, 1.35, pos.z + i * .5); }
    }
    len = 0; tun = { shaftK: 0 };
  } else if (id === 'tunel' || id === 'esgoto') {
    const tu = P('tunel', t), es = P('esgoto', t);
    len = id === 'tunel' ? 60 * eio(seg(tu, .18, .95)) : lerp(60, 75.4, eio(seg(es, .42, .9)));
    const fx = TX0 + len;
    const follow = { pos: v3(fx - 5.5, -2.0, 8.5), look: v3(fx - .5, -3.1, 0) };
    if (id === 'tunel') { const k = eio(seg(tu, 0, .2)); cam = { pos: lerpV(v3(-97, 5.4, 10), follow.pos, k), look: lerpV(v3(-62, 3.2, 1), follow.look, k) }; fade = lerp(1, .06, eio(seg(tu, .03, .16))); tun = { shaftK: eout(seg(tu, .05, .2)), lightsK: seg(tu, .45, 1) }; }
    else { cam = follow; fade = .06; sewer.visible = true; }
    sewer.visible = id === 'esgoto' || len > 59;
    // escavador + tambor + ajudante
    const top = topAt(fx); place(crew[0], fx - .9, top - TH, .1, 0, .78); poseGuy(crew[0], { crouch: .9, arms: -1.1 + Math.sin(t * 9) * .5 });
    const ph = (t * .32) % 1, dx = ph < .5 ? lerp(fx - 2.5, TX0 + 1, ph * 2) : lerp(TX0 + 1, fx - 2.5, (ph - .5) * 2);
    drum.visible = true; drum.position.set(dx, topAt(dx) - TH + .3, .2);
    place(crew[1], TX0 - 1.6, .18, 1.4, Math.PI / 2, 1); poseGuy(crew[1], { arms: -.6 + Math.sin(t * 3) * .3 });
    if (id === 'esgoto') { place(crew[2], fx - 2.6, topAt(fx - 2.6) - TH, .1, 0, .78); poseGuy(crew[2], { crouch: .9 }); }
    O.fx = fx; O.len = len;
    if (id === 'esgoto' && es > .5 && es < .9) cam.shake = .05;
    tun.riserK = 0;
  } else if (id === 'laje') {
    const la = p; cam = camPath([{ p: 0, pos: v3(57.5, -2.0, 8.5), look: v3(62.5, -3.1, 0) }, { p: .28, pos: v3(60.2, -2.5, 9.2), look: v3(63, -1.5, 0) }, { p: 1, pos: v3(60.8, -2.4, 8.4), look: v3(63, -1.3, 0) }], la);
    fade = .06; const cut = eio(seg(la, .3, .85)), brk = eout(seg(la, .86, 1));
    tun = { riserK: eio(seg(la, 0, .2)), cutK: cut };
    place(crew[2], 62.4, -3.5, .1, 0, .8); poseGuy(crew[2], { crouch: .3, arms: -2.6 });
    place(crew[0], 59.8, -3.5, .1, 0, .78); poseGuy(crew[0], { crouch: .9 });
    if (la > .28 && la < .87) {
      saw.visible = true; saw.position.set(63, -1.1 + 1.1 * cut - .05, .75); saw.rotation.set(Math.PI / 2, t * 40, 0); saw.scale.setScalar(.7);
      sparks.visible = true; const arr = sparkGeo.attributes.position.array; const r = rng(Math.floor(t * 30));
      for (let i = 0; i < 80; i++) { const a = r() * Math.PI * 2, d = r() * 1.4; arr[i * 3] = 63 + Math.cos(a) * d; arr[i * 3 + 1] = saw.position.y - r() * 1.2; arr[i * 3 + 2] = .7 + Math.sin(a) * .3; }
      sparkGeo.attributes.position.needsUpdate = true;
    }
    breakLight.intensity = brk * 60; O.cut = cut; O.brk = brk;
  } else if (id === 'cofre' || id === 'fecho') {
    bankG.visible = false; vaultG.visible = true; len = 75.4;
    const k = id === 'cofre' ? eio(seg(p, .08, .92)) : 1; const left = Math.round(PALLETS.length * (1 - k));
    PALLETS.forEach((pl, i) => pl.visible = i < left);
    sensor.rotation.z = Math.sin(t * 1.2) * .5;
    if (id === 'cofre') {
      cam = camPath([{ p: 0, pos: v3(53, 14.5, 21), look: v3(65.5, 0, .5) }, { p: 1, pos: v3(56, 13.5, 20), look: v3(65.5, 0, .5) }], p);
      const path = [v3(63, .2, 1.2), v3(63, .2, 7.6), v3(72.6, .2, 7.6), v3(72.6, .2, -7.6), v3(70, .2, -7.6)];
      const L = []; let tot = 0; for (let i = 1; i < path.length; i++) { const d = path[i].distanceTo(path[i - 1]); L.push(d); tot += d; }
      const at = s => { let d = s * tot; for (let i = 0; i < L.length; i++) { if (d <= L[i]) { const q = d / L[i]; return { p: lerpV(path[i], path[i + 1], q), dir: path[i + 1].clone().sub(path[i]) }; } d -= L[i]; } return { p: path[path.length - 1], dir: v3(1, 0, 0) }; };
      for (let i = 0; i < 3; i++) {
        const ph = (t * .16 + i / 3) % 1, back = ph > .5, s2 = back ? 1 - (ph - .5) * 2 : ph * 2; const { p: pp, dir } = at(s2);
        if (back) dir.negate(); const ry = Math.atan2(-dir.z, dir.x);
        place(crew[i + 1], pp.x, pp.y, pp.z, ry, 1); poseGuy(crew[i + 1], { walk: t * 9 + i * 2, arms: back ? -1.3 : 0 });
        if (back) { bundles[i].visible = true; bundles[i].position.set(pp.x + Math.cos(ry) * .45, 1.35, pp.z - Math.sin(ry) * .45); }
      }
      O.k = k;
    } else {
      const fe = p; door.rotation.y = -eout(seg(fe, .05, .15)) * 1.6;
      const cz = lerp(-10.5, -6.5, eio(seg(fe, .1, .25))); place(clerk, 65, .2, cz, -Math.PI / 2, 1); poseGuy(clerk, { walk: fe < .25 ? t * 9 : null });
      O.clerk = v3(65, 2.4, cz);
      const k2 = eio(seg(fe, .35, .7));
      if (k2 > 0) { bankG.visible = k2 > .5; vaultG.visible = k2 <= .5; }
      cam = camPath([{ p: 0, pos: v3(56, 13.5, 20), look: v3(65.5, 0, .5) }, { p: .35, pos: v3(57, 13, 19), look: v3(65, 0, -2) }, { p: .7, pos: AERIAL.pos, look: AERIAL.look }, { p: 1, pos: v3(-20, 116, 126), look: v3(6, 0, -6) }], fe);
      const dawn = seg(fe, .4, .8); hemi.color.lerpColors(new THREE.Color('#9fb4e8'), new THREE.Color('#ffd2a8'), dawn); scene.background.lerpColors(new THREE.Color(C.bg), new THREE.Color('#1a1626'), dawn);
      O.route = seg(fe, .5, .75);
    }
  }
  if (!['tunel', 'esgoto'].includes(id)) sewer.visible = fade < .5;
  setFade(fade);
  setTunnel(len, tun);
  setCam(cam.pos, cam.look, cam.shake || 0, t);
}

/* ---------- overlay por cena ---------- */
const HIL = /\d|milhões|metros|metro|concreto|esgoto|grama|sintética|túnel|diamante|toneladas|cinquenta|segunda|mapa|crime|setenta|sessenta|cem|oito|três|banco|fácil|rastrear|casa/i;
function overlay(t) {
  const { id, p } = O;
  if (id === 'gancho') {
    tag3D(O.vault, -220, -60, '1,10 m DE CONCRETO', 'ENTRE ELES E O DINHEIRO', C.red, eout(seg(p, .12, .25)) * (1 - seg(p, .5, .6)));
    const mk = eio(seg(p, .42, .95)); counter('NO COFRE, EM NOTAS DE R$ 50', brl(164700000 * mk), W - 64, 200, C.amber, seg(p, .4, .5), 'right', 100);
  }
  if (id === 'terreno') {
    tag3D(v3(56, 15, -10), 120, -140, 'BANCO CENTRAL', 'AV. DOM MANUEL × R. HERÁCLITO GRAÇA', C.bank, eout(seg(p, .1, .3)));
    tag3D(v3(-43, 7.5, 0), -120, -150, 'CASA ALUGADA', 'RUA 25 DE MARÇO, 1071', C.red, eout(seg(p, .5, .65)));
    dim3D(v3(-43, 8, 0), v3(65, 15, 0), '≈ 100 m', eio(seg(p, .68, .95)));
  }
  if (id === 'fachada') {
    tag(64, 230, 'EMPRESA DE FACHADA', 'REGISTRADA EM NOME FALSO', C.green, eout(seg(p, .2, .35)));
    tag3D(v3(-70, 2.4, 5), 160, 90, 'TERRA SAINDO', 'TODO DIA, EM SACOS', C.amber, eout(seg(p, .55, .7)));
  }
  if (id === 'tunel' || id === 'esgoto') {
    counter('EXTENSÃO ESCAVADA', `${O.len.toFixed(1).replace('.', ',')} m`, W - 64, 760, C.red, 1, 'right', 96);
    if (id === 'tunel') { tag3D(v3(TX0, -1.6, .6), 120, -40, '3 m ABAIXO DO CHÃO', 'POÇO NA EDÍCULA', C.amber, eout(seg(p, .2, .3)) * (1 - seg(p, .45, .55))); tag(64, 230, '≈ 900 TÁBUAS', 'ESCORAMENTO · LUZ · VENTILAÇÃO', C.amber, eout(seg(p, .6, .72))); }
    else { tag3D(v3(SEWX, -3.6, .6), -60, 120, 'ESGOTO', 'NÃO ESTAVA NA PLANTA', C.teal, eout(seg(p, .1, .2))); tag(64, 230, 'TÚNEL SOBE ≈ 70 cm', 'COLADO NO ASFALTO', C.amber, eout(seg(p, .4, .52))); }
  }
  if (id === 'laje') {
    tag3D(v3(58, -.55, -.8), -120, -160, 'LAJE · 1,10 m', 'CONCRETO ARMADO', C.white, eout(seg(p, .15, .28)));
    tag(64, 230, 'SERRA C/ DISCO DIAMANTADO', 'CORTE DE BAIXO PARA CIMA', C.amber, eout(seg(p, .35, .48)));
    counter('CORTE', `${Math.round(O.cut * 100)}%`, W - 64, 760, C.amber, seg(p, .3, .38), 'right', 96);
    if (O.brk > 0 && O.brk < 1) { g.fillStyle = `rgba(255,241,208,${(1 - O.brk) * .85})`; g.fillRect(0, 0, W, H); }
  }
  if (id === 'cofre') {
    counter('LEVADO', brl(164700000 * O.k), 64, 740, C.amber, 1, 'left', 88);
    counter('PESO', `${(3.5 * O.k).toFixed(1).replace('.', ',')} t`, W - 64, 740, C.amber, 1, 'right', 88);
    tag3D(v3(58.5, 1.4, -6.5), -40, 170, 'NOTAS NOVAS', 'SERIADAS · NÃO LEVADAS', C.dim, eout(seg(p, .05, .15)));
    tag3D(v3(63, .5, 7.6), 220, -110, 'RENTE ÀS PAREDES', 'FORA DO ALCANCE DO SENSOR', C.red, eout(seg(p, .3, .4)));
  }
  if (id === 'fecho') {
    if (p < .4) { tag3D(O.clerk, 140, -140, 'COFRE VAZIO', 'SEGUNDA-FEIRA DE MANHÃ', C.red, eout(seg(p, .2, .28)) * (1 - seg(p, .33, .38))); }
    if (O.route > 0) { const A = toScreen(v3(-14, .4, 0)), B = toScreen(v3(63, .4, 0)); if (A && B) { const E = { x: lerp(A.x, B.x, O.route), y: lerp(A.y, B.y, O.route) }; g.save(); g.strokeStyle = C.red; g.lineWidth = 8; g.setLineDash([22, 12]); g.shadowColor = C.red; g.shadowBlur = 20; g.beginPath(); g.moveTo(A.x, A.y); g.lineTo(E.x, E.y); g.stroke(); g.restore(); } }
    if (O.route > .9) tag3D(v3(25, .4, 0), 0, -170, 'TÚNEL · 75,4 m', 'DA EDÍCULA À CAIXA-FORTE', C.red, seg(p, .72, .8));
  }
  // transições: corte seco com fade preto entre "mundos"
  const { s, local, i } = sceneAt(t);
  if (['fachada', 'cofre'].includes(s.id) && local < .35) { g.fillStyle = `rgba(0,0,0,${1 - local / .35})`; g.fillRect(0, 0, W, H); }
  const prev = TL.scenes[i + 1]; if (prev && ['fachada', 'cofre'].includes(prev.id) && t > prev.start - .3) { g.fillStyle = `rgba(0,0,0,${clamp((t - prev.start + .3) / .3)})`; g.fillRect(0, 0, W, H); }

  vignette();
  const intro = 1 - seg(t, 1.5, 2.1), endK = seg(t, TL.total - 3.6, TL.total - 3.0);
  hud(t, { caso: 'CASO 01 · FURTO AO BANCO CENTRAL · FORTALEZA–CE', chapters: CH, clock }, seg(t, 1.8, 2.3) * (1 - endK));
  if (endK < 1) caption(t, HIL, 66);
  txt('REPRESENTAÇÃO ILUSTRATIVA · FORA DE ESCALA', 64, H - 24, { size: 18, weight: 700, color: 'rgba(200,210,225,.7)', track: 2 });
  if (intro > 0) {
    g.save(); g.globalAlpha = intro; g.fillStyle = '#04060a'; g.fillRect(0, 0, W, H);
    const s1 = '05.08.2005 — 21:00'; const n = Math.floor(seg(t, .1, .9) * s1.length);
    txt(s1.slice(0, n), W / 2, H / 2, { size: 84, weight: 900, align: 'center', track: 6, font: '"DejaVu Sans Mono", monospace' });
    txt('FORTALEZA · CEARÁ', W / 2, H / 2 + 70, { size: 32, weight: 800, color: C.red, align: 'center', track: 12, alpha: seg(t, .8, 1.2) });
    g.restore();
  }
  if (endK > 0) {
    g.save(); g.globalAlpha = endK; g.fillStyle = 'rgba(5,7,11,.93)'; g.fillRect(0, 0, W, H); g.restore();
    txt('MAPA DO CRIME', W / 2, 560, { size: 124, weight: 900, align: 'center', track: 10, alpha: endK });
    txt('O CRIME VISTO DE CIMA', W / 2, 630, { size: 34, weight: 800, color: C.red, align: 'center', track: 12, alpha: endK });
    txt('CASO 01 · O FURTO DO BANCO CENTRAL — EPISÓDIO COMPLETO EM BREVE', W / 2, 740, { size: 28, weight: 700, color: C.dim, align: 'center', track: 3, alpha: endK });
    txt('Fontes: Estadão, “Os Toupeiras” (2015); Polícia Federal; Justiça Federal do Ceará. Representação ilustrativa.', W / 2, H - 56, { size: 20, weight: 600, color: C.dim, align: 'center', alpha: endK });
  }
}

run(draw, overlay);

/* thumbnail 1280x720: cena da laje + texto grande (máx. 4 palavras + 1 número) */
import { renderer } from 'engine';
window.renderThumb = () => {
  g.clearRect(0, 0, W, H); draw(41.6); renderer.render(scene, camera);
  const gr = g.createLinearGradient(0, 0, 0, 420); gr.addColorStop(0, 'rgba(4,6,10,.92)'); gr.addColorStop(1, 'rgba(4,6,10,0)'); g.fillStyle = gr; g.fillRect(0, 0, W, 420);
  txt('75 METROS', 80, 220, { size: 200, weight: 900, color: '#fff' });
  txt('ATÉ O COFRE', 92, 320, { size: 92, weight: 900, color: C.amber, track: 3 });
  g.fillStyle = 'rgba(4,6,10,.85)'; g.fillRect(W - 1100, H - 230, 1040, 170); g.fillStyle = C.red; g.fillRect(W - 1100, H - 230, 10, 170);
  txt('R$ 164,7 MILHÕES', W - 90, H - 105, { size: 110, weight: 900, color: C.red, align: 'right' });
  vignette();
};
