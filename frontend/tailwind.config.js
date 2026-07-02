/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        shl: {
          green: '#86BC25',
          dark: '#333333',
          light: '#F5F5F5',
        },
      },
    },
  },
  plugins: [],
}
