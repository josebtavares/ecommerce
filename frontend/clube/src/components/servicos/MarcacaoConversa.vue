<template>
  <!-- Conversa de uma marcação (cliente ↔ loja/profissional): mensagens, fotos e propostas de preço -->
  <section class="rounded-2xl border p-4 space-y-3" :class="cartao" data-teste="conversa">
    <div class="flex items-center gap-2">
      <p class="text-xs font-bold uppercase tracking-wider flex-1" :class="suave">Conversa {{ papel === 'cliente' ? 'com a loja' : 'com o cliente' }}</p>
      <button type="button" @click="carregar" aria-label="Actualizar" class="text-xs" :class="suave">
        <font-awesome-icon :icon="['fas', 'rotate-right']" /></button>
    </div>

    <p v-if="!podeConversar" class="text-xs" :class="suave">Marcação feita pela loja sem conta de cliente — não há conversa.</p>
    <template v-else>
      <div ref="lista" class="space-y-2 max-h-96 overflow-y-auto pr-1">
        <p v-if="!mensagens.length" class="text-xs text-center py-4" :class="suave">
          {{ papel === 'cliente' ? 'Fala aqui com a loja sobre o serviço: dúvidas, a tua ideia, fotos de referência…' : 'Ainda sem mensagens.' }}</p>
        <div v-for="m in mensagens" :key="m.id" :class="m.papel === 'sistema' ? 'flex justify-center' : (m.papel === papel ? 'flex justify-end' : 'flex justify-start')">
          <!-- sistema (propostas, aceites…) -->
          <div v-if="m.papel === 'sistema'" class="max-w-[90%] rounded-xl px-3 py-2 text-xs text-center"
               :class="isDark ? 'bg-zinc-800/70 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
            <p>{{ m.texto }}</p>
            <div v-if="m.proposta_id && propostaPendente(m.proposta_id) && papel === 'cliente'" class="flex gap-2 justify-center mt-2" data-teste="proposta-pendente">
              <button type="button" @click="$emit('responder', { id: m.proposta_id, aceitar: true })" :disabled="ocupado"
                class="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white font-bold">Aceitar</button>
              <button type="button" @click="$emit('responder', { id: m.proposta_id, aceitar: false })" :disabled="ocupado"
                class="px-3 py-1.5 rounded-lg border" :class="isDark ? 'border-zinc-600 text-zinc-200' : 'border-gray-300 text-zinc-700'">Recusar</button>
            </div>
            <p v-else-if="m.proposta_id && propostaPendente(m.proposta_id)" class="mt-1 font-semibold text-amber-400">À espera do cliente</p>
          </div>
          <div v-else class="max-w-[85%] rounded-2xl px-3 py-2 text-sm"
               :class="m.papel === papel ? 'bg-red-600 text-white rounded-br-md' : (isDark ? 'bg-zinc-800 text-zinc-100 rounded-bl-md' : 'bg-gray-100 text-zinc-900 rounded-bl-md')">
            <p class="text-[10px] font-semibold opacity-70 mb-0.5">{{ m.autor }}</p>
            <p v-if="m.texto" class="whitespace-pre-line break-words">{{ m.texto }}</p>
            <div v-if="m.fotos.length" class="flex flex-wrap gap-1.5 mt-1.5">
              <a v-for="f in m.fotos" :key="f.id" :href="f.url" target="_blank" rel="noopener">
                <img :src="f.url" alt="Foto" class="w-24 h-24 rounded-lg object-cover" loading="lazy" />
              </a>
            </div>
            <p class="text-[10px] opacity-60 mt-1 text-right">{{ quando(m.criada_em) }}</p>
          </div>
        </div>
      </div>

      <form @submit.prevent="enviar" class="space-y-2">
        <div v-if="fotos.length" class="flex flex-wrap gap-1.5">
          <span v-for="(f, i) in fotos" :key="i" class="text-[11px] px-2 py-1 rounded-lg" :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
            {{ f.name }} <button type="button" @click="fotos.splice(i, 1)" aria-label="Tirar foto" class="ml-1">✕</button></span>
        </div>
        <div class="flex gap-2 items-end">
          <label class="h-10 w-10 flex-shrink-0 rounded-xl border flex items-center justify-center cursor-pointer"
                 :class="isDark ? 'border-zinc-700 text-zinc-400 hover:text-zinc-200' : 'border-gray-300 text-zinc-500'" aria-label="Juntar foto">
            <font-awesome-icon :icon="['fas', 'camera']" />
            <input type="file" accept="image/*" multiple class="sr-only" @change="escolherFotos" />
          </label>
          <textarea v-model="texto" rows="1" maxlength="2000" placeholder="Escreve uma mensagem…" aria-label="Mensagem"
            @keydown.enter.exact.prevent="enviar"
            class="flex-1 px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
            :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea>
          <button type="submit" :disabled="aEnviar || (!texto.trim() && !fotos.length)"
            class="h-10 px-4 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Enviar</button>
        </div>
        <p v-if="erro" class="text-xs text-red-400" role="alert">{{ erro }}</p>
      </form>
    </template>
  </section>
