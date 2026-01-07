/// <reference types="cypress" />

// Auth + Navigation flow: ensures login token persists across pages
describe('Auth Flow and Navigation', () => {
  const base = 'http://127.0.0.1:8001';

  it('login.html sets token and redirects to monitor', () => {
    cy.visit(base + '/pages/login.html');
    // Fill minimal valid values
    cy.get('#account').type('admin@example.com');
    cy.get('#password').type('admin123');
    cy.get('#loginBtn').click();
    // After fake/demo login, token should be set in localStorage
    cy.window().then(win => {
      const token = win.localStorage.getItem('yl_token');
      expect(token).to.be.a('string').and.not.be.empty;
    });
    // Redirect to monitor.html
    cy.url({ timeout: 5000 }).should('include', '/pages/monitor.html');
  });

  it('token is readable on index.html and api-doc.html', () => {
    // Visit index
    cy.visit(base + '/pages/index.html');
    cy.window().then(win => {
      const token = win.localStorage.getItem('yl_token');
      expect(token).to.be.a('string').and.not.be.empty;
    });
    // Visit api-doc
    cy.visit(base + '/pages/api-doc.html');
    cy.window().then(win => {
      const token = win.localStorage.getItem('yl_token');
      expect(token).to.be.a('string').and.not.be.empty;
    });
  });

  it('index modules run navigates to run.html with script param', () => {
    cy.visit(base + '/pages/index.html');
    // Ensure modules are rendered and click the first card run button
    cy.get('#modules-list .module-card .btn[data-act="run"]', { timeout: 10000 })
      .first()
      .click();
    cy.url({ timeout: 5000 }).should('include', '/pages/run.html?script=');
  });
});
