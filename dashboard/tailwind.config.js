/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        serif: ['Georgia', 'Cambria', 'serif'],
      },
      typography: {
        invert: {
          css: {
            '--tw-prose-body': '#cbd5e1',
            '--tw-prose-headings': '#f8fafc',
            '--tw-prose-lead': '#94a3b8',
            '--tw-prose-links': '#22d3ee',
            '--tw-prose-bold': '#f8fafc',
            '--tw-prose-counters': '#64748b',
            '--tw-prose-bullets': '#475569',
            '--tw-prose-hr': '#1e293b',
            '--tw-prose-quotes': '#f1f5f9',
            '--tw-prose-quote-borders': '#1e293b',
            '--tw-prose-captions': '#94a3b8',
            '--tw-prose-code': '#e2e8f0',
            '--tw-prose-pre-code': '#e2e8f0',
            '--tw-prose-pre-bg': '#0f172a',
            '--tw-prose-th-borders': '#334155',
            '--tw-prose-td-borders': '#1e293b',
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
