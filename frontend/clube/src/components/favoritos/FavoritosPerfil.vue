<template>
  <!-- separador "Favoritos" do perfil: produtos e lojas guardados com o coração -->
  <div>
    <div role="tablist" class="flex gap-1 p-1 rounded-xl mb-4" :class="isDark ? 'bg-zinc-900' : 'bg-gray-100'">
      <button v-for="t in TIPOS" :key="t.key" type="button" role="tab" :aria-selected="tipo === t.key" @click="tipo = t.key"
        class="flex-1 py-2 rounded-lg text-xs font-semibold transition"
        :class="tipo === t.key
          ? (isDark ? 'bg-zinc-700 text-white' : 'bg-white text-zinc-900 shadow-sm')
          : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-500 hover:text-zinc-800')">
        {{ t.label }}<span v-if="contagem[t.key] != null" class="ml-1 opacity-60">{{ contagem[t.key] }}</span>
      </button>
    </div>

    <div v-if="aCarregar && !itens.length" class="grid gap-3" :class="tipo === 'produto' ? 'grid-cols-2' : 'grid-cols-1'">
      <div v-for="n in 4" :key="n" class="rounded-xl animate-pulse"
           :class="[isDark ? 'bg-zinc-900' : 'bg-gray-100', tipo === 'produto' ? 'aspect-[3/4]' : 'h-16']"></div>
    </div>

    <div v-else-if="!itens.length" class="text-center py-10 text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      <svg viewBox="0 0 24 24" width="34" height="34" class="mx-auto mb-3 opacity-60" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">
        <path d="M12 21s-7.5-4.6-9.6-9.2C1 8.6 3 5 6.6 5c2 0 3.4 1.1 4.4 2.4C12 6.1 13.4 5 15.4 5 19 5 21 8.6 21.6 11.8 19.5 16.4 12 21 12 21z" />
      </svg>
      <template v-if="tipo === 'produto'">Ainda não guardaste produtos.<br/>Toca no coração de um produto para o guardares aqui.</template>
      <template v-else>Ainda não guardaste lojas.<br/>Toca em "Guardar loja" na página de uma loja.</template>
    </div>

    <!-- produtos: grelha de cards -->
    <div v-else-if="tipo === 'produto'" class="grid grid-cols-2 sm:grid-cols-3 gap-3">
      <div v-for="f in itens" :key="f.id" class="group relative">
        <button type="button" class="block w-full text-left" :disabled="!f.disponivel" @click="abrirProduto(f)">
          <div class="relative aspect-square rounded-xl overflow-hidden" :class="isDark ? 'bg-zinc-900' : 'bg-gray-100'">
            <img v-if="f.produto.imagem" :src="f.produto.imagem" :alt="f.produto.nome" loading="lazy"
                 class="w-full h-full object-cover transition group-hover:scale-105"
                 :class="!f.disponivel && 'grayscale opacity-50'" />
            <span v-else class="w-full h-full flex items-center justify-center text-2xl font-bold"
                  :class="isDark ? 'text-zinc-600' : 'text-zinc-300'">{{ f.produto.nome.charAt(0) }}</span>
            <span v-if="!f.disponivel"
                  class="absolute left-2 bottom-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-black/70 text-white">
              Indisponível
            </span>
          </div>
          <p class="mt-2 text-xs font-semibold truncate" :class="[isDark ? 'text-zinc-100' : 'text-zinc-900', !f.disponivel && 'opacity-50']">{{ f.produto.nome }}</p>
          <p class="text-[11px] truncate" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ f.loja.nome }}</p>
          <p v-if="f.disponivel" class="text-xs font-bold text-red-500">{{ preco(f.produto.preco) }}</p>
        </button>
        <BotaoFavorito tipo="produto" :id="f.produto.id" :tamanho="30" class="absolute top-2 right-2" />
      </div>
    </div>

    <!-- lojas: lista -->
    <div v-else class="space-y-2">
      <div v-for="f in itens" :key="f.id"
           class="flex items-center gap-3 p-2.5 rounded-xl border transition"
           :class="[isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-gray-50 border-gray-200',
                    f.disponivel && (isDark ? 'hover:border-red-500/30' : 'hover:border-red-400/50')]">
        <button type="button" class="flex items-center gap-3 flex-1 min-w-0 text-left" :disabled="!f.disponivel" @click="abrirLoja(f)">
          <img v-if="f.loja.logo || f.loja.imagem" :src="f.loja.logo || f.loja.imagem" :alt="f.loja.nome"
               class="w-11 h-11 rounded-lg object-cover flex-shrink-0" :class="!f.disponivel && 'grayscale opacity-50'" />
          <span v-else class="w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold"
                :class="isDark ? 'bg-zinc-700 text-zinc-400' : 'bg-gray-200 text-zinc-500'">{{ f.loja.nome.charAt(0) }}</span>
          <span class="min-w-0">
            <span class="block text-sm font-semibold truncate" :class="[isDark ? 'text-zinc-100' : 'text-zinc-900', !f.disponivel && 'opacity-50']">{{ f.loja.nome }}</span>
            <span v-if="f.disponivel" class="block text-xs truncate" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ f.loja.categoria }}</span>
            <span v-else class="block text-[10px] font-bold uppercase tracking-wide" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Indisponível</span>
          </span>
        </button>
        <BotaoFavorito tipo="loja" :id="f.loja.id" variante="simples" :tamanho="34" :isDark="isDark" />
      </div>
    </div>

    <button v-if="temMais" type="button" @click="carregar(true)" :disabled="aCarregar"
      class="w-full mt-4 py-2 rounded-xl border text-xs font-semibold transition"
      :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
      {{ aCarregar ? 'A carregar…' : 'Ver mais' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { favoritos, garantirFavoritos } from '@/services/favoritos'
import BotaoFavorito from '@/components/favoritos/BotaoFavorito.vue'

defineProps({ isDark: { type: Boolean, default: true } })
const emit = defineEmits(['fechar'])

const TIPOS = [{ key: 'produto', label: 'Produtos' }, { key: 'loja', label: 'Lojas' }]
const LIMITE = 12

const router    = useRouter()
const tipo      = ref('produto')
const lista     = ref([])
const total     = ref(0)
const contagem  = ref({ produto: null, loja: null })
const aCarregar = ref(false)
let pedido = 0

// retirar no coração tira logo da lista (sem esperar pelo servidor); voltar a tocar repõe
const itens = computed(() => lista.value.filter(f =>
  f.tipo === 'loja' ? favoritos.lojas.has(f.loja.id) : favoritos.produtos.has(f.produto.id)))
const temMais = computed(() => lista.value.length < total.value)

async function carregar (mais = false) {
  const meu = ++pedido
  aCarregar.value = true
  try {
    const { data } = await api.get('/app/favoritos/', {
      params: { tipo: tipo.value, limit: LIMITE, offset: mais ? lista.value.length : 0 },
    })
    if (meu !== pedido) return
    lista.value = mais ? [...lista.value, ...data.results] : data.results
    total.value = data.count
    contagem.value = { ...contagem.value, [tipo.value]: data.count }
  } catch (e) { console.error(e) }
  finally { if (meu === pedido) aCarregar.value = false }
}

function preco (v) {
  return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)
}

function abrirProduto (f) {
  if (!f.disponivel) return
  emit('fechar')
  router.push({ path: `/loja/${f.loja.id}`, query: { produto: f.produto.id } })
}

function abrirLoja (f) {
  if (!f.disponivel) return
  emit('fechar')
  router.push(`/loja/${f.loja.id}`)
}

watch(tipo, () => { lista.value = []; carregar() })

// guardado noutro sítio (ex.: num card com o perfil fechado) — recarrega, sem perder os que se acabou de retirar
watch(() => favoritos.versao, () => {
  const ids = new Set(lista.value.map(f => f.tipo === 'loja' ? f.loja.id : f.produto.id))
  const conj = tipo.value === 'loja' ? favoritos.lojas : favoritos.produtos
  if ([...conj].some(id => !ids.has(id))) carregar()
})

onMounted(async () => { await garantirFavoritos(); carregar() })
</script>
