<!-- AdminDocumentosLoja.vue — Admin → Lojas → ficha: documentos legais da loja (verificar_documentos).
     Backend Views/documentoLojaView.py: abrir (fica registado), aprovar com validade, rejeitar com motivo,
     e tornar os documentos obrigatórios para esta loja (entra nos requisitos para publicar). -->
<template>
  <div class="rounded-xl border border-zinc-800 p-4 space-y-3" data-teste="admin-documentos">
    <div class="flex items-center justify-between gap-3">
      <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">
        <font-awesome-icon :icon="['fas', 'id-card']" class="mr-1.5" />Documentos
      </h3>
      <span v-if="resumo" data-teste="admin-documentos-selo"
            :class="['px-2 py-0.5 rounded-full text-[10px] font-bold',
                     resumo.verificada ? 'bg-green-500/15 text-green-400' : 'bg-zinc-800 text-zinc-400']">
        {{ resumo.verificada ? 'Verificada' : 'Não verificada' }}
      </span>
    </div>

    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>
    <p v-else-if="erroCarregar" class="text-xs text-red-400">{{ erroCarregar }}</p>

    <template v-else>
      <label class="flex items-start gap-3 cursor-pointer" data-teste="admin-documentos-obrigatorios">
        <input type="checkbox" :checked="resumo.obrigatorios" @change="mudarObrigatorios($event.target.checked)"
          :disabled="aMudar" class="mt-0.5 w-4 h-4 accent-red-600" />
        <span class="text-sm text-zinc-300">
          Obrigatórios para esta loja
          <span class="block text-xs text-zinc-500">
            "Loja verificada" passa a ser requisito para publicar. Para quem vende coisas pessoais em casa, deixa desligado.
          </span>
        </span>
      </label>

      <p v-if="!resumo.verificada && resumo.em_falta.length" class="text-[11px] text-zinc-500">
        Para ficar verificada falta: {{ resumo.em_falta.join(' e ') }}.
      </p>

      <ul v-if="documentos.length" class="space-y-2">
        <li v-for="d in documentos" :key="d.id" class="rounded-lg bg-zinc-800/50 px-3 py-2.5 space-y-2" data-teste="admin-documento">
          <div class="flex items-start gap-2">
            <div class="flex-1 min-w-0">
              <p class="text-sm text-zinc-100 font-semibold">
                {{ d.tipo_nome }}<span v-if="d.descricao" class="text-zinc-400 font-normal"> — {{ d.descricao }}</span>
              </p>
              <p class="text-[11px] text-zinc-500 break-all">
                {{ d.formato.toUpperCase() }} · {{ d.enviado_em }} por {{ d.enviado_por || '—' }}
                <template v-if="d.validade"> · válido até {{ dataCurta(d.validade) }}</template>
                <template v-if="d.revisto_por"> · revisto por {{ d.revisto_por }} em {{ d.revisto_em }}</template>
              </p>
              <p v-if="d.estado === 'rejeitado' && d.motivo" class="text-xs text-red-400">Rejeitado: {{ d.motivo }}</p>
            </div>
            <span :class="['px-2 py-0.5 rounded text-[10px] font-bold flex-shrink-0', classeEstado(d)]" data-teste="admin-documento-estado">
              {{ d.expirado ? 'Expirado' : d.estado_nome }}
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <button type="button" @click="abrir(d)" :data-teste="'admin-documento-abrir-' + d.id"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition">
              Abrir (fica registado)
            </button>
            <template v-if="decidir?.id !== d.id">
              <button v-if="d.estado !== 'aprovado' || d.expirado" type="button" @click="comecar(d, 'aprovar')"
                :data-teste="'admin-documento-aprovar-' + d.id"
                class="px-3 py-1.5 rounded-lg bg-green-500/15 text-green-400 hover:bg-green-500/25 text-xs font-bold transition">
                Aprovar
              </button>
              <button v-if="d.estado !== 'rejeitado'" type="button" @click="comecar(d, 'rejeitar')"
                :data-teste="'admin-documento-rejeitar-' + d.id"
                class="px-3 py-1.5 rounded-lg bg-red-500/15 text-red-400 hover:bg-red-500/25 text-xs font-bold transition">
                Rejeitar
              </button>
            </template>
          </div>

          <!-- decisão -->
          <form v-if="decidir?.id === d.id" @submit.prevent="confirmar" class="space-y-2 pt-1" data-teste="admin-documento-decisao">
            <template v-if="decidir.acao === 'aprovar'">
              <label class="text-xs text-zinc-500 block" :for="'val-' + d.id">Válido até (vazio = não expira)</label>
              <input :id="'val-' + d.id" v-model="decidir.validade" type="date" data-teste="admin-documento-validade"
                class="w-full sm:w-48 px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
              <p v-if="d.tipo !== 'outro'" class="text-[11px] text-zinc-500">Os outros documentos deste tipo são apagados (este substitui-os).</p>
            </template>
            <template v-else>
              <label class="text-xs text-zinc-500 block" :for="'mot-' + d.id">Motivo (a loja vê)</label>
              <input :id="'mot-' + d.id" v-model="decidir.motivo" maxlength="300" data-teste="admin-documento-motivo"
                placeholder="Ex.: ilegível, nome diferente do titular, fora da validade"
                class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
            </template>
            <div class="flex items-center gap-2">
              <button type="submit" :disabled="aDecidir" data-teste="admin-documento-confirmar"
                :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition disabled:opacity-50',
                         decidir.acao === 'aprovar' ? 'bg-green-600 hover:bg-green-500 text-white' : 'bg-red-600 hover:bg-red-500 text-white']">
                {{ decidir.acao === 'aprovar' ? 'Confirmar aprovação' : 'Confirmar rejeição' }}
              </button>
              <button type="button" @click="decidir = null" class="text-xs text-zinc-400 hover:text-zinc-200">Cancelar</button>
            </div>
          </form>
        </li>
      </ul>
      <p v-else class="text-xs text-zinc-500">A loja não enviou documentos.</p>

      <p v-if="erro" class="text-xs text-red-400" role="alert" data-teste="admin-documentos-erro">{{ erro }}</p>

      <details v-if="registo.length" class="text-[11px] text-zinc-500">
        <summary class="cursor-pointer text-zinc-400">Registo ({{ registo.length }})</summary>
        <p v-for="r in registo" :key="r.id" class="mt-1" data-teste="admin-documentos-registo">
          {{ r.quando }} · {{ r.quem || '—' }} · {{ r.acao_nome }}<template v-if="r.detalhe"> · {{ r.detalhe }}</template>
        </p>
      </details>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminDocumentosLoja',

  props: {
    lojaId: { type: Number, required: true },
  },

  emits: ['alterado'],

  data () {
    return {
      carregando: true, erroCarregar: '', erro: '',
      documentos: [], resumo: null, registo: [],
      decidir: null, aDecidir: false, aMudar: false,
    }
  },

  watch: {
    lojaId: { handler: 'carregar', immediate: true },
  },

  methods: {
    aplicar (data) {
      this.documentos = data.documentos
      this.resumo = data.resumo
      this.registo = data.registo || []
    },

    async carregar () {
      this.carregando = true; this.erroCarregar = ''; this.decidir = null
      try {
        const { data } = await api.get(`/app/admin/lojas/${this.lojaId}/documentos/`)
        this.aplicar(data)
      } catch (e) { this.erroCarregar = e.response?.data?.detail || 'Sem acesso aos documentos.' }
      finally { this.carregando = false }
    },

    comecar (d, acao) {
      this.erro = ''
      this.decidir = { id: d.id, acao, motivo: '', validade: d.validade || '' }
    },

    async confirmar () {
      this.aDecidir = true; this.erro = ''
      try {
        const { data } = await api.post(`/app/admin/documentos/${this.decidir.id}/`, {
          acao: this.decidir.acao, motivo: this.decidir.motivo, validade: this.decidir.validade || null,
        })
        this.aplicar(data)
        this.decidir = null
        this.$emit('alterado', data.resumo)
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível guardar a decisão.' }
      finally { this.aDecidir = false }
    },

    async mudarObrigatorios (valor) {
      this.aMudar = true; this.erro = ''
      try {
        const { data } = await api.patch(`/app/admin/lojas/${this.lojaId}/documentos/`, { obrigatorios: valor })
        this.aplicar(data)
        this.$emit('alterado', data.resumo)
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível mudar.' }
      finally { this.aMudar = false }
    },

    async abrir (d) {
      const separador = window.open('', '_blank')
      try {
        const { data } = await api.post(`/app/admin/documentos/${d.id}/abrir/`)
        if (separador) { separador.opener = null; separador.location = data.url }
        else window.location.href = data.url
        this.carregarRegisto()
      } catch (e) {
        separador?.close()
        this.erro = e.response?.data?.detail || 'Não foi possível abrir o documento.'
      }
    },

    async carregarRegisto () {
      try {
        const { data } = await api.get(`/app/admin/lojas/${this.lojaId}/documentos/`)
        this.registo = data.registo || []
      } catch { /* o registo não é essencial */ }
    },

    classeEstado (d) {
      if (d.expirado) return 'bg-red-500/15 text-red-400'
      return { aprovado: 'bg-green-500/15 text-green-400', rejeitado: 'bg-red-500/15 text-red-400' }[d.estado]
        || 'bg-amber-500/15 text-amber-300'
    },

    dataCurta (iso) { return iso.split('-').reverse().join('/') },
  },
}
</script>
