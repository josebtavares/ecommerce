<!-- PesquisaGlobal.vue — lupa do cabeçalho (ao lado do carrinho, ver multiCart.vue) que abre a pesquisa:
     ecrã inteiro no telemóvel, painel no topo no computador. Atalhos: "/" ou Ctrl/⌘+K. -->
<template>
  <!-- campo: no computador, caixa larga "Pesquisar…" (abre o mesmo painel); no telemóvel fica a lupa -->
  <button v-if="campo" type="button" @click="abrir" aria-label="Pesquisar" data-teste="pesquisa-topo"
    class="pesquisa-topo hidden md:flex items-center gap-2.5 px-4 rounded-full border text-sm transition shadow-sm"
    :class="isDark ? 'bg-zinc-900/90 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200'
                   : 'bg-white/95 border-stone-300 text-zinc-500 hover:border-stone-400 hover:text-zinc-700'">
    <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="text-[14px] flex-shrink-0" />
    <span class="flex-1 text-left truncate"><span class="lg:hidden">Pesquisar…</span><span class="hidden lg:inline">Pesquisar produtos, lojas…</span></span>
    <kbd class="text-[11px] font-mono px-1.5 py-0.5 rounded border flex-shrink-0"
         :class="isDark ? 'border-zinc-700 text-zinc-500' : 'border-stone-300 text-zinc-400'">/</kbd>
  </button>
  <button type="button" @click="abrir" aria-label="Pesquisar" title="Pesquisar (/)" data-teste="pesquisa-lupa"
    class="loja-acao-btn" :class="[campo ? 'md:!hidden' : '', isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200']"
>
    <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="text-[15px]" :class="isDark ? 'text-white' : 'text-zinc-700'" />
  </button>

  <teleport to="body">
    <transition enter-active-class="transition duration-150" enter-from-class="opacity-0"
                leave-active-class="transition duration-100" leave-to-class="opacity-0">
      <div v-if="aberta" class="fixed inset-0 z-[1000] bg-black/60 backdrop-blur-sm md:pt-[10vh]" @click.self="fechar"
           data-teste="pesquisa-painel">
        <div role="dialog" aria-modal="true" aria-label="Pesquisar"
             class="w-full h-full md:h-auto md:max-h-[75vh] md:max-w-2xl md:mx-auto md:rounded-2xl md:border shadow-2xl flex flex-col overflow-hidden"
             :class="isDark ? 'bg-zinc-950 md:border-zinc-800' : 'bg-white md:border-stone-200'">
          <div class="flex-1 overflow-y-auto overscroll-contain px-3 pt-3 md:px-4 md:pt-4 pb-4">
            <CaixaPesquisa ref="caixa" painel :isDark="isDark" @fechar="fechar">
              <template #lado>
                <button type="button" @click="fechar" class="px-2 h-12 text-sm font-semibold flex-shrink-0"
                  :class="isDark ? 'text-zinc-300 hover:text-white' : 'text-zinc-600 hover:text-zinc-900'">Cancelar</button>
              </template>
            </CaixaPesquisa>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script>
import CaixaPesquisa from './CaixaPesquisa.vue'

export default {
  name: 'PesquisaGlobal',
  components: { CaixaPesquisa },
  props: {
    isDark: { type: Boolean, default: true },
    campo: { type: Boolean, default: false },
  },

  data () { return { aberta: false } },

  watch: {
    '$route.fullPath' () { this.aberta = false },
    aberta (v) { document.documentElement.style.overflow = v ? 'hidden' : '' },
  },

  mounted () { document.addEventListener('keydown', this.atalho) },
  beforeUnmount () {
    document.removeEventListener('keydown', this.atalho)
    document.documentElement.style.overflow = ''
  },

  methods: {
    abrir () {
      this.aberta = true
      this.$nextTick(() => this.$refs.caixa?.focar())
    },
    fechar () { this.aberta = false },
    atalho (e) {
      const escrever = /^(input|textarea|select)$/i.test(e.target?.tagName || '') || e.target?.isContentEditable
      if ((e.key === '/' && !escrever) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')) {
        e.preventDefault()
        this.abrir()
      }
    },
  },
}
</script>

<style scoped>
.pesquisa-topo { height: var(--acoes-botao, 36px); width: clamp(240px, 26vw, 380px); }
</style>
