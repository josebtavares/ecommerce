<template>
  <div :style="divStyle" class="bg-black font-koulen">
    <swiper :pagination="pagination" :modules="modules" :autoplay="{ delay: 2000, disableOnInteraction: true }"
      :speed="1000" class="mySwiper h-full">

      <swiper-slide v-for="(item, idx) in data" :key="idx"
        class="flex justify-center items-stretch h-full cursor-pointer" @click.prevent="see_more(item)">
        <!-- CARD -->
        <div class="grid w-full h-full bg-white rounded-lg shadow-lg overflow-hidden"
          style="grid-template-rows:65% 35%">

          <!-- imagem ---------------------------------------------------------->
          <div class="overflow-hidden">
            <img :src="backendUrl + item.foto" alt="notícia" class="w-full h-full object-cover" />
          </div>

          <!-- bloco de texto -------------------------------------------------->
          <div class="grid grid-rows-[auto_1fr_auto] h-full p-4">

            <!-- título (não rola) -->
            <h3 class="text-xl font-bold text-gray-900 break-words" @click.stop.prevent="see_more(item)">
              {{ item.titulo }}
            </h3>

            <!-- conteudo rolável somente na vertical -->
            <div class="overflow-y-auto break-words whitespace-pre-line text-sm text-gray-700 pr-1">
              {{ item.conteudo }}
            </div>

            <!-- rodapé fixo ------------------------------------------------------>
            <div class="flex items-center justify-between pt-2 border-t text-xs">
              <!-- data -->
              <span class="text-gray-500">{{ item.data.slice(0, 10) }}</span>

              <!-- acções -->
              <div class="flex items-center gap-5 text-sm">
                <!-- ♥ like -->
                <button @click.stop="toggleLike(item)" class="flex items-center gap-1 ">
                  <i :class="liked.has(item.id)
                    ? 'fas fa-heart text-blue-600 cursor-pointer'
                    : 'far fa-heart text-gray-500 cursor-pointer'" class="text-lg">
                  </i>
                  <span class="text-black">{{ displayedLikes(item) }}</span>
                </button>

                <!-- 💬 comentários (apenas mostra) -->
                <div class="flex items-center gap-1">
                  <i class="far fa-comment text-gray-500 text-lg cursor-pointer"></i>
                  <span class="text-black">{{ item.comentarios }}</span>
                </div>

                <!-- Ler -->
                <button class="text-blue-600 hover:text-blue-800 cursor-pointer" @click.stop.prevent="see_more(item)">
                  Ler &gt;
                </button>
              </div>
            </div>
          </div>
        </div>

      </swiper-slide>
    </swiper>
  </div>

  <NewsCard
    :open="showNewsCard"
    :noticia-id="selected_news.id"
    :user-id="user.id"
    @close="showNewsCard = false"
    @like="toggleLike(selected_news)"
    @unlike="toggleLike(selected_news)"
    @update-comments="updateComments"
    
  />
</template>
  
  
<script>
import api from '@/services/api'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Navigation, Pagination, Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'
import NewsCard from '@/components/cards/newsCard.vue'

