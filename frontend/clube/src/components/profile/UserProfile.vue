<!-- ProfileDrawer.vue -->
<template>
  <div class="text-white fixed top-6 right-[2.5vw] z-20">
    <!-- ícone para abrir -->
    <font-awesome-icon :icon="['fas', 'user']" size="xl" class="cursor-pointer"
                       @click="toggle" />

    <!-- gaveta -->
    <div
      class="fixed top-0 right-0 w-[50vw] h-screen bg-[#171717]
             text-white p-4 transition-transform duration-300
             translate-x-full profile-panel overflow-hidden">

      <!-- cabeçalho --------------------------------------------------->
      <div class="flex justify-between items-center mb-4">
        <font-awesome-icon :icon="['fas', 'xmark']" class="cursor-pointer" @click="toggle" />
      </div>

      <!-- avatar + botão upload -------------------------------------->
      <div class="flex items-center gap-4 mb-6">
        <div class="relative">
          <div class="">

                <div class="mt-2 flex  justify-center gap-3">
                    <!-- Avatar preview -->
                    <img :src="previewUrl" alt="preview" class="h-25 w-25 rounded-full object-cover border" />

                    <!-- INPUT FILE escondido -->
                    <input ref="fileInput" id="foto" type="file" accept="image/*" @change="onFileChange"
                        class="hidden" />

                    <!-- Ícone plus: só ele é clicável -->
                    <div class="cursor-pointer">
                        <!-- Font Awesome ícone plus -->
                        <i class="fa-solid fa-circle-plus " @click="triggerFileSelect" style="color: #ffffff;"></i>
                    </div>
                </div>
            </div>
        </div>
        <div>
          <p class="text-lg font-bold">{{ data.username }}</p>
          <button @click="$emit('log_out')" class="text-sm hover:underline">
            Terminar sessão
          </button>
        </div>
      </div>

      <!-- grelha ------------------------------------------------------>
      <div
        ref="grid"
        class="gallery-grid overscroll-contain overflow-y-auto pr-1"
        @scroll="onScroll"
        @wheel.stop         
        @touchmove.stop>    

        <!-- cartão “+”  -->
        <figure @click="showModal=true" class="gallery-item upload">
          <i class="fa-solid fa-circle-plus fa-xl text-gray-300" />
        </figure>

        <!-- itens da galeria -->
        <figure v-for="item in galeria" :key="item.id" class="gallery-item" @click="openPreview(item)">
          <img   v-if="!isVideo(item.ficheiro_url)" :src="item.ficheiro_url" />
          <video v-else              
           :src="item.ficheiro_url"
           muted playsinline loop controls></video>

            <!-- quick-tap like on thumbnail -->
          <button class="thumb-like" @click.stop="toggleLike(item)">
            <i :class="isLiked(item.id) ? 'fas fa-heart' : 'far fa-heart'"/>
          </button>
        </figure>

        <div v-if="loading" class="py-4 text-center col-span-3">
          <span class="animate-pulse text-sm text-gray-400">a carregar…</span>
        </div>
        <div ref="sentinel"></div>
      </div>
    </div>
  </div>

  <!-- MODAL upload ---------------------------------------------------->
  <transition name="fade">
    <div v-if="showModal"
         class="fixed inset-0 z-70 bg-black/60 flex items-center
                justify-center">
      <div class="bg-[#1f1f1f] w-[90vw] max-w-md p-6 rounded-lg text-white">

        <h3 class="text-lg font-semibold mb-4">Novo item da galeria</h3>

        <form @submit.prevent="uploadItem" class="flex flex-col gap-4">
          <input v-model="form.titulo" placeholder="Título"
                 class="p-2 rounded bg-gray-700 outline-none" />

          <textarea v-model="form.descricao" rows="3"
                    placeholder="Descrição (opcional)"
                    class="p-2 rounded bg-gray-700 outline-none"></textarea>

          <div class="flex items-center gap-2">
            <input
              ref="modalFileInput"
              type="file"
              accept="image/*,video/*"
              @change="e => form.ficheiro = e.target.files[0]"
              class="hidden"
            />
            <button
              type="button"
              @click="$refs.modalFileInput.click()"
              class="px-3 py-1 bg-blue-600 rounded hover:bg-blue-700 text-white"
            >
              Selecionar ficheiro
            </button>
            <span v-if="form.ficheiro" class="text-xs text-gray-300 truncate max-w-[120px]">
              {{ form.ficheiro.name }}
            </span>

            <!-- opcao de postar na feed tamvbém botao toggle -->
            <label class="flex items-center gap-2">
              <span class="text-sm">Postar na feed</span>
              <input type="checkbox" v-model="postarNaFeed" class="cursor-pointer" />
            </label>

            
          </div>

          <div class="flex justify-end gap-3 mt-2">
            <button type="button" @click="resetModal"
                    class="px-4 py-1 bg-gray-600 rounded">Cancelar</button>
            <button type="submit" :disabled="!form.ficheiro"
                    class="px-4 py-1 bg-blue-600 rounded
                           disabled:bg-gray-500">
              Enviar
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>

  <!-- ─────────── FULL-VIEW OVERLAY ─────────── -->
