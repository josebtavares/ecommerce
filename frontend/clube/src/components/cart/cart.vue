<template>
    <div class="text-white fixed top-6 right-32">
        <div @click.prevent="toggle_cart" class=" cursor-pointer">
            <font-awesome-icon :icon="['fas', 'cart-shopping']" size="xl" />

        </div>

        <div class="fixed cart_fixed top-0 right-0 w-[30vw] h-[100vh] bg-[#171717] text-white p-4 transition-transform duration-300 transform translate-x-full overflow-auto z-10 bg-opacity-70">
            <div class="pb-3 w-6 h-6 cursor-pointer">
                <font-awesome-icon :icon="['fas', 'xmark']" @click.prevent="toggle_cart" />
            </div>
            <div class="flex flex-col gap-2 justify-between h-[90%]">
                <ul class=" flex flex-col h-[57vh]  text-xl overflow-auto">
                
                    <li class="flex gap-3 p-2 pb-5 h-1/3 border-b border-gray-500 items-center justify-center " v-for="(item, index) in cart_data.filter(cart_item => cart_item.quantidade > 0)" :key="index" ref="listItem">
                       <div class="w-1/2 h-full">
                           <img class="w-full h-full object-cover" :src="item.photo" alt="">
                       </div>
    
                       <div class="flex flex-col gap-1 text-xs w-full">
                              <div><h3>{{ item.nome }}</h3></div>
                              <div class="text-gray-500"><h3>{{ item.desconto *100}}%</h3></div>
                              <div class="flex gap-1 items-center justify-between">
                                  <div><h3>{{truncateDecimals(item.preco * item.desconto, 2) }}€</h3></div>
                                  <div class="flex gap-2">
                                      <font-awesome-icon :icon="['fas', 'circle-minus']" size="xl" style="color:#FFFFFF; cursor: pointer;" @click="set_qtd(item,-1)"/>
                                      <div ><h3>{{ item.quantidade }}</h3></div>
                                      <font-awesome-icon :icon="['fas', 'circle-plus']" size="xl" style="color: #FFFFFF; cursor: pointer;" @click="set_qtd(item,1)"/>
                                  </div>
                            </div>
                            
                        </div>
                    </li>
                </ul>
    
                <div>
                    <div class="flex justify-between p-1 ">
                        <div class=" text-white-200"><h3>Itens</h3></div>
                        <div><h3>{{ items_price }}€</h3></div>
                    </div>
                    <div class="flex justify-between p-1 ">
                        <div class=" text-white-200"><h3>Taxa</h3></div>
                        <div><h3>{{ taxa}}€</h3></div>
                    </div>
                    
                    <div class="flex justify-between p-1 text-[#ffffff]">
                        <div ><h3>Total</h3></div>
                        <div><h3>{{ total_price }}€</h3></div>
                    </div>
    
                    <button class="bg-[#ffffff] text-black p-2 rounded-lg w-full" @click="goto_payment">Finalizar compra</button>
                </div>
            </div>
        </div>

    </div>
</template>


<script>

import api from '@/services/api'
export default {
    name: 'AppCart',
    components: {
        
    },
    props: {
        data: {
            type: Array,
            default: () => [{
                photo: '',
                nome: '',
                preco: 0,
                quantidade: 0,
            }]
        },
    },

    created() {
        this.get_items_price()
        this.get_total_price()
    },

    watch: {
        data: {
            handler() {
                // console.log('cart updated')
                this.cart_data = [...this.data]
                this.$nextTick(() => {
                    if (this.$refs.listItem && this.$refs.listItem.length > 0) {
                        this.$refs.listItem[this.$refs.listItem.length - 1].scrollIntoView();
                    }
                });
                
                
            },
            deep: false
        },

        cart_data: {
            handler() {
                // console.log('cart_data updated')
                this.get_items_price()
                this.get_total_price()
            },
            deep: true
        }
    },
    methods: {
        async toggle_cart() {
            const cart = document.querySelector('.cart_fixed')
            cart.classList.toggle('translate-x-full')
            cart.classList.toggle('translate-x-0')

            

            await this.update_cart()
            this.$emit('toggle_cart')

        },
        get_items_price(){
            this.taxa=this.truncateDecimals(this.taxa, 2)
            this.items_price = 0
            this.cart_data.forEach(item => {
                this.items_price += this.truncateDecimals((item.preco*item.desconto) * item.quantidade, 2)
            })
            
        },

        get_total_price(){
            this.total_price = this.truncateDecimals(this.items_price + this.taxa, 2)
        },

        truncateDecimals(num, dec) {
            const calcDec = Math.pow(10, dec);
            return Math.trunc(calcDec * num) / calcDec;
        },
        set_qtd(item, qtd){
            this.cart_data.forEach(async cart_item => {
                if(cart_item.id === item.id){
                    cart_item.quantidade += qtd
                    if(cart_item.quantidade < 0){
                        cart_item.quantidade = 0
                    }
                    await this.update_cart()
                }
            })
            this.cart_data = this.cart_data.filter(cart_item => cart_item.quantidade > 0);
            
            // console.log("carrinho:",this.cart_data)
        },

        goto_payment(){
            const payment_info={
                total: this.total_price,
                produtos:[
                    ...this.cart_data.filter(cart_item => cart_item.quantidade > 0).map(cart_item => {
                        return {
                            nome: cart_item.nome,
                            quantidade:cart_item.quantidade
                        }
                    })
                ]
            }
            this.$emit('goto_payment', payment_info)
        },

        async update_cart(){
            for (const item of this.cart_data) {
                if(item.quantidade === 0){
                    await api.delete(`/app/carrinho_produto/eliminar/carrinho=${item.cart_id}/produto=${item.id}/`)

                }
                else if(this.data.some(cart_item => cart_item.id === item.id)){
                    item.quantidade = this.data.find(cart_item => cart_item.id === item.id).quantidade
                    const update_data={
                        carrinho:item.cart_id,
                        produto:item.id,
                        quantidade:item.quantidade
                    }
                    
                    await api.put(`/app/carrinho_produto/editar/carrinho=${item.cart_id}/produto=${item.id}/`, update_data)
                    
                }
                else{
                    const new_data={
                        carrinho:item.cart_id,
                        produto:item.id,
                        quantidade:item.quantidade
                    }
                    await api.post('/app/carrinho_produto/registar/', new_data)
                }
            }
        },

       
    },
    data() {
        return {
            cart_data: [...this.data],
            items_price:0,
            taxa: 2.30,
            total_price: 0
        }
    },

    

}   

</script>


<style scoped>

</style>

