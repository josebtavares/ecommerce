<template>
  <section id="equipa"
           class="w-screen min-h-screen  bg-gray-900 text-white px-4 py-6 flex flex-col gap-6">
    <h1 class="text-2xl font-bold">Equipas</h1>

    <!-- Tabs ---------------------------------------------------------->
    <div class="flex gap-3 overflow-x-auto pb-2">
      <button
        v-for="e in equipas"
        :key="e.id"
        @click="selectEquipa(e)"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-full shrink-0',
          e.id === equipaId ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
        ]">
        <img :src="backend + e.foto"
             class="h-6 w-6 object-cover rounded-full" />
        <span class="whitespace-nowrap">{{ e.nome }}</span>
      </button>
    </div>

    <!-- Pesquisa ------------------------------------------------------>
    <div class="flex gap-2 items-center">
      <input
        v-model="filter"
        @keyup.enter="resetJogadores"
        placeholder="Procurar jogador…"
        class="flex-1 px-3 py-2 rounded bg-gray-800 outline-none" />
      <button @click="resetJogadores"
              class="px-3 py-2 bg-blue-600 rounded">🔍</button>
    </div>

    <!-- Carrossel + setas -------------------------------------------->
    <div class="relative flex-1">
      <!-- seta ESQ -->
      <button
        v-if="canScrollLeft"
        @click="scrollLeft"
        class="absolute left-0 top-1/2 -translate-y-1/2 z-10
               bg-black/50 hover:bg-black/70 rounded-full p-2">
        ‹
      </button>

      <!-- lista horizontal -->
      <div ref="scroller"
      
           class=" scroller h-full overflow-x-auto flex gap-4 pb-4 scroll-smooth"
           @scroll="onScroll">
        <JogadorCard v-for="j in jogadores" :key="j.id" :data="j" 
                     @select="selectPlayer" />

        <!-- loader circle spinning-->
        <div v-if="loading" class="flex items-center justify-center w-40 h-40">
          <i class="fa-solid fa-spinner fa-spin text-2xl text-gray-400"></i>
        </div>
      </div>

      <!-- seta DIR -->
      <button
        v-if="canScrollRight"
        @click="scrollRight"
        class="absolute right-0 top-1/2 -translate-y-1/2 z-10
               bg-black/50 hover:bg-black/70 rounded-full p-2">
        ›
      </button>
    </div>
    <!-- Detalhes do jogador selecionado (opcional) ------------------->
    <div v-if="selectedPlayer" class="mt-6 p-4 bg-gray-800 rounded-lg relative">
      <button @click="selectedPlayer = null"
                class="absolute top-2 right-2 text-2xl text-white-500  h-8 w-8 flex items-center justify-center ">
                <i class="fa-regular fa-circle-xmark"></i>
      </button>
      
      <div class="flex  gap-4">
        <JogadorCard :data="selectedPlayer" />
        <div>
          <!-- Detalhes do jogador (nome, posicao, data nascimento, data contratacao, nacionalidade, numero, altura, peso, biografia) ------------------->

          <h2 class="text-lg font-bold">{{ selectedPlayer.nome }}</h2>
          <p class="text-sm text-gray-400">{{ selectedPlayer.posicao }} · #{{ selectedPlayer.numero }}</p>
          <p v-if="selectedPlayer.idade" class="text-sm text-gray-400">{{ selectedPlayer.idade }} anos</p>
          <p v-if="selectedPlayer.nacionalidade" class="text-sm text-gray-400">{{ selectedPlayer.nacionalidade }}</p>
          <p v-if="selectedPlayer.altura" class="text-sm text-gray-400">Altura: {{ selectedPlayer.altura }} cm</p>
          <p v-if="selectedPlayer.peso" class="text-sm text-gray-400">Peso: {{ selectedPlayer.peso }} kg</p>
          <p v-if="selectedPlayer.data_nascimento" class="text-sm text-gray-400">Nascimento: {{ selectedPlayer.data_nascimento }}</p>
          <p v-if="selectedPlayer.data_contratacao" class="text-sm text-gray-400">Contratação: {{ selectedPlayer.data_contratacao }}</p>
          <p v-if="selectedPlayer.biografia" class="text-sm text-gray-400">{{ selectedPlayer.biografia }}</p>

        </div>

      </div>

      
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import JogadorCard from '@/components/cards/jogadorCard.vue'
import api from '@/services/api'