<transition name="fade">
  <div v-if="preview" class="preview-overlay" @click.self="closePreview">
    <button class="close-btn" @click="closePreview">
      <i class="fas fa-times"></i>
    </button>

    <!-- media itself -->
    <video v-if="isVideo(preview.ficheiro_url)"
           :src="preview.ficheiro_url"
           controls autoplay
           class="preview-media" />
    <img   v-else :src="preview.ficheiro_url" class="preview-media" />

    <!-- NEW CAPTION STRIP -->
    <div class="caption">
      <h3 class="title">{{ preview.titulo }}</h3>
      <p  class="desc" v-if="preview.descricao">{{ preview.descricao }}</p>
    </div>

    <!-- like / comment icons -->
    <div class="preview-actions">
      <button class="action relative"
          :class="previewLiked ? 'text-red-500' : ''"
          @click="toggleLike(preview)">
          <span class="absolute top-1 right-1 text-xs bg-gray-600 text-white rounded-full px-1">
            {{ preview.likes || 0 }}
          </span>
          <i :class="isLiked(preview.id) ? 'fas fa-heart text-blue-600' : 'far fa-heart'"/>
        <span class="sr-only">Gostos</span>
      </button>
      <button class="action relative" @click.prevent="openComment(preview)">
        <i class="far fa-comment"></i>
        <span class="absolute top-1 right-1 text-xs bg-gray-600 text-white rounded-full px-1">
          {{ preview.comentarios || 0 }}
        </span>
        <span class="sr-only">Comentários</span>
      </button>
    </div>
  </div>
</transition>
<div class ="w-full" >
  <GaleriaComment
  :open="showGalComment"
  :galeria-id="selectedItem && selectedItem.id"
  :user-id="data.id"
  @close="showGalComment = false"
  @new-comment="selectedItem.comentarios++"
/>

</div>

</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, defineProps, reactive } from 'vue'
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'
import { toast } from 'vue3-toastify'
import GaleriaComment from '@/components/comment/galeriaCommentDrawer.vue'



/* props */
const props = defineProps({
  data: { type: Object, default: () => ({}) },
  backendUrl: { type: String, default: () => process.env.VUE_APP_URL_BASE },
})

/* estado */
const previewUrl = ref('')
const galeria    = ref([])
const offset     = ref(0)
const loading    = ref(false)
const PAGE       = 6

const postarNaFeed = ref(false) // novo estado para opção de postar na feed
/* refs dom */
const fileInput = ref(null)
const grid      = ref(null)
const sentinel  = ref(null)
const showGalComment = ref(false) // estado para mostrar o comentário da galeria
const selectedItem = ref(null) // item selecionado para comentários


const preview = ref(null)

function openPreview (item) { 
  preview.value = item

  /* ask once per item whether the user already liked it ----------- */
  if (!likedCache.has(item.id)) {
    api.get(`/app/galerialike/check/galeria/${item.id}/utilizador/${props.data.id}/`)
       .then(r => likedCache.set(item.id, !!r.data.liked))
       .catch(() => likedCache.set(item.id, false))
       .finally(() => previewLiked.value = likedCache.get(item.id))
  } else {
    previewLiked.value = likedCache.get(item.id)
  }

}
function closePreview ()    { preview.value = null }

