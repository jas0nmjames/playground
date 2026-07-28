import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Relative asset paths so the built dist/ works from any URL (Netlify, GitHub Pages subfolder, file://)
  base: './',
  // PORT lets more than one dev session run at once without colliding.
  server: { port: Number(process.env.PORT) || 5174, open: true },
});
