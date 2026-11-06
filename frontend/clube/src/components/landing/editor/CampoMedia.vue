<!-- CampoMedia.vue — escolher a imagem ou o vídeo de uma secção da landing page (editor).
     Carrega por POST /app/admin/home/imagens/ (video=1: o mesmo envio e a mesma conversão da home; R2 na produção).
     v-model = id (HomeImagem) ou null; `media` = o que o servidor devolveu (url, tipo, estado do vídeo).
     Vídeo acabado de carregar: vai perguntando o estado até ficar pronto. -->
<template>
  <div class="space-y-2" :data-teste="'campo-media-' + nome">
    <div class="relative rounded-xl overflow-hidden border border-zinc-700 bg-zinc-950 aspect-video flex items-center justify-center">
      <template v-if="atual">
        <video v-if="atual.tipo === 'video' && atual.estado === 'pronto' && atual.url" :src="atual.url" :poster="atual.poster || undefined"
               muted loop autoplay playsinline class="w-full h-full object-cover"></video>
        <img v-else-if="atual.tipo === 'video' && atual.poster" :src="atual.poster" alt="" class="w-full h-full object-cover" />
        <img v-else-if="atual.tipo !== 'video'" :src="atual.url" alt="" class="w-full h-full object-cover" data-teste="media-previa" />
        <span v-if="atual.tipo === 'video' && atual.estado !== 'pronto'"
              class="absolute inset-x-2 bottom-2 rounded-lg px-3 py-1.5 text-xs font-semibold"
              :class="atual.estado === 'erro' ? 'bg-red-600 text-white' : 'bg-amber-500 text-black'" data-teste="media-estado">
          {{ atual.estado === 'erro' ? 'Não foi possível converter o vídeo — carrega outro.' : 'Vídeo a ser otimizado… podes continuar a editar.' }}
        </span>
      </template>
      <span v-else class="text-xs text-zinc-500">{{ vazio }}</span>
      <span v-if="aCarregar" class="absolute inset-0 bg-black/70 flex items-center justify-center text-sm text-zinc-200">A carregar…</span>
    </div>
    <div class="flex flex-wrap gap-2">
      <label class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 cursor-pointer">
        <font-awesome-icon :icon="['fas', 'upload']" class="mr-1" />{{ atual ? 'Trocar' : 'Carregar' }}
        <input type="file" class="hidden" :accept="aceita" @change="carregar" :data-teste="'input-media-' + nome" />
      </label>
      <button v-if="atual" type="button" @click="$emit('update:modelValue', null)" :data-teste="'remover-media-' + nome"
              class="px-3 py-1.5 rounded-lg border border-zinc-700 text-xs font-semibold text-zinc-300 hover:bg-zinc-800">Remover</button>
    </div>
    <p class="text-[11px] text-zinc-500">{{ ajuda }}</p>
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import api from '@/services/api'

const VIDEO_EXT = /\.(mp4|webm|mov)$/i

export default {
  name: 'CampoMedia',
  props: {
    modelValue: { type: Number, default: null },
    media: { type: Object, default: null },          // do servidor (rascunho)
    nome: { type: String, default: 'media' },
    video: { type: Boolean, default: true },
    limites: { type: Object, default: () => ({ imagem_max_mb: 20, video_max_mb: 25, video_max_s: 30 }) },
    vazio: { type: String, default: 'Sem imagem' },
  },
  emits: ['update:modelValue', 'media'],
  data () { return { novo: null, aCarregar: false } },
  computed: {
    atual () {
      if (!this.modelValue) return null
      if (this.novo && this.novo.id === this.modelValue) return this.novo
      return this.media && this.media.id === this.modelValue ? this.media : null
    },
    aceita () { return this.video ? 'image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime' : 'image/jpeg,image/png,image/webp' },
    ajuda () {
      const l = this.limites
      return this.video ? `Imagem JPG/PNG/WEBP até ${l.imagem_max_mb} MB, ou vídeo MP4/WEBM/MOV até ${l.video_max_s} s e ${l.video_max_mb} MB (sem som).`
                        : `JPG, PNG ou WEBP até ${l.imagem_max_mb} MB.`
    },
  },
  beforeUnmount () { this.fechado = true; clearTimeout(this.timer) },
  methods: {
    async carregar (e) {
      const f = e.target.files?.[0]
      e.target.value = ''
      if (!f) return
      const eVideo = f.type.startsWith('video/') || VIDEO_EXT.test(f.name)
      if (eVideo && !this.video) { toast.error('Aqui só imagens.'); return }
      const max = eVideo ? this.limites.video_max_mb : this.limites.imagem_max_mb
      if (f.size > max * 1024 * 1024) { toast.error(`${eVideo ? 'O vídeo' : 'A imagem'} tem de ter no máximo ${max} MB.`); return }
      this.aCarregar = true
      try {
        const fd = new FormData()
        fd.append('ficheiro', f)
        if (this.video) fd.append('video', '1')
        const { data } = await api.post('/app/admin/home/imagens/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        this.novo = data
        this.$emit('media', data)
        this.$emit('update:modelValue', data.id)
        this.seguir()
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Não foi possível carregar o ficheiro.')
      } finally { this.aCarregar = false }
    },
    seguir () {
      const m = this.novo
      if (!m || m.tipo !== 'video' || m.estado === 'pronto' || m.estado === 'erro' || this.fechado) return
      this.timer = setTimeout(async () => {
        try {
          const { data } = await api.get(`/app/admin/home/imagens/${m.id}/`)
          if (this.novo?.id === m.id) { this.novo = data; this.$emit('media', data) }
        } catch (e) { /* tenta outra vez */ }
        this.seguir()
      }, 3000)
    },
  },
}
</script>
