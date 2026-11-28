import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';

function nonBlockingCesiumAssets(): Plugin {
  return {
    name: 'non-blocking-cesium-assets',
    enforce: 'post',
    transformIndexHtml(html: string): string {
      return html
        .replace(
          /<link\s+rel="stylesheet"\s+href="(\/cesium\/Widgets\/widgets\.css)"\s*\/?>/i,
          '<link rel="stylesheet" href="$1" media="print" onload="this.media=\'all\'" />'
        )
        .replace(
          /<script\s+src="(\/cesium\/Cesium\.js)"\s*><\/script>/i,
          '<script defer src="$1"></script>'
        );
    }
  };
}

export default defineConfig({
  plugins: [react(), cesium(), nonBlockingCesiumAssets()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api/v1/stream': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true
      },
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
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string): string | undefined {
          const normId = id.replace(/\\/g, '/');
          if (!normId.includes('/node_modules/')) {
            return undefined;
          }
          if (normId.includes('/node_modules/cesium/') || normId.includes('/node_modules/@cesium/')) {
            return 'vendor-cesium';
          }
          if (normId.includes('/node_modules/mapbox-gl/') || normId.includes('/node_modules/maplibre-gl/')) {
            return 'vendor-mapbox';
          }
          if (normId.includes('/node_modules/framer-motion/')) {
            return 'vendor-motion';
          }
          if (normId.includes('/node_modules/lucide-react/')) {
            return 'vendor-icons';
          }
          if (
            normId.includes('/node_modules/react/') ||
            normId.includes('/node_modules/react-dom/') ||
            normId.includes('/node_modules/scheduler/')
          ) {
            return 'vendor-react';
          }
          return undefined;
        }
      }
    }
  }
});
