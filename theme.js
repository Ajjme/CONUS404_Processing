module.exports = {
  theme: {
    extend: {
      colors: {
        circad: {
          red: '#AA2634',
          blue: '#205196',
          purple: '#673399',
          teal: '#2F8F7F',
          tan: '#D9A341',
          lightBlue: '#6FA8DC',
          iceBlue: '#E9ECEF',
          grey: '#333333',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      transitionTimingFunction: {
        'expo-out': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'quart-out': 'cubic-bezier(0.25, 1, 0.5, 1)',
      }
    },
  },
  plugins: [],
}