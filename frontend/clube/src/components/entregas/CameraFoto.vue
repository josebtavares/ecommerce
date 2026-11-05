<!-- CameraFoto.vue — câmara dentro do site (getUserMedia, câmara de trás). Não sai para a app da câmara: no Android o
     browser às vezes descartava a página enquanto ela estava aberta e, ao voltar, a foto e o modal tinham-se perdido.
     Emite 'foto' (Blob JPEG), 'fechar', ou 'falhou' (sem câmara / sem permissão → quem usa abre a app da câmara). -->
<template>
  <div class="fixed inset-0 z-[70] bg-black flex flex-col" role="dialog" aria-modal="true" aria-label="Câmara" data-teste="camera">
    <div class="flex-1 relative overflow-hidden">
      <video ref="video" autoplay playsinline muted class="absolute inset-0 w-full h-full object-cover"></video>
      <p v-if="!pronta" class="absolute inset-0 flex items-center justify-center text-sm text-zinc-300">A abrir a câmara…</p>
    </div>
    <div class="flex items-center justify-between gap-4 px-6 py-5 bg-black">
      <button type="button" @click="fechar" class="px-4 py-2 rounded-xl border border-zinc-700 text-sm text-zinc-300">Cancelar</button>
      <button type="button" @click="capturar" :disabled="!pronta" aria-label="Tirar foto" data-teste="camera-capturar"
        class="w-16 h-16 rounded-full bg-white border-4 border-zinc-400 disabled:opacity-40"></button>
      <span class="w-[5.5rem]"></span>
    </div>
  </div>
</template>

<script>
const LADO_MAX = 1600

export function camaraNoSite () {
  return !!(window.isSecureContext && navigator.mediaDevices?.getUserMedia)
}

export default {
  name: 'CameraFoto',
  emits: ['foto', 'fechar', 'falhou'],
  data () { return { pronta: false } },
  async mounted () {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false,
      })
      if (this.parado) { this.parar(); return }
      const v = this.$refs.video
      v.srcObject = this.stream
      await v.play().catch(() => {})
      this.pronta = true
    } catch (e) {
      console.warn('câmara', e?.name)
      this.$emit('falhou', e?.name || 'erro')
    }
  },
  beforeUnmount () { this.parado = true; this.parar() },
  methods: {
    parar () { this.stream?.getTracks().forEach(t => t.stop()); this.stream = null },
    fechar () { this.parar(); this.$emit('fechar') },
    capturar () {
      const v = this.$refs.video
      if (!v?.videoWidth) return
      const k = Math.min(1, LADO_MAX / Math.max(v.videoWidth, v.videoHeight))
      const c = document.createElement('canvas')
      c.width = Math.round(v.videoWidth * k); c.height = Math.round(v.videoHeight * k)
      c.getContext('2d').drawImage(v, 0, 0, c.width, c.height)
      c.toBlob(b => { this.parar(); if (b) this.$emit('foto', b); else this.$emit('falhou', 'captura') }, 'image/jpeg', 0.85)
    },
  },
}
</script>
