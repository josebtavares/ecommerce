<template>
  <!-- ╔═══════════ DATA MODE ═══════════╗ -->
  <div
    v-if="!isFetchMode"
    class="modal-backdrop"
    @click.self="close"
  >
    <div class="modal-container data-mode">
      <!-- <div class="modal-header">
        <h2 class="modal-title">
          
          Produtos em Destaque
        </h2>
        <button class="close-btn" @click="close">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div> -->
       <button class="close-btn"
        @click="close">
          <i class="fa-regular fa-circle-xmark"></i>
        </button>
      <div class="data-scroll">
        <div
          v-for="(item, idx) in data"
          :key="idx"
          class="product-showcase"
          :style="{ animationDelay: `${idx * 0.1}s` }"
        >
          <div class="showcase-image">
            <img :src="item.photo" :alt="item.nome" />
            
          </div>
          
          <div class="showcase-content">
            <div class="product-header">
              <h1 class="product-title text-white">{{ item.nome }}</h1>
              <!-- <div class="rating-stars">
                <span v-for="n in 5" :key="n" class="star">⭐</span>
              </div> -->
            </div>
            
            <div class="price-section">
              <div class="price-container">
                <span v-if="item.desconto < 1" class="original-price">
                  €{{ truncateDecimals(item.preco, 2) }}
                </span>
                <span class="current-price">
                  €{{ truncateDecimals(item.preco * item.desconto, 2) }}
                </span>
              </div>
              <div v-if="item.desconto < 1" class="savings">
                Poupa €{{ truncateDecimals(item.preco * (1 - item.desconto), 2) }}
              </div>
            </div>
            
            <!-- <div class="product-features">
              <div class="feature-item">
                <span class="feature-icon">🚚</span>
                <span>Envio Grátis</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">↩️</span>
                <span>Devolução 30 dias</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <span>Entrega Rápida</span>
              </div>
            </div> -->
            
            <button class="add-to-cart-btn showcase" @click.prevent="add_to_cart(item)">
              <span class="btn-icon">
                <font-awesome-icon :icon="['fas', 'cart-shopping']" />
              </span>
              <span class="btn-text">Adicionar ao Carrinho</span>
              <div class="btn-ripple"></div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ╔══════════ FETCH-URL MODE ══════════╗ -->
  <div
    v-else
    class="modal-backdrop"
    @click.self="close"
  >
    <div class="modal-container grid-mode">
      <!-- <div class="modal-header">
        <h2 class="modal-title">
          <span class="title-icon">🏪</span>
          Catálogo de Produtos
        </h2>
        <button class="close-btn" @click="close">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div> -->

      <button class="close-btn"
        @click="close">
          <i class="fa-regular fa-circle-xmark"></i>
        </button>
      
      <div class="grid-container">
        <div class="products-grid">
          <div
            v-for="(p, index) in items"
            :key="p.id"
            class="product-card"
            :style="{ animationDelay: `${(index % 6) * 0.1}s` }"
          >
            <div class="card-image">
              <img :src="p.photo" :alt="p.nome" />
              <div class="card-overlay">
                <div v-if="p.desconto < 1" class="discount-tag">
                  -{{ Math.round((1 - p.desconto) * 100) }}%
                </div>
                <button class="quick-view-btn">
                  <font-awesome-icon :icon="['fas', 'eye']" />
                </button>
              </div>
            </div>
            
            <div class="card-content">
              <h3 class="card-title">{{ p.nome }}</h3>
              
              <div class="card-rating">
                <!-- <div class="stars-small">
                  <span v-for="n in 5" :key="n" class="star-small">⭐</span>
                </div> -->
                <!-- <span class="rating-count">({{ Math.floor(Math.random() * 100) + 1 }})</span> -->
              </div>
              
              <div class="card-price">
                <span v-if="p.desconto < 1" class="old-price">
                  €{{ truncateDecimals(p.preco, 2) }}
                </span>
                <span class="new-price">
                  €{{ truncateDecimals(p.preco * p.desconto, 2) }}
                </span>
              </div>
              
              <button class="add-to-cart-btn card" @click.prevent="add_to_cart(p)">
                <font-awesome-icon :icon="['fas', 'cart-shopping']" />
                <span>Adicionar</span>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Sentinel for infinite scroll -->
        <div ref="sentinel" class="sentinel"></div>
      </div>
      
      <!-- Loading states -->
      <div v-if="loadingMore" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">A carregar mais produtos...</p>
      </div>
      
      <div v-else-if="reachedEnd && items.length === 0" class="empty-state">
        
        <h3>Nenhum produto encontrado</h3>
        <p>Não foram encontrados produtos nesta categoria.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, defineEmits, defineProps } from 'vue'
