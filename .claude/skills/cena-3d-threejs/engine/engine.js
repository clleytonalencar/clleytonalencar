// =====================================================================
// engine.js — motor de vídeo 3D determinístico (Three.js + overlay 2D)
//
// Cada quadro é função pura do tempo t: o render.mjs chama
// window.renderFrame(t), que posiciona tudo, renderiza o WebGL e desenha
// HUD/legendas/etiquetas num canvas 2D por cima. Nada de
// requestAnimationFrame, nada de Math.random() sem semente.
// =====================================================================
import * as THREE from 'three';
export { THREE };

export const W = 1920, H = 1080;

/* ---------- paleta do canal (mesma do motion graphics) ---------- */
export const C = {
  bg: '#070a12', red: '#e5383b', amber: '#f2a93b', white: '#f4f6f8', dim: '#9aa8b8',
  bank: '#d6e2ee', teal: '#3fb8a5', green: '#3fd47a', ink: 'rgba(6,8,12,.88)',
};
export const FONT = 'Inter, "Inter Display", system-ui, sans-serif';

/* ---------- matemática de animação ---------- */
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, k) => a + (b - a) * k;
export const seg = (p, a, b) => clamp((p - a) / (b - a));
export const eio = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
export const eout = k => 1 - Math.pow(1 - k, 3);
export function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
export const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
export function lerpV(a, b, k) { return new THREE.Vector3(lerp(a.x, b.x, k), lerp(a.y, b.y, k), lerp(a.z, b.z, k)); }

/* ---------- timeline (vem do tts.py via window.TIMELINE) ---------- */
export const TL = window.TIMELINE || { total: 60, scenes: [] };
const SC = {}; TL.scenes.forEach((s, i) => { SC[s.id] = { ...s, i }; });
export function sceneAt(t) {
  let cur = TL.scenes[0]; for (const s of TL.scenes) if (t >= s.start) cur = s;
  const i = TL.scenes.indexOf(cur), st = i === 0 ? 0 : cur.start, en = i === TL.scenes.length - 1 ? TL.total : cur.end;
  return { s: cur, i, p: clamp((t - st) / (en - st)), local: t - st, dur: en - st };
}
/** progresso 0..1 da cena `id` no tempo t */
export function P(id, t) { const s = SC[id]; if (!s) return 0; const st = s.i === 0 ? 0 : s.start; const en = s.i === TL.scenes.length - 1 ? TL.total : s.end; return clamp((t - st) / (en - st)); }

/* ---------- renderer, cena, câmera, overlay ---------- */
export const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.25;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.domElement.style.cssText = 'position:absolute;left:0;top:0';
document.body.appendChild(renderer.domElement);

export const scene = new THREE.Scene();
scene.background = new THREE.Color(C.bg);
export const camera = new THREE.PerspectiveCamera(40, W / H, .1, 2000);

const ov = document.createElement('canvas'); ov.width = W; ov.height = H; ov.style.cssText = 'position:absolute;left:0;top:0';
document.body.appendChild(ov);
export const g = ov.getContext('2d');

/** câmera: posição + alvo, com leve tremor opcional */
export function setCam(pos, look, shake = 0, t = 0) {
  camera.position.copy(pos);
  if (shake) camera.position.add(v3(Math.sin(t * 53) * shake, Math.cos(t * 41) * shake, 0));
  camera.lookAt(look); camera.updateMatrixWorld();
}
/** keyframes de câmera [{p:0..1, pos, look}] interpolados com easing */
export function camPath(keys, p) {
  let a = keys[0], b = keys[keys.length - 1];
  for (let i = 0; i < keys.length - 1; i++) if (p >= keys[i].p && p <= keys[i + 1].p) { a = keys[i]; b = keys[i + 1]; break; }
  const k = a === b ? 0 : eio(clamp((p - a.p) / (b.p - a.p)));
  return { pos: lerpV(a.pos, b.pos, k), look: lerpV(a.look, b.look, k) };
}
/** projeta ponto 3D para pixels de tela (null se atrás da câmera) */
export function toScreen(p) { const v = p.clone().project(camera); if (v.z > 1) return null; return { x: (v.x + 1) / 2 * W, y: (1 - v.y) / 2 * H }; }

/* ---------- materiais e texturas utilitárias ---------- */
export const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: .85, metalness: 0, ...o });
export function canvasTex(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); } return t;
}
/** placa com texto (letreiro 3D) */
export function signMesh(text, { w = 8, h = 1.6, bg = '#1f6b3a', fg = '#e9fff0', edge = '#7dff9a', size = 120 } = {}) {
  const tex = canvasTex(1024, Math.round(1024 * h / w), (x, cw, ch) => {
    x.fillStyle = bg; x.fillRect(0, 0, cw, ch); x.strokeStyle = edge; x.lineWidth = 18; x.strokeRect(9, 9, cw - 18, ch - 18);
    x.fillStyle = fg; x.font = `900 ${size}px ${FONT}`; while (x.measureText(text).width > cw - 90 && size > 20) { size -= 4; x.font = `900 ${size}px ${FONT}`; } x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, cw / 2, ch / 2 + 6);
  });
  return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, emissive: '#ffffff', emissiveMap: tex, emissiveIntensity: .55, roughness: .6 }));
}

