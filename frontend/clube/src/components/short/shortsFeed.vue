<!-- src/components/Shorts.vue -->
<template>
  <!-- wrapper --------------------------------------------------------->
  <section class="shorts-wrapper" id="feed">

        <div class="relative flex items-center gap-4">

            <!-- current short ------------------------------------------------->
            <div v-if="current"
     class="short transition-all duration-300 mr-4"
     :class="{ 'mr-[calc(320px+1rem)]': showComments }">  <!-- 320 + gap -->
                <!-- media -->
                <video v-if="isVideo(current.ficheiro_url)"
                        :src="current.ficheiro_url"
                        autoplay muted loop controls
                        class="media" />
                <img   v-else :src="current.ficheiro_url" class="media" />
    
                <!-- overlay (simple ― customise) -->
                <div class="overlay">
                    <div class="flex items-center gap-2 mb-2">
                        <img
                            :src="current.utilizador.foto_url || defaultAvatar"
                            class="h-8 w-8 rounded-full object-cover"/>
                        <h3>{{ current.utilizador.username }}</h3>
                    </div>
                    <h3>{{ current.titulo }}</h3>
                    <p class="desc">{{ current.descricao }}</p>
                </div>
            </div>
    
            <div v-else class="short flex items-center justify-center">
                <span class="text-white text-xl font-extralight">
                    A carregar...    
                </span>
                <i class="fa-solid fa-spinner fa-spin fa-2xl text-white"></i>
                
            </div>
            <!-- drawer (height = short height) ---------------------------- -->
            <ShortComment
                v-if="current "
                :open="showComments"
                :postagem-id="current.id"
                :user-id="props.logged_user.id"
                @new-comment="incrementComments"
                @close="closeComments" />
        </div>
        
   
    

        <section class="flex flex-col gap-4 mt-auto mb-[2.8rem]">

            <div class="flex flex-col items-center gap-4 mb-2">
                <!-- nav arrows ---------------------------------------------------->
                <button class=" w-10 h-10 rounded-full bg-gray-700/40
                               hover:bg-gray-600/60 transition cursor-pointer
                               flex items-center justify-center"
                    
                    :class="{ 'cursor-not-allowed opacity-50': !canPrev }"
                   :disabled="!canPrev" @click="prev">
                    <i class="fa-solid fa-circle-up fa-2xl" style="color: #ffffff;"></i>

                </button>

               <button class=" w-10 h-10 rounded-full bg-gray-700/40
                               hover:bg-gray-600/60 transition cursor-pointer
                               flex items-center justify-center"
                        :disabled="loading" @click="next">
                    <i class="fa-solid fa-circle-down fa-2xl" style="color: #ffffff;"></i>
                </button>

                <!-- upload «+» ---------------------------------------------------->
                <button class="fab" @click="showModal = true">
                    <i class="fa-solid fa-circle-plus fa-2x" />
                </button>

            </div>

            
            <!-- like button and likes ---------------------------------------------------->
            <div class="flex flex-col items-center justify-center gap-4">
                <!-- likes -->
                <button @click="toggleLike" class="flex cursor-pointer items-center gap-1 font-extralight">
                    <i :class="liked ? 'fas fa-heart fa-xl  text-blue-600' : 'far fa-heart fa-xl text-white'"></i>
                </button>
                <span class="text-white text-xl font-extralight">{{ likeCount || 0 }}</span>
            </div>
            <!-- comment button and comments ---------------------------------------------------->
            <div class="flex flex-col items-center gap-1">
                <button class="text-white cursor-pointer text-xl font-extralight" @click="openComments">
                    <i class="fa-regular fa-comment-dots fa-lg"></i>            
                </button>
                <span class="text-white text-xl font-extralight">{{ current?.comentarios || 0 }}</span>
            </div>
            <!-- share button ---------------------------------------------------->
            <div class="flex flex-col items-center gap-1">
                <button class="text-white cursor-pointer text-xl font-extralight" @click="shareShort">
                <i class="fa-solid fa-share fa-lg"></i>
                </button>
                <span class="text-white text-[1rem] font-extralight">Partilhar</span>
            </div>

            <div v-if="current" class="flex flex-col items-center gap-2">
                <img
                    :src="current.utilizador.foto_url || defaultAvatar"
                    class="h-12 w-12 rounded-l-[0.5rem]  rounded-r-[0.5rem] object-cover"/>
            </div>
            
            


            
        </section>

        <!-- nav arrows ---------------------------------------------------->
        <button class="nav up"   :disabled="!canPrev" @click="prev">
            <i class="fa-solid fa-circle-up fa-2xl" style="color: #ffffff;"></i>

        </button>

        <button class="nav down" :disabled="loading" @click="next">
            <i class="fa-solid fa-circle-down fa-2xl" style="color: #ffffff;"></i>
        </button>

        <!-- upload «+» ---------------------------------------------------->
        <button class="fab" @click="showModal = true">
            <i class="fa-solid fa-circle-plus fa-2x" />
        </button>
    </section>

  

  <!-- MODAL upload ---------------------------------------------------->
  <transition name="fade">
    <div v-if="showModal"
         class="fixed inset-0 z-70 bg-black/60 flex items-center
                justify-center">
      <div class="bg-[#1f1f1f] w-[90vw] max-w-md p-6 rounded-lg text-white">

        <h3 class="text-lg font-semibold mb-4">Novo Short</h3>

        <form @submit.prevent="upload" class="flex flex-col gap-4">
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
              @change="e => form.file = e.target.files[0]"
              class="hidden"
            />
            <button
              type="button"
              @click="$refs.modalFileInput.click()"
              class="px-3 py-1 bg-blue-600 rounded hover:bg-blue-700 text-white"
            >
              Selecionar ficheiro
            </button>
            <span v-if="form.file" class="text-xs text-gray-300 truncate max-w-[120px]">
              {{ form.file.name }}
            </span>

            <!-- opcao de postar na feed tamvbém botao toggle -->
            <label class="flex items-center gap-2">
              <span class="text-sm">Postar na Galeria</span>
              <input type="checkbox" v-model="postarNaGaleria" class="cursor-pointer" />
            </label>

            
          </div>

          <div class="flex justify-end gap-3 mt-2">
            <button type="button" @click="resetModal"
                    class="px-4 py-1 bg-gray-600 rounded">Cancelar</button>
            <button type="submit" :disabled="!form.file"
                    class="px-4 py-1 bg-blue-600 rounded
                           disabled:bg-gray-500">
              Enviar
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted, computed, defineEmits, defineProps } from 'vue'
import { useAsyncAction } from '@/composables/useAsyncAction'
import api   from '@/services/api'
import { toast } from 'vue3-toastify'
import ShortComment from '@/components/comment/shortCommentDrawer.vue'

