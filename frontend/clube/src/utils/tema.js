// Preferência de tema do site (uma só para todas as páginas). Claro por defeito;
// quem já escolheu fica com a escolha. 'home_dark_mode' é a chave antiga da home.
const CHAVE = 'theme_preference'

export function temaEscuro () {
  try {
    const t = localStorage.getItem(CHAVE)
    if (t) return t === 'dark'
    const home = localStorage.getItem('home_dark_mode')
    if (home !== null) return home === 'true'
  } catch (e) { /* sem localStorage: fica o defeito */ }
  return false
}

export function guardarTema (escuro) {
  try {
    localStorage.setItem(CHAVE, escuro ? 'dark' : 'light')
    localStorage.setItem('home_dark_mode', String(!!escuro))
  } catch (e) { /* sem localStorage: só nesta página */ }
}

// Páginas escritas só em escuro (backoffice, admin, criar loja, checkout...): no tema claro
// o <html> leva a classe 'tema-claro' e assets/tema-claro.css troca as cores. Fica no <html>
// para apanhar também os modais teleportados para o <body>.
export function aplicarTemaPainel (escuro) {
  document.documentElement.classList.toggle('tema-claro', !escuro)
}

export function sairTemaPainel () {
  document.documentElement.classList.remove('tema-claro')
}

// Mixin das páginas escritas só em escuro: isDark + alternarTema(), e a classe no <html>.
export const temaPainel = {
  data () { return { isDark: temaEscuro() } },
  watch: {
    isDark (v) { guardarTema(v); aplicarTemaPainel(v) },
  },
  created () { aplicarTemaPainel(this.isDark) },
  unmounted () { sairTemaPainel() },
  methods: {
    alternarTema () { this.isDark = !this.isDark },
  },
}