export default {
  name: 'NewsSlider',
  components: { Swiper, SwiperSlide, NewsCard },

  props: {
    data: Array,
    width: { type: String, default: '100vw' },
    height: { type: String, default: '100vh' }
  },
 

  data() {
    return {
      backendUrl: process.env.VUE_APP_URL_BASE,
      liked: new Set()  ,        // ids que o utilizador já curtiu nesta sessão
      user:{}, // utilizador logado, se existir
      selected_news:{},
      showNewsCard: false, // controla a visibilidade do card de notícias
    }
  },

  computed: {
    divStyle() { return { width: this.width, height: this.height } }
  },

  created() {
    //carregar utilizador do localStorage
    const user = localStorage.getItem('user')
    this.user = user ? JSON.parse(user) : {}
    this.user= this.user.utilizador
    console.log('news Utilizador carregado:', this.user)
    // carregar likes do backend
    if (this.user.id) {
      this.liked = new Set() // reiniciar o conjunto de likes
      // buscar likes do utilizador
      // (se o utilizador não estiver logado, não faz nada)

      api.get(`/app/noticialike/utilizador/${this.user.id}/`)
        .then(res => {
          res.data.forEach(like => this.liked.add(like.noticia_id))
        })
        .catch(error => {
          console.error('Erro ao carregar likes:', error)
        })
    }
  },

  setup() {
    return {
      pagination: {
        clickable: true,
        renderBullet: (i, cls) => `<span class="${cls}"></span>`
      },
      modules: [Navigation, Pagination, Autoplay]
    }
  },

  methods: {
    /* mostra likes recebidos do backend + like local se existir */
    displayedLikes(item) {
      
      return item.likes;
    },

    async toggleLike(item) {
      if (this.liked.has(item.id)) {
        this.liked.delete(item.id)
        //enviar para backend
        try {
          await api.delete(`/app/noticialike/unlike/noticia/${item.id}/utilizador/${this.user.id}/`)
          // remover o like do item
          item.likes = (item.likes || 0) - 1; // decrementa o número de likes
          //atualizar lista de likes

          
        } catch (error) {
          console.error('Erro ao remover like:', error)
        }
      } else {
        this.liked.add(item.id)
        //enviar para backend
        try {
          console.log('Adicionando like para:', item.id, 'utilizador:', this.user.id)
          const res= await api.post('/app/noticialike/registar/', {
            noticia_id: item.id,
            utilizador_id: this.user.id
          })
          console.log('Like adicionado:', res.data)
          // adicionar o like ao item
          item.likes = (item.likes || 0) + 1; // incrementa o número de likes
        } catch (error) {
          console.error('Erro ao adicionar like:', error)
        }
        
      }
    },

    item_clicked(item) { this.$emit('item_clicked', item) },
    see_more(item) { 
      this.selected_news = item
      this.showNewsCard = true
      //this.$emit('see_more', item) 
    },
    updateComments(comments) {
      // Atualiza o número de comentários na notícia selecionada
      this.selected_news.comentarios = comments
    }
  },

  // watch: {
  //   // se o utilizador mudar, reiniciar os likes
  //   async user(newUser) {
  //     this.liked = new Set()
  //     if (newUser.id) {
  //       await api.get(`/noticialike/utilizador/${newUser.id}/`)
  //         .then(res => {
  //           res.data.forEach(like => this.liked.add(like.noticia_id))
  //         })
  //         .catch(error => {
  //           console.error('Erro ao carregar likes:', error)
  //         })
  //     }
  //   },
  //   async data(newData) {
  //     console.log('Dados atualizados:', newData)
  //     // reiniciar os likes quando os dados mudarem
  //     this.liked = new Set()
  //     if (this.user.id) {
  //       await api.get(`/noticialike/utilizador/${this.user.id}/`)
  //         .then(res => {
  //           res.data.forEach(like => this.liked.add(like.noticia_id))
  //         })
  //         .catch(error => {
  //           console.error('Erro ao carregar likes:', error)
  //         })
  //     }
  //   },
  //   immediate: true, // para garantir que os likes são carregados ao iniciar
  //   deep: true // para garantir que os likes são atualizados quando os dados mudam
  // }
}
</script>


  
  <style scoped>
  /* optional line-clamp helpers (Tailwind ≥ v3.3 já tem utilities) */
  .line-clamp-2, .line-clamp-3 {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .line-clamp-2 {
  .line-clamp-3 {
    -webkit-line-clamp: 3;
    line-clamp: 3;
  }
    line-clamp: 2;
  }
  .line-clamp-3 {
    -webkit-line-clamp: 3;
    line-clamp: 3;
  }
  
  .swiper {
    --swiper-pagination-bullet-inactive-color: #424242;
    --swiper-pagination-color: var(--color-blue-600);
    --swiper-pagination-bullet-size: 8px;
  }
  .swiper-pagination-bullet-active { background:#ffffff !important; }
  </style>
  
