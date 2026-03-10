<template>
    <div class="w-[100vw] h-[100vh] bg-black">
        <NavBar class="absolute top-0 left-0 w-full z-10" />
        <Profile :data="user.utilizador" class=" z-10" @log_out="log_out()"/>
        
       
    </div>

    

    

    


    
    


</template>

<script>


import { Navigation, Pagination, Autoplay } from 'swiper/modules'
import NavBar from '@/components/navbar/navbar.vue'
import Profile from '@/components/profile/UserProfile.vue'

import api from '@/services/api'


import 'swiper/css'
import 'swiper/css/pagination'




export default {
    name: 'AppHome',
    components: {
       
        NavBar,
        Profile,
        
        
        

    },
    data() {
        return {
            homeNews: [],
            news: [],
            backendUrl: process.env.VUE_APP_URL_BASE,
            user: {},
            user_credit_card:{},
            cart_data: [],

            cart_id: 0,

            show_cart: false,

            male_combos: [],

            male_shoes: [],

            male_extras: [],

            show_produtoCard: false,
  
            info_card_data: [],
            
            refreshStats: false,

            produtoFetchUrl: '/app/produto/pagination/?tipo_produto=combo',

            produtoMode: 'data', // 'data' or 'fetch'
            
        }
    },
    async created() {
        const user = localStorage.getItem('user')
        this.user = user ? JSON.parse(user) : {}
        await this.get_user_credit_cards(this.user.utilizador.id)
        await this.get_cart(this.user.utilizador.id)
        console.log("card id:",this.cart_id)
        await this.get_cart_data(this.cart_id)
        await this.fetchHomeNews()
        await this.fetchNews()
        await this.fetchProdutos()
    },
    methods: {
        stopAutoplay() {
            if (this.$refs.mySwiper && this.$refs.mySwiper.swiper) {
                this.$refs.mySwiper.swiper.autoplay.stop()
            }
        },
        startAutoplay() {
            if (this.$refs.mySwiper && this.$refs.mySwiper.swiper) {
                this.$refs.mySwiper.swiper.autoplay.start()
            }
        },
        slider_clicked(item) {
            console.log(item)
        },
        async fetchHomeNews() {
            try {
                const res = await api.get('/app/noticiahome/')
                this.homeNews = res.data
            } catch (error) {
                console.error('Erro ao buscar notícias:', error)
            }
        },

        async fetchNews() {
            try {
                const res = await api.get('/app/noticia/')
                this.news = res.data
            } catch (error) {
                console.error('Erro ao buscar notícias:', error)
            }
        },
        log_out() {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            this.user = {}
            this.user_credit_card = {}
            this.cart_data = []
            this.cart_id = 0
            this.show_cart = false;
            this.show_produtoCard = false;
            this.info_card_data = [];
            console.log("User logged out")
            this.$router.push('/login')
        },

        async get_user_credit_cards(utilizador_id) {
            try {
                const res = await api.get(`/app/cartao/utilizador/${utilizador_id}/`)
                console.log(res.data)
                this.user_credit_card = res.data
            } catch (error) {
                console.error('Erro ao buscar cartões de crédito:', error)
            }
        },

        async get_cart(utilizador_id) {
            try {
                const cart = await api.get(`/app/carrinho/utilizador/${utilizador_id}/`)
                console.log(cart)
                this.cart_id = cart.data.id
            } catch (error) {
                console.error('Erro ao buscar carrinho:', error)
            }
        },

        async get_cart_data(cart_id) {
            console.log("cart_id", cart_id)
            const cart_produtos = (await api.get(`/app/carrinho_produto/carrinho/${cart_id}`)).data
            let produtos = await api.get(`/app/carrinho_produto/carrinho=${cart_id}/produtos/`)
            produtos = produtos.data
            produtos.forEach(produto => {
                produto.photo = `${this.backendUrl}${produto.photo}`
            })
            this.cart_data = produtos.map(produto => {
                const cart_produto = cart_produtos.find(cart_produto => cart_produto.produto == produto.id)
                return {
                    ...produto,
                    quantidade: cart_produto.quantidade,
                    cart_id: cart_id
                }
            })

        },

        async toggle_cart() {
            this.show_cart = false;
            this.close_produtoCard();
            await this.get_cart_data(this.cart_id);
        },

        async add_to_cart(item) {
            console.log("item for the cart:", item)
            if (this.cart_data.some(cart_item => cart_item.id === item.id)) {
                const cart_item = this.cart_data.find(cart_item => cart_item.id === item.id)
                cart_item.quantidade += 1
                const update_data = {
                    carrinho: this.cart_id,
                    produto: cart_item.id,
                    quantidade: cart_item.quantidade
                }
                await api.put(`/app/carrinho_produto/editar/carrinho=${this.cart_id}/produto=${cart_item.id}/`, update_data)
            }
            else {
                const data = {
                    carrinho: this.cart_id,
                    produto: item.id,
                    quantidade: 1
                }
                console.log("add data:", data)
                await api.post('/app/carrinho_produto/registar/', data)

            }
            await this.get_cart_data(this.cart_id);
            this.close_produtoCard();
            const cart = document.querySelector('.cart_fixed')
            cart.classList.toggle('translate-x-full')
            cart.classList.toggle('translate-x-0')

        },

        refresh_Stats(jogo_id) {
            console.log("refresh stats called for game id:", jogo_id)
            this.refreshStats = !this.refreshStats;
            console.log("refresh stats:", this.refreshStats)
        },

        open_produtoCard(item) {
            const cart = document.querySelector('.cart_fixed')
            cart.classList.add('translate-x-full')


            this.info_card_data = [];
            this.info_card_data.push(item);
            console.log(item)
            this.produtoMode = 'data'; // Set mode to 'data' for ProdutoCard
            this.show_produtoCard = true;
        },

        close_produtoCard() {
            this.show_produtoCard = false;
        },
  

        async fetchProdutos() {
            try {
                const combos = await api.get('/app/produto/pagination/?tipo_produto=combo&&offset=0&limit=3')
                const shoes = await api.get('/app/produto/pagination/?tipo_produto=sapato&&offset=0&limit=3')
                const extras = await api.get('/app/produto/pagination/?tipo_produto=acessorio&&offset=0&limit=3')

                this.male_combos = combos.data.results
                this.male_shoes = shoes.data.results
                this.male_extras = extras.data.results
            } catch (error) {
                console.error('Erro ao buscar produtos:', error)
            }
        },
        

        see_more(item) {
            console.log("see more clicked for:", item)
            this.produtoMode = 'fetch'; // Set mode to 'fetch' for ProdutoCard
            this.produtoFetchUrl = `/app/produto/pagination/?tipo_produto=${item.tipo_produto}&&tipo_pessoa=${item.tipo_pessoa}`
            this.show_produtoCard = true;
           
        },

      
    },
    setup() {
        return {
            pagination: {
                clickable: true,
                renderBullet: function (index, className) {
                    return '<span class="' + className + '"></span>'
                },
            },
            modules: [Navigation, Pagination, Autoplay],
        }
    },
}
</script>

<style scoped>
.swiper {
    --swiper-pagination-bullet-inactive-color: #ffffff;
    --swiper-pagination-color: white;
    --swiper-pagination-bullet-size: 12px;
    /* Adjust this value as needed */
  
  }
  
  
  .swiper-pagination-bullet-active {
    background-color: #ffffff !important;
  }
  
  
  .swiper-pagination-bullet .swiper-pagination-bullet-active {
    color: white;
    background-color: white !important;
  }

  .background_loja {
    background-image: url('../assets/img/fundo_loja.png');
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
    
  }

  /* .background_noticia {
    background-image: url('../assets/img/fundo_noticia.jpg');
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
  } */

  .background_noticia {
    position: relative;
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
    overflow: hidden;
}

.background_noticia::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('../assets/img/fundo_noticia.jpg');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    opacity: 0.3; /* Adjust the opacity as needed */
}

</style>