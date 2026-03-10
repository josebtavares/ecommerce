<template>
    <div :style="divStyle" class="bg-black relative font-koulen">
        <swiper :pagination="pagination" :modules="modules" :autoplay="{ delay: 2000, disableOnInteraction: false }"
            :speed="1000" class="mySwiper">
            <swiper-slide v-for="(item, index) in data" :key="index" 
                style="cursor:pointer;">
                <div class="w-full h-full text-white relative">
                    <img :src="item.photo" alt="Image" class="object-cover" :style="divStyle" @click.prevent="item_clicked(item)">
                    <h3 class="font-koulen text-[20px] absolute top-[15px] right-[15px] text-shadow" @click.prevent="see_more(item)">Ver Mais ></h3>
                    <h1 class="font-koulen text-[40px] absolute bottom-[100px] left-[25px] text-shadow">{{ item.nome }} - {{ item.desconto * 100 }}%</h1>
                    <h1 class="font-koulen text-[40px] absolute bottom-[40px] left-[25px] text-shadow">Total - {{truncateDecimals(item.preco * item.desconto, 2) }}€</h1>
                </div>
            </swiper-slide>
        </swiper>
    </div>
</template>


<script>


import { Swiper, SwiperSlide } from 'swiper/vue'
import { Navigation, Pagination, Autoplay } from 'swiper/modules'

// Import Swiper styles
import 'swiper/css';

import 'swiper/css/pagination';



export default {
    name: 'AppClotheSlider',
    components: {
        Swiper,
        SwiperSlide

    },

    props: {
        data: {
            type: Array,

        },

        width: {
            type: String,
            default: '100vw'
        },

        height: {
            type: String,
            default: '100vh'
        },

    },

    computed: {
        divStyle() {
            return {
                width: this.width,
                height: this.height
            };
        }
    },

    data() {
        return {
            backendUrl: process.env.VUE_APP_URL_BASE,

        };
    },

    created() {

    },
    setup() {
        return {
            pagination: {
                clickable: true,
                renderBullet: function (index, className) {
                    return '<span class="' + className + '"></span>';
                },
            },
            modules: [Navigation, Pagination, Autoplay],
        };
    },

    methods: {
        truncateDecimals(num, dec) {
            const calcDec = Math.pow(10, dec);
            return Math.trunc(calcDec * num) / calcDec;
        },

        see_more(item) {
            // this.$router.push({ name: 'Product', params: { id: item.id } });
            this.$emit('see_more', item)
            console.log(item)
        },
        item_clicked(item) {
            this.$emit('item_clicked', item)
            console.log(item)
        }  
    },
}

</script>

<style scoped>
.swiper {
    --swiper-pagination-bullet-inactive-color: #ffffff;
    --swiper-pagination-color: white;
    --swiper-pagination-bullet-size: 8px;
    /* Adjust this value as needed */

}


.swiper-pagination-bullet-active {
    background-color: #ffffff !important;
}


.swiper-pagination-bullet .swiper-pagination-bullet-active {
    color: white;
    background-color: white !important;
}

.text-shadow {
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8); /* Adjust the shadow size and opacity as needed */
}
</style>