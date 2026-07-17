/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        liturgical: {
          gold: "#d4af37",
          goldHover: "#f3e5ab",
          slavonic: "#f59e0b",
        }
      }
    },
  },
  plugins: [],
}