const likedCache = new Map()   //  id → true/false  (local cache)
const previewLiked = ref(false)   /* controls heart icon state */

const liked = reactive({})      // id → true / false  (reactive!)
const isLiked = id => !!liked[id]
const setLiked = (id,v)=> liked[id]=v   // keep in one place

async function seedLikes () {
  const { data } = await api.get(
    `/app/galerialike/utilizador/${props.data.id}/`)
  data.forEach(l => setLiked(l.galeria_id, true))
}

async function toggleLike (item) {
  console.log('Toggling like for item:', item)
  try {
    if (isLiked(item.id)) {
      await api.delete(
        `/app/galerialike/unlike/galeria/${item.id}/utilizador/${props.data.id}/`)
      item.likes--                          // ← SAME NAME
      setLiked(item.id,false)
    } else {
      await api.post('/app/galerialike/registar/', {
        galeria_id:item.id, utilizador_id:props.data.id })
      item.likes++
      setLiked(item.id,true)
    }
  } catch (e) { console.error(e) }
}

/* helpers */
const backend = process.env.VUE_APP_URL_BASE

/* novo estado para modal upload ------------------------------------*/
const showModal = ref(false)
const form = ref({ titulo:'', descricao:'', ficheiro:null })
function resetModal () {
  form.value = { titulo:'', descricao:'', ficheiro:null }
  showModal.value = false
}

function isVideo (url) { return /\.(mp4|webm|mov|mkv)$/i.test(url) }

/* ───────── toggle gaveta ───────── */
function toggle () {
  document.querySelector('.profile-panel')
    .classList.toggle('translate-x-full')

  
}

function openComment (item) {
  console.log('Abrindo comentário para:', item)
  selectedItem.value = item
  showGalComment.value = true
}

/* ───────── carregar galeria ────── */
async function fetchGalery (reset = false) {
  if (!props.data?.id || loading.value) return  
  if (loading.value) return
  loading.value = true
  if (reset) {
    galeria.value = []
    offset.value  = 0
  }
  const { data } = await api.get(
    `/app/galeria/utilizador/${props.data.id}/`,
    { params: { offset: offset.value, limit: PAGE } }
  )
  galeria.value.push(...data.results)
  offset.value = data.next_offset ?? null
  loading.value = false
}

/* IntersectionObserver para infinite-scroll */
let io = null
function createObserver () {
  if (io) io.disconnect()
  io = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && offset.value !== null) {
      fetchGalery()
    }
  }, { root: grid.value, threshold: 0.1 })
  io.observe(sentinel.value)
}

/* upload de item da galeria ----------------------------------------*/
function uploadItem () {
  if (!form.value.ficheiro) return
  wrap(async () => {
    const fd = new FormData()
    fd.append('titulo', form.value.titulo)
    fd.append('descricao', form.value.descricao)
    fd.append('utilizador_id', props.data.id)
    fd.append('ficheiro', form.value.ficheiro)
    fd.append('postar_na_feed', postarNaFeed.value) // inclui opção de postar na feed
    
    const { data:newItem } = await api.post(
    '/app/galeria/registar/', fd,
     { headers:{'Content-Type':'multipart/form-data'} })

   /* mostra logo o upload na 1ª posição                              */
   galeria.value.unshift(newItem)

   /* como acrescentámos um registo localmente, ajustamos o offset    */
   if (offset.value !== null) offset.value += 1

   toast.success('Item adicionado!', { autoClose: 1200 })
   postarNaFeed.value = false
   resetModal()
  })
}

