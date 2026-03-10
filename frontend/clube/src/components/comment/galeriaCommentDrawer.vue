<!-- components/GaleriaComment.vue -->
<template>
  <transition name="slide-up">
    <div v-if="open"
         class="drawer flex flex-col"
         @wheel.stop
         @click.stop>

      <!-- handle & close ------------------------------------------------>
      <div class="mx-auto mt-1 h-1 w-12 rounded bg-gray-500/60" />
      <button class="absolute top-2 right-3 text-gray-400 hover:text-gray-200"
              @click="$emit('close')">
        <i class="fas fa-times text-xs" />
      </button>

      <!-- comments list ------------------------------------------------->
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
            <div class="bg-gray-700/70 rounded-lg px-3 py-1.5 w-fit">
              <p class="font-semibold text-sm text-white">
                {{ c.utilizador.username }}
              </p>
              <p class="text-sm break-words text-gray-200">
                {{ c.conteudo }}
              </p>
            </div>
            <div class="text-[11px] text-gray-400 flex gap-4 mt-0.5">
              <span>{{ c.data.slice(0,10) }}</span>
              <span>{{ c.likes }} likes</span>
            </div>
          </div>
        </div>

        <p v-if="loadingMore"
           class="w-full text-center text-xs text-gray-400">
          a carregar…
        </p>
      </transition-group>

      <!-- input bar ----------------------------------------------------->
      <form @submit.prevent="submitComment"
            class="border-t border-gray-600 flex items-center gap-2 px-3 py-2">
        <input v-model="newText"
               placeholder="Adicionar comentário…"
               class="flex-1 rounded-full px-3 py-1 bg-gray-700 text-gray-100
                      placeholder-gray-400 text-sm outline-none" />
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

/* props / emits ---------------------------------------------------*/
const props = defineProps({
  galeriaId : { type: Number, required: true },   // <- id do item da galeria
  open      : { type: Boolean, default: false },
  userId    : { type: Number, required: true }
})
const emit = defineEmits(['close', 'new-comment'])

/* state -----------------------------------------------------------*/
const defaultAvatar = '/default-avatar.png'
const comments      = ref([])
const offset        = ref(0)
const loadingMore   = ref(false)
const newText       = ref('')
const { wrap }      = useAsyncAction()
const PAGE = 10

/* get comments ----------------------------------------------------*/
async function fetchComments (reset = false) {
  if (loadingMore.value) return
  loadingMore.value = true
  if (reset) { comments.value = []; offset.value = 0 }
  try {
    const { data } = await api.get(
      `/app/galeriacomentario/galeria/${props.galeriaId}/`,
      { params: { offset: offset.value, limit: PAGE } }
    )
    comments.value.push(...data.results)
    offset.value = data.next_offset ?? null
  } finally {
    loadingMore.value = false
  }
}

/* send comment ----------------------------------------------------*/
const submitComment = () => wrap(async () => {
  if (!newText.value.trim()) return
  const { data:newComment } = await api.post(
    '/app/galeriacomentario/registar/',
    {
      galeria_id   : props.galeriaId,
      utilizador_id: props.userId,
      conteudo     : newText.value.trim()
    }
  )
  newText.value = ''
  comments.value.unshift(newComment)   // adiciona só o novo
  emit('new-comment')
})

/* infinite scroll -------------------------------------------------*/
function onScroll (e) {
  const el = e.target
  if (
    offset.value !== null &&
    el.scrollTop + el.clientHeight >= el.scrollHeight - 40
  ) {
    fetchComments()
  }
}

/* open watcher ----------------------------------------------------*/
watch(() => props.open, v => { if (v) fetchComments(true) })
</script>

<style scoped>
/* ocupa 100 % de largura do profile drawer e 50 % da altura --------*/
.drawer{
  position:fixed;          /* instead of absolute                */
  right:0; bottom:0;        /* hug the right edge                 */
  width:50vw;              /* match the profile drawer’s width   */
  height:50%;
  background:#1a1a1a;
  border-top:1px solid #333;
  border-radius:12px 0 0 0; /* only top-left rounded now */
  z-index:95;
}

/* slide animation -------------------------------------------------*/
.slide-up-enter-active,
.slide-up-leave-active { transition:transform .25s }
.slide-up-enter-from   { transform:translateY(100%) }
.slide-up-leave-to     { transform:translateY(100%) }

/* items fade / slide ---------------------------------------------*/
.fade-slide-enter-active,
.fade-slide-leave-active{transition:all .25s}
.fade-slide-enter-from,
.fade-slide-leave-to   {opacity:0; transform:translateY(10px)}

/* prevent parent scroll ------------------------------------------*/
.overscroll-contain{overscroll-behavior:contain}
</style>
