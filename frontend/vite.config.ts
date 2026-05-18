import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'


function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '')
        return path.resolve(__dirname, 'src/assets', filename)
      }
    },
  }
}

export default defineConfig({
  plugins: [
    figmaAssetResolver(),
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    // Same-origin proxy so the browser never calls localhost:8000 cross-origin.
    proxy: {
      '/locations': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/places': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/routes': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/weather': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ai': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/users': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
    watch: {
      usePolling: true,
      interval: 250,
    },
    hmr: {
      host: '127.0.0.1',
      protocol: 'ws',
      clientPort: 5173,
    },
  },
})
