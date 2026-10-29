<!-- SeccaoDocumentos.vue — Configurações da loja (só o dono): documentos legais opcionais que a Bende verifica.
     Backend: /app/loja/<id>/documentos/ (utils/documentos_loja.py). Ficheiros privados; abrem-se por um link
     de 2 minutos e cada consulta da Bende aparece aqui. -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="seccao-documentos">
    <div class="flex items-start justify-between gap-3 mb-1">
      <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Documentos</h2>
      <span v-if="resumo" data-teste="documentos-selo"
            :class="['px-2 py-0.5 rounded-full text-[11px] font-bold flex-shrink-0',
                     resumo.verificada ? 'bg-green-500/15 text-green-400' : 'bg-zinc-800 text-zinc-400']">
        <font-awesome-icon :icon="['fas', resumo.verificada ? 'circle-check' : 'shield-halved']" class="mr-1" />
        {{ resumo.verificada ? 'Loja verificada' : 'Não verificada' }}
      </span>
    </div>
    <p class="text-xs text-zinc-600 mb-4">
      <template v-if="resumo?.obrigatorios">A Bende pediu estes documentos para publicar a loja.</template>
      <template v-else>Opcional.</template>
      Mostram que a loja é legítima: a Bende verifica-os e a loja fica <b class="text-zinc-400">verificada</b> com o
      documento de identificação e o início de atividade (ou certidão comercial) aprovados.
      São privados — só tu e a equipa da Bende os abrem, e cada consulta fica registada.
    </p>

    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>

    <template v-else>
      <p v-if="resumo && !resumo.verificada && resumo.em_falta.length" class="text-xs text-amber-300 mb-4" data-teste="documentos-falta">
        Para ficar verificada falta: {{ resumo.em_falta.join(' e ') }}.
      </p>

      <!-- lista -->
      <ul v-if="documentos.length" class="space-y-2 mb-5" data-teste="documentos-lista">
        <li v-for="d in documentos" :key="d.id" data-teste="documento"
            class="flex flex-col sm:flex-row sm:items-center gap-3 px-4 py-3 rounded-xl bg-zinc-800/50">
          <div class="flex-1 min-w-0">
            <p class="text-sm text-zinc-100 font-semibold">
              {{ d.tipo_nome }}<span v-if="d.descricao" class="text-zinc-400 font-normal"> — {{ d.descricao }}</span>
            </p>
            <p class="text-[11px] text-zinc-500 break-all">
              {{ d.nome_original || d.formato.toUpperCase() }} · {{ tamanho(d.tamanho) }} · enviado {{ d.enviado_em }}
              <template v-if="d.validade"> · válido até {{ dataCurta(d.validade) }}</template>
            </p>
            <p v-if="d.estado === 'rejeitado' && d.motivo" class="text-xs text-red-400 mt-0.5" data-teste="documento-motivo">
              Rejeitado: {{ d.motivo }}
            </p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span :class="['px-2 py-0.5 rounded text-[10px] font-bold', classeEstado(d)]" data-teste="documento-estado">
              {{ d.expirado ? 'Expirado' : d.estado_nome }}
            </span>
            <button type="button" @click="abrir(d)" :data-teste="'documento-abrir-' + d.id"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition">
              Ver
            </button>
            <button type="button" @click="apagar(d)" :disabled="aApagar === d.id" :data-teste="'documento-apagar-' + d.id"
              class="px-3 py-1.5 rounded-lg text-red-400 hover:bg-red-500/10 text-xs font-semibold transition disabled:opacity-50">
              Apagar
            </button>
          </div>
        </li>
      </ul>
      <p v-else class="text-xs text-zinc-500 mb-5">Ainda não enviaste nenhum documento.</p>

      <!-- enviar -->
      <form v-if="disponivel" @submit.prevent="enviar" class="space-y-3 border-t border-zinc-800 pt-4" data-teste="documentos-form">
        <p class="text-xs font-semibold text-zinc-400">Enviar documento</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block" for="doc-tipo">Tipo</label>
            <select id="doc-tipo" v-model="form.tipo" data-teste="documento-tipo"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition">
              <option value="" disabled>Escolhe o tipo</option>
              <option v-for="t in tipos" :key="t.valor" :value="t.valor">{{ t.nome }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block" for="doc-validade">Válido até (se tiver)</label>
            <input id="doc-validade" v-model="form.validade" type="date" :min="hojeIso" data-teste="documento-validade"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block" for="doc-descricao">
              Descrição {{ form.tipo === 'outro' ? '' : '(opcional)' }}
            </label>
            <input id="doc-descricao" v-model="form.descricao" maxlength="120" data-teste="documento-descricao"
              :placeholder="form.tipo === 'outro' ? 'Que documento é?' : 'Ex.: frente e verso'"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block" for="doc-ficheiro">Ficheiro (PDF, JPG ou PNG, até 10 MB)</label>
            <input id="doc-ficheiro" ref="ficheiro" type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
              @change="escolher" data-teste="documento-ficheiro"
              class="block w-full text-sm text-zinc-400 file:mr-3 file:px-3 file:py-2 file:rounded-xl file:border-0 file:bg-zinc-800 file:text-zinc-200 file:text-sm file:font-semibold hover:file:bg-zinc-700" />
          </div>
        </div>
        <p v-if="erro" class="text-xs text-red-400" role="alert" data-teste="documentos-erro">{{ erro }}</p>
        <div class="flex items-center gap-3">
          <button type="submit" :disabled="aEnviar || !form.tipo || !ficheiro" data-teste="documento-enviar"
            class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold transition">
            {{ aEnviar ? 'A enviar…' : 'Enviar' }}
          </button>
          <span v-if="enviado" class="text-xs text-green-500" data-teste="documento-enviado">Enviado ✓ — a Bende vai verificá-lo.</span>
        </div>
      </form>
      <p v-else class="text-xs text-zinc-500 border-t border-zinc-800 pt-4">O envio de documentos não está disponível de momento.</p>

      <!-- consultas da Bende -->
      <div v-if="consultas.length" class="mt-5 border-t border-zinc-800 pt-4" data-teste="documentos-consultas">
        <p class="text-xs font-semibold text-zinc-400 mb-1.5">Atividade da Bende nos teus documentos</p>
        <p v-for="c in consultas" :key="c.id" class="text-[11px] text-zinc-500">
          {{ c.quando }} · {{ c.acao_nome }}<template v-if="c.tipo"> · {{ nomeTipo(c.tipo) }}</template>
        </p>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'SeccaoDocumentos',

  props: {
    lojaId: { type: [String, Number], required: true },
  },

  emits: ['alterado'],

  data () {
    return {
      carregando: true, documentos: [], tipos: [], resumo: null, consultas: [], disponivel: true,
      form: { tipo: '', validade: '', descricao: '' }, ficheiro: null,
      aEnviar: false, enviado: false, erro: '', aApagar: null,
    }
  },

  computed: {
    hojeIso () { return new Date().toISOString().slice(0, 10) },
  },

  created () { this.carregar() },

  methods: {
    aplicar (data) {
      this.documentos = data.documentos
      this.tipos = data.tipos
      this.resumo = data.resumo
      this.consultas = data.consultas_bende || []
      this.disponivel = data.disponivel !== false
    },

    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/documentos/`)
        this.aplicar(data)
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar os documentos.' }
      finally { this.carregando = false }
    },

    escolher (e) {
      this.ficheiro = e.target.files?.[0] || null
      this.erro = ''
      if (this.ficheiro && this.ficheiro.size > 10 * 1024 * 1024) {
        this.erro = 'O ficheiro tem mais de 10 MB.'
        this.ficheiro = null
        e.target.value = ''
      }
    },

    async enviar () {
      this.aEnviar = true; this.erro = ''; this.enviado = false
      const corpo = new FormData()
      corpo.append('tipo', this.form.tipo)
      corpo.append('descricao', this.form.descricao)
      if (this.form.validade) corpo.append('validade', this.form.validade)
      corpo.append('ficheiro', this.ficheiro)
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/documentos/`, corpo)
        this.aplicar(data)
        this.form = { tipo: '', validade: '', descricao: '' }
        this.ficheiro = null
        if (this.$refs.ficheiro) this.$refs.ficheiro.value = ''
        this.enviado = true
        this.$emit('alterado')
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível enviar o documento.' }
      finally { this.aEnviar = false }
    },

    async abrir (d) {
      // o separador abre-se já (no clique), senão o browser bloqueia-o como pop-up
      const separador = window.open('', '_blank')
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/documentos/${d.id}/abrir/`)
        if (separador) { separador.opener = null; separador.location = data.url }
        else window.location.href = data.url
      } catch (e) {
        separador?.close()
        this.erro = e.response?.data?.detail || 'Não foi possível abrir o documento.'
      }
    },

    async apagar (d) {
      const aviso = d.estado === 'aprovado' && ['identificacao', 'atividade'].includes(d.tipo) && !d.expirado
        ? '\n\nEstá aprovado — a loja deixa de estar verificada.' : ''
      if (!confirm(`Apagar "${d.tipo_nome}"?${aviso}`)) return
      this.aApagar = d.id; this.erro = ''
      try {
        const { data } = await api.delete(`/app/loja/${this.lojaId}/documentos/${d.id}/`)
        this.aplicar(data)
        this.$emit('alterado')
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível apagar.' }
      finally { this.aApagar = null }
    },

    classeEstado (d) {
      if (d.expirado) return 'bg-red-500/15 text-red-400'
      return { aprovado: 'bg-green-500/15 text-green-400', rejeitado: 'bg-red-500/15 text-red-400' }[d.estado]
        || 'bg-amber-500/15 text-amber-300'
    },

    nomeTipo (t) { return this.tipos.find(x => x.valor === t)?.nome || '' },
    tamanho (b) { return b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB` },
    dataCurta (iso) { return iso.split('-').reverse().join('/') },
  },
}
</script>