/* ---------- boneco low-poly (personagem genérico) ---------- */
const SKINS = ['#c68642', '#8d5524', '#e0ac69', '#a86b3c'];
export function makeGuy(shirt = '#3fa34d', skinIdx = 0, hair = '#2b1d14') {
  const gr = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(.24, .55, 4, 10), mat(shirt));
  body.position.y = 1.05; gr.add(body);
  const head = new THREE.Mesh(new THREE.SphereGeometry(.17, 16, 12), mat(SKINS[skinIdx % 4]));
  head.position.y = 1.62; gr.add(head);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(.18, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(hair)); cap.position.y = 1.64; gr.add(cap);
  const legM = mat('#2b3a67'); const legs = [];
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.16, .62, .18), legM); l.geometry.translate(0, -.31, 0); l.position.set(0, .66, s * .11); gr.add(l); legs.push(l); }
  const armM = mat(shirt); const arms = [];
  for (const s of [-1, 1]) { const a = new THREE.Mesh(new THREE.BoxGeometry(.12, .55, .12), armM); a.geometry.translate(0, -.27, 0); a.position.set(0, 1.35, s * .3); gr.add(a); arms.push(a); }
  gr.userData = { body, head, cap, legs, arms };
  return gr;
}
/** pose: walk (fase em rad), crouch (0..1), arms (ângulo extra p/ carregar/cavar) */
export function poseGuy(gr, { walk = null, crouch = 0, arms = 0 } = {}) {
  const u = gr.userData; const sw = walk === null ? 0 : Math.sin(walk) * .6;
  u.legs[0].rotation.z = sw; u.legs[1].rotation.z = -sw;
  u.arms[0].rotation.z = -sw * .8 + arms; u.arms[1].rotation.z = sw * .8 + arms;
  const dy = -crouch * .55; u.body.position.y = 1.05 + dy; u.head.position.y = 1.62 + dy; u.cap.position.y = 1.64 + dy;
  u.arms.forEach(a => a.position.y = 1.35 + dy); u.legs.forEach(l => { l.position.y = .66 + dy * .5; l.scale.y = 1 - crouch * .45; });
  u.body.rotation.z = -crouch * .5;
}

/* ---------- overlay: HUD, etiquetas, contadores, legendas ---------- */
export function txt(s, x, y, { size = 28, weight = 700, color = C.white, align = 'left', base = 'alphabetic', track = 0, alpha = 1, font = FONT, shadow = true } = {}) {
  g.save(); g.globalAlpha *= alpha; g.textAlign = align; g.textBaseline = base; g.font = `${weight} ${size}px ${font}`; g.letterSpacing = track + 'px';
  if (shadow) { g.shadowColor = 'rgba(0,0,0,.85)'; g.shadowBlur = 10; g.shadowOffsetY = 2; }
  g.fillStyle = color; g.fillText(s, x, y); g.restore();
}
/** etiqueta com barra lateral — LEGÍVEL NO CELULAR: título ≥ 34px, sub ≥ 24px */
export function tag(x, y, label, sub, color, alpha = 1, align = 'left') {
  if (alpha <= 0) return;
  g.save(); g.globalAlpha = alpha; g.font = `800 34px ${FONT}`; g.letterSpacing = '2px';
  const w1 = g.measureText(label).width; g.font = `600 24px ${FONT}`; g.letterSpacing = '1px';
  const w2 = sub ? g.measureText(sub).width : 0; const w = Math.max(w1, w2) + 52, h = sub ? 100 : 62;
  const x0 = align === 'left' ? x : align === 'right' ? x - w : x - w / 2;
  g.fillStyle = C.ink; g.fillRect(x0, y, w, h); g.fillStyle = color; g.fillRect(x0, y, 7, h);
  g.restore();
  txt(label, x0 + 26, y + 44, { size: 34, weight: 800, color, track: 2, alpha, shadow: false });
  if (sub) txt(sub, x0 + 26, y + 80, { size: 24, weight: 600, color: C.dim, track: 1, alpha, shadow: false });
}
/** etiqueta presa a um ponto 3D, com linha-guia */
export function tag3D(p, dx, dy, label, sub, color, alpha = 1) {
  const s = toScreen(p); if (!s || alpha <= 0) return;
  g.save(); g.globalAlpha = alpha; g.strokeStyle = color; g.lineWidth = 3; g.beginPath(); g.moveTo(s.x, s.y); g.lineTo(s.x + dx, s.y + dy); g.stroke();
  g.fillStyle = color; g.beginPath(); g.arc(s.x, s.y, 7, 0, Math.PI * 2); g.fill(); g.restore();
  tag(s.x + dx, s.y + dy - (dy < 0 ? 100 : 0), label, sub, color, alpha, dx < 0 ? 'right' : 'left');
}
export function counter(label, value, x, y, color = C.amber, alpha = 1, align = 'left', size = 84) {
  if (alpha <= 0) return;
  txt(label, x, y, { size: 24, weight: 800, color: C.dim, align, track: 4, alpha });
  txt(value, x, y + size + 4, { size, weight: 900, color, align, alpha });
}
/** linha de cota entre dois pontos 3D (desenhada no overlay, grossa e legível) */
export function dim3D(a, b, label, k = 1, color = C.amber) {
  const A = toScreen(a), B = toScreen(b); if (!A || !B || k <= 0) return;
  const E = { x: lerp(A.x, B.x, k), y: lerp(A.y, B.y, k) };
  g.save(); g.strokeStyle = color; g.lineWidth = 4; g.setLineDash([16, 10]); g.shadowColor = color; g.shadowBlur = 12;
  g.beginPath(); g.moveTo(A.x, A.y); g.lineTo(E.x, E.y); g.stroke(); g.restore();
  if (k > .7) txt(label, (A.x + B.x) / 2, (A.y + B.y) / 2 - 22, { size: 48, weight: 900, color, align: 'center', alpha: seg(k, .7, 1) });
}
export const brl = v => 'R$ ' + Math.round(v).toLocaleString('pt-BR');

