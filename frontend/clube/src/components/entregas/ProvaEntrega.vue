<!-- ProvaEntrega.vue — prova de entrega OPCIONAL (backend: Views/entregaProvaView.prova_juntar, utils/prova_entrega.py).
     Abre depois de marcar a entrega como feita (já está concluída: isto não a atrasa) ou mais tarde no cartão
     (até 24 h). Foto, assinatura do cliente e nome de quem recebeu — tudo opcional; cada parte grava-se uma vez. -->
<template>
  <div class="fixed inset-0 z-[60] flex items-end sm:items-center justify-center sm:p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('fechar')">
    <div class="bg-zinc-900 sm:rounded-2xl rounded-t-2xl border border-zinc-800 w-full max-w-md p-5 space-y-4 shadow-2xl max-h-[92vh] overflow-y-auto"
         role="dialog" aria-modal="true" data-teste="prova-modal">
      <div>
        <h3 class="text-base font-bold text-zinc-100">Prova de entrega <span class="text-xs font-normal text-zinc-500">(opcional)</span></h3>
        <p class="text-xs text-zinc-400 mt-1">
          Encomenda <strong>#{{ entrega.encomenda }}</strong> já está entregue. Se puderes, junta uma foto ou a assinatura —
          se o cliente não estiver, salta.
        </p>
      </div>

      <!-- Foto -->
      <div v-if="!jaTem.foto">
        <p class="text-xs font-semibold text-zinc-300 mb-1.5">Foto</p>
        <div v-if="fotoUrl" class="relative">
          <img :src="fotoUrl" alt="Foto da entrega" class="w-full max-h-48 object-cover rounded-xl border border-zinc-700" />
          <button type="button" @click="limparFoto" class="absolute top-2 right-2 px-2 py-1 rounded-lg bg-black/70 text-xs text-zinc-200">Trocar</button>
        </div>
        <label v-else class="flex items-center justify-center gap-2 py-3 rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-400 cursor-pointer hover:border-zinc-500">
          <font-awesome-icon :icon="['fas', 'camera']" />Tirar foto
          <input type="file" accept="image/*" capture="environment" class="hidden" data-teste="prova-foto" @change="escolherFoto" />
        </label>
      </div>

      <!-- Assinatura -->
      <div v-if="!jaTem.assinatura">
        <div class="flex items-center justify-between mb-1.5">
          <p class="text-xs font-semibold text-zinc-300">Assinatura do cliente</p>
          <button v-if="assinou" type="button" @click="limparAssinatura" class="text-xs text-zinc-500 hover:text-zinc-300">Limpar</button>
        </div>
        <canvas ref="tela" data-teste="prova-assinatura"
          class="w-full h-36 rounded-xl bg-white touch-none cursor-crosshair"
          @pointerdown="comecar" @pointermove="desenhar" @pointerup="parar" @pointerleave="parar" @pointercancel="parar"></canvas>
        <p v-if="!assinou" class="text-[11px] text-zinc-500 mt-1">O cliente assina com o dedo no quadro.</p>
      </div>

      <!-- Quem recebeu -->
      <div v-if="!jaTem.nome">
        <p class="text-xs font-semibold text-zinc-300 mb-1.5">Quem recebeu</p>
        <input v-model="nome" type="text" maxlength="100" placeholder="Ex.: o próprio, a vizinha Maria…" data-teste="prova-nome"
          class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
      </div>

      <div class="flex gap-3 pt-1">
        <button type="button" @click="$emit('fechar')" data-teste="prova-saltar"
          class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
          {{ temAlgo ? 'Cancelar' : 'Saltar' }}
        </button>
        <button type="button" @click="guardar" :disabled="!temAlgo || aGuardar" data-teste="prova-guardar"
          class="flex-1 py-2.5 rounded-xl bg-green-600 hover:bg-green-500 text-white text-sm font-bold transition disabled:opacity-40">
          {{ aGuardar ? 'A guardar…' : 'Guardar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'

const LADO_MAX = 1600     // reduz a foto no telemóvel antes de enviar (dados móveis)

function reduzir (ficheiro) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(ficheiro)
    const img = new Image()
    img.onload = () => {
      const k = Math.min(1, LADO_MAX / Math.max(img.width, img.height))
      const c = document.createElement('canvas')
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k)
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height)
      URL.revokeObjectURL(url)
      c.toBlob(b => resolve(b || ficheiro), 'image/jpeg', 0.85)
    }
    img.onerror = () => { URL.revokeObjectURL(url); resolve(ficheiro) }
    img.src = url
  })
}

