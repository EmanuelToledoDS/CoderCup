module.exports = {
  content: ['./templates/**/*.html', './detector/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        noche: '#12182B',
        nochesoft: '#1B2340',
        faro: '#FFB84D',
        alerta: '#FF6B5B',
        seguro: '#4ECDC4',
        crema: '#F5F3EE',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        body: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  safelist: [
    { pattern: /bg-(noche|nochesoft|faro|alerta|seguro|crema)\/(10|20|30|40|50|60|70|80)/ },
    { pattern: /text-(noche|nochesoft|faro|alerta|seguro|crema)\/(10|20|30|40|50|60|70|80)/ },
    { pattern: /border-(noche|nochesoft|faro|alerta|seguro|crema)\/(10|20|30|40|50|60|70|80)/ },
  ],
  plugins: [],
}
