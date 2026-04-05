import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.smoke.test.{ts,tsx}'],
    exclude: ['node_modules', 'e2e'],
    testTimeout: 10000,
  },
});
