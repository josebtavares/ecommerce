<template>
  <!-- Backoffice → Serviços → Serviços: o catálogo (nome, duração, preço, quem faz, imagens) -->
  <div class="space-y-4" data-teste="catalogo">
    <div class="flex flex-wrap items-center gap-3">
      <p class="text-sm text-zinc-400 flex-1 min-w-[200px]">
        {{ servicos.length ? `${servicos.filter(s => s.ativo).length} serviço(s) activo(s)` : 'Ainda não tens serviços.' }}
      </p>
      <button v-if="podeGerir" type="button" @click="abrir(null)"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold">+ Novo serviço</button>
    </div>

    <div v-if="carregando" class="h-24 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <div v-else class="grid sm:grid-cols-2 gap-3">
      <div v-for="s in servicos" :key="s.id" :data-teste="`servico-${s.id}`"
           :class="['bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex gap-3', !s.ativo && 'opacity-60']">
        <img v-if="s.imagens.length" :src="s.imagens[0].url" alt="" class="w-16 h-16 rounded-xl object-cover flex-shrink-0" />
        <div v-else class="w-16 h-16 rounded-xl bg-zinc-800 flex items-center justify-center flex-shrink-0 text-zinc-600">
          <font-awesome-icon :icon="['fas', 'scissors']" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-zinc-100 truncate">{{ s.nome }}
            <span v-if="!s.ativo" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">inactivo</span>
          </p>
          <p class="text-xs text-zinc-400">{{ duracaoTexto(s.duracao_min) }} · {{ s.preco_texto }}
            <template v-if="s.categoria"> · {{ s.categoria }}</template></p>
          <p class="text-[11px] text-zinc-500 mt-1 truncate">
            {{ s.profissionais.length ? nomesProf(s.profissionais) : 'Sem profissionais — ninguém o pode fazer' }}
          </p>
        </div>
        <button v-if="podeGerir" type="button" @click="abrir(s)" :aria-label="`Editar ${s.nome}`"
          class="self-start px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Editar</button>
      </div>
    </div>

    <!-- formulário -->
    <div v-if="form" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="form = null">
      <form @submit.prevent="guardar" role="dialog" :aria-label="form.id ? 'Editar serviço' : 'Novo serviço'"
            class="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-2xl p-5 w-full sm:max-w-lg max-h-[92vh] overflow-y-auto space-y-4">
        <h3 class="text-base font-bold text-zinc-100">{{ form.id ? 'Editar serviço' : 'Novo serviço' }}</h3>
        <label class="block"><span class="text-xs text-zinc-500">Nome</span>
          <input v-model="form.nome" maxlength="120" required :class="[CAMPO, 'mt-1']" placeholder="ex.: Corte de cabelo" /></label>
        <div class="grid grid-cols-2 gap-3">
          <label class="block"><span class="text-xs text-zinc-500">Duração</span>
            <select v-model.number="form.duracao_min" :class="[CAMPO, 'mt-1']">
              <option v-for="d in DURACOES" :key="d" :value="d">{{ duracaoTexto(d) }}</option>
            </select></label>
          <label class="block"><span class="text-xs text-zinc-500">Pausa depois</span>
            <select v-model.number="form.intervalo_min" :class="[CAMPO, 'mt-1']">
              <option v-for="d in [0, 5, 10, 15, 20, 30, 45, 60]" :key="d" :value="d">{{ d ? d + ' min' : 'Nenhuma' }}</option>
            </select></label>
          <label class="block"><span class="text-xs text-zinc-500">Preço (CVE)</span>
            <input v-model="form.preco" type="number" min="0" step="1" required :class="[CAMPO, 'mt-1']" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Tipo de preço</span>
            <select v-model="form.tipo_preco" :class="[CAMPO, 'mt-1']">
              <option value="fixo">Fixo</option>
              <option value="a_partir">A partir de (acerta-se com o cliente)</option>
            </select></label>
        </div>
        <label class="block"><span class="text-xs text-zinc-500">Pagamento</span>
          <select v-model="form.pagamento" :class="[CAMPO, 'mt-1']">
            <option value="ambos">O cliente escolhe: já ou no local</option>
            <option value="antecipado">Só antecipado</option>
            <option value="local">Só no local</option>
          </select></label>
        <label class="block"><span class="text-xs text-zinc-500">Categoria (opcional)</span>
          <input v-model="form.categoria" maxlength="80" :class="[CAMPO, 'mt-1']" placeholder="ex.: Cabelo, Unhas, Tatuagem" /></label>
        <label class="block"><span class="text-xs text-zinc-500">Descrição (opcional)</span>
          <textarea v-model="form.descricao" maxlength="2000" rows="3" :class="[CAMPO, 'mt-1']"></textarea></label>

        <fieldset>
          <legend class="text-xs text-zinc-500 mb-1">Quem faz este serviço</legend>
          <p v-if="!profissionais.length" class="text-xs text-amber-300">Cria primeiro os profissionais.</p>
          <div class="flex flex-wrap gap-2">
            <label v-for="p in profissionais.filter(p => p.ativo)" :key="p.id"
              :class="['px-3 py-1.5 rounded-lg border text-xs cursor-pointer select-none',
                       form.profissionais.includes(p.id) ? 'border-red-500 bg-red-500/10 text-zinc-100' : 'border-zinc-700 text-zinc-400']">
              <input type="checkbox" :value="p.id" v-model="form.profissionais" class="sr-only" />{{ p.nome }}
            </label>
          </div>
        </fieldset>

        <div v-if="form.id">
          <p class="text-xs text-zinc-500 mb-1">Imagens ({{ form.imagens.length }}/6)</p>
          <div class="flex flex-wrap gap-2">
            <div v-for="i in form.imagens" :key="i.id" class="relative">
              <img :src="i.url" alt="" class="w-16 h-16 rounded-lg object-cover" />
              <button type="button" @click="apagarImagem(i)" aria-label="Tirar imagem"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-zinc-950 border border-zinc-700 text-zinc-300 text-[10px]">✕</button>
            </div>
            <label v-if="form.imagens.length < 6"
              class="w-16 h-16 rounded-lg border border-dashed border-zinc-700 flex items-center justify-center text-zinc-500 text-xl cursor-pointer hover:border-zinc-500">
              +<input type="file" accept="image/*" class="sr-only" @change="enviarImagem" aria-label="Adicionar imagem" />
            </label>
          </div>
        </div>
        <p v-else class="text-[11px] text-zinc-500">As imagens adicionam-se depois de criar o serviço.</p>

        <label v-if="form.id" class="flex items-center gap-2 text-sm text-zinc-300">
          <input type="checkbox" v-model="form.ativo" class="accent-red-600" /> Activo (os clientes podem marcar)</label>

        <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
        <div class="flex flex-wrap gap-2 pt-1">
          <button type="submit" :disabled="aGuardar"
            class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
            {{ form.id ? 'Guardar' : 'Criar serviço' }}</button>
          <button type="button" @click="form = null" class="px-4 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm">Cancelar</button>
          <button v-if="form.id" type="button" @click="apagar" :disabled="aGuardar"
            class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-red-400 hover:text-red-300 text-sm">Apagar</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { CAMPO, duracaoTexto } from '@/utils/servicos'

