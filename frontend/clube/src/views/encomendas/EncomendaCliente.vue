<template>
  <!-- /encomendas/<id> — ficha de uma encomenda do cliente (os avisos e os emails apontam para aqui). Tempo real.
       Só o comprador a vê aqui: quem é da loja vai para a ficha do backoffice; outra pessoa vê "não encontrada". -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="voltar" data-teste="voltar-encomendas"
              class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold flex-1 truncate">Encomenda #{{ id }}</h1>
      <NotificacaoSino :isDark="isDark" />
    </header>

    <main class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-24">
      <div v-if="carregando" class="flex justify-center py-10"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>

      <div v-else-if="naoEncontrada" class="text-center py-10" data-teste="encomenda-nao-encontrada">
        <p class="text-sm text-zinc-500">Esta encomenda não existe ou não é tua.</p>
        <router-link to="/encomendas" class="inline-block mt-4 text-sm font-semibold text-red-500 hover:text-red-400">Ver as minhas encomendas</router-link>
      </div>

      <div v-else-if="erro" class="text-center py-10">
        <p class="text-sm text-red-400">{{ erro }}</p>
        <button type="button" @click="carregar()" class="mt-4 text-sm font-semibold text-red-500 hover:text-red-400">Tentar outra vez</button>
      </div>

      <template v-else-if="enc">
        <section class="rounded-2xl border p-4" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'" data-teste="encomenda-cabecalho">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <router-link :to="`/loja/${enc.loja}`" class="font-semibold hover:underline truncate block">{{ enc.loja_nome }}</router-link>
              <p class="text-xs text-zinc-500 mt-0.5">Feita a {{ dataCurta(enc.data_criacao) }}</p>
            </div>
            <span class="text-lg font-bold text-red-500 flex-shrink-0">{{ formatarDinheiro(enc.valor_total || 0) }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-2 mt-3">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', corEstado(enc)]" data-teste="estado-encomenda">{{ nomeEstado(enc) }}</span>
            <EstadoReembolso v-if="enc.reembolso" :estado="enc.reembolso.estado" :valor="enc.reembolso.valor" :metodo="enc.reembolso.metodo" />
            <span v-if="enc.entrega_status && enc.tipo_entrega === 'entrega'" class="text-[11px] text-zinc-500">
              <font-awesome-icon :icon="['fas', 'truck']" class="mr-1" />{{ textoEntrega(enc.entrega_status) }}
            </span>
          </div>
          <p v-if="enc.agendada_texto && !['concluido', 'cancelado'].includes(enc.status)"
             class="text-[11px] font-semibold mt-2" :class="isDark ? 'text-amber-300' : 'text-amber-700'">
            {{ enc.agendamento_origem === 'cliente' ? 'Agendada para' : 'Preparada a partir de' }} {{ enc.agendada_texto }}
          </p>
        </section>

        <section class="rounded-2xl border p-4" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
          <DetalheEncomendaCliente :detalhe="enc" :isDark="isDark"
            @detalhe="d => { enc = d }" @atualizada="carregar(true)" />
        </section>
      </template>
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import DetalheEncomendaCliente from '@/components/encomendas/DetalheEncomendaCliente.vue'
import { temaEscuro } from '@/utils/tema'
import { formatarDinheiro } from '@/utils/dinheiro'
import { ouvirEncomendas } from '@/utils/tempoRealEncomendas'
import { utilizadorGuardado } from '@/services/confirmarEmail'
import { nomeEstado, corEstado, dataCurta } from '@/utils/encomendasCliente'

const ENTREGA = { pendente: 'À espera de condutor', atribuido: 'Condutor atribuído', a_caminho: 'A caminho',
                  entregue: 'Entregue', falhou: 'Não foi possível entregar', cancelada: 'Entrega cancelada' }

export default {
  name: 'EncomendaCliente',
  components: { NotificacaoSino, EstadoReembolso, DetalheEncomendaCliente },
  data () {
    return { enc: null, carregando: true, naoEncontrada: false, erro: '', isDark: temaEscuro() }
  },
  computed: {
    id () { return String(this.$route.params.id) },
  },
  watch: {
    // de uma ficha para outra (um aviso no sino com a página aberta): carrega a nova
    id () { this.enc = null; this.carregar() },
  },
  created () { this.carregar() },
  mounted () {
    // tempo real: só os avisos desta encomenda (ou "recarregar tudo" quando a ligação volta)
    this.desligar = ouvirEncomendas(() => this.carregar(true), { filtro: a => !a.id || String(a.id) === this.id })
  },
  beforeUnmount () { this.desligar?.() },
  methods: {
    formatarDinheiro, nomeEstado, corEstado, dataCurta,
    textoEntrega (s) { return ENTREGA[s] || s },
    async meuId () {
      const u = utilizadorGuardado()
      if (u?.id) return u.id
      try { return (await api.get('/app/utilizador/me/')).data.id } catch { return null }
    },
    async carregar (silencioso = false) {
      const id = this.id
      if (!/^\d+$/.test(id)) { this.naoEncontrada = true; this.carregando = false; return }
      const pedido = (this.pedido || 0) + 1
      this.pedido = pedido
      if (!silencioso) { this.carregando = true; this.erro = '' }
      try {
        const { data } = await api.get(`/app/encomenda/${id}/`)
        if (pedido !== this.pedido || id !== this.id) return
        // o GET também responde a quem é da loja: a ficha deles é a do backoffice (com as acções da loja)
        if (String(data.comprador) !== String(await this.meuId())) {
          if (pedido !== this.pedido) return
          this.$router.replace(`/loja/${data.loja}/backoffice/encomendas/${data.id}`)
          return
        }
        this.enc = data
        this.naoEncontrada = false
        this.erro = ''
      } catch (e) {
        if (pedido !== this.pedido) return
        const s = e.response?.status
        if (s === 403 || s === 404) { this.naoEncontrada = true; this.enc = null }   // sem dizer se existe
        else if (!silencioso) this.erro = 'Não foi possível carregar a encomenda.'
      } finally {
        if (pedido === this.pedido) this.carregando = false
      }
    },
    voltar () {
      // veio da lista (ou de outra página do site): volta para lá; aberta de um email/aviso: a lista
      if (window.history.state?.back) this.$router.back()
      else this.$router.push('/encomendas')
    },
  },
}
</script>
