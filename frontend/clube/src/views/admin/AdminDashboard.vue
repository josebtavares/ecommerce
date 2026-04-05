<template>
  <div class="space-y-6">

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="n in 6" :key="n" class="h-28 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <template v-else-if="stats">
      <!-- KPIs -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="kpi in kpis" :key="kpi.label"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <p class="text-2xl">{{ kpi.icon }}</p>
          <p class="text-2xl font-extrabold text-zinc-100 mt-2">{{ kpi.valor }}</p>
          <p class="text-xs text-zinc-500 mt-1">{{ kpi.label }}</p>
          <p v-if="kpi.sub" class="text-xs mt-1" :class="kpi.subColor || 'text-zinc-600'">{{ kpi.sub }}</p>
        </div>
      </div>

      <!-- Encomendas por estado -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Encomendas por estado</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div v-for="(count, estado) in stats.encomendas.por_estado" :key="estado"
               class="bg-zinc-800 rounded-xl p-3 text-center">
            <p class="text-xl font-bold text-zinc-100">{{ count }}</p>
            <p :class="['text-xs font-semibold mt-1 capitalize', statusColor(estado)]">{{ estado }}</p>
          </div>
        </div>
      </div>

      <!-- Resumo lojas e utilizadores -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-3">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Lojas</h2>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Total</span>
            <span class="text-sm font-bold text-zinc-100">{{ stats.lojas.total }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Activas</span>
            <span class="text-sm font-bold text-green-400">{{ stats.lojas.ativas }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Pendentes/Inactivas</span>
            <span class="text-sm font-bold text-yellow-400">{{ stats.lojas.pendentes }}</span>
          </div>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-3">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Utilizadores</h2>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Total</span>
            <span class="text-sm font-bold text-zinc-100">{{ stats.utilizadores.total }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Verificados</span>
            <span class="text-sm font-bold text-green-400">{{ stats.utilizadores.verificados }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-zinc-400">Nao verificados</span>
            <span class="text-sm font-bold text-zinc-500">{{ stats.utilizadores.total - stats.utilizadores.verificados }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminDashboard',
  data () { return { loading: true, stats: null } },

  async created () {
    try {
      const { data } = await api.get('/app/admin/stats/')
      this.stats = data
    } catch (e) { console.error(e) }
    finally { this.loading = false }
  },

  computed: {
    kpis () {
      if (!this.stats) return []
      return [
        { icon: '🏪', valor: this.stats.lojas.total,              label: 'Lojas totais',      sub: `${this.stats.lojas.ativas} activas`, subColor: 'text-green-500' },
        { icon: '👥', valor: this.stats.utilizadores.total,       label: 'Utilizadores',      sub: `${this.stats.utilizadores.verificados} verificados`, subColor: 'text-blue-400' },
        { icon: '📦', valor: this.stats.produtos,                 label: 'Produtos activos'   },
        { icon: '🛍️', valor: this.stats.encomendas.total,         label: 'Encomendas totais'  },
        { icon: '💶', valor: `€${parseFloat(this.stats.vendas_total).toFixed(2)}`, label: 'Volume de vendas', subColor: 'text-green-400' },
        { icon: '⏳', valor: this.stats.lojas.pendentes,           label: 'Lojas pendentes',   sub: 'a aguardar activacao', subColor: 'text-yellow-400' },
      ]
    },
  },

  methods: {
    statusColor (s) {
      const map = { pendente: 'text-yellow-400', pago: 'text-blue-400', preparando: 'text-purple-400', enviado: 'text-indigo-400', concluido: 'text-green-400', cancelado: 'text-red-400' }
      return map[s] || 'text-zinc-400'
    },
  },
}
</script>
