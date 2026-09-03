import react from '@vitejs/plugin-react';

export default {
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
};
