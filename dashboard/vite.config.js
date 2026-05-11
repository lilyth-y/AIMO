import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    const apiTarget = env.VITE_API_URL || 'http://localhost:8080';

    return {
        plugins: [react()],
        root: '.',
        publicDir: 'public',
        build: {
            outDir: 'dist',
        },
        server: {
            port: 5176,
            host: '0.0.0.0',
            strictPort: false,
            proxy: {
                '/api': {
                    target: apiTarget,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ''),
                },
            },
        },
    };
});
