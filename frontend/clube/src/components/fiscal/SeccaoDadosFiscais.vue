<!-- SeccaoDadosFiscais.vue — editar os dados fiscais (Configurações da loja / do POS).
     fiscal: payload do backend { nif, regime_fiscal, completos, aceites_em }; url: PATCH …/fiscal/.
     POS ligado a uma loja (fiscal.loja): pode usar os dados da loja (fiscal.da_loja — PATCH { da_loja: true }).
     Loja: fiscal.pos_seguem = POS que usam estes dados. -->
<template>
  <div :class="c.caixa" data-teste="seccao-fiscal">
    <h2 :class="c.titulo">Dados fiscais</h2>
    <p :class="c.sub">
      Só tu e a plataforma veem o NIF. Ao guardar, voltas a aceitar a declaração de responsabilidade.
    </p>
    <p v-if="fiscal?.pos_seguem?.length" :class="c.nota" data-teste="fiscal-pos-seguem">
      {{ fiscal.pos_seguem.length === 1 ? 'O POS' : 'Os POS' }} {{ fiscal.pos_seguem.join(', ') }}
      {{ fiscal.pos_seguem.length === 1 ? 'usa' : 'usam' }} estes dados: ao alterá-los aqui, mudam também.
    </p>

    <label v-if="fiscal?.loja" :class="c.opcao" data-teste="fiscal-da-loja">
      <input type="checkbox" :checked="daLoja" :disabled="aGuardar" class="mt-0.5 h-4 w-4 shrink-0" @change="mudarDaLoja($event.target.checked)" />
      <span>
        <span class="font-bold">Usar os dados fiscais da loja {{ fiscal.loja.nome }}</span>
        <span class="block text-xs opacity-75">O POS fica com o mesmo NIF e atividade, e acompanha quando os mudares na loja.
          Desliga se o POS fatura com outro NIF.</span>
      </span>
    </label>

    <template v-if="daLoja">
      <div v-if="fiscal.loja.completos" :class="c.resumo" data-teste="fiscal-resumo-loja">
        <p>NIF <span class="font-bold">{{ fiscal.nif }}</span></p>
        <p>{{ regimeTitulo }}</p>
      </div>
      <p v-else :class="c.aviso" data-teste="fiscal-loja-sem-dados">
        A loja {{ fiscal.loja.nome }} ainda não tem dados fiscais. Preenche-os nas Configurações da loja
        e o POS fica logo com os mesmos.
      </p>
      <p v-if="erro" class="mt-3 text-xs text-red-400">{{ erro }}</p>
      <span v-if="guardado" class="mt-3 block text-xs text-green-500">Guardado ✓</span>
    </template>

    <template v-else>
    <DadosFiscais v-model="form" :tema="tema" />
    <p v-if="erro" class="mt-3 text-xs text-red-400">{{ erro }}</p>
    <div class="mt-4 flex items-center gap-3">
      <button type="button" @click="guardar" :disabled="!valido || aGuardar" data-teste="guardar-fiscal"
        :class="[c.botao, (!valido || aGuardar) ? 'opacity-50 cursor-not-allowed' : '']">
        {{ aGuardar ? 'A guardar…' : 'Guardar dados fiscais' }}
      </button>
      <span v-if="guardado" class="text-xs text-green-500">Guardado ✓</span>
    </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import DadosFiscais from './DadosFiscais.vue'
import { dadosFiscaisValidos, corpoDadosFiscais, REGIMES } from '@/utils/fiscal'

const TEMAS = {
  escuro: {
    caixa: 'bg-zinc-900 rounded-2xl border border-zinc-800 p-6',
    titulo: 'text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1',
    sub: 'text-xs text-zinc-600 mb-5',
    botao: 'px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition',
    nota: 'mb-4 rounded-xl border border-zinc-700 bg-zinc-800/60 px-3 py-2 text-xs text-zinc-300',
    opcao: 'mb-4 flex cursor-pointer items-start gap-3 rounded-xl border border-zinc-700 p-3 text-sm text-zinc-200',
    resumo: 'rounded-xl border border-zinc-700 bg-zinc-800/60 px-4 py-3 text-sm text-zinc-200',
    aviso: 'rounded-xl border border-amber-700 bg-amber-950/40 px-4 py-3 text-xs text-amber-300',
  },
  claro: {
    caixa: 'rounded-[1.5rem] border border-slate-200 bg-white p-5',
    titulo: 'text-lg font-black text-slate-950',
    sub: 'mt-1 mb-5 text-sm font-semibold text-slate-500',
    botao: 'h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800',
    nota: 'mb-4 rounded-2xl bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-600',
    opcao: 'mb-4 flex cursor-pointer items-start gap-3 rounded-2xl border border-slate-200 p-4 text-sm text-slate-700',
    resumo: 'rounded-2xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700',
    aviso: 'rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-semibold text-amber-800',
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
      daLoja: !!this.fiscal?.da_loja,
      aGuardar: false,
      guardado: false,
      erro: '',
    }
  },
  computed: {
    c () { return TEMAS[this.tema] || TEMAS.escuro },
    valido () { return dadosFiscaisValidos(this.form) },
    regimeTitulo () { return REGIMES.find(r => r.valor === this.fiscal?.regime_fiscal)?.titulo || '' },
  },
  watch: {
    // os dados chegam/atualizam depois (backoffice recarregado, POS guardado): mantém a declaração por aceitar
    fiscal (n) {
      this.form = { ...this.form, nif: n?.nif || '', regime_fiscal: n?.regime_fiscal || '' }
      this.daLoja = !!n?.da_loja
    },
  },
  methods: {
    // ligar: passa já a usar os da loja; desligar: só mostra o formulário (deixa de seguir ao gravar os próprios)
    async mudarDaLoja (ligar) {
      this.erro = ''; this.guardado = false
      if (!ligar) { this.daLoja = false; return }
      this.aGuardar = true
      try {
        const { data } = await api.patch(this.url, { da_loja: true })
        this.daLoja = true
        this.guardado = true
        this.$emit('guardado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
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