export function hud(t, { brand = 'MAPA DO CRIME', caso = '', chapters = {}, clock = () => ['', ''] } = {}, alpha = 1) {
  if (alpha <= 0) return;
  g.save(); g.globalAlpha = alpha;
  g.fillStyle = C.red; g.fillRect(64, 54, 16, 16);
  txt(brand, 94, 70, { size: 26, weight: 900, track: 4 });
  txt(caso, 64, 108, { size: 22, weight: 600, color: C.dim, track: 2 });
  const [d, h] = clock(t);
  txt(d, W - 64, 70, { size: 24, weight: 800, color: C.dim, align: 'right', track: 3 });
  txt(h, W - 64, 118, { size: /^\d\d:\d\d$/.test(h) ? 48 : 28, weight: 900, color: C.amber, align: 'right', track: 2 });
  const { s, local } = sceneAt(t); const ch = chapters[s.id];
  if (ch) {
    const k = eout(clamp(local / .5)); g.globalAlpha = alpha * k; g.font = `800 24px ${FONT}`; g.letterSpacing = '4px';
    const cw = g.measureText(ch).width + 44; const cx = 64 - (1 - k) * 40;
    g.fillStyle = C.ink; g.fillRect(cx, 146, cw, 50); g.fillStyle = C.red; g.fillRect(cx, 146, 6, 50);
    txt(ch, cx + 22, 180, { size: 24, weight: 800, track: 4, alpha: alpha * k, shadow: false });
  }
  g.restore();
}

/* legendas: frases do SRT quebradas em blocos de ~5 palavras, 64px, palavras-chave em âmbar */
let CHUNKS = null;
export function caption(t, hilite = /\d/, size = 64) {
  if (!CHUNKS) {
    CHUNKS = [];
    for (const s of TL.scenes) for (const c of s.cues) {
      const words = c.text.split(/\s+/); const groups = []; let gp = [];
      for (const w of words) { gp.push(w); const len = gp.join(' ').length; if (len > 24 || (/[.,:;]$/.test(w) && len > 10)) { groups.push(gp); gp = []; } }
      if (gp.length) groups.push(gp);
      const tot = groups.reduce((a, x) => a + x.join(' ').length, 0); let tt = c.start;
      for (const x of groups) { const d = (c.end - c.start) * x.join(' ').length / tot; CHUNKS.push({ start: tt, end: tt + d, words: x }); tt += d; }
    }
  }
  const c = CHUNKS.find(c => t >= c.start && t < c.end + .05); if (!c) return;
  const k = eout(clamp((t - c.start) / .12));
  g.save(); g.font = `900 ${size}px ${FONT}`; g.letterSpacing = '0px';
  const parts = c.words.map(w => ({ w: w.toUpperCase(), wd: g.measureText(w.toUpperCase()).width })); const sp = size * .28;
  const tot = parts.reduce((a, p) => a + p.wd, 0) + sp * (parts.length - 1);
  let x = W / 2 - tot / 2; const y = H - 110 + (1 - k) * 12;
  g.globalAlpha = k; g.fillStyle = 'rgba(0,0,0,.82)';
  g.beginPath(); g.roundRect(W / 2 - tot / 2 - 32, y - size - 2, tot + 64, size + 36, 14); g.fill();
  for (const p of parts) { g.fillStyle = hilite.test(p.w.replace(/[.,:;]/g, '')) ? C.amber : '#fff'; g.fillText(p.w, x, y + 10); x += p.wd + sp; }
  g.restore();
}
export function vignette() {
  const v = g.createRadialGradient(W / 2, H / 2, H * .45, W / 2, H / 2, H * .95);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.45)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
}

/** registra a função de quadro: draw(t) posiciona a cena; overlay(t) desenha por cima */
export function run(draw, overlay) {
  window.renderFrame = t => { g.clearRect(0, 0, W, H); draw(t); renderer.render(scene, camera); overlay(t); return true; };
  window.READY = true;
}
