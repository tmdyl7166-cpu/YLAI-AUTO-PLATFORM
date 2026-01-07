describe('Pages injection and linking', () => {
  const pages = ['index','api-doc','run','monitor','ai-demo','login','rbac','api-map']
  pages.forEach(p => {
    it(`validates head/footer/version/aria/script for ${p}.html`, () => {
      cy.request(`/pages/${p}.html`).its('status').should('eq', 200)
      cy.request(`/pages/${p}.html`).then(({body}) => {
        expect(body).to.include('modulepreload')
        expect(body).to.include('© 2025')
        expect(body).to.include('v=')
        expect(body).to.match(/aria-live=["']polite["']/)
        expect(body).to.match(/<script[^>]*type=["']module["'][^>]*defer/)
      })
    })
  })

  const generated = ['index','log','collect-task','crack-task','enum-task','param_deploy','recognize-task','smart-schedule','status','workflow-deploy']
  generated.forEach(p => {
    it(`validates footer/version/aria for generated/${p}.html`, () => {
      cy.request(`/pages/generated/${p}.html`).its('status').should('eq', 200)
      cy.request(`/pages/generated/${p}.html`).then(({body}) => {
        expect(body).to.include('© 2025')
        expect(body).to.include('v=')
        expect(body).to.match(/aria-live=["']polite["']/)
      })
    })
  })
})
