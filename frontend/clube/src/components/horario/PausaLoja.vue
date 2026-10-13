<template>
  <!-- "Fechar agora": fecha a loja para encomendas por um tempo (POST /app/loja/<id>/pausa/).
       Encomendas, Configurações → Horário. Quem trata das encomendas (também o staff) pode usar. -->
  <div v-if="estado" ref="raiz" class="bg-zinc-900 rounded-2xl border px-4 py-3 flex flex-wrap items-center gap-3"
       :class="estado.pausa_ate ? 'border-amber-500/40' : 'border-zinc-800'">
    <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :class="estado.aberta ? 'bg-green-500' : 'bg-amber-500'"></span>
    <p class="text-sm text-zinc-300 mr-auto">
      <template v-if="estado.pausa_ate">Fechaste a loja até às <b class="text-zinc-100">{{ estado.pausa_hora }}</b> — não entram encomendas para agora.</template>
      <template v-else>Loja: <b class="text-zinc-100">{{ estado.texto }}</b></template>
    </p>

    <button v-if="estado.pausa_ate" type="button" @click="enviar({ reabrir: true })" :disabled="aGuardar"
      class="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-bold">
      Reabrir já
    </button>
    <div v-else-if="estado.aberta" class="relative">
      <button type="button" @click="menu = !menu" :aria-expanded="menu ? 'true' : 'false'"
        class="px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-zinc-200 text-xs font-semibold">
        <font-awesome-icon :icon="['fas', 'pause']" class="mr-1" />Fechar agora
      </button>
      <div v-if="menu" class="absolute right-0 top-full mt-2 z-30 w-56 bg-zinc-900 border border-zinc-700 rounded-xl p-1.5 shadow-xl" role="menu">
        <p class="text-[11px] text-zinc-500 px-2 py-1">Não aceitar encomendas para agora…</p>
        <button v-for="o in OPCOES" :key="o.label" type="button" role="menuitem" @click="enviar(o.corpo)"
          class="w-full text-left px-2 py-1.5 rounded-lg text-sm text-zinc-200 hover:bg-zinc-800">{{ o.label }}</button>
        <button v-if="estado.horario_ativo" type="button" role="menuitem" @click="enviar({ ate_fechar: true })"
          class="w-full text-left px-2 py-1.5 rounded-lg text-sm text-zinc-200 hover:bg-zinc-800">Até ao fim do horário de hoje</button>
      </div>
    </div>
    <p v-if="erro" class="w-full text-xs text-red-400" role="alert">{{ erro }}</p>
  </div>
</template>

<script>
import api from '@/services/api'

const OPCOES = [
  { label: 'Durante 15 minutos', corpo: { minutos: 15 } },
  { label: 'Durante 30 minutos', corpo: { minutos: 30 } },
  { label: 'Durante 1 hora',     corpo: { minutos: 60 } },
  { label: 'Durante 2 horas',    corpo: { minutos: 120 } },
]

export default {
  name: 'PausaLoja',
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['alterado'],

  data () {
    return { OPCOES, estado: null, menu: false, aGuardar: false, erro: '', timer: null }
  },

  created () { this.carregar() },
  beforeUnmount () { clearInterval(this.timer) },
  mounted () {
    this.timer = setInterval(this.carregar, 60000)     // a pausa acaba sozinha
    document.addEventListener('click', this.fecharMenu)
  },
  unmounted () { document.removeEventListener('click', this.fecharMenu) },

  methods: {
    fecharMenu (e) { if (this.menu && !this.$refs.raiz?.contains(e.target)) this.menu = false },   // $el seria o comentário do topo
    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/estado/`)
        this.estado = data
      } catch (e) { /* sem permissão → não mostra */ }
    },
    async enviar (corpo) {
      this.menu = false
      this.aGuardar = true
      this.erro = ''
      try {
        await api.post(`/app/loja/${this.lojaId}/pausa/`, corpo)
        await this.carregar()
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível mudar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
