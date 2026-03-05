/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{ts,tsx}'],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            colors: {
                // Primary B&W palette
                ink: {
                    50: '#f8f8f8',
                    100: '#f0f0f0',
                    200: '#e4e4e4',
                    300: '#d0d0d0',
                    400: '#a8a8a8',
                    500: '#737373',
                    600: '#525252',
                    700: '#3d3d3d',
                    800: '#262626',
                    900: '#171717',
                    950: '#0a0a0a',
                },
                // Accent neon-green for live indicators
                neon: {
                    DEFAULT: '#00ff88',
                    dim: '#00cc6a',
                },
                // Confidence tag colours
                high: '#22c55e',
                mid: '#f59e0b',
                low: '#ef4444',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'fade-in': 'fadeIn 0.3s ease-in-out',
                'slide-up': 'slideUp 0.25s ease-out',
                'blink': 'blink 1.2s step-start infinite',
            },
            keyframes: {
                fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
                slideUp: { '0%': { transform: 'translateY(8px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
                blink: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
            },
        },
    },
    plugins: [],
}
