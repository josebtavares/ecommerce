// "Resolver" da barra de requisitos (components/loja/BarraProntidao): depois de mudar de secção, rola até à parte
// exacta da página onde se resolve (marcada com data-alvo="<chave>"), destaca-a uns segundos e põe o cursor no
// primeiro campo. A secção pode ainda estar a carregar: espera até ESPERA_MS pelo elemento; se não aparecer
// (ex.: sem permissão para essa parte) fica só a secção.
const ESPERA_MS = 5000
const DESTAQUE_MS = 2600
// alvos que não são data-alvo: o primeiro produto incompleto da lista (BackofficeProdutos); sem nenhum (a loja ainda
// não tem produtos), o botão "Novo produto" — só depois de RESERVA_MS, para a lista ter tempo de carregar
const RESERVA_MS = 1500
const SELETORES = {
  produto: ['[data-teste="produto-incompleto"]', '[data-alvo="produto-novo"]'],
  produtos: ['[data-teste="produto-incompleto"]'],
}
const CAMPOS = 'input:not([type=hidden]):not([type=file]):not([disabled]), textarea:not([disabled]), select:not([disabled])'

let pedido = 0

function visivel (sel) {
  return [...document.querySelectorAll(sel)].find(el => el.offsetParent !== null || el.getClientRects().length) || null
}

function procurar (chave, passou) {
  const [principal, reserva] = SELETORES[chave] || [`[data-alvo~="${chave}"]`]
  return visivel(principal) || (reserva && passou > RESERVA_MS ? visivel(reserva) : null)
}

function destacar (el) {
  el.classList.remove('alvo-destaque')
  void el.offsetWidth      // reinicia a animação se já estava destacado
  el.classList.add('alvo-destaque')
  setTimeout(() => el.classList.remove('alvo-destaque'), DESTAQUE_MS)
}

export function focarAlvo (chave) {
  if (!chave || typeof document === 'undefined') return Promise.resolve(false)
  const meu = ++pedido
  const inicio = Date.now()
  let ultimoTopo = null
  return new Promise(resolve => {
    const tentar = () => {
      if (meu !== pedido) return resolve(false)          // outro "Resolver" entretanto
      const el = procurar(chave, Date.now() - inicio)
      if (!el) {
        if (Date.now() - inicio > ESPERA_MS) return resolve(false)
        return setTimeout(tentar, 100)
      }
      // a secção acabou de abrir e ainda carrega dados (a altura da página muda): espera que o alvo pare de mexer
      const topo = el.getBoundingClientRect().top
      if (topo !== ultimoTopo && Date.now() - inicio < ESPERA_MS) {
        ultimoTopo = topo
        return setTimeout(tentar, 150)
      }
      const reduzir = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      el.scrollIntoView({ behavior: reduzir ? 'auto' : 'smooth', block: 'center' })
      destacar(el)
      const campo = el.matches(CAMPOS) ? el : el.querySelector(CAMPOS)
      if (campo) setTimeout(() => campo.focus({ preventScroll: true }), reduzir ? 0 : 350)
      // se algo ainda empurrar a página depois (imagens, avisos), volta a pôr o alvo à vista
      setTimeout(() => {
        if (meu !== pedido || !el.isConnected) return
        const r = el.getBoundingClientRect()
        if (r.bottom < 0 || r.top > window.innerHeight) el.scrollIntoView({ behavior: 'auto', block: 'center' })
      }, 1200)
      resolve(true)
    }
    // a secção nova só aparece depois do próximo render
    setTimeout(tentar, 50)
  })
}
