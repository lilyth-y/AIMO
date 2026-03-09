import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    root: '.',
    publicDir: 'public',
    build: {
        outDir: 'dist',
    },
    server: {
        port: 5176,
        host: '0.0.0.0', // IPv4(127.0.0.1) + IPv6(::1) 모두 접속 가능
        strictPort: false,
    },
});