import api from '@/services/api'
import { toast } from 'vue3-toastify'

/* ─── props & mode ─────────────────────────────────────────────── */
const props = defineProps({
  data: { type: Array, default: () => [] },
  fetchUrl: { type: String, default: '' },
})

const emit = defineEmits(['close', 'add_to_cart', 'loaded'])
const isFetchMode = computed(() => !!props.fetchUrl)

/* ─── shared helpers ───────────────────────────────────────────── */
function truncateDecimals(num, dec) {
  const k = 10 ** dec
  return Math.trunc(num * k) / k
}

function close() { 
  emit('close') 
}

function add_to_cart(p) { 
  emit('add_to_cart', p) 
}

/* ════════════════════════════════════════════════════════════════
   FETCH-MODE STATE
   ════════════════════════════════════════════════════════════════ */
const items = ref([])
const nextOffset = ref(0)
const loadingMore = ref(false)
const reachedEnd = ref(false)
const sentinel = ref(null)

async function loadMore() {
  if (loadingMore.value || reachedEnd.value) return
  loadingMore.value = true
  
  try {
    const sep = props.fetchUrl.includes('?') ? '&' : '?'
    const url = `${props.fetchUrl}${sep}limit=6&offset=${nextOffset.value}`
    const { data } = await api.get(url)
    
    items.value.push(...(data.results ?? data))
    nextOffset.value = data.next_offset ?? null
    
    if (nextOffset.value === null) reachedEnd.value = true
    emit('loaded', items.value.length)
  } catch (e) {
    toast.error('Erro ao buscar produtos')
    reachedEnd.value = true
  } finally { 
    loadingMore.value = false 
  }
}