</template>

<script>
import api from '@/services/api'
import { diaDe, hora, rotuloDia, hojeCV } from '@/utils/servicos'

export default {
  name: 'MarcacaoConversa',
  props: {
    marcacaoId: { type: Number, required: true },
    isDark: { type: Boolean, default: true },
    ocupado: { type: Boolean, default: false },
    versao: { type: Number, default: 0 },          // o pai muda isto quando algo mudou (proposta nova…)
  },
  emits: ['responder', 'mudou'],
  data () { return { papel: '', podeConversar: true, mensagens: [], propostas: [], texto: '', fotos: [], aEnviar: false, erro: '' } },
  computed: {
    cartao () { return this.isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200' },
    suave () { return 'text-zinc-500' },
  },
  watch: { versao () { this.carregar() }, marcacaoId () { this.carregar() } },
  created () { this.carregar() },
  mounted () { this.relogio = setInterval(() => { if (document.visibilityState === 'visible') this.carregar(true) }, 20000) },
  beforeUnmount () { clearInterval(this.relogio) },
  methods: {
    quando (iso) { return (diaDe(iso) === hojeCV() ? '' : rotuloDia(diaDe(iso)) + ' ') + hora(iso) },
    propostaPendente (id) { return this.propostas.some(p => p.id === id && p.estado === 'pendente') },
    aplicar (data) {
      const novas = data.mensagens.length !== this.mensagens.length
      this.papel = data.papel
      this.podeConversar = data.pode_conversar
      this.mensagens = data.mensagens
      this.propostas = data.propostas
      if (novas) this.$nextTick(() => { const l = this.$refs.lista; if (l) l.scrollTop = l.scrollHeight })
      return novas
    },
    async carregar (silencioso = false) {
      try {
        const { data } = await api.get(`/app/marcacoes/${this.marcacaoId}/mensagens/`)
        if (this.aplicar(data) && silencioso) this.$emit('mudou')
      } catch (e) { if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar a conversa.' }
    },
    escolherFotos (ev) {
      this.fotos.push(...Array.from(ev.target.files || []).slice(0, 10 - this.fotos.length))
      ev.target.value = ''
    },
    async enviar () {
      if (!this.texto.trim() && !this.fotos.length) return
      this.erro = ''; this.aEnviar = true
      try {
        let corpo = { texto: this.texto }
        if (this.fotos.length) {
          corpo = new FormData()
          corpo.append('texto', this.texto)
          this.fotos.forEach(f => corpo.append('fotos', f))
        }
        const { data } = await api.post(`/app/marcacoes/${this.marcacaoId}/mensagens/`, corpo)
        this.texto = ''; this.fotos = []
        this.aplicar(data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível enviar.'
      } finally { this.aEnviar = false }
    },
  },
}
</script>
