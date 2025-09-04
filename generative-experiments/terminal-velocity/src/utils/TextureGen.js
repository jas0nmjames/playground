
import * as THREE from 'three';

function makeCanvas(size = 256) { const c = document.createElement('canvas'); c.width = c.height = size; return c; }

function noise2D(x, y, seed=1337) {
  const n = Math.sin(x * 127.1 + y * 311.7 + seed) * 43758.5453123;
  return n - Math.floor(n);
}
function fbm(x, y, oct=4, seed=1337) {
  let f=0, amp=0.5, freq=1.0;
  for (let i=0;i<oct;i++) { f += noise2D(x*freq, y*freq, seed+i*1000)*amp; amp*=0.5; freq*=2.0; }
  return f;
}
function paint(c, fn) {
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(c.width, c.height);
  const d = img.data;
  for (let y=0; y<c.height; y++) for (let x=0; x<c.width; x++) {
    const i = (y*c.width + x) * 4;
    const [r,g,b,a] = fn(x/c.width, y/c.height);
    d[i]=r; d[i+1]=g; d[i+2]=b; d[i+3]=a;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

export function generateGrassTexture(size=512) {
  const c = makeCanvas(size);
  paint(c, (u,v) => {
    const n = fbm(u*8, v*8, 4, 42);
    const g = 120 + Math.floor(70 * n);
    const r = 45 + Math.floor(20 * n);
    const b = 45 + Math.floor(20 * n);
    return [r, g, b, 255];
  });
  const tex = new THREE.CanvasTexture(c); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.needsUpdate = true; return tex;
}

export function generateRockTexture(size=512) {
  const c = makeCanvas(size);
  paint(c, (u,v) => {
    const n = fbm(u*6, v*6, 5, 31415);
    const g = 110 + Math.floor(60 * n);
    const r = 100 + Math.floor(30 * n);
    const b = 100 + Math.floor(30 * n);
    return [r, g, b, 255];
  });
  const tex = new THREE.CanvasTexture(c); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.needsUpdate = true; return tex;
}

export function generateSnowTexture(size=512) {
  const c = makeCanvas(size);
  paint(c, (u,v) => {
    const n = fbm(u*4, v*4, 3, 7);
    const base = 235 + Math.floor(20 * n);
    return [base, base, base+5, 255];
  });
  const tex = new THREE.CanvasTexture(c); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.needsUpdate = true; return tex;
}

// Macro noise (broad color breakup)
export function generateMacroNoise(size=512) {
  const c = makeCanvas(size);
  paint(c, (u,v) => {
    const n = fbm(u*2.0, v*2.0, 5, 9001); // slow-varying
    const g = Math.floor(n*255);
    return [g, g, g, 255];
  });
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.needsUpdate = true; return tex;
}

// Micro detail (grain)
export function generateDetailNoise(size=512) {
  const c = makeCanvas(size);
  paint(c, (u,v) => {
    const n = fbm(u*24.0, v*24.0, 4, 1338); // fast-varying
    const g = Math.floor(n*255);
    return [g, g, g, 255];
  });
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.needsUpdate = true; return tex;
}
