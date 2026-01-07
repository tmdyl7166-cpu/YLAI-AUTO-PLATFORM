const BASE = process.env.CYPRESS_BASE_URL || 'http://localhost:3001';

module.exports = {
  e2e: {
    // 开发环境：dev-server 注入 __HEAD__/__FOOTER__/__ASSET_VERSION__
    baseUrl: BASE,
    specPattern: 'cypress/e2e/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
    setupNodeEvents(on, config) {
      config.env.ASSET_VERSION = process.env.ASSET_VERSION || 'dev';
      return config;
    },
  },
};
