import { defineConfig } from 'windicss/helpers'

export default defineConfig({
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 健康科技主色调
        primary: {
          50: '#e6fff7',
          100: '#b3ffe6',
          200: '#80ffd5',
          300: '#4dffc4',
          400: '#1affb3',
          500: '#00ff9d', // 主色
          600: '#00cc7d',
          700: '#00995e',
          800: '#00663e',
          900: '#00331f'
        },
        // 科技蓝
        tech: {
          50: '#e6f7ff',
          100: '#b3e9ff',
          200: '#80dbff',
          300: '#4dcdff',
          400: '#1abfff',
          500: '#00e4ff', // 次要色
          600: '#00b7cc',
          700: '#008a99',
          800: '#005c66',
          900: '#002e33'
        },
        // 警告橙
        warning: {
          50: '#fff7e6',
          100: '#ffe9b3',
          200: '#ffdb80',
          300: '#ffcd4d',
          400: '#ffbf1a',
          500: '#ffa726',
          600: '#cc851f',
          700: '#996417',
          800: '#66420f',
          900: '#332108'
        },
        // 错误红
        error: {
          50: '#ffe6e6',
          100: '#ffb3b3',
          200: '#ff8080',
          300: '#ff4d4d',
          400: '#ff1a1a',
          500: '#ff6b6b',
          600: '#cc5555',
          700: '#994040',
          800: '#662a2a',
          900: '#331515'
        },
        // 背景色
        bg: {
          primary: '#0a1525',
          secondary: '#1a2332',
          card: 'rgba(6, 18, 25, 0.9)',
          overlay: 'rgba(0, 0, 0, 0.8)'
        }
      },
      fontFamily: {
        tech: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        display: ['Inter', 'PingFang SC', 'Hiragino Sans GB', 'sans-serif']
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'scan': 'scan 2s linear infinite',
        'data-flow': 'dataFlow 3s ease-in-out infinite'
      },
      keyframes: {
        glow: {
          '0%': { 
            'box-shadow': '0 0 5px rgba(0, 255, 157, 0.5)',
            'text-shadow': '0 0 10px rgba(0, 255, 157, 0.5)'
          },
          '100%': { 
            'box-shadow': '0 0 20px rgba(0, 255, 157, 0.8)',
            'text-shadow': '0 0 20px rgba(0, 255, 157, 0.8)'
          }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        scan: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        },
        dataFlow: {
          '0%': { transform: 'translateX(-100%) scaleX(0)' },
          '50%': { transform: 'translateX(0) scaleX(1)' },
          '100%': { transform: 'translateX(100%) scaleX(0)' }
        }
      },
      backdropBlur: {
        xs: '2px'
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem'
      }
    }
  },
  plugins: [
    require('windicss/plugin/aspect-ratio'),
    require('windicss/plugin/line-clamp'),
    require('windicss/plugin/scroll-snap')
  ],
  shortcuts: {
    // 快捷类
    'card-tech': 'bg-bg-card backdrop-blur-sm border border-primary-500/30 rounded-lg shadow-lg',
    'text-glow': 'text-primary-500 animate-glow',
    'btn-tech': 'bg-gradient-to-r from-primary-500 to-tech-500 text-white font-medium py-2 px-4 rounded-lg hover:shadow-lg transition-all duration-300',
    'glass-effect': 'bg-white/10 backdrop-blur-md border border-white/20',
    'neon-border': 'border border-primary-500 shadow-[0_0_10px_rgba(0,255,157,0.5)]'
  }
})