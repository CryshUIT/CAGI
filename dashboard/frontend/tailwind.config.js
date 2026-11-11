/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#060D1B",
        sidebar: "#091426",
        card: "#0D1B30",
        elevated: "#11243C",
        border: "#203650",
        accent: "#00D4F5",
        accent2: "#1C9BFF",
        early: "#18D6A3",
        late: "#FFBA36",
        danger: "#FF5267",
        neutral: "#91A6C2",
        text: "#F3F7FC",
        textSecondary: "#93A9C4",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