export default {
  name: 'ProvaEntrega',
  props: {
    lojaId:  { type: [String, Number], required: true },
    entrega: { type: Object, required: true },
  },
  emits: ['fechar', 'guardada'],
  data () {
    return { foto: null, fotoUrl: '', nome: '', assinou: false, aDesenhar: false, aGuardar: false }
  },
  computed: {
    jaTem () {
      const p = this.entrega.prova || {}
      return { foto: !!p.foto, assinatura: !!p.assinatura, nome: !!p.recebido_por }
    },
    temAlgo () { return !!(this.foto || this.assinou || this.nome.trim()) },
  },
  mounted () { this.prepararTela() },
  beforeUnmount () { if (this.fotoUrl) URL.revokeObjectURL(this.fotoUrl) },
  methods: {
    prepararTela () {
      const c = this.$refs.tela
      if (!c) return
      const r = c.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      c.width = Math.round(r.width * dpr); c.height = Math.round(r.height * dpr)
      const ctx = c.getContext('2d')
      ctx.scale(dpr, dpr)
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, r.width, r.height)
      ctx.lineWidth = 2.5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = '#111'
      this.ctx = ctx
    },
    ponto (ev) {
      const r = this.$refs.tela.getBoundingClientRect()
      return [ev.clientX - r.left, ev.clientY - r.top]
    },
    comecar (ev) {
      if (!this.ctx) return
      ev.preventDefault()
      this.$refs.tela.setPointerCapture?.(ev.pointerId)
      this.aDesenhar = true
      const [x, y] = this.ponto(ev)
      this.ctx.beginPath(); this.ctx.moveTo(x, y)
      this.tracos = 0
    },
    desenhar (ev) {
      if (!this.aDesenhar) return
      const [x, y] = this.ponto(ev)
      this.ctx.lineTo(x, y); this.ctx.stroke()
      if (++this.tracos > 3) this.assinou = true     // um toque solto não conta como assinatura
    },
    parar () { this.aDesenhar = false },
    limparAssinatura () { this.assinou = false; this.prepararTela() },

    async escolherFoto (ev) {
      const f = ev.target.files?.[0]
      ev.target.value = ''
      if (!f) return
      this.foto = await reduzir(f)
      if (this.fotoUrl) URL.revokeObjectURL(this.fotoUrl)
      this.fotoUrl = URL.createObjectURL(this.foto)
    },
    limparFoto () {
      if (this.fotoUrl) URL.revokeObjectURL(this.fotoUrl)
      this.foto = null; this.fotoUrl = ''
    },

    assinaturaBlob () {
      return new Promise(resolve => this.$refs.tela.toBlob(resolve, 'image/png'))
    },

    async guardar () {
      if (!this.temAlgo) return
      this.aGuardar = true
      try {
        const fd = new FormData()
        if (this.foto) fd.append('foto', this.foto, 'foto.jpg')
        if (this.assinou) fd.append('assinatura', await this.assinaturaBlob(), 'assinatura.png')
        if (this.nome.trim()) fd.append('recebido_por', this.nome.trim())
        const { data } = await api.post(`/app/loja/${this.lojaId}/encomendas/${this.entrega.encomenda}/entrega/prova/`, fd,
          { headers: { 'Content-Type': 'multipart/form-data' } })
        toast.success('Prova de entrega guardada.')
        this.$emit('guardada', data)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível guardar a prova. A entrega já está feita — podes tentar de novo no cartão.')
      } finally { this.aGuardar = false }
    },
  },
}
</script>
