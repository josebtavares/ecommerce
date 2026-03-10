<!-- components/NewsComments.vue  (versão light + 50 % altura) -->
<template>
  <transition name="slide-up">
    <div v-if="open"
         class="drawer flex flex-col"      
         @wheel.stop
         @click.stop>

      <!-- “handle” + botão fechar -->
      <div class="mx-auto mt-1 h-1 w-12 rounded bg-gray-400/70" />
      <button class="absolute top-2 right-3 text-gray-500 hover:text-gray-800"
              @click="$emit('close')">
        <i class="fas fa-times text-xs" />
      </button>

      <!-- lista ----------------------------------------------------->
      <transition-group
        name="fade-slide" tag="div"
        ref="scrollArea"
        class="flex-1 overflow-y-auto overscroll-contain
               px-3 py-2 space-y-3"
        @scroll="onScroll">

        <div v-for="c in comments" :key="c.id" class="flex gap-2">
          <img :src="c.utilizador.foto_url || defaultAvatar"
               class="h-7 w-7 rounded-full object-cover" />

          <div class="flex-1">
            <div class="bg-gray-200 rounded-lg px-3 py-1.5 w-fit">
              <p class="font-semibold text-sm text-gray-800">
                {{ c.utilizador.username }}
              </p>
              <p class="text-sm break-words  text-gray-700">
                {{ c.conteudo }}
              </p>
            </div>
            <div class="text-[11px] text-gray-500 flex gap-4 mt-0.5">
              <span>{{ c.data.slice(0,10) }}</span>
              <span>{{ c.likes }} likes</span>
            </div>
          </div>
        </div>

        <p v-if="loadingMore"
           class="w-full text-center text-xs text-gray-500">
          a carregar…
        </p>
      </transition-group>

      <!-- input ----------------------------------------------------->
      <form @submit.prevent="submitComment"
            class="border-t border-gray-300 flex items-center gap-2 px-3 py-2">
        <input v-model="newText"
               placeholder="Adicionar comentário…"
               class="flex-1 rounded-full px-3 py-1 bg-gray-100 text-black
                      placeholder-gray-400 text-sm outline-none" />
        <button type="submit"
                :disabled="!newText.trim()"
                class="px-3 py-1 bg-blue-600 text-white rounded-full text-sm
                       hover:bg-blue-500 disabled:bg-gray-400
                       transition disabled:cursor-not-allowed">
          Enviar
        </button>
      </form>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue'
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'

/* props / emits --------------------------------------------------*/
const props = defineProps({
  noticiaId : { type: Number, required: true },
  open      : { type: Boolean, default: false },
  userId    : { type: Number, required: true }
})
const emit = defineEmits(['close','new-comment'])

/* state ----------------------------------------------------------*/
const defaultAvatar = '/default-avatar.png'
const comments      = ref([])
const offset        = ref(0)
const loadingMore   = ref(false)
const newText       = ref('')
const { wrap }      = useAsyncAction()
const PAGE = 10

/* fetch ----------------------------------------------------------*/
async function fetchComments (reset=false){
  if (loadingMore.value) return
  loadingMore.value = true
  if (reset){ comments.value=[]; offset.value=0 }
  try{
    const { data } = await api.get(
      `/app/noticiacomentario/noticia/${props.noticiaId}/`,
      { params:{ offset:offset.value, limit:PAGE } }
    )
    comments.value.push(...data.results)
    offset.value = data.next_offset ?? null
  }finally{ loadingMore.value=false }
}

/* enviar ---------------------------------------------------------*/
const submitComment = () => wrap(async ()=>{
  if(!newText.value.trim()) return
  const { data:newComment } = await api.post(
    '/app/noticiacomentario/registar/',
    { noticia_id:props.noticiaId,
      utilizador_id:props.userId,
      conteudo:newText.value.trim() }
  )
  newText.value = ''
  comments.value.unshift(newComment)   // anima só o novo
  emit('new-comment')
})

/* infinite scroll -----------------------------------------------*/
function onScroll(e){
  const el = e.target
  if(offset.value!==null &&
     el.scrollTop + el.clientHeight >= el.scrollHeight-40){
    fetchComments()
  }
}

/* watcher open ---------------------------------------------------*/
watch(()=>props.open, v=>{ if(v) fetchComments(true) })
</script>

<style scoped>
/* Drawer ocupa 100 % de largura do card e 50 % da altura */
.drawer{
  position:absolute;
  left:0; bottom:0;
  width:100%;
  height:50%;          /* ← metade da altura do cartão */
  background:#ffffff;
  border-top:1px solid #e5e7eb;
  border-radius:12px 12px 0 0;
  /* resto igual … */
}

/* animações ------------------------------------------------------*/
.slide-up-enter-active,
.slide-up-leave-active{transition:transform .25s}
.slide-up-enter-from {transform:translateY(100%)}
.slide-up-leave-to   {transform:translateY(100%)}

.fade-slide-enter-active{transition:all .25s}
.fade-slide-leave-active{transition:all .25s}
.fade-slide-enter-from,
.fade-slide-leave-to{opacity:0;transform:translateY(10px)}

.overscroll-contain{overscroll-behavior:contain}
</style>
