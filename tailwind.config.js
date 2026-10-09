/** Tailwind v3 — только публичный сайт ZEA.
 *  Шаблоны ZEA Hub (templates/hub, partners, contracts, projects, team)
 *  используют Bootstrap и в сборку НЕ входят.
 *
 *  Дизайн-система «обведённый объём»: светлая база (молоко / туман),
 *  графитовый контур, приглушённые акценты лайм / коралл / небо. */
module.exports = {
  content: [
    './app/templates/index.html',
    './app/templates/site/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        milk:  '#FAF8F4',
        fog:   '#ECEEF1',
        ink:   { DEFAULT: '#17181C', soft: '#2B2D33' },
        muted: '#5A5D66',
        lime:  { DEFAULT: '#D4E89A', soft: '#F1F4E6', deep: '#A9BF5E' },
        coral: { DEFAULT: '#EFA28E', soft: '#F8E7E1', deep: '#CF8A76' },
        sky:   { DEFAULT: '#C3D5EE', soft: '#E3ECF8', deep: '#9DB4D6' },
        butter: '#E9D48E',
      },
      fontFamily: {
        display: ['Unbounded', 'Manrope', 'system-ui', 'sans-serif'],
        sans:    ['Manrope', 'system-ui', '-apple-system', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      maxWidth: {
        site: '78rem',
      },
    },
  },
  plugins: [],
};
