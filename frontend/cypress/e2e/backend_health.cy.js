describe('Backend health and echo', () => {
  const host = Cypress.env('API_HOST') || '127.0.0.1'
  const port = Cypress.env('API_PORT') || '8001'
  const proto = Cypress.env('API_PROTO') || 'http'
  const base = `${proto}://${host}:${port}`

  it('returns health JSON', () => {
    cy.request({ url: `${base}/health`, failOnStatusCode: false }).then((resp) => {
      expect(resp.status).to.eq(200)
      expect(resp.body).to.have.property('ok', true)
    })
  })
  it('echoes run payload', () => {
    cy.request({ method: 'POST', url: `${base}/api/run`, body: { x: 1 }, failOnStatusCode: false }).then((resp) => {
      expect(resp.status).to.eq(200)
      expect(resp.body).to.have.property('ok', true)
      expect(resp.body.echo).to.have.property('x', 1)
    })
  })
})
