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
        // Custom ZKP theme colors
        zkp: {
          primary: '#6366f1',    // Indigo
          secondary: '#8b5cf6',  // Violet
          accent: '#06b6d4',     // Cyan
          success: '#10b981',    // Emerald
          warning: '#f59e0b',    // Amber
          error: '#ef4444',      // Red
          dark: {
            bg: '#0f172a',       // Slate 900
            card: '#1e293b',     // Slate 800
            border: '#334155',   // Slate 700
          }
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
        'bounce-slow': 'bounce 2s infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'fold': 'fold 1.5s ease-in-out infinite',
        'flow': 'flow 3s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgb(99 102 241 / 0.5), 0 0 10px rgb(99 102 241 / 0.3)' },
          '100%': { boxShadow: '0 0 20px rgb(99 102 241 / 0.8), 0 0 40px rgb(99 102 241 / 0.5)' }
        },
        fold: {
          '0%, 100%': { transform: 'scaleY(1)', opacity: 1 },
          '50%': { transform: 'scaleY(0.5)', opacity: 0.7 }
        },
        flow: {
          '0%': { strokeDashoffset: 1000 },
          '100%': { strokeDashoffset: 0 }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      }
    },
  },
  plugins: [],
}
