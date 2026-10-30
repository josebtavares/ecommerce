<!-- Turnstile.vue — "não sou um robô" da Cloudflare (backend: utils/turnstile.py).
     Sem VUE_APP_TURNSTILE_SITE_KEY não mostra nada e o v-model fica '' (o backend também não verifica).
     v-model = a resposta a mandar no campo `turnstile`; repor() depois de um erro (cada resposta só vale uma vez).
     A política de segurança (scripts/csp.js) deixa carregar challenges.cloudflare.com quando há chave. -->
<template>
  <div v-if="chave" class="flex justify-center min-h-[65px]" data-teste="turnstile">
    <div ref="caixa"></div>
  </div>
</template>

<script>
const CHAVE = process.env.VUE_APP_TURNSTILE_SITE_KEY || ''
const SCRIPT = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
let carregar = null

// o script da Cloudflare, uma só vez para o site todo
function script () {
  if (window.turnstile) return Promise.resolve(window.turnstile)
  if (!carregar) {
    carregar = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = SCRIPT
      s.async = true
      s.onload = () => resolve(window.turnstile)
      s.onerror = () => { carregar = null; reject(new Error('turnstile')) }
      document.head.appendChild(s)
    })
  }
  return carregar
}

export default {
  name: 'TurnstileWidget',
  props: {
    modelValue: { type: String, default: '' },
    isDark:     { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'erro'],

  data () {
    return { chave: CHAVE, id: null }
  },

  async mounted () {
    if (!this.chave) return
    try {
      const ts = await script()
      if (!this.$refs.caixa) return          // a página mudou entretanto
      this.id = ts.render(this.$refs.caixa, {
        sitekey: this.chave,
        theme: this.isDark ? 'dark' : 'light',
        language: 'pt',
        callback: t => this.$emit('update:modelValue', t),
        'expired-callback': () => this.$emit('update:modelValue', ''),
        'error-callback': () => { this.$emit('update:modelValue', ''); this.$emit('erro') },
      })
    } catch (e) {
      this.$emit('erro')
    }
  },

  beforeUnmount () {
    if (this.id !== null && window.turnstile) window.turnstile.remove(this.id)
  },

  methods: {
    repor () {
      this.$emit('update:modelValue', '')
      if (this.id !== null && window.turnstile) window.turnstile.reset(this.id)
    },
  },
}
</script>
