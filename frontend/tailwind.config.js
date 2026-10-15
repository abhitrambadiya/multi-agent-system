/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        hq: {
          bg: '#0D0F12',
          s1: '#171A20',
          s2: '#1e222a',
          ln: '#262b35',
          ink: '#e6e8ee',
          mu: '#8b93a3',
          ac: '#8b7cff',
          ok: '#4cc38a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
