/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#000000',
        'input-surface': '#1E1E20',
        'input-focus': '#252528',
        'text-primary': '#E3E3E3',
        'text-secondary': '#9CA3AF',
        'accent-blue': '#A8C7FA',
        'chip-bg': '#1E3A8A',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'pill': '32px',
      },
    },
  },
  plugins: [],
}
