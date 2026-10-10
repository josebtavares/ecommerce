<!-- TemplatePreviewFrame.vue — mostra a loja real num iframe com viewport simulado
     (desktop 1440px / mobile 390px) e escala-o para caber no contentor.
     O iframe tem o seu próprio viewport, por isso vh, position:fixed e media queries
     comportam-se exactamente como na loja publicada. -->
<template>
  <div ref="box" class="tpf-box">
    <div
      class="tpf-device"
      :class="{ 'tpf-device--mobile': device === 'mobile' }"
      :style="deviceStyle"
    >
      <iframe
        ref="frame"
        :key="src"
        :src="src"
        class="tpf-iframe"
        :style="{ width: vw + 'px', height: vh + 'px', transform: `scale(${scale})` }"
        title="Pré-visualização do template"
        @load="loading = false"
      ></iframe>

      <div v-if="loading" class="tpf-loading">
        <svg class="animate-spin h-7 w-7" fill="none" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
          <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" class="opacity-75"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<script>
const DEVICES = {
  desktop: { w: 1440, h: 900 },
  mobile:  { w: 390,  h: 844 },
}

export default {
  name: 'TemplatePreviewFrame',

  props: {
    src:    { type: String, required: true },
    device: { type: String, default: 'desktop' },
    // opcional: { corPrimaria, corSecundaria, darkMode } aplicado ao vivo, sem recarregar
    tema:   { type: Object, default: null },
  },

  data () {
    return { boxW: 0, boxH: 0, loading: true }
  },

  computed: {
    vw () { return DEVICES[this.device]?.w || DEVICES.desktop.w },
    vh () { return DEVICES[this.device]?.h || DEVICES.desktop.h },
    scale () {
      if (!this.boxW || !this.boxH) return 0.5
      return Math.min(this.boxW / this.vw, this.boxH / this.vh, 1)
    },
    deviceStyle () {
      return { width: this.vw * this.scale + 'px', height: this.vh * this.scale + 'px' }
    },
  },

  watch: {
    src ()    { this.loading = true },
    device () { this.loading = true },
    tema: {
      deep: true,
      handler () { this.enviarTema() },
    },
  },

  mounted () {
    this.ro = new ResizeObserver(([entry]) => {
      this.boxW = entry.contentRect.width
      this.boxH = entry.contentRect.height
    })
    this.ro.observe(this.$refs.box)
    window.addEventListener('message', this.onMessage)
  },

  beforeUnmount () {
    this.ro?.disconnect()
    window.removeEventListener('message', this.onMessage)
  },

  methods: {
    enviarTema () {
      const win = this.$refs.frame?.contentWindow
      if (!this.tema || !win) return
      win.postMessage({ type: 'tema-preview', ...this.tema }, window.location.origin)
    },

    // a loja dentro do iframe avisa quando o template está montado
    onMessage (e) {
      if (e.origin !== window.location.origin || e.data?.type !== 'preview-pronto') return
      if (e.source !== this.$refs.frame?.contentWindow) return
      this.enviarTema()
    },
  },
}
</script>

<style scoped>
.tpf-box {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.tpf-device {
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  background: #0a0a0b;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.08), 0 20px 60px rgba(0,0,0,0.5);
  transition: width .3s ease, height .3s ease;
}
.tpf-device--mobile {
  border-radius: 22px;
  box-shadow: 0 0 0 6px #18181b, 0 0 0 7px rgba(255,255,255,0.1), 0 20px 60px rgba(0,0,0,0.5);
}
.tpf-iframe {
  position: absolute;
  top: 0;
  left: 0;
  border: 0;
  transform-origin: 0 0;
  background: #0a0a0b;
}
.tpf-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0a0a0b;
  color: #71717a;
}
</style>
