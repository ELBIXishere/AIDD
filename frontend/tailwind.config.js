/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0f172a',
        'bg-secondary': '#1e293b',
        'bg-tertiary': '#334155',
        'accent': '#3b82f6',
        'accent-light': '#60a5fa',
        'accent-dark': '#2563eb',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'sans': ['Pretendard', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
