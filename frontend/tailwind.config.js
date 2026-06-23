/** @type {import('tailwindcss').Config} */
// Tailwind v4 is configured via CSS (@import "tailwindcss" in src/index.css);
// this file exists mainly so tooling that expects a config can find one.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
