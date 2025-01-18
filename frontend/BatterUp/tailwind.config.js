/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'custom-blue': '#041e42', 
        'custom-gold': '#eece70',
        'custom-red': '#bf0d3e',
      },
    },
  },
  plugins: [],
}
