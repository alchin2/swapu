import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
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
  server: {
    proxy: {
      // Proxy all API requests to FastAPI backend
      '/auth': 'http://localhost:8000',
      '/items': 'http://localhost:8000',
      '/deals': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/chatrooms': 'http://localhost:8000',
      '/negotiate': 'http://localhost:8000',
      '/match': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
    },
  },
  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],
})
