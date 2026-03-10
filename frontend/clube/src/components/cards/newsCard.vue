<template>
    <!-- overlay -->
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70">

        <!-- cartão -->
        <div class="relative w-[90vw] max-w-4xl max-h-[90vh] bg-white rounded-lg overflow-hidden flex flex-col">

            <!-- botão fechar -->
            <button @click="closeNews"
                class="absolute top-4 right-4 text-2xl text-white-500  h-8 w-8 flex items-center justify-center ">
                <i class="fa-regular fa-circle-xmark"></i>            </button>

            
            <!-- conteúdo rolável -->
            <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden      
                 ">

                <!-- imagem de capa -->
                <img v-if="news.foto" :src="backendUrl + news.foto" alt="capa" class="w-full h-[30rem] object-cover object-center" />
                <div class="flex-1 space-y-4 p-6 break-words">
                    <h1 class="text-3xl font-bold text-black break-words">
                    {{ news.titulo }}
                    </h1>

                    <p v-if="news.subtitulo" class="text-lg text-gray-600 break-words">
                        {{ news.subtitulo }}
                    </p>

                    <div class="text-xs text-gray-500 flex gap-4">
                        <span>{{ news.data?.slice(0,10) }}</span>
                        <span v-if="news.autor">por {{ news.autor }}</span>
                    </div>

                    <p v-if="news.resumo" class="italic text-gray-600">{{ news.resumo }}</p>

                    <!-- citação destacada -->
                    <blockquote v-if="news.quote" class="border-l-4 border-blue-600 pl-4 text-blue-700 italic">
                        {{ news.quote }}
                    </blockquote>
                    
                    <p class="whitespace-pre-line text-gray-600 break-words">
                        {{ news.conteudo }}
                    </p>

                    

                </div>
                
            </div>

            <CommentsDrawer
              :open="showComments"
              :noticia-id="noticiaId"
              :user-id="userId"
              @close="showComments=false"
              @new-comment="incrementComments"
            />

            <!-- rodapé fixo -->
            <div class="border-t p-4 flex items-center justify-between text-sm">
                <div class="flex items-center gap-6">
                    <!-- likes -->
                    <button @click="toggleLike" class="flex items-center gap-1">
                        <i :class="liked ? 'fas fa-heart text-blue-600' : 'far fa-heart text-gray-500'"></i>
                        <span class="text-gray-500">{{ likeCount }}</span>
                    </button>

                    <!-- comentários -->
                    <div class="flex items-center gap-1">
                        <i class="far fa-comment text-gray-500"></i>
                        <span class="text-gray-500">{{ news.comentarios }}</span>
                    </div>
                </div>

                <button class="text-blue-600 hover:text-blue-800" @click="openComments">
                  Ver comentários
                </button>
            </div>
        </div>
    </div>
    
</template>
  
  <script>
  import api from '@/services/api'

 
  import { ref, watch, onMounted } from 'vue'
  import { useAsyncAction } from '@/composables/useAsyncAction'
  import CommentsDrawer from '@/components/comment/commentsDrawer.vue'
  
  export default {
    name: 'NewsModal',
    props: {
      noticiaId: { type: Number, required: true },
      open:      { type: Boolean, default: false },
      userId:    { type: Number, required: true }
    },
    components: {
      CommentsDrawer
    },
    emits: ['close', 'like', 'unlike', 'open-comments', 'update-comments'],
  
    setup (props, { emit }) {
      const backendUrl = process.env.VUE_APP_URL_BASE || ''
      const news       = ref({})
      const liked      = ref(false)
      const likeCount  = ref(0)
      const { wrap }   = useAsyncAction()

      const showComments = ref(false)
      
      function openComments () { showComments.value = true }

      function closeNews () {
        emit('close')
        showComments.value = false
      }
  
      /* carregar notícia */
      const fetchNews = async () => {
        if (!props.noticiaId) return
        const res = await api.get(`/app/noticia/${props.noticiaId}/`)
        news.value      = res.data
        likeCount.value = res.data.likes
        // opcional: pedir se o user já curtiu
        const chk = await api.get(`/app/noticialike/check/noticia/${props.noticiaId}/utilizador/${props.userId}/`)
        //if return empty object, then liked is false
        liked.value = chk.data.liked
      }
  
      /* like / unlike */
      const toggleLike = () => wrap(async () => {
        if (liked.value) {
          // un-like
          await api.delete(
            `/app/noticialike/unlike/noticia/${props.noticiaId}/utilizador/${props.userId}/`
          )
          liked.value = false
          likeCount.value--
          emit('unlike', news.value)
        } else {
          await api.post(
            `/app/noticialike/registar/`,
            { noticia_id: props.noticiaId, utilizador_id: props.userId }
          )
          liked.value = true
          likeCount.value++
          emit('like', news.value)
        }
      })

      const incrementComments = () => {
        news.value.comentarios++
        emit('update-comments', news.value.comentarios)

      }
      

      
  
      /* reactivo: sempre que modal abrir ou id mudar, recarrega */
      watch(() => props.open, v => v && fetchNews())
      watch(() => props.noticiaId, fetchNews)
  
      onMounted(fetchNews)
  
      return { backendUrl, news, liked, likeCount, toggleLike,openComments, showComments,incrementComments, closeNews}

      
    }
  }
  </script>
  
  <style scoped>
  /* scrollbar discreta para o conteúdo */
  div[style*="overflow-y-auto"]::-webkit-scrollbar {
    width: 6px;
  }
  div[style*="overflow-y-auto"]::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .text-shadow {
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8); /* Adjust the shadow size and opacity as needed */
}
  </style>
  