const DURACOES = [5, 10, 15, 20, 30, 45, 60, 75, 90, 120, 150, 180, 240, 300, 360, 480, 600, 720]

export default {
  name: 'CatalogoServicos',
  props: {
    lojaId: { type: [String, Number], required: true },
    profissionais: { type: Array, default: () => [] },
    podeGerir: { type: Boolean, default: false },
  },
  emits: ['alterado'],
  data () {
    return { servicos: [], carregando: true, form: null, erro: '', aGuardar: false, CAMPO, DURACOES }
  },
  created () { this.carregar() },
  methods: {
    duracaoTexto,
    base () { return `/app/loja/${this.lojaId}/servicos/catalogo/` },
    nomesProf (ids) { return ids.map(id => this.profissionais.find(p => p.id === id)?.nome).filter(Boolean).join(', ') },
    async carregar () {
      try { this.servicos = (await api.get(this.base())).data } finally { this.carregando = false }
    },
    abrir (s) {
      this.erro = ''
      this.form = s
        ? { ...s, preco: Number(s.preco), profissionais: [...s.profissionais], imagens: [...s.imagens],
            duracao_min: DURACOES.includes(s.duracao_min) ? s.duracao_min : s.duracao_min }
        : { id: null, nome: '', duracao_min: 30, intervalo_min: 0, preco: '', tipo_preco: 'fixo', pagamento: 'ambos',
            categoria: '', descricao: '', ativo: true, imagens: [],
            profissionais: this.profissionais.filter(p => p.ativo).map(p => p.id) }
      if (s && !DURACOES.includes(s.duracao_min)) this.DURACOES = [...DURACOES, s.duracao_min].sort((a, b) => a - b)
    },
    async guardar () {
      this.erro = ''; this.aGuardar = true
      const f = this.form
      const corpo = { nome: f.nome, duracao_min: f.duracao_min, intervalo_min: f.intervalo_min, preco: String(f.preco),
                      tipo_preco: f.tipo_preco, pagamento: f.pagamento, categoria: f.categoria, descricao: f.descricao,
                      profissionais: f.profissionais }
      if (f.id) corpo.ativo = f.ativo
      try {
        if (f.id) await api.patch(`${this.base()}${f.id}/`, corpo)
        else await api.post(this.base(), corpo)
        this.form = null
        await this.carregar()
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false }
    },
    async apagar () {
      if (!confirm(`Apagar "${this.form.nome}"?\n\nSe já tiver marcações, fica só inactivo (o histórico mantém-se).`)) return
      this.aGuardar = true
      try {
        const { data } = await api.delete(`${this.base()}${this.form.id}/`)
        if (data.desativado) alert(data.detail)
        this.form = null
        await this.carregar()
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível apagar.'
      } finally { this.aGuardar = false }
    },
    async enviarImagem (ev) {
      const f = ev.target.files?.[0]
      ev.target.value = ''
      if (!f) return
      const fd = new FormData()
      fd.append('ficheiro', f)
      this.erro = ''
      try {
        const { data } = await api.post(`${this.base()}${this.form.id}/imagens/`, fd)
        this.form.imagens = data.imagens
        await this.carregar()
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível enviar a imagem.' }
    },
    async apagarImagem (i) {
      try {
        const { data } = await api.delete(`/app/loja/${this.lojaId}/servicos/imagens/${i.id}/`)
        this.form.imagens = data.imagens
        await this.carregar()
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível tirar a imagem.' }
    },
  },
}
</script>
