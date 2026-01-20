/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1F3A5F",
        secondary: "#6B7280",
        background: "#F5F7FA",
        card: "#FFFFFF",

        riskLow: "#2E7D32",
        riskMedium: "#F9A825",
        riskHigh: "#C62828",
      },
    },
  },
  plugins: [],
};