/* Shorts component - name handled by <script setup> */
/* ------------------------------------------------------------------ */
/* helpers                                                            */
/* ------------------------------------------------------------------ */
//const backend = process.env.VUE_APP_URL_BASE || ''
function isVideo (url = '') {
  return /\.(mp4|webm|mov|mkv|gif)$/i.test(url)
}

const PAGE = 1      // 1 short de cada vez
/* ------------------------------------------------------------------ */
/* state                                                              */
/* ------------------------------------------------------------------ */
const shorts  = ref([])   // pilha já carregada
const offset  = ref(0)
const loading = ref(false)
const showModal = ref(false)
const form = ref({ titulo:'', descricao:'', file:null })
const emit = defineEmits(['new-short'])
const defaultAvatar = '/default-avatar.png'
const liked = ref(false)
const showComments = ref(false)   // opens / closes the panel
const postarNaGaleria = ref(false) // novo estado para opção de postar na feed
const likeCount  = ref(0)


/* props */
const props = defineProps({
  logged_user: { type: Object, default: () => ({}) },
})

/* computed curto */
const current   = computed(() => shorts.value.at(-1) || null)
const canPrev   = computed(() => shorts.value.length > 1)


/* ------------------------------------------------------------------ */
/* fetching                                                           */
async function fetchNext () {
  if (!props.logged_user || !props.logged_user.id) {    
    return
  }
  if (loading.value) return
  loading.value = true

  const { data } = await api.get('/app/postagem/pagination/', {
    params: { offset: offset.value, limit: PAGE }
  })
  if (!data.results || data.results.length === 0) {
    //toast.info('Não há mais shorts para mostrar.', { autoClose: 1500 })
    loading.value = false
    return
  }
    const short = data.results[0]

  // pergunta ao backend se o user curtiu
  const chk = await api.get(
    `/app/postagemlike/check/postagem/${short.id}/utilizador/${props.logged_user.id}/`
  )

  /* guarda info dentro do próprio objeto ------------------------ */
  short.userLiked = chk.data.liked
  likeCount.value = short.likes || 0

  liked.value = short.userLiked       // reflecte no botão

  shorts.value.push(short)
  offset.value += PAGE
  loading.value = false
}

/* navegação */
function next () { fetchNext() }
// function prev () {
//   if (canPrev.value){
//     showComments.value = false // fecha comentários ao navegar

//     shorts.value.pop()  // remove o último short


//     offset.value -= PAGE
//     if (offset.value < 0) offset.value = 0 // evita offset negativo


//   }
  

// }

function prev () {
  if (canPrev.value) {
    showComments.value = false
    shorts.value.pop()

    offset.value -= PAGE
    if (offset.value < 0) offset.value = 0

   /* recarrega estado de like/likes do short actual -------------- */
   if (current.value) {
     liked.value     = !!current.value.userLiked
     likeCount.value = current.value.likes || 0
   }
  }
}

