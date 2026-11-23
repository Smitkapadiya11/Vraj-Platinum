import { defineConfig } from 'vite';

export default defineConfig({
  define: { __BUILD__: JSON.stringify(Date.now().toString(36)) },
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 1200,
    rollupOptions: { output: { manualChunks: (id: string) => (id.includes('node_modules/three') ? 'three' : id.includes('node_modules/gsap') ? 'gsap' : undefined) } },
  },
  server: { host: true },
});
