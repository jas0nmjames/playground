import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Relative asset paths so the built dist/ works from any URL (Netlify, GitHub Pages subfolder, file://)
  base: './',
  server: { port: 5174, open: true },
});
