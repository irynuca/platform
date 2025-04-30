// chart_theme.js

// Get CSS variable values dynamically (from Bootstrap or your own theme)
function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  
  // Central chart color palette used across all charts
  window.chartTheme = {
    pink: {
      base: cssVar('--bs-pink'),
      hover: 'rgba(232, 62, 140, 0.7)',
      active: '#b52a6c'
    },
    red: {
      base: cssVar('--bs-red'),
      hover: 'rgba(238, 50, 50, 0.7)',
      active: '#b92424'
    },
    orange: {
      base: cssVar('--bs-orange'),
      hover: 'rgba(255, 153, 0, 0.7)',
      active: '#cc7a00'
    },
    yellow: {
      base: cssVar('--bs-yellow'),
      hover: 'rgba(255, 250, 111, 0.7)',
      active: '#d4d058'
    },
    green: {
      base: cssVar('--bs-green'),
      hover: 'rgba(41, 127, 0, 0.7)',
      active: '#1b5500'
    },
    teal: {
      base: cssVar('--bs-teal'),
      hover: 'rgba(32, 201, 151, 0.7)',
      active: '#178c6b'
    },
    cyan: {
      base: cssVar('--bs-cyan'),
      hover: 'rgba(48, 101, 208, 0.7)',
      active: '#254ba0'
    },
    primary: {
      base: cssVar('--bs-primary'),
      hover: 'rgba(83, 202, 253, 0.7)',
      active: '#027fb5'
    },
    secondary: {
      base: cssVar('--bs-secondary'),
      hover: 'rgba(228, 59, 255, 0.7)',
      active: '#9d2ea8'
    },
    success: {
      base: cssVar('--bs-success'),
      hover: 'rgba(30, 174, 122, 0.7)',
      active: '#167d56'
    },
    info: {
      base: cssVar('--bs-info'),
      hover: 'rgba(0, 175, 239, 0.7)',
      active: '#0083b2'
    },
    warning: {
      base: cssVar('--bs-warning'),
      hover: 'rgba(255, 170, 43, 0.7)',
      active: '#cc8421'
    },
    danger: {
      base: cssVar('--bs-danger'),
      hover: 'rgba(247, 43, 80, 0.7)',
      active: '#a8203f'
    },
    blue: {
      base: cssVar('--bs-blue'),
      hover: 'rgba(57, 25, 149, 0.7)',
      active: '#2c0d80'
    },
    indigo: {
      base: cssVar('--bs-indigo'),
      hover: 'rgba(102, 16, 242, 0.7)',
      active: '#430bbb'
    },
    purple: {
      base: cssVar('--bs-purple'),
      hover: 'rgba(111, 66, 193, 0.7)',
      active: '#4f2e9b'
    }
  };
  