/* ───────── upload avatar ───────── */
const { wrap } = useAsyncAction()
function triggerFileSelect () { fileInput.value.click() }
function onFileChange (e) {
  const file = e.target.files[0]
  if (!file) return
  previewUrl.value = URL.createObjectURL(file)

  wrap(async () => {
    const form = new FormData()
    form.append('foto', file)
    const url = `${backend}/app/utilizador/editar/${props.data.id}/`
    const res = await api.put(url, form,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    previewUrl.value = backend + res.data.foto
    toast.success('Foto actualizada!', { autoClose: 1000 })
  })
}

/* ───────── eventos lifecycle ───── */
onMounted(async () => {
  previewUrl.value = props.data.foto
    ? backend + props.data.foto
    : backend + '/media/utilizadores/default.png'
  fetchGalery(true).then(createObserver)

  await Promise.all([ fetchGalery(true), seedLikes() ])   // <── HERE
  createObserver(grid.value)
})
onUnmounted(() => io && io.disconnect())

/* recarrega grelha quando mudar utilizador */
watch(
  () => props.data.id,
  id => {
    if (id) {
      fetchGalery(true)          // utilizador válido → recarrega
    } else {
      galeria.value = []         // logout → limpa grelha
      offset.value  = 0
    }
  }
)
</script>

<style scoped>
.gallery-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:8px;

  /* mostra duas linhas; o resto surge ao fazer scroll        */
  --cell: calc(50vw / 3);           /* largura de uma célula  */
  /* height: calc(var(--cell) * 2 + 8px);    */
  height:75vh;
}

/* ------------- cada célula quadrada                       */
.gallery-item{
  position:relative;
  width:100%;
  padding-bottom:100%;      /* ← altura = largura (quadrado) */
  overflow:hidden;
  border-radius:8px;
}

/* ------------- conteúdo ocupa 100 % da célula              */
.gallery-item img,
.gallery-item video{
  position:absolute; inset:0;       /* top:0 right:0 bottom:0 left:0 */
  width:100%; height:100%;
  object-fit:cover;
}

/* ------------- cartão de upload                            */
.gallery-item.upload {
  position: relative;
  display: flex;           /* you can even leave these or remove them */
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,.08);
  cursor: pointer;
  transition: background .2s;
}

/* Then absolutely center the icon inside it */
.gallery-item.upload i {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  /* optional: enlarge it a bit */
  font-size: 2.5rem;
  color: #cbd5e1;
}
.gallery-item.upload:hover{
  background:rgba(255,255,255,.15);
}
.profile-panel { transition: transform .3s }
.fade-enter-active, .fade-leave-active { transition: opacity .2s }
.fade-enter-from,  .fade-leave-to      { opacity: 0 }

.preview-overlay{
  position:fixed;
  top:0; right:0;                     /* stay inside the drawer */
  width:50vw; height:100vh;           /* same size as the drawer */
  background:#171717; z-index:80;
  display:flex; align-items:center; justify-content:center;
  overflow:hidden;
  
}

/* close (x) button  */
.close-btn{
  position:absolute; top:12px; right:12px;
  font-size:1.25rem; color:#fff;
}

/* actual media */
.preview-media{
  max-width:100%; max-height:100%;
  object-fit:contain;
}

/* like / comment icons */
.preview-actions{
  position:absolute; bottom:20px; right:20px;
  display:flex; flex-direction:column; gap:18px;
}
.action{
  width:44px; height:44px;
  border-radius:50%; background:rgba(255,255,255,.15);
  display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:1.1rem;
}
.action:hover{ background:rgba(255,255,255,.3); }

/* fade transition reused */
.fade-enter-active,.fade-leave-active{transition:opacity .2s}
.fade-enter-from,.fade-leave-to{opacity:0}

.caption{
  position:absolute;
  bottom:0; left:0;            /* stick to bottom edge   */
  width:100%;
  padding:14px 18px 20px;
  background:linear-gradient(0deg,rgba(0,0,0,.7) 0%, rgba(0,0,0,0) 90%);
  box-sizing:border-box;
  color:#fff;
}
.title{
  font-size:1rem;
  font-weight:600;
  line-height:1.3;
  margin:0 0 4px 0;
  word-break:break-word;
  text-shadow:0 1px 2px rgba(0,0,0,.5);
}
.desc{
  font-size:.9rem;
  line-height:1.35;
  opacity:.9;
  max-height:3.6em;            /* ≈ 2 lines; remove if not needed   */
  overflow:hidden;
  text-overflow:ellipsis;
  text-shadow:0 1px 2px rgba(0,0,0,.5);

}

.thumb-like{
  position:absolute; bottom:6px; right:6px;
  font-size:.85rem; color:#e2e8f0;
}
.thumb-like .fas{ color:var(--color-blue-600); }


</style>
