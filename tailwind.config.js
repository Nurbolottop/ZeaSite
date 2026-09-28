/** Tailwind v3 — только публичный сайт ZEA.
 *  Шаблоны ZEA Hub (templates/hub, partners, contracts, projects, team)
 *  используют Bootstrap и в сборку НЕ входят. */
module.exports = {
  content: [
    './app/templates/index.html',
    './app/templates/site/**/*.html',
  ],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
    },
  },
  plugins: [],
};
