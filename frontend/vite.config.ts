import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';

export default defineConfig({
  plugins: [react(), cesium()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        configure: (proxy) => {
          let lastWarnTime = 0;
          proxy.on('error', (_err: any, _req: any, res: any) => {
            const now = Date.now();
            if (now - lastWarnTime > 3000) {
              console.log('\x1b[33m[vite:proxy]\x1b[0m Digital Twin backend warming up at http://127.0.0.1:8000 (retrying...)');
              lastWarnTime = now;
            }
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(503, {
                'Content-Type': 'application/json',
                'Retry-After': '1',
              });
              res.end(JSON.stringify({
                status: 'warming_up',
                message: 'Digital Twin backend is warming up or reloading. Retrying automatically...',
                code: 'BACKEND_WARMING_UP'
              }));
            }
          });
        }
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', () => {
            // Silently handle WebSocket disconnects during backend reload
          });
        }
      }
    }
  }
});