const backend   = process.env.VUE_APP_URL_BASE || ''
const equipas   = ref([])
const equipaId  = ref(null)
const jogadores = ref([])
const offset    = ref(0)
const loading   = ref(false)
const filter    = ref('')
const PAGE      = 6

/* refs html */
const scroller  = ref(null)
const selectedPlayer = ref(null)

/* ───────── helpers API ───────── */
async function fetchEquipas () {
  const { data } = await api.get('/app/equipa/')
  equipas.value  = data
  equipaId.value = data[0]?.id
}

async function selectPlayer (jogador) {
  // aqui poderias abrir um modal ou navegar para a página do jogador
  selectedPlayer.value = jogador
  console.log('Jogador selecionado:', jogador)
}

async function fetchJogadores (reset = false) {
  if (!equipaId.value || loading.value) return
  loading.value = true
  if (reset) {
    jogadores.value = []
    offset.value    = 0
  }
  const { data } = await api.get(
    `/app/jogador/equipa/${equipaId.value}/`,
    { params: { offset: offset.value, limit: PAGE, q: filter.value || undefined } }
  )
  jogadores.value.push(...data.results)
  offset.value = data.next_offset ?? null
  loading.value = false
}

/* ───────── navegação UI ───────── */
function selectEquipa (e) {
  if (e.id !== equipaId.value) {
    selectedPlayer.value = null // limpa seleção anterior
    equipaId.value = e.id
    fetchJogadores(true)
  }
}
function resetJogadores () { fetchJogadores(true) }

/* scroll infinito (wheel / arrastar) */
function onScroll (e) {
  const el = e.target
  if (
    offset.value !== null &&
    el.scrollLeft + el.clientWidth >= el.scrollWidth - 120
  ) {
    fetchJogadores()
  }
}

/* scroll por setas */
function scrollLeft ()  { scroller.value?.scrollBy({ left: -300, behavior: 'smooth' }) }
function scrollRight () {
  scroller.value?.scrollBy({ left:  300, behavior: 'smooth' })
  // se estiver perto do fim, antecipa fetch
  const el = scroller.value
  if (
    offset.value !== null &&
    el.scrollLeft + el.clientWidth >= el.scrollWidth - 320
  ) {
    fetchJogadores()
  }
}

/* mostrar / ocultar setas */
const canScrollLeft  = computed(() => scroller.value?.scrollLeft > 0)
const canScrollRight = computed(() => {
  const el = scroller.value
  return el && el.scrollLeft + el.clientWidth < el.scrollWidth - 2
})

/* recomputa setas ao rolar */
function updateArrows () {
  canScrollLeft.value  // re-avaliado
  canScrollRight.value // idem
}
watch(() => [jogadores.value.length, filter.value], () => nextTick(updateArrows))

/* ───────── lifecycle ───────── */
onMounted(async () => {
  await fetchEquipas()
  fetchJogadores(true)
})
watch(filter, v => { if (!v) fetchJogadores(true) })
</script>


<style scoped>

/* largura fina + cores */
.scroller::-webkit-scrollbar        { height:6px }
.scroller::-webkit-scrollbar-track  { background:#1f2937 }  /* gray-800 */
.scroller::-webkit-scrollbar-thumb  { background:#4b5563 }  /* gray-600 */
.scroller::-webkit-scrollbar-thumb:hover { background:#6b7280 } /* gray-500 */

/* Firefox */
.scroller { scrollbar-color:#4b5563 #1f2937; scrollbar-width:thin; }

</style>

