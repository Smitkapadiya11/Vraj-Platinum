// Compress Blender exports for the web: weld + dedup + meshopt geometry compression + WebP textures.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, weld, prune, reorder, quantize, meshopt, textureCompress } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});
const src = 'blender/out', dst = 'public/models';
fs.mkdirSync(dst, { recursive: true });
const only = process.argv.slice(2);
for (const f of fs.readdirSync(src).filter((f) => f.endsWith('.glb'))) {
  if (only.length && !only.some((o) => f.includes(o))) continue;
  const doc = await io.read(path.join(src, f));
  await doc.transform(
    dedup(), weld(), prune(),
    textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 86, resize: [2048, 2048] }),
    reorder({ encoder: MeshoptEncoder }), quantize({ quantizePosition: 16, quantizeNormal: 10, quantizeTexcoord: 14 }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  const out = path.join(dst, f);
  await io.write(out, doc);
  console.log(f, (fs.statSync(path.join(src, f)).size / 1024).toFixed(0) + 'KB ->', (fs.statSync(out).size / 1024).toFixed(0) + 'KB');
}
