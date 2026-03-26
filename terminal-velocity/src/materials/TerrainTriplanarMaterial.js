
import * as THREE from 'three';

export function makeTerrainTriplanarMaterial(grassTex, rockTex, snowTex, macroTex, detailTex) {
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, roughness: 0.95, metalness: 0.0
  });

  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uGrass = { value: grassTex };
    shader.uniforms.uRock  = { value: rockTex };
    shader.uniforms.uSnow  = { value: snowTex };
    shader.uniforms.uMacro = { value: macroTex };
    shader.uniforms.uDetail= { value: detailTex };

    shader.uniforms.uScaleGrass = { value: 1/9.0 };
    shader.uniforms.uScaleRock  = { value: 1/6.0 };
    shader.uniforms.uScaleSnow  = { value: 1/7.0 };
    shader.uniforms.uScaleMacro = { value: 1/80.0 };
    shader.uniforms.uScaleDetail= { value: 1/3.5 };

    shader.uniforms.uAltLow  = { value: 3.8 };
    shader.uniforms.uAltHigh = { value: 9.5 };
    shader.uniforms.uDetailStrength = { value: 0.12 };

    shader.vertexShader = shader.vertexShader.replace(
      '#include <common>',
      `#include <common>
       varying vec3 vWorldPos;
       varying vec3 vWorldNormal;`
    );
    shader.vertexShader = shader.vertexShader.replace(
      '#include <begin_vertex>',
      `#include <begin_vertex>
       vWorldPos = (modelMatrix * vec4(transformed,1.0)).xyz;
       vWorldNormal = normalize(mat3(modelMatrix) * objectNormal);`
    );

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        uniform sampler2D uGrass, uRock, uSnow, uMacro, uDetail;
        uniform float uScaleGrass, uScaleRock, uScaleSnow, uScaleMacro, uScaleDetail;
        uniform float uAltLow, uAltHigh, uDetailStrength;
        varying vec3 vWorldPos; varying vec3 vWorldNormal;

        vec3 triplanarColor(sampler2D t, vec3 wp, vec3 wn, float sc) {
          vec3 n = abs(normalize(wn));
          n = pow(n, vec3(4.0)); // sharpen blending
          n /= (n.x + n.y + n.z + 1e-6);
          vec2 uvx = wp.zy * sc; // X projection uses YZ
          vec2 uvy = wp.xz * sc; // Y uses XZ (top-down)
          vec2 uvz = wp.xy * sc; // Z uses XY
          vec3 cx = texture2D(t, uvx).rgb;
          vec3 cy = texture2D(t, uvy).rgb;
          vec3 cz = texture2D(t, uvz).rgb;
          return cx * n.x + cy * n.y + cz * n.z;
        }
        float triplanarGray(sampler2D t, vec3 wp, vec3 wn, float sc) {
          vec3 c = triplanarColor(t, wp, wn, sc);
          return dot(c, vec3(0.3333));
        }`)
      .replace('#include <map_fragment>', `
        float alt = vWorldPos.y;
        float slope = 1.0 - clamp(vWorldNormal.y, 0.0, 1.0);

        vec3 grass = triplanarColor(uGrass, vWorldPos, vWorldNormal, uScaleGrass);
        vec3 rock  = triplanarColor(uRock,  vWorldPos, vWorldNormal, uScaleRock);
        vec3 snow  = triplanarColor(uSnow,  vWorldPos, vWorldNormal, uScaleSnow);

        float wGrass = smoothstep(uAltLow+1.5, uAltLow-0.5, alt) * (1.0 - smoothstep(0.2, 0.6, slope));
        float wRock  = smoothstep(0.15, 0.7, slope) * smoothstep(uAltLow-1.0, uAltHigh, alt);
        float wSnow  = smoothstep(uAltHigh-1.0, uAltHigh+1.8, alt);

        vec3 baseCol = (grass*wGrass + rock*wRock + snow*wSnow);
        baseCol /= max(0.0001, wGrass + wRock + wSnow);

        // Macro variation (broad color breakup)
        float macro = triplanarGray(uMacro, vWorldPos, vWorldNormal, uScaleMacro);
        baseCol *= mix(0.9, 1.12, macro);

        // Micro detail (grain/speckle)
        float det = triplanarGray(uDetail, vWorldPos, vWorldNormal, uScaleDetail);
        baseCol = mix(baseCol, baseCol*1.15, det * uDetailStrength);

        // Faux AO: prefer flats and low alt
        float ao = mix(0.7, 1.0, 1.0 - slope) * mix(0.82, 1.0, smoothstep(uAltLow-0.5, uAltHigh, alt));
        baseCol *= ao;

        vec4 texelColor = vec4(baseCol, 1.0);
        texelColor = mapTexelToLinear(texelColor);
        diffuseColor *= texelColor;
      `);
  };

  return mat;
}
