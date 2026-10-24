<!-- SeccaoDadosFiscais.vue — editar os dados fiscais (Configurações da loja / do POS).
     fiscal: payload do backend { nif, regime_fiscal, completos, aceites_em }; url: PATCH …/fiscal/. -->
<template>
  <div :class="c.caixa" data-teste="seccao-fiscal">
    <h2 :class="c.titulo">Dados fiscais</h2>
    <p :class="c.sub">
      Só tu e a plataforma veem o NIF. Ao guardar, voltas a aceitar a declaração de responsabilidade.
    </p>
    <DadosFiscais v-model="form" :tema="tema" />
    <p v-if="erro" class="mt-3 text-xs text-red-400">{{ erro }}</p>
    <div class="mt-4 flex items-center gap-3">
      <button type="button" @click="guardar" :disabled="!valido || aGuardar" data-teste="guardar-fiscal"
        :class="[c.botao, (!valido || aGuardar) ? 'opacity-50 cursor-not-allowed' : '']">
        {{ aGuardar ? 'A guardar…' : 'Guardar dados fiscais' }}
      </button>
      <span v-if="guardado" class="text-xs text-green-500">Guardado ✓</span>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import DadosFiscais from './DadosFiscais.vue'
import { dadosFiscaisValidos, corpoDadosFiscais } from '@/utils/fiscal'

const TEMAS = {
  escuro: {
    caixa: 'bg-zinc-900 rounded-2xl border border-zinc-800 p-6',
    titulo: 'text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1',
    sub: 'text-xs text-zinc-600 mb-5',
    botao: 'px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition',
  },
  claro: {
    caixa: 'rounded-[1.5rem] border border-slate-200 bg-white p-5',
    titulo: 'text-lg font-black text-slate-950',
    sub: 'mt-1 mb-5 text-sm font-semibold text-slate-500',
    botao: 'h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800',
  },
}

export default {
  name: 'SeccaoDadosFiscais',
  components: { DadosFiscais },
  props: {
    fiscal: { type: Object, default: null },
    url:    { type: String, required: true },
    tema:   { type: String, default: 'escuro' },
  },
  emits: ['guardado'],
  data () {
    return {
      form: { nif: this.fiscal?.nif || '', regime_fiscal: this.fiscal?.regime_fiscal || '', declaracao_fiscal: false },
      aGuardar: false,
      guardado: false,
      erro: '',
    }
  },
  computed: {
    c () { return TEMAS[this.tema] || TEMAS.escuro },
    valido () { return dadosFiscaisValidos(this.form) },
  },
  watch: {
    // os dados chegam/atualizam depois (backoffice recarregado, POS guardado): mantém a declaração por aceitar
    fiscal (n) {
      this.form = { ...this.form, nif: n?.nif || '', regime_fiscal: n?.regime_fiscal || '' }
    },
  },
  methods: {
    async guardar () {
      this.aGuardar = true; this.erro = ''; this.guardado = false
      try {
        const { data } = await api.patch(this.url, corpoDadosFiscais(this.form))
        this.guardado = true
        this.form.declaracao_fiscal = false
        this.$emit('guardado', data)
      } catch (e) {
        const d = e.response?.data
        this.erro = d?.detail || (d && typeof d === 'object' && [].concat(Object.values(d)[0])[0]) || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
