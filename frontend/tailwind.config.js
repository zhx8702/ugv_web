/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    fontFamily: {
      'orbitron': ['Orbitron', 'monospace'],
      'rajdhani': ['Rajdhani', 'sans-serif'],
      'mono': ['Share Tech Mono', 'monospace'],
      'exo': ['Exo 2', 'sans-serif'],
      'sans': ['Rajdhani', 'sans-serif'],
    },
    extend: {
      colors: {
        // Cyber Neon Color Palette
        cyber: {
          cyan: '#00f0ff',
          blue: '#0080ff',
          purple: '#8000ff',
          pink: '#ff00ff',
          green: '#00ff88',
          yellow: '#ffff00',
          orange: '#ff6b35',
          red: '#ff0040',
        },
        primary: {
          DEFAULT: '#00f0ff',
          hover: '#00d4e0',
          active: '#00b8c4',
          glow: 'rgba(0, 240, 255, 0.5)',
        },
        secondary: {
          DEFAULT: '#00ff88',
          hover: '#00e077',
          glow: 'rgba(0, 255, 136, 0.5)',
        },
        accent: {
          DEFAULT: '#ff6b35',
          hover: '#ff5722',
          glow: 'rgba(255, 107, 53, 0.5)',
        },
        danger: {
          DEFAULT: '#ff0040',
          hover: '#e00038',
          glow: 'rgba(255, 0, 64, 0.5)',
        },
        warning: {
          DEFAULT: '#ffff00',
          hover: '#e0e000',
          glow: 'rgba(255, 255, 0, 0.5)',
        },
        success: {
          DEFAULT: '#00ff88',
          hover: '#00e077',
          glow: 'rgba(0, 255, 136, 0.5)',
        },
        // Dark Theme - Deep Space
        dark: {
          bg: {
            primary: '#030712',
            secondary: '#0a1628',
            tertiary: '#111d32',
            card: 'rgba(10, 22, 40, 0.8)',
          },
          text: {
            primary: '#e0f7ff',
            secondary: '#8cb4c4',
            tertiary: '#4a6a7a',
          },
          border: '#1a3a4a',
        },
        // Grid/Line colors
        grid: {
          primary: 'rgba(0, 240, 255, 0.1)',
          secondary: 'rgba(0, 240, 255, 0.05)',
        }
      },
      boxShadow: {
        'neon-cyan': '0 0 5px #00f0ff, 0 0 20px rgba(0, 240, 255, 0.4), 0 0 40px rgba(0, 240, 255, 0.2)',
        'neon-green': '0 0 5px #00ff88, 0 0 20px rgba(0, 255, 136, 0.4), 0 0 40px rgba(0, 255, 136, 0.2)',
        'neon-orange': '0 0 5px #ff6b35, 0 0 20px rgba(255, 107, 53, 0.4), 0 0 40px rgba(255, 107, 53, 0.2)',
        'neon-red': '0 0 5px #ff0040, 0 0 20px rgba(255, 0, 64, 0.4), 0 0 40px rgba(255, 0, 64, 0.2)',
        'inner-glow': 'inset 0 0 20px rgba(0, 240, 255, 0.1)',
        'card': '0 4px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
      },
      backgroundImage: {
        'grid-pattern': `
          linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px)
        `,
        'cyber-gradient': 'linear-gradient(135deg, #030712 0%, #0a1628 50%, #111d32 100%)',
        'card-gradient': 'linear-gradient(135deg, rgba(0, 240, 255, 0.05) 0%, transparent 50%)',
        'glow-gradient': 'radial-gradient(ellipse at center, rgba(0, 240, 255, 0.15) 0%, transparent 70%)',
      },
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin': 'spin 1s linear infinite',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'fade-in': 'fadeIn 0.5s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'scan-line': 'scanLine 3s linear infinite',
        'data-stream': 'dataStream 20s linear infinite',
        'border-flow': 'borderFlow 3s linear infinite',
        'flicker': 'flicker 0.15s infinite',
        'typing': 'typing 2s steps(20) infinite',
        'radar-sweep': 'radarSweep 2s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'hud-corner': 'hudCorner 0.3s ease-out',
      },
      keyframes: {
        slideUp: {
          'from': { transform: 'translateY(20px)', opacity: '0' },
          'to': { transform: 'translateY(0)', opacity: '1' }
        },
        slideDown: {
          'from': { transform: 'translateY(-20px)', opacity: '0' },
          'to': { transform: 'translateY(0)', opacity: '1' }
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' }
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 5px #00f0ff, 0 0 10px rgba(0, 240, 255, 0.3)' },
          '50%': { boxShadow: '0 0 10px #00f0ff, 0 0 30px rgba(0, 240, 255, 0.5), 0 0 50px rgba(0, 240, 255, 0.3)' }
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' }
        },
        dataStream: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' }
        },
        borderFlow: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' }
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' }
        },
        typing: {
          '0%': { width: '0' },
          '50%': { width: '100%' },
          '100%': { width: '0' }
        },
        radarSweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' }
        },
        hudCorner: {
          'from': { clipPath: 'polygon(0 0, 0 0, 0 0, 0 0)' },
          'to': { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    }
  },
  plugins: []
}
