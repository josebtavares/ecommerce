<template>
    <div class="text-white fixed top-6 right-[2.5vw]">
        <div @click.prevent="toggle_profile" class=" cursor-pointer">
            <font-awesome-icon :icon="['fas', 'user']" size="xl" />
        </div>

        <div
            class="fixed profile_fixed top-0 right-0 w-[50vw] h-[100vh] bg-[#171717] text-white p-4 transition-transform duration-300 transform translate-x-full overflow-auto z-10 bg-opacity-80">
            <div class="pb-3 w-6 h-6 cursor-pointer">
                <font-awesome-icon :icon="['fas', 'xmark']" @click.prevent="toggle_profile" />
            </div>
            <div class="flex flex-col gap-2  h-[95%] p-2">
                <!-- Campo de foto --------------------------------------------------->
                <div class="">

                    <div class="mt-2 flex  justify-center gap-3">
                        <!-- Avatar preview -->
                        <img :src="previewUrl" alt="preview" class="h-30 w-30 rounded-full object-cover border" />

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
                <div class>

                    <div class="mt-4">
                        <h3>Bem-vindo(a) {{ data.username }}</h3>
                    </div>
                    <!-- <div><h3>{{ data.email_address }}</h3></div> -->
                    <!-- <div><h3>Olá {{ data.email_address }}</h3></div> -->

                    <!-- <div><h3>{{ data.email_address }}</h3></div> -->
                </div>

                <div class="w-fit mt-auto" @click.prevent="log_out">
                    <h3 class="cursor-pointer hover:underline">Terminar sessão</h3>
                </div>

            </div>
        </div>

    </div>
</template>


<script>
import { useAsyncAction } from '@/composables/useAsyncAction'
import { toast } from 'vue3-toastify'
import api from '@/services/api'

export default {
    name: 'AppProfile',
    props: {
        data: {
            type: Object,
            default: () => ({}),
        },
    },
    data() {
        return {
            isComprasDropdownVisible: false,
            backendUrl: process.env.VUE_APP_URL_BASE,
            previewUrl: '',
            file: null,
        }
    },
    setup() {
        const { loading, wrap } = useAsyncAction()
        return { loading, wrap }
    },
    created() {
        console.log('data', this.data)
        if (this.data.foto)
            this.previewUrl = this.backendUrl + this.data.foto
        
        else
            this.previewUrl = this.backendUrl + '/media/utilizadores/default.png'
    },
    methods: {
        toggle_profile() {
            const profile = document.querySelector('.profile_fixed')
            profile.classList.toggle('translate-x-full')
            profile.classList.toggle('translate-x-0')
            this.$emit('toggle_profile')
        },
        log_out() {
            this.$emit('log_out')
        },
        onFileChange(event) {
            const file = event.target.files[0]
            if (!file) return

            this.previewUrl = URL.createObjectURL(file)

            this.wrap(async () => {
                const form = new FormData()
                form.append('foto', file)

                const url = `${this.backendUrl}/app/utilizador/editar/${this.data.id}/`

                try {
                    const res = await api.put(url, form, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    })

                    const updated = res.data
                    this.$emit('profile-updated', updated)
                    toast.success('Foto actualizada com sucesso!', {
                        position: toast.POSITION.TOP_RIGHT,
                        autoClose: 1000,
                    })
                    this.previewUrl = this.backendUrl + updated.foto
                } catch (err) {
                    console.error('Erro ao actualizar foto:', err)
                }
            })
        },
        triggerFileSelect() {
            this.$refs.fileInput.click()
        },
    },
    watch: {
        data: {
            handler(newValue) {
                if (newValue.foto)
                    this.previewUrl = this.backendUrl + newValue.foto
                else
                    this.previewUrl = this.backendUrl + '/media/utilizadores/default.png'
            },
            deep: true,
        },
    },
}
</script>


<style>


</style>


