/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#1e1e1e",
          elevated: "#2d2d2d",
          hover: "#3d3d3d",
        },
        accent: {
          DEFAULT: "#6366f1",
          hover: "#818cf8",
        },
        success: "#22c55e",
        warning: "#f59e0b",
        error: "#ef4444",
      },
    },
  },
  plugins: [],
};
