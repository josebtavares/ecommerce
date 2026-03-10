<!--  src/components/PostagemComments.vue  -->
<template>
  <!-- drawer (anchored to the right of the short) -->
  <transition name="slide-right">
    <div v-if="open"
         class="panel comments-panel"
         @wheel.stop                      
         @click.stop>

      <!-- little handle bar & close btn --------------------------->
      <div class="mx-auto my-2 h-1 w-12 rounded bg-gray-500/50" />
      <button @click="emit('close')"
              class="absolute top-3 right-3 text-gray-400 hover:text-white">
        <i class="fas fa-times text-sm" />
      </button>

      <!-- comment list ------------------------------------------->
      <transition-group
        name="fade-slide"
        tag="div"
        ref="scrollArea"
        class="flex-1 overflow-y-auto overscroll-contain px-4 py-3 space-y-4"
        @scroll="onScroll">

        <div v-for="c in comments" :key="c.id" class="flex gap-3">
          <img :src="c.utilizador.foto_url || defaultAvatar"
               class="h-9 w-9 rounded-full object-cover" />

          <div class="flex-1">
            <div class="bg-gray-700/70 rounded-lg px-3 py-2 w-fit">
              <p class="font-semibold text-sm text-white">
                {{ c.utilizador.username }}
              </p>
              <p class="text-sm break-words text-gray-200">
                {{ c.conteudo }}
              </p>
            </div>
            <div class="text-[11px] text-gray-400 flex gap-4 mt-1">
              <span>{{ c.data.slice(0,10) }}</span>
              <span>{{ c.likes }} likes</span>
            </div>
          </div>
        </div>

        <!-- loader -->
        <p v-if="loadingMore"
           class="w-full text-center text-xs text-gray-400">a carregar…</p>
      </transition-group>

      <!-- input bar --------------------------------------------->
      <form @submit.prevent="submitComment"
            class="border-t border-gray-700 flex items-center gap-3 px-4 py-2">
        <input v-model="newText"
               placeholder="Adicionar comentário…"
               class="flex-1 rounded-full px-4 py-1 bg-gray-700
                      text-gray-100 placeholder-gray-400 text-sm outline-none" />
        <button type="submit"
                :disabled="!newText.trim()"
                class="px-3 py-1 bg-blue-600 text-white rounded-full text-sm
                       hover:bg-blue-500 disabled:bg-gray-500
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

/* props & emits ----------------------------------------------------*/
const props = defineProps({
  postagemId : { type: Number, required: true },
  open       : { type: Boolean, default: false },
  userId     : { type: Number, required: true }
})
const emit = defineEmits(['close', 'new-comment'])

/* state ------------------------------------------------------------*/
const defaultAvatar = '/default-avatar.png'
const comments    = ref([])
const offset      = ref(0)
const loadingMore = ref(false)
const newText     = ref('')
const { wrap }    = useAsyncAction()

const PAGE = 10

/* API helpers ------------------------------------------------------*/
async function fetchComments (reset = false) {
  if (loadingMore.value) return
  loadingMore.value = true
  if (reset) { comments.value = []; offset.value = 0 }
  try {
    const { data } = await api.get(
      `/app/postagemcomentario/postagem/${props.postagemId}/`,
      { params: { offset: offset.value, limit: PAGE } }
    )
    comments.value.push(...data.results)
    offset.value = data.next_offset ?? null
  } finally { loadingMore.value = false }
}

const submitComment = () => wrap(async () => {
  if (!newText.value.trim()) return
  const { data:newComment } = await api.post(
    '/app/postagemcomentario/registar/',
    {
      postagem_id   : props.postagemId,
      utilizador_id : props.userId,
      conteudo      : newText.value.trim()
    }
  )
  newText.value = ''
  /* 👇 adiciona só o novo – sem recarregar tudo */
  comments.value.unshift(newComment)
  emit('new-comment')
})

/* infinite scroll --------------------------------------------------*/
function onScroll (e) {
  const el = e.target
  if (offset.value !== null &&
      el.scrollTop + el.clientHeight >= el.scrollHeight - 40) {
    fetchComments()
  }
}

/* open / close watcher --------------------------------------------*/
watch(() => props.open, v => v && fetchComments(true))
</script>

<style scoped>
/* drawer dimensions & styling -------------------------------------*/
.panel{
  position:absolute; top:0; right:0;
  width:320px; height:100%;
  background:#1a1a1a;
  display:flex; flex-direction:column;
  border:1px solid #333;
  border-radius:14px;
}

/* drawer slide ----------------------------------------------------*/
.slide-right-enter-active,
.slide-right-leave-active { transition:transform .25s }
.slide-right-enter-from   { transform:translateX(100%) }
.slide-right-leave-to     { transform:translateX(100%) }

/* fade/slide-in for list items ------------------------------------*/
.fade-slide-enter-active{transition:all .25s}
.fade-slide-leave-active{transition:all .25s}
.fade-slide-enter-from,
.fade-slide-leave-to   { opacity:0; transform:translateY(12px) }

/* general ---------------------------------------------------------*/
.overscroll-contain{overscroll-behavior:contain}
</style>
