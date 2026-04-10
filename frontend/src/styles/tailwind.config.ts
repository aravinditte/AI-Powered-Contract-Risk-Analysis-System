import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1F3A5F",
        secondary: "#6B7280",
        background: "#F5F7FA",
      },
    },
  },
  plugins: [],
} satisfies Config;
