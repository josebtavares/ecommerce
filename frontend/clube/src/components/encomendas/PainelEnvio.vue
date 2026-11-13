<template>
  <!-- Envio por transportadora na ficha da encomenda (backoffice) — backend utils/envios.py.
       Mostra a transportadora e os códigos; envia, corrige o código, marca devolvida e reenvia. -->
  <div class="border-t border-zinc-800 pt-3 space-y-3" data-teste="painel-envio">
    <div class="flex items-center justify-between gap-2">
      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider">
        <font-awesome-icon :icon="['fas', 'box']" class="mr-1" />Envio por transportadora
      </p>
      <span v-if="envio" :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', COR[envio.estado] || 'bg-zinc-500/15 text-zinc-400']">
        {{ ESTADO[envio.estado] || envio.estado }}
      </span>
    </div>

    <p v-if="encomenda.opcao_entrega_nome && !envio" class="text-xs text-zinc-400">
      O cliente escolheu <b class="text-zinc-200">{{ encomenda.opcao_entrega_nome }}</b>.
    </p>

    <!-- dados do envio -->
    <div v-if="envio" class="rounded-xl bg-zinc-800/50 p-3 space-y-2 text-xs">
      <div class="flex justify-between gap-2">
        <span class="text-zinc-500">Transportadora</span>
        <span class="text-zinc-200 font-semibold text-right">{{ envio.transportadora }}</span>
      </div>
      <div class="flex justify-between gap-2 items-start">
        <span class="text-zinc-500">{{ envio.codigos.length > 1 ? 'Códigos' : 'Código' }}</span>
        <span v-if="!envio.codigos.length" class="text-zinc-500 italic" data-teste="envio-sem-codigo">sem código de rastreio</span>
        <span v-else class="flex flex-col items-end gap-1">
          <span v-for="c in envio.codigos" :key="c.codigo" class="flex items-center gap-2">
            <span class="font-mono text-zinc-100 select-all" data-teste="envio-codigo">{{ c.codigo }}</span>
            <a v-if="c.link" :href="c.link" target="_blank" rel="noopener noreferrer"
               class="text-red-400 hover:text-red-300" title="Seguir na transportadora">
              <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
            </a>
          </span>
        </span>
      </div>
      <div v-if="envio.data_envio" class="flex justify-between gap-2">
        <span class="text-zinc-500">Enviada a</span>
        <span class="text-zinc-300">{{ dataHora(envio.data_envio) }}</span>
      </div>
      <div v-if="envio.fecho_previsto_em" class="flex justify-between gap-2" data-teste="envio-fecho">
        <span class="text-zinc-500">Fecho automático</span>
        <span :class="envio.nao_recebido_em ? 'text-amber-300' : 'text-zinc-300'">
          {{ envio.nao_recebido_em ? 'parado (o cliente não recebeu)' : data(envio.fecho_previsto_em) + ' (se o cliente não disser nada)' }}
        </span>
      </div>
      <div v-if="envio.talao" class="flex justify-between gap-2">
        <span class="text-zinc-500">Talão</span>
        <a :href="envio.talao" target="_blank" rel="noopener noreferrer" class="text-red-400 hover:text-red-300">Ver foto</a>
      </div>
      <details v-if="(envio.historico || []).length > 1" class="pt-1">
        <summary class="cursor-pointer text-zinc-500 hover:text-zinc-300">Histórico ({{ envio.historico.length }})</summary>
        <ul class="mt-2 space-y-1.5">
          <li v-for="(h, i) in envio.historico.slice().reverse()" :key="i" class="text-[11px] text-zinc-400">
            <b class="text-zinc-300">{{ ACAO[h.acao] || h.acao }}</b> · {{ dataHora(h.em) }}{{ h.por_nome ? ' · ' + h.por_nome : '' }}
            <br />{{ h.transportadora }} — {{ (h.codigos || []).join(', ') || 'sem código' }}<span v-if="h.nota" class="italic"> · “{{ h.nota }}”</span>
          </li>
        </ul>
      </details>
    </div>

    <p v-if="envio && envio.estado === 'a_caminho' && envio.nao_recebido_em" data-teste="envio-nao-recebido"
       class="text-xs text-amber-200 rounded-lg bg-amber-500/10 border border-amber-500/30 px-2.5 py-2">
      <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mr-1" />
      <b>O cliente diz que não recebeu</b> ({{ dataHora(envio.nao_recebido_em) }}){{ envio.nao_recebido_nota ? ': “' + envio.nao_recebido_nota + '”' : '' }}.
      Confirma com a transportadora: corrige o código, marca-a como devolvida ou conclui-a se já foi entregue.
    </p>

    <p v-if="envio && envio.estado === 'devolvida'" class="text-xs text-amber-200 rounded-lg bg-amber-500/10 border border-amber-500/30 px-2.5 py-2">
      <font-awesome-icon :icon="['fas', 'rotate-left']" class="mr-1" />
      A transportadora devolveu a encomenda. Reenvia-a (o cliente não paga outra vez) ou cancela a encomenda — o cliente é reembolsado e o stock volta.
    </p>

    <!-- botões -->
    <div v-if="!modo" class="flex flex-wrap gap-2">
      <button v-if="podeEnviar" type="button" @click="abrir('enviar')" :disabled="!!bloqueio" data-teste="envio-enviar"
              :title="bloqueio"
              class="px-3 py-1.5 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-500 text-white transition disabled:opacity-40 disabled:cursor-not-allowed">
        <font-awesome-icon :icon="['fas', 'truck-fast']" class="mr-1" />{{ envio && envio.estado === 'devolvida' ? 'Reenviar' : 'Enviar por transportadora' }}
      </button>
      <template v-if="envio && envio.estado === 'a_caminho'">
        <button type="button" @click="abrir('corrigir')" data-teste="envio-corrigir"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition">
          <font-awesome-icon :icon="['fas', envio.codigos.length ? 'pen-to-square' : 'plus']" class="mr-1" />{{ envio.codigos.length ? 'Corrigir código' : 'Adicionar código' }}
        </button>
        <button type="button" @click="abrir('devolvida')" data-teste="envio-devolvida"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/15 text-amber-300 hover:bg-amber-500/25 transition">
          <font-awesome-icon :icon="['fas', 'rotate-left']" class="mr-1" />Devolvida pela transportadora
        </button>
      </template>
    </div>
    <p v-if="podeEnviar && bloqueio && !modo" class="text-[11px] text-zinc-500">{{ bloqueio }}</p>

    <!-- formulário: enviar / reenviar / corrigir -->
    <div v-if="modo === 'enviar' || modo === 'corrigir'" class="rounded-xl border border-zinc-700 p-3 space-y-3" data-teste="envio-form">
      <div>
        <label class="text-[11px] text-zinc-500 mb-1 block">Transportadora</label>
        <select v-model="form.transportadora" data-teste="envio-transportadora"
                class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500">
          <option value="" disabled>Escolhe a transportadora</option>
          <option v-for="t in transportadoras" :key="t.id" :value="String(t.id)">{{ t.nome }}</option>
          <option value="outra">Outra…</option>
        </select>
        <input v-if="form.transportadora === 'outra'" v-model="form.outra" type="text" maxlength="80" placeholder="Nome da transportadora"
               class="mt-2 w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
      </div>
      <div>
        <label class="text-[11px] text-zinc-500 mb-1 block">Código de rastreio <span class="text-zinc-600">(opcional — o cliente vê-o na encomenda; podes juntá-lo depois)</span></label>
        <div v-for="(c, i) in form.codigos" :key="i" class="flex gap-2 mb-2">
          <input v-model="form.codigos[i]" type="text" maxlength="60" :placeholder="i === 0 ? 'ex.: RR123456789CV' : 'Outro volume'"
                 data-teste="envio-codigo-input" autocapitalize="characters" spellcheck="false"
                 class="flex-1 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 font-mono focus:outline-none focus:border-red-500" />
          <button v-if="form.codigos.length > 1" type="button" @click="form.codigos.splice(i, 1)" aria-label="Tirar código"
                  class="w-8 rounded-lg bg-zinc-800 text-zinc-400 hover:text-zinc-200">×</button>
        </div>
        <button v-if="form.codigos.length < 10" type="button" @click="form.codigos.push('')"
                class="text-[11px] text-red-400 hover:text-red-300">+ Outro volume (outro código)</button>
      </div>
      <div v-if="modo === 'enviar'">
        <label class="text-[11px] text-zinc-500 mb-1 block">Foto do talão <span class="text-zinc-600">(opcional)</span></label>
        <p v-if="!form.codigos.some(c => c.trim())" class="text-[11px] text-amber-300 mb-1" data-teste="envio-dica-talao">
          Sem código, a foto do talão ajuda se o cliente disser que não recebeu.
        </p>
        <input type="file" accept="image/*" @change="form.talao = $event.target.files[0] || null"
               class="block w-full text-xs text-zinc-400 file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border-0 file:bg-zinc-800 file:text-zinc-300" />
      </div>
      <input v-if="modo === 'corrigir'" v-model="form.nota" type="text" maxlength="200" placeholder="O que estava errado (opcional)"
             class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
      <p v-if="erro" class="text-xs text-red-400" role="alert">{{ erro }}</p>
      <div class="flex justify-end gap-2">
        <button type="button" @click="fechar" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200">Voltar</button>
        <button type="button" @click="submeter" :disabled="aGuardar" data-teste="envio-confirmar"
                class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-40">
          {{ aGuardar ? 'A guardar…' : (modo === 'corrigir' ? 'Guardar correção' : 'Confirmar envio') }}
        </button>
      </div>
    </div>

    <!-- formulário: devolvida -->
    <div v-if="modo === 'devolvida'" class="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 space-y-3">
      <p class="text-xs text-amber-100">A encomenda volta a "em preparação": depois reenvias ou cancelas.</p>
      <input v-model="form.nota" type="text" maxlength="200" placeholder="O que aconteceu (ex.: morada não encontrada)"
             data-teste="envio-nota-devolvida"
             class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-amber-500" />
      <p v-if="erro" class="text-xs text-red-400" role="alert">{{ erro }}</p>
      <div class="flex justify-end gap-2">
        <button type="button" @click="fechar" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200">Voltar</button>
        <button type="button" @click="submeter" :disabled="aGuardar || form.nota.trim().length < 5" data-teste="envio-confirmar-devolvida"
                class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-40">
          {{ aGuardar ? 'A guardar…' : 'Marcar como devolvida' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const ESTADO = { a_caminho: 'A caminho', entregue: 'Entregue', devolvida: 'Devolvida', cancelada: 'Cancelada' }
const COR = { a_caminho: 'bg-indigo-500/15 text-indigo-400', entregue: 'bg-green-500/15 text-green-400',
              devolvida: 'bg-amber-500/15 text-amber-300', cancelada: 'bg-zinc-500/15 text-zinc-400' }
const ACAO = { enviado: 'Enviada', corrigido: 'Dados corrigidos', adicionado: 'Código adicionado', devolvido: 'Devolvida', reenviado: 'Reenviada',
               recebido: 'O cliente confirmou que recebeu', fechado_auto: 'Fechada automaticamente (sem resposta do cliente)' }

export default {
  name: 'PainelEnvio',
  props: {
    lojaId:     { type: [String, Number], required: true },
    encomenda:  { type: Object, required: true },        // detalhe (EncomendaSerializer)
    pedido:     { type: Number, default: 0 },           // muda → abre o formulário de envio (botão "Enviado")
  },
  emits: ['atualizada', 'ocupado'],
  data () {
    return { ESTADO, COR, ACAO, modo: '', aGuardar: false, erro: '', transportadoras: [], form: this.formVazio() }
  },
  computed: {
    envio () { return this.encomenda.envio },
    podeEnviar () {
      return ['pago', 'preparando'].includes(this.encomenda.status) &&
             (!this.envio || this.envio.estado === 'devolvida')
    },
    // o servidor confirma; isto só explica porque o botão está apagado
    bloqueio () {
      if (this.encomenda.transferencia_por_confirmar) return 'Confirma primeiro que a transferência chegou.'
      if (this.encomenda.pagamento_status !== 'aprovado') return 'Só se envia por transportadora uma encomenda já paga.'
      return ''
    },
  },
  watch: {
    pedido (n) { if (n && this.podeEnviar && !this.bloqueio) this.abrir('enviar') },
    modo (m) { this.$emit('ocupado', !!m) },
  },
  methods: {
    formVazio () { return { transportadora: '', outra: '', codigos: [''], talao: null, nota: '' } },
    data (d) { return new Date(d).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit' }) },
    dataHora (d) { return new Date(d).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) },
    async carregarTransportadoras () {
      if (this.transportadoras.length) return
      try { this.transportadoras = (await api.get('/app/transportadoras/')).data } catch { this.transportadoras = [] }
    },
    async abrir (modo) {
      this.erro = ''
      this.form = this.formVazio()
      this.modo = modo
      if (modo === 'devolvida') return
      await this.carregarTransportadoras()
      const e = this.envio
      if (modo === 'corrigir' && e) {
        this.form.transportadora = e.transportadora_id ? String(e.transportadora_id) : 'outra'
        this.form.outra = e.transportadora_id ? '' : e.transportadora
        this.form.codigos = e.codigos.length ? e.codigos.map(c => c.codigo) : ['']    // sem código: um campo vazio p/ juntar
      } else {
        // a transportadora da opção que o cliente escolheu (ou a do envio devolvido)
        const id = e?.transportadora_id || this.encomenda.opcao_transportadora_id
        if (id && this.transportadoras.some(t => t.id === id)) this.form.transportadora = String(id)
      }
    },
    fechar () { this.modo = ''; this.erro = '' },
    async submeter () {
      if (this.aGuardar) return
      this.erro = ''
      const base = `/app/loja/${this.lojaId}/encomendas/${this.encomenda.id}/envio/`
      try {
        this.aGuardar = true
        let data
        if (this.modo === 'devolvida') {
          ({ data } = await api.post(`${base}devolvida/`, { nota: this.form.nota }))
        } else {
          const codigos = this.form.codigos.map(c => c.trim()).filter(Boolean)
          if (!this.form.transportadora) throw new Error('Escolhe a transportadora.')
          const t = this.form.transportadora
          if (this.modo === 'corrigir') {
            ({ data } = await api.post(`${base}corrigir/`, {
              transportadora_id: t === 'outra' ? null : Number(t), transportadora_outra: t === 'outra' ? this.form.outra : '',
              codigos, nota: this.form.nota,
            }))
          } else {
            const fd = new FormData()
            if (t === 'outra') fd.append('transportadora_outra', this.form.outra)
            else fd.append('transportadora_id', t)
            fd.append('codigos', JSON.stringify(codigos))
            if (this.form.talao) fd.append('talao', this.form.talao)
            ;({ data } = await api.post(base, fd, { headers: { 'Content-Type': 'multipart/form-data' } }))
          }
        }
        this.modo = ''
        this.$emit('atualizada', data)
      } catch (e) {
        const d = e.response?.data
        this.erro = d?.detail || (d && Object.values(d).flat()[0]) || e.message || 'Não foi possível guardar.'
      } finally { this.aGuardar = false }
    },
  },
}
</script>
