<!-- AdminCatalogo.vue — Admin → Catálogo: o que a SISP/o banco notam ao rever o site, loja a loja
     (backend utils/qualidade.py). Só lê; "Avisar a loja" manda ao dono o resumo (uma vez por dia). -->
<template>
  <div class="space-y-5">
    <div v-if="loading" class="space-y-3">
      <div class="h-24 bg-zinc-900 rounded-2xl animate-pulse"></div>
      <div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>
    <p v-else-if="erro" class="text-sm text-red-400">{{ erro }}</p>

    <template v-else-if="dados">
      <!-- resumo -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3" data-teste="catalogo-resumo">
        <div v-for="k in kpis" :key="k.label" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
          <p class="text-2xl font-extrabold" :class="k.cor">{{ k.valor }}</p>
          <p class="text-xs text-zinc-500 mt-0.5">{{ k.label }}</p>
        </div>
      </div>

      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2">Produtos a rever, por problema</p>
        <div class="flex flex-wrap gap-2">
          <span v-for="t in dados.resumo.por_tipo" :key="t.chave" :data-teste="'tipo-' + t.chave"
                :class="['px-2.5 py-1 rounded-lg text-xs font-semibold', t.total ? 'bg-amber-500/15 text-amber-300' : 'bg-zinc-800 text-zinc-500']">
            {{ t.titulo }}: {{ t.total }}
          </span>
        </div>
        <p class="text-[11px] text-zinc-500 mt-2">
          Só avisos — nada fica escondido. Lojas activas e pendentes (as que o público pode ver ou vai ver).
        </p>
      </div>

      <!-- filtros -->
      <div class="flex flex-wrap items-center gap-3">
        <select v-model="estado" @change="carregar" data-teste="catalogo-estado"
          class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Activas e pendentes</option>
          <option value="ativa">Só activas</option>
          <option value="pendente">Só pendentes</option>
        </select>
        <label class="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
          <input v-model="semDemo" type="checkbox" @change="carregar" data-teste="catalogo-sem-demo" class="w-4 h-4 accent-red-600" />
          Esconder as lojas demo
        </label>
        <label class="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
          <input v-model="soProblemas" type="checkbox" class="w-4 h-4 accent-red-600" />
          Só com problemas
        </label>
      </div>

      <!-- lojas -->
      <div class="space-y-2" data-teste="catalogo-lojas">
        <div v-for="l in lojasVisiveis" :key="l.id" class="bg-zinc-900 border border-zinc-800 rounded-2xl" data-teste="catalogo-loja">
          <button type="button" @click="abrir(l)" class="w-full flex items-center gap-3 p-4 text-left">
            <span :class="['w-9 h-9 rounded-xl flex items-center justify-center text-xs font-extrabold flex-shrink-0',
                           l.pontos ? 'bg-red-500/15 text-red-400' : 'bg-green-500/15 text-green-400']">
              <font-awesome-icon v-if="!l.pontos" :icon="['fas', 'check']" />
              <template v-else>{{ l.pontos }}</template>
            </span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-sm font-bold text-zinc-100">{{ l.nome }}</p>
                <span v-if="l.estado === 'pendente'" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-yellow-500/15 text-yellow-400">Pendente</span>
                <span v-if="l.demo" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-500/15 text-sky-400" data-teste="catalogo-demo">Demo</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', l.completa ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400']">
                  {{ l.completa ? 'Completa' : `Incompleta ${l.percentagem}%` }}
                </span>
              </div>
              <p class="text-xs text-zinc-500 mt-0.5">
                {{ l.produtos_com_problemas }} de {{ l.produtos_total }} produto(s) a rever
                <template v-if="l.avisos.length"> · {{ l.avisos.map(a => a.titulo).join(' · ') }}</template>
              </p>
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0 text-zinc-500 transition-transform"
                 :class="aberta?.id === l.id && 'rotate-180'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- detalhe -->
          <div v-if="aberta?.id === l.id" class="px-4 pb-4 border-t border-zinc-800 pt-3 space-y-3" data-teste="catalogo-detalhe">
            <p v-if="!detalhe" class="text-xs text-zinc-500">A carregar…</p>
            <template v-else>
              <ul v-if="detalhe.avisos.length" class="flex flex-wrap gap-1.5">
                <li v-for="a in detalhe.avisos" :key="a.chave" class="px-2 py-0.5 rounded bg-red-500/10 text-red-300 text-xs">{{ a.titulo }}</li>
              </ul>
              <div v-if="detalhe.produtos.length" class="divide-y divide-zinc-800 rounded-xl bg-zinc-800/40">
                <div v-for="p in detalhe.produtos" :key="p.id" class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 px-3 py-2" data-teste="catalogo-produto">
                  <p class="flex-1 min-w-0 text-sm text-zinc-200 truncate">{{ p.nome }} <span class="text-zinc-500 text-xs">· {{ $dinheiro(p.preco) }}</span></p>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="pr in p.problemas" :key="pr.chave" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-300">{{ pr.titulo }}</span>
                  </div>
                </div>
              </div>
              <p v-else class="text-xs text-zinc-500">Todos os produtos activos estão completos.</p>

              <div class="flex flex-wrap items-center gap-2 pt-1">
                <button v-if="l.pontos" type="button" @click="avisar(l)" :disabled="aAvisar" data-teste="catalogo-avisar"
                  class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold transition">
                  {{ aAvisar ? 'A avisar…' : 'Avisar a loja' }}
                </button>
                <a :href="`/loja/${l.id}`" target="_blank" rel="noopener"
                  class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                  Ver loja pública <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="ml-1" />
                </a>
                <router-link :to="`/admin/lojas/${l.id}`"
                  class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                  Ficha da loja
                </router-link>
                <span v-if="detalhe.ultimo_aviso" class="text-[11px] text-zinc-500" data-teste="catalogo-ultimo-aviso">
                  Avisada em {{ detalhe.ultimo_aviso }}
                </span>
              </div>
              <p v-if="msgAviso" class="text-xs" :class="msgAvisoOk ? 'text-green-400' : 'text-amber-300'" data-teste="catalogo-msg">{{ msgAviso }}</p>
            </template>
          </div>
        </div>
        <p v-if="!lojasVisiveis.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">
          Nenhuma loja com problemas. 🎉
        </p>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminCatalogo',

  data () {
    return {
      loading: true, erro: '', dados: null,
      estado: '', semDemo: false, soProblemas: true,
      aberta: null, detalhe: null, aAvisar: false, msgAviso: '', msgAvisoOk: false,
    }
  },

  computed: {
    kpis () {
      const r = this.dados.resumo
      return [
        { label: 'Lojas com algo a rever', valor: `${r.lojas_com_problemas}/${r.lojas}`, cor: r.lojas_com_problemas ? 'text-red-400' : 'text-green-400' },
        { label: 'Lojas incompletas', valor: r.lojas_incompletas, cor: r.lojas_incompletas ? 'text-red-400' : 'text-green-400' },
        { label: 'Produtos a rever', valor: `${r.produtos_com_problemas}/${r.produtos}`, cor: r.produtos_com_problemas ? 'text-amber-300' : 'text-green-400' },
        { label: 'Lojas demo', valor: r.demo, cor: 'text-sky-400' },
      ]
    },
    lojasVisiveis () {
      return this.soProblemas ? this.dados.lojas.filter(l => l.pontos) : this.dados.lojas
    },
  },

  created () { this.carregar() },

  methods: {
    async carregar () {
      this.loading = !this.dados; this.erro = ''
      try {
        const params = {}
        if (this.estado) params.estado = this.estado
        if (this.semDemo) params.demo = '0'
        const { data } = await api.get('/app/admin/qualidade/', { params })
        this.dados = data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível analisar o catálogo.' }
      finally { this.loading = false }
    },

    async abrir (l) {
      this.msgAviso = ''
      if (this.aberta?.id === l.id) { this.aberta = null; return }
      this.aberta = l; this.detalhe = null
      try {
        const { data } = await api.get(`/app/admin/qualidade/lojas/${l.id}/`)
        if (this.aberta?.id === l.id) this.detalhe = data
      } catch (e) { this.msgAviso = e.response?.data?.detail || 'Não foi possível abrir.'; this.msgAvisoOk = false }
    },

    async avisar (l) {
      this.aAvisar = true; this.msgAviso = ''
      try {
        const { data } = await api.post(`/app/admin/qualidade/lojas/${l.id}/avisar/`)
        this.msgAviso = 'Avisada — o dono recebe uma notificação com o resumo.'; this.msgAvisoOk = true
        if (this.detalhe) this.detalhe.ultimo_aviso = data.ultimo_aviso
      } catch (e) {
        this.msgAviso = e.response?.data?.detail || 'Não foi possível avisar a loja.'; this.msgAvisoOk = false
      } finally { this.aAvisar = false }
    },
  },
}
</script>
