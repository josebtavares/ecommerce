<template>
  <!-- Backoffice → Serviços → Serviços: o catálogo (nome, duração, preço, quem faz, imagens) -->
  <div class="space-y-4" data-teste="catalogo">
    <div class="flex flex-wrap items-center gap-3">
      <p class="text-sm text-zinc-400 flex-1 min-w-[200px]">
        {{ servicos.length ? `${servicos.filter(s => s.ativo).length} serviço(s) activo(s)` : 'Ainda não tens serviços.' }}
      </p>
      <button v-if="podeGerir && simples.length >= 2" type="button" @click="abrir(null, true)" data-teste="novo-pacote"
        class="px-4 py-2 rounded-xl border border-zinc-700 hover:border-zinc-500 text-zinc-200 text-sm font-bold">+ Novo pacote</button>
      <button v-if="podeGerir" type="button" @click="abrir(null)"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold">+ Novo serviço</button>
    </div>

    <div v-if="carregando" class="h-24 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <div v-else class="grid sm:grid-cols-2 gap-3">
      <div v-for="s in servicos" :key="s.id" :data-teste="`servico-${s.id}`"
           :class="['bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex gap-3', !s.ativo && 'opacity-60']">
        <img v-if="s.imagens.length" :src="s.imagens[0].url" alt="" class="w-16 h-16 rounded-xl object-cover flex-shrink-0" />
        <div v-else class="w-16 h-16 rounded-xl bg-zinc-800 flex items-center justify-center flex-shrink-0 text-zinc-600">
          <font-awesome-icon :icon="['fas', s.e_pacote ? 'layer-group' : 'scissors']" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-zinc-100 truncate">{{ s.nome }}
            <span v-if="s.e_pacote" class="ml-1 text-[10px] font-bold uppercase text-red-400">pacote</span>
            <span v-if="!s.ativo" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">inactivo</span>
            <span v-else-if="!s.visivel" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">só em pacotes</span>
          </p>
          <p class="text-xs text-zinc-400">{{ duracaoTexto(s.duracao_min) }} · {{ s.preco_texto }}
            <template v-if="s.categoria"> · {{ s.categoria }}</template></p>
          <p v-if="s.e_pacote" class="text-[11px] text-zinc-400 mt-1 line-clamp-2">Inclui: {{ s.componentes.map(c => c.nome).join(' + ') }}</p>
          <p class="text-[11px] text-zinc-500 mt-1 truncate">
            {{ s.profissionais.length ? nomesProf(s.profissionais) : 'Sem profissionais — ninguém o pode fazer' }}
          </p>
          <p v-if="s.ativo && s.em_falta.length" class="text-[11px] text-amber-300 mt-1" data-teste="pacote-em-falta">
            Indisponível para os clientes: {{ s.em_falta.join(', ') }} {{ s.em_falta.length === 1 ? 'está inactivo' : 'estão inactivos' }}.</p>
        </div>
        <button v-if="podeGerir" type="button" @click="abrir(s)" :aria-label="`Editar ${s.nome}`"
          class="self-start px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Editar</button>
      </div>
    </div>

    <!-- formulário -->
    <div v-if="form" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="form = null">
      <form @submit.prevent="guardar" role="dialog" :aria-label="form.id ? 'Editar serviço' : 'Novo serviço'"
            class="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-2xl p-5 w-full sm:max-w-lg max-h-[92vh] overflow-y-auto space-y-4">
        <h3 class="text-base font-bold text-zinc-100">{{ titulo }}</h3>
        <label class="block"><span class="text-xs text-zinc-500">Nome</span>
          <input v-model="form.nome" maxlength="120" required :class="[CAMPO, 'mt-1']"
                 :placeholder="form.e_pacote ? 'ex.: Mãos e pés, Pacote noiva' : 'ex.: Corte de cabelo'" /></label>

        <fieldset v-if="form.e_pacote" data-teste="pacote-servicos">
          <legend class="text-xs text-zinc-500 mb-1">Serviços do pacote <span class="text-zinc-600">(pela ordem em que se fazem)</span></legend>
          <div class="flex flex-wrap gap-2">
            <button v-for="c in simples" :key="c.id" type="button" @click="alternarComponente(c.id)"
              :aria-pressed="form.componentes.includes(c.id)"
              :class="['px-3 py-1.5 rounded-lg border text-xs flex items-center gap-1.5',
                       form.componentes.includes(c.id) ? 'border-red-500 bg-red-500/10 text-zinc-100' : 'border-zinc-700 text-zinc-400',
                       !c.ativo && 'opacity-50']">
              <span v-if="form.componentes.includes(c.id)" class="w-4 h-4 rounded-full bg-red-600 text-white text-[10px] font-bold flex items-center justify-center">
                {{ form.componentes.indexOf(c.id) + 1 }}</span>
              {{ c.nome }}<span v-if="!c.ativo" class="text-[10px]">(inactivo)</span>
            </button>
          </div>
          <p class="text-[11px] text-zinc-500 mt-1.5">
            <template v-if="escolhidos.length">Separados: {{ duracaoTexto(soma.duracao) }} · {{ formatarDinheiro(soma.preco) }}</template>
            <template v-else>Escolhe 2 ou mais serviços.</template></p>
        </fieldset>

        <div class="grid grid-cols-2 gap-3">
          <div class="block">
            <span class="text-xs text-zinc-500">Duração</span>
            <select v-if="!(form.e_pacote && form.duracao_auto)" v-model.number="form.duracao_min" :class="[CAMPO, 'mt-1']" aria-label="Duração">
              <option v-for="d in DURACOES" :key="d" :value="d">{{ duracaoTexto(d) }}</option>
            </select>
            <p v-else :class="[CAMPO, 'mt-1 text-zinc-400']">{{ duracaoTexto(soma.duracao) }}</p>
            <label v-if="form.e_pacote" class="flex items-center gap-1.5 text-[11px] text-zinc-400 mt-1">
              <input type="checkbox" v-model="form.duracao_auto" class="accent-red-600" /> A soma dos serviços</label>
          </div>
          <label class="block"><span class="text-xs text-zinc-500">Pausa depois</span>
            <select v-model.number="form.intervalo_min" :class="[CAMPO, 'mt-1']">
              <option v-for="d in [0, 5, 10, 15, 20, 30, 45, 60]" :key="d" :value="d">{{ d ? d + ' min' : 'Nenhuma' }}</option>
            </select></label>
          <div class="block">
            <span class="text-xs text-zinc-500">Preço (CVE)</span>
            <input v-if="!(form.e_pacote && form.preco_auto)" v-model="form.preco" type="number" min="0" step="1" required
                   :class="[CAMPO, 'mt-1']" aria-label="Preço (CVE)" />
            <p v-else :class="[CAMPO, 'mt-1 text-zinc-400']">{{ formatarDinheiro(soma.preco) }}</p>
            <label v-if="form.e_pacote" class="flex items-center gap-1.5 text-[11px] text-zinc-400 mt-1">
              <input type="checkbox" v-model="form.preco_auto" class="accent-red-600" /> A soma dos serviços</label>
            <p v-if="poupanca > 0" class="text-[11px] text-emerald-400 mt-1">O cliente poupa {{ formatarDinheiro(poupanca) }}</p>
          </div>
          <label class="block"><span class="text-xs text-zinc-500">Tipo de preço</span>
            <select v-model="form.tipo_preco" :disabled="form.e_pacote && form.preco_auto" :class="[CAMPO, 'mt-1 disabled:opacity-60']">
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
          <legend class="text-xs text-zinc-500 mb-1">{{ form.e_pacote ? 'Quem faz o pacote (todos os serviços, seguidos)' : 'Quem faz este serviço' }}</legend>
          <p v-if="form.e_pacote && escolhidos.length" class="text-[11px] mb-1.5" :class="foraDosComuns.length ? 'text-amber-300' : 'text-zinc-500'">
            <template v-if="comuns.length">Fazem todos estes serviços: {{ nomesProf(comuns) }}.</template>
            <template v-else>Ninguém faz todos estes serviços — escolhe quem vai fazer o pacote.</template>
            <template v-if="foraDosComuns.length"> {{ nomesProf(foraDosComuns) }} não {{ foraDosComuns.length === 1 ? 'faz' : 'fazem' }} todos.</template>
          </p>
          <p v-if="!profissionais.length" class="text-xs text-amber-300">Cria primeiro os profissionais.</p>
          <div class="flex flex-wrap gap-2">
            <label v-for="p in profissionais.filter(p => p.ativo)" :key="p.id"
              :class="['px-3 py-1.5 rounded-lg border text-xs cursor-pointer select-none',
                       form.profissionais.includes(p.id) ? 'border-red-500 bg-red-500/10 text-zinc-100' : 'border-zinc-700 text-zinc-400']">
              <input type="checkbox" :value="p.id" v-model="form.profissionais" @change="form.profsTocados = true" class="sr-only" />{{ p.nome }}
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
        <div v-else>
          <p class="text-xs text-zinc-500 mb-1">Imagens ({{ novas.length }}/6)</p>
          <div class="flex flex-wrap gap-2">
            <div v-for="(n, i) in novas" :key="n.url" class="relative">
              <img :src="n.url" alt="" class="w-16 h-16 rounded-lg object-cover" />
              <button type="button" @click="tirarNova(i)" aria-label="Tirar imagem"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-zinc-950 border border-zinc-700 text-zinc-300 text-[10px]">✕</button>
            </div>
            <label v-if="novas.length < 6"
              class="w-16 h-16 rounded-lg border border-dashed border-zinc-700 flex items-center justify-center text-zinc-500 text-xl cursor-pointer hover:border-zinc-500">
              +<input type="file" accept="image/*" multiple class="sr-only" @change="escolherNovas" aria-label="Adicionar imagens" />
            </label>
          </div>
        </div>

        <label v-if="form.id" class="flex items-center gap-2 text-sm text-zinc-300">
          <input type="checkbox" v-model="form.ativo" class="accent-red-600" /> Activo (os clientes podem marcar)</label>
        <div v-if="!form.e_pacote">
          <label class="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" v-model="form.visivel" class="accent-red-600" /> Mostrar aos clientes sozinho</label>
          <p class="text-[11px] text-zinc-500 ml-6">Desliga se este serviço só se vende dentro de pacotes.</p>
          <p v-if="form.em_pacotes && form.em_pacotes.length" class="text-[11px] text-zinc-400 ml-6 mt-1">
            Está em: {{ form.em_pacotes.map(p => p.nome).join(', ') }}.</p>
        </div>

        <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
        <div class="flex flex-wrap gap-2 pt-1">
          <button type="submit" :disabled="aGuardar"
            class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
            {{ form.id ? 'Guardar' : form.e_pacote ? 'Criar pacote' : 'Criar serviço' }}</button>
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
import { formatarDinheiro } from '@/utils/dinheiro'
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
    return { servicos: [], carregando: true, form: null, erro: '', aGuardar: false, novas: [], CAMPO, DURACOES }
  },
  computed: {
    titulo () {
      const o = this.form.e_pacote ? 'pacote' : 'serviço'
      return this.form.id ? `Editar ${o}` : `Novo ${o}`
    },
    // os serviços que podem entrar num pacote (não pacotes, não o próprio)
    simples () { return this.servicos.filter(s => !s.e_pacote) },
    escolhidos () { return this.form ? this.form.componentes.map(id => this.simples.find(s => s.id === id)).filter(Boolean) : [] },
    soma () {
      return { preco: this.escolhidos.reduce((t, s) => t + Number(s.preco), 0),
               duracao: Math.min(Math.max(this.escolhidos.reduce((t, s) => t + s.duracao_min, 0), 5), 720) }
    },
    poupanca () {
      if (!this.form?.e_pacote || this.form.preco_auto || this.form.preco === '') return 0
      return this.soma.preco - Number(this.form.preco)
    },
    // profissionais activos que fazem todos os serviços escolhidos
    comuns () {
      const ativos = this.profissionais.filter(p => p.ativo).map(p => p.id)
      return ativos.filter(id => this.escolhidos.every(s => s.profissionais.includes(id)))
    },
    foraDosComuns () { return this.form ? this.form.profissionais.filter(id => !this.comuns.includes(id)) : [] },
  },
  created () { this.carregar() },
  methods: {
    duracaoTexto, formatarDinheiro,
    alternarComponente (id) {
      const lista = this.form.componentes
      const i = lista.indexOf(id)
      if (i >= 0) lista.splice(i, 1)
      else lista.push(id)
      // num pacote novo, quem faz segue os que fazem tudo (até o dono mexer)
      if (!this.form.id && !this.form.profsTocados) this.form.profissionais = [...this.comuns]
    },
    base () { return `/app/loja/${this.lojaId}/servicos/catalogo/` },
    nomesProf (ids) { return ids.map(id => this.profissionais.find(p => p.id === id)?.nome).filter(Boolean).join(', ') },
    async carregar () {
      try { this.servicos = (await api.get(this.base())).data } finally { this.carregando = false }
    },
    escolherNovas (ev) {
      Array.from(ev.target.files || []).slice(0, 6 - this.novas.length)
        .forEach(f => this.novas.push({ ficheiro: f, url: URL.createObjectURL(f) }))
      ev.target.value = ''
    },
    tirarNova (i) { URL.revokeObjectURL(this.novas[i].url); this.novas.splice(i, 1) },
    abrir (s, pacote = false) {
      this.novas.forEach(n => URL.revokeObjectURL(n.url))
      this.novas = []
      this.erro = ''
      this.form = s
        ? { ...s, preco: Number(s.preco), profissionais: [...s.profissionais], imagens: [...s.imagens],
            componentes: s.componentes.map(c => c.id), profsTocados: true }
        : { id: null, nome: '', duracao_min: 30, intervalo_min: 0, preco: '', tipo_preco: 'fixo', pagamento: 'ambos',
            categoria: '', descricao: '', ativo: true, visivel: true, imagens: [],
            e_pacote: pacote, preco_auto: pacote, duracao_auto: pacote, componentes: [], profsTocados: false,
            profissionais: pacote ? [] : this.profissionais.filter(p => p.ativo).map(p => p.id) }
      if (s && !DURACOES.includes(s.duracao_min)) this.DURACOES = [...DURACOES, s.duracao_min].sort((a, b) => a - b)
    },
    async guardar () {
      this.erro = ''; this.aGuardar = true
      const f = this.form
      const corpo = { nome: f.nome, intervalo_min: f.intervalo_min, pagamento: f.pagamento, categoria: f.categoria,
                      descricao: f.descricao, profissionais: f.profissionais, visivel: f.visivel }
      if (!(f.e_pacote && f.duracao_auto)) corpo.duracao_min = f.duracao_min
      if (!(f.e_pacote && f.preco_auto)) Object.assign(corpo, { preco: String(f.preco), tipo_preco: f.tipo_preco })
      if (f.e_pacote) {
        if (f.componentes.length < 2) { this.erro = 'Escolhe pelo menos 2 serviços para o pacote.'; this.aGuardar = false; return }
        Object.assign(corpo, { e_pacote: true, componentes: f.componentes, preco_auto: f.preco_auto, duracao_auto: f.duracao_auto })
      }
      if (f.id) corpo.ativo = f.ativo
      try {
        if (f.id) {
          try { await api.patch(`${this.base()}${f.id}/`, corpo) } catch (e) {
            // desactivar um serviço que está em pacotes: confirma
            if (e.response?.status !== 409 || !confirm(`${e.response.data.detail}\n\nDesactivar mesmo assim?`)) throw e
            await api.patch(`${this.base()}${f.id}/?confirmar=1`, corpo)
          }
        } else {
          const { data } = await api.post(this.base(), corpo)
          // as imagens escolhidas ao criar vão logo a seguir
          for (const n of this.novas) {
            const fd = new FormData()
            fd.append('ficheiro', n.ficheiro)
            try { await api.post(`${this.base()}${data.id}/imagens/`, fd) } catch (e) {
              this.erro = `Serviço criado, mas uma imagem falhou: ${e.response?.data?.detail || 'erro'}`
            }
          }
          this.novas = []
          if (this.erro) { await this.carregar(); this.$emit('alterado'); return }
        }
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
