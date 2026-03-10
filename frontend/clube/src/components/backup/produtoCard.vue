<template>
  <!-- ╔═══════════ DATA MODE ═══════════╗ -->
  <div
    v-if="!isFetchMode"
    class="modal backdrop"
    @click.self="close"
  >
    <div class="modal-panel">
      <button class="icon-btn" @click="close">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>

      <div class="stack-scroll">
        <div
          v-for="(item, idx) in data"
          :key="idx"
          class="stack-row"
        >
          <div class="stack-img">
            <img :src="item.photo" :alt="item.nome" />
          </div>

          <div class="stack-info">
            <h1 class="title">{{ item.nome }}</h1>
            <h2 class="discount">Desconto: {{ item.desconto * 100 }}%</h2>
            <h2 class="price">
              €{{ truncateDecimals(item.preco * item.desconto, 2) }}
            </h2>

            <button class="primary-btn" @click.prevent="add_to_cart(item)">
              <font-awesome-icon :icon="['fas', 'cart-shopping']" />
              Adicionar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ╔══════════ FETCH-URL MODE ══════════╗ -->
  <div
    v-else
    class="modal backdrop"
    @click.self="close"
  >
    <div class="modal-panel grid-mode">
      <button class="icon-btn" @click="close">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>

      <div class="grid-scroll">
        <div
          v-for="p in items"
          :key="p.id"
          class="prod-card"
        >
          <img :src="p.photo" :alt="p.nome" />
          <h3>{{ p.nome }}</h3>
          <p class="price">
            €{{ truncateDecimals(p.preco * p.desconto, 2) }}
          </p>
          <button class="primary-btn sm" @click.prevent="add_to_cart(p)">
            <font-awesome-icon :icon="['fas', 'cart-shopping']" />
            <p>Adicionar</p>
          </button>
        </div>

        <!-- sentinel (IO) -->
        <div ref="sentinel" class="sentinel"></div>
      </div>

      <p v-if="loadingMore" class="loader">A carregar…</p>
      <p v-else-if="reachedEnd && items.length === 0" class="empty">
        Sem produtos.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, defineEmits, defineProps } from 'vue'
import api from '@/services/api'
import { toast } from 'vue3-toastify'         // optional (if you use it)

/* ─── props & mode ─────────────────────────────────────────────── */
const props = defineProps({
  data     : { type: Array,  default: () => [] },
  fetchUrl : { type: String, default: '' },
})

const emit = defineEmits(['close', 'add_to_cart', 'loaded'])
const isFetchMode = computed(() => !!props.fetchUrl)

/* ─── shared helpers ───────────────────────────────────────────── */
function truncateDecimals (num, dec) {
  const k = 10 ** dec
  return Math.trunc(num * k) / k
}
function close () { emit('close') }
function add_to_cart (p) { emit('add_to_cart', p) }

/* ════════════════════════════════════════════════════════════════
   FETCH-MODE STATE
   ════════════════════════════════════════════════════════════════ */
const items       = ref([])
const nextOffset  = ref(0)
const loadingMore = ref(false)
const reachedEnd  = ref(false)
const sentinel    = ref(null)

async function loadMore () {
  if (loadingMore.value || reachedEnd.value) return
  loadingMore.value = true
  try {
    const sep  = props.fetchUrl.includes('?') ? '&' : '?'
    const url  = `${props.fetchUrl}${sep}limit=6&offset=${nextOffset.value}`
    const { data } = await api.get(url)

    items.value.push(...(data.results ?? data))
    nextOffset.value = data.next_offset ?? null
    if (nextOffset.value === null) reachedEnd.value = true

    emit('loaded', items.value.length)
  } catch (e) {
    toast.error('Erro ao buscar produtos')   // if you want feedback
    reachedEnd.value = true
  } finally { loadingMore.value = false }
}

/* reset / (re)fetch when url changes */
watch(() => props.fetchUrl, (newUrl) => {
  if (!newUrl) return            // guard
  items.value      = []
  nextOffset.value = 0
  reachedEnd.value = false
  loadMore()
}, { immediate: true })

/* IntersectionObserver to auto-load */
onMounted(() => {
  if (!isFetchMode.value) return
  const io = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) loadMore()
  }, { rootMargin: '400px' })

  nextTick(() => sentinel.value && io.observe(sentinel.value))
})
</script>

<style scoped>
/* ─── generic backdrop & panel ─────────────────────────────────── */
.backdrop{
  position:fixed; inset:0; background:rgba(0,0,0,.75);
  display:flex; justify-content:center; align-items:flex-start;
  padding-top:10vh; z-index:999;
}
.modal-panel{
  background:#1e1f23; color:#e5e5e7; width:50vw; max-height:70vh;
  display:flex; flex-direction:column; border-radius:8px; overflow:hidden;
  padding:1rem; position:relative;
}
.icon-btn{
  position:absolute; top:8px; right:8px;
  background:transparent; border:none; color:#e5e5e7; cursor:pointer;
  font-size:1.25rem;
}
.icon-btn:hover{ color:#fff; }

/* ─── DATA-MODE stacked layout ─────────────────────────────────── */
.stack-scroll{ overflow-y:auto; display:flex; flex-direction:column; gap:1rem;}
.stack-row{ display:flex; gap:1.5rem;}
.stack-img img{ width:100%; height:60vh; object-fit:cover; border-radius:4px;}
.stack-img{ width:50%;}
.stack-info{ flex:1; display:flex; flex-direction:column; gap:.5rem;}
.title{ font-family:Koulen, sans-serif; font-size:2.5rem;}
.discount{ font-family:Koulen,sans-serif; font-size:1.75rem;}
.price{ font-family:Koulen,sans-serif; font-size:1.75rem;}
.primary-btn{
  background:#0d6efd; color:#fff; border:none; padding:.5rem 1rem;
  border-radius:6px; cursor:pointer; display:flex; align-items:center; gap:.5rem;
}
.primary-btn.sm{ padding:.25rem .5rem; font-size:.9rem;}
.primary-btn:hover{ background:#2a7eff; }

/* ─── FETCH-MODE grid layout  ─────────────────────────────────── */
.grid-mode{ padding:1.5rem;}
.grid-scroll{
  display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:1rem; overflow-y:auto; max-height:calc(70vh - 2.5rem);
}
.prod-card{
  background:#2b2c31; border-radius:6px; padding:.75rem; display:flex;
  flex-direction:column; gap:.5rem; align-items:center;
}
.prod-card img{ width:100%; aspect-ratio:1/1; object-fit:cover; border-radius:4px;}
.prod-card h3{ font-size:1rem; text-align:center; }
.prod-card .price{ color:#0d6efd; font-weight:600; }
.loader,.empty{ text-align:center; margin-top:1rem; color:#999; }

/* sentinel – invisible but keeps 1px height */
.sentinel{ width:100%; height:1px; }
</style>