/* reset / (re)fetch when url changes */
watch(() => props.fetchUrl, (newUrl) => {
  if (!newUrl) return
  items.value = []
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
/* ═══════════════════════════════════════════════════════════════
   GLOBAL STYLES & ANIMATIONS
   ═══════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  box-sizing: border-box;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

/* ═══════════════════════════════════════════════════════════════
   MODAL BACKDROP & CONTAINER
   ═══════════════════════════════════════════════════════════════ */

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  z-index: 999;
  animation: fadeInUp 0.3s ease-out;
}

.modal-container {
  background: linear-gradient(145deg, #1a1b23 0%, #2d2e3f 100%);
  border-radius: 10px;
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  overflow: hidden;
  position: relative;
  animation: slideInRight 0.4s ease-out;
}

.modal-container.data-mode {
  width: min(90vw, 1000px);
  max-height: 85vh;
}

.modal-container.grid-mode {
  width: min(95vw, 1200px);
  max-height: 90vh;
}

/* ═══════════════════════════════════════════════════════════════
   MODAL HEADER
   ═══════════════════════════════════════════════════════════════ */

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-title {
  font-family: 'Inter', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 1.75rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.close-btn {
  
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  /* position at the right end  */
  position: absolute;
  top: 0.2rem;
  right: 0.5rem;
  z-index: 10;

}

.close-btn:hover {
  
  transform: scale(1.1);
}

/* ═══════════════════════════════════════════════════════════════
   DATA MODE - SHOWCASE LAYOUT
   ═══════════════════════════════════════════════════════════════ */

.data-scroll {
  padding: 2rem;
  overflow-y: auto;
  max-height: calc(85vh - 100px);
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.product-showcase {
  display: flex;
  gap: 2rem;
  background: linear-gradient(135deg, #2a2d3a 0%, #212530 100%);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: fadeInUp 0.6s ease-out both;
  transition: all 0.3s ease;
}

.product-showcase:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.showcase-image {
  flex: 0 0 300px;
  height: 400px;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}

.showcase-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-showcase:hover .showcase-image img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(0, 0, 0, 0.1) 0%, transparent 50%);
}

.discount-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(45deg, #ff6b6b, #ee5a24);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.9rem;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
  animation: pulse 2s infinite;
}

.showcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  color: #e5e5e7;
}

.product-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.product-title {
  
  
  font-size: 2rem;
  
  margin: 0;
  color:white;
  
}

.rating-stars {
  display: flex;
  gap: 0.25rem;
}

.star {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.price-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.price-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.original-price {
  font-size: 1.2rem;
  color: #999;
  text-decoration: line-through;
}

.current-price {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(78, 205, 196, 0.3);
}

.savings {
  font-size: 0.9rem;
  color: white;
  font-weight: 500;
}

.product-features {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
  color: #b8b9be;
}

.feature-icon {
  font-size: 1.1rem;
}

/* ═══════════════════════════════════════════════════════════════
   GRID MODE - CARD LAYOUT
   ═══════════════════════════════════════════════════════════════ */

.grid-container {
  padding: 2rem;
  overflow-y: auto;
  max-height: calc(90vh - 100px);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: linear-gradient(135deg, #2a2d3a 0%, #212530 100%);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out both;
}

.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.card-image {
  position: relative;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 300px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .card-image img {
  transform: scale(1.1);
}

.card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(0, 0, 0, 0.1) 0%, transparent 50%);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
}

.discount-tag {
  background: linear-gradient(45deg, #ff6b6b, #ee5a24);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 15px;
  font-weight: 700;
  font-size: 0.8rem;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
}

.quick-view-btn {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
  color: #333;
}

.product-card:hover .quick-view-btn {
  opacity: 1;
  transform: scale(1.1);
}

.card-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.card-title {
  font-family: 'Inter', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: #e5e5e7;
  line-height: 1.4;
}

.card-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stars-small {
  display: flex;
  gap: 0.1rem;
}

.star-small {
  font-size: 0.9rem;
}

.rating-count {
  font-size: 0.8rem;
  color: #999;
}

.card-price {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.old-price {
  font-size: 0.9rem;
  color: #999;
  text-decoration: line-through;
}

.new-price {
  font-size: 1.3rem;
  font-weight: 700;
  color: white;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════ */

.add-to-cart-btn {
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.add-to-cart-btn.showcase {
  background: #007bff;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  margin-top: auto;
}

.add-to-cart-btn.card {
  background: #007bff;
  color: white;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  width: 100%;
}

.add-to-cart-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.add-to-cart-btn:active {
  transform: translateY(0);
}

.btn-ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
  animation: ripple 0.6s linear;
  pointer-events: none;
}

.add-to-cart-btn:active .btn-ripple {
  animation: ripple 0.6s linear;
}

/* ═══════════════════════════════════════════════════════════════
   LOADING & EMPTY STATES
   ═══════════════════════════════════════════════════════════════ */

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #e5e5e7;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(2) {
  animation-delay: 0.1s;
  border-top-color: #764ba2;
}

.spinner-ring:nth-child(3) {
  animation-delay: 0.2s;
  border-top-color: white;
}

.loading-text {
  font-size: 1rem;
  color: #b8b9be;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 2rem;
  color: #e5e5e7;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.empty-state p {
  margin: 0;
  color: #b8b9be;
  font-size: 1rem;
}

.sentinel {
  width: 100%;
  height: 1px;
  grid-column: 1 / -1;
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE DESIGN
   ═══════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
  .modal-backdrop {
    padding: 1rem;
  }
  
  .modal-container.data-mode,
  .modal-container.grid-mode {
    width: 100%;
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 1rem 1.5rem;
  }
  
  .modal-title {
    font-size: 1.2rem;
  }
  
  .data-scroll,
  .grid-container {
    padding: 1rem;
  }
  
  .product-showcase {
    flex-direction: column;
    gap: 1rem;
  }
  
  .showcase-image {
    flex: none;
  }
  
  .showcase-image img {
    height: 200px;
  }
  
  .product-title {
    font-size: 1.5rem;
  }
  
  .current-price {
    font-size: 1.5rem;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  .add-to-cart-btn.showcase {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .products-grid {
    grid-template-columns: 1fr;
  }
  
  .product-showcase {
    padding: 1rem;
  }
  
  .card-content {
    padding: 1rem;
  }
  
  .modal-title {
    font-size: 1rem;
  }
  
  .title-icon {
    font-size: 1.2rem;
  }
}
</style>
