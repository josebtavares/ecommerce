<template>
  <!-- /perfil/reembolsos — os pedidos de reembolso e cancelamento do cliente -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="$router.push({ path: '/Home', query: { perfil: 'encomendas' } })"
              class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold">Reembolsos</h1>
      <NotificacaoSino class="ml-auto" :isDark="isDark" />
    </header>

    <main class="max-w-2xl mx-auto px-4 py-5 space-y-2">
      <div v-if="carregando" class="flex justify-center py-16">
        <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
      </div>
      <div v-else-if="!lista.length" class="text-center py-16 text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
        Ainda não fizeste nenhum pedido de reembolso.<br />
        Podes pedi-lo nas tuas encomendas, no perfil.
      </div>

      <button v-for="r in lista" :key="r.id" type="button" @click="$router.push(`/perfil/reembolsos/${r.id}`)"
        class="w-full text-left rounded-2xl border p-4 flex items-center gap-3 transition"
        :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-300'">
        <div class="flex-1 min-w-0">
          <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
            Encomenda #{{ r.encomenda_id }} · {{ r.loja_nome }} · {{ dataHora(r.data_criacao) }}
          </p>
          <p class="text-sm font-semibold truncate">{{ r.tipo === 'cancelamento' && r.motivo !== 'esgotado' ? 'Cancelamento' : r.motivo_label }}</p>
        </div>
        <div class="text-right flex-shrink-0 space-y-1">
          <EstadoReembolso :estado="r.estado" :valor="r.valor_aprovado ?? undefined" :metodo="r.metodo" />
          <p class="text-sm font-bold">{{ formatarDinheiro(r.valor_aprovado ?? r.valor_pedido) }}</p>
        </div>
      </button>

      <div v-if="proximo !== null" class="text-center pt-2">
        <button type="button" @click="carregar(true)" :disabled="aCarregarMais"
          class="px-4 py-2 rounded-xl text-xs" :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-200 text-zinc-600'">
          {{ aCarregarMais ? 'A carregar…' : 'Ver mais' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import { useTempoRealReembolsos } from '@/composables/useTempoRealReembolsos'

const isDark        = ref(localStorage.getItem('theme_preference') !== 'light')
const lista         = ref([])
const proximo       = ref(null)
const carregando    = ref(true)
const aCarregarMais = ref(false)

async function carregar (mais = false) {
  if (mais) aCarregarMais.value = true
  try {
    const { data } = await api.get('/app/reembolsos/', { params: { offset: mais ? proximo.value : 0, limit: 20 } })
    lista.value = mais ? [...lista.value, ...data.results] : data.results
    proximo.value = data.next_offset
  } catch (e) { console.error(e) }
  finally { carregando.value = false; aCarregarMais.value = false }
}

onMounted(() => carregar())
useTempoRealReembolsos(() => carregar())
</script>
