// Mixin das secções da landing: `visivel` passa a true quando a secção entra no ecrã (para as animações de entrada).
// Sem IntersectionObserver (ou com "reduzir movimento"), fica logo visível.
export default {
  data () { return { visivel: false } },
  mounted () {
    const reduzir = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (!('IntersectionObserver' in window) || reduzir) { this.visivel = true; return }
    this.observador = new IntersectionObserver(entradas => {
      if (entradas.some(e => e.isIntersecting)) { this.visivel = true; this.observador.disconnect() }
    }, { rootMargin: '0px 0px -15% 0px' })
    this.observador.observe(this.$el)
  },
  beforeUnmount () { this.observador?.disconnect() },
}