function openComments () { showComments.value = true }
function closeComments () { showComments.value = false }

function incrementComments () {
  if (current.value) {
    current.value.comentarios = (current.value.comentarios || 0) + 1
  }
}

function resetModal () {
  form.value = { titulo:'', descricao:'', file:null }
  showModal.value = false
}

/* wheel / swipe listener throttled */
// let last = 0
// function handleWheel (e) {
//   const now = Date.now()
//   if (now - last < 600) return   // ~0.6 s debounce
//   last = now
//   e.deltaY > 0 ? next() : prev()
// }

/* ------------------------------------------------------------------ */
/* upload                                                             */
const { wrap } = useAsyncAction()

function closeModal () {
  form.value = { titulo:'', descricao:'', file:null }
  showModal.value = false
}

/* like / unlike */
const toggleLike = () => wrap(async () => {
  if (!current.value) return
  if (liked.value) {
    await api.delete(
      `/app/postagemlike/unlike/postagem/${current.value.id}/utilizador/${props.logged_user.id}/`
    )
    liked.value           = false
    likeCount.value      -= 1
    current.value.userLiked = false
    current.value.likes     = likeCount.value
  } else {
    await api.post(
      `/app/postagemlike/registar/`,
      { postagem_id: current.value.id, utilizador_id: props.logged_user.id }
    )
    liked.value           = true
    likeCount.value      += 1
    current.value.userLiked = true
    current.value.likes     = likeCount.value
  }
})

function upload () {
  if (!form.value.file) return
  wrap(async () => {
    const fd = new FormData()
    fd.append('titulo',        form.value.titulo)
    fd.append('descricao',     form.value.descricao)
    fd.append('utilizador_id', props.logged_user.id)
    fd.append('ficheiro',      form.value.file)
    fd.append('postar_na_galeria', postarNaGaleria.value) // inclui opção de postar na feed


    await api.post('/app/postagem/registar/', fd,
      { headers:{'Content-Type':'multipart/form-data'} })

    toast.success('Short enviado!', { autoClose: 1200 })
    postarNaGaleria.value = false

    closeModal()
    offset.value = 0           // reinicia paginação
    shorts.value = []
    await fetchNext()


    /* avisa pai opcionalmente */
    emit('new-short')
  })
}

/* ------------------------------------------------------------------ */
/* boot                                                                */
/* ------------------------------------------------------------------ */
onMounted(async () => {
    console.log('short utilizador', props.logged_user)
  await fetchNext()
  // window.addEventListener('wheel', handleWheel, { passive:true })
})
</script>

<style scoped>
.shorts-wrapper{
  position:relative;
  width:100vw;
  height:90vh;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#000;
  overflow:hidden;
  display:flex;
  gap: 24px;
}
.short{
  position:relative;
  width:360px;
  height:640px;
  border-radius:14px;
  overflow:hidden;
}
.media{width:100%;height:100%;object-fit:cover;}
.overlay{
  position:absolute;left:0;top:0;width:100%;
  padding:12px;background:linear-gradient(transparent,rgba(0,0,0,.6));
  color:#fff;font-size:.9rem;
}
.desc{font-size:.75rem;opacity:.8;}

.nav{
  position:absolute;right:24px;
  width:42px;height:42px;border-radius:50%;
  background:rgba(255,255,255,.15);color:#fff;
  display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;cursor:pointer;border:none;
  transition:.2s;
}
.nav.up   {top:calc(50% - 100px);}
.nav.down {top:calc(50% + 100px);}
.nav:disabled{opacity:.35;cursor:default;}
.nav:not(:disabled):hover{background:rgba(255,255,255,.3);}

.fab{
  position:absolute;bottom:24px;right:24px;
  width:56px;height:56px;border-radius:50%;
  background:#2563eb;display:flex;align-items:center;justify-content:center;
  color:#fff;cursor:pointer;border:none;
  transition:.2s;
}
.fab:hover{background:#1e4fc5;}

.fade-enter-active,.fade-leave-active{transition:opacity .2s}
.fade-enter-from,.fade-leave-to{opacity:0}

.modal-cover{
  position:fixed;inset:0;background:rgba(0,0,0,.6);
  display:flex;align-items:center;justify-content:center;
}
.modal{
  background:#1f1f1f;padding:20px;border-radius:10px;width:340px;
}
.field{width:100%;padding:8px;border-radius:6px;background:#323232;color:#fff;}
.file{color:#cbd5e1}
.actions{display:flex;justify-content:flex-end;gap:8px;margin-top:12px}
.actions button{padding:6px 14px;border-radius:6px;background:#2563eb;color:#fff;}
.actions button:first-child{background:#555}
.actions button:disabled{opacity:.5;cursor:default}
</style>
