<!-- SeccaoVinti4.vue — Configurações da loja (só o dono): pagamento com cartão = contrato vinti4 da própria loja.
     A SISP não deixa a Bendi receber por conta das lojas: cada loja adere e recebe direto na conta dela.
     Backend: GET/POST/PUT /app/loja/<id>/vinti4/ (utils/vinti4.py). A chave nunca volta do servidor.
     Tempo real: recarrega quando a loja, os documentos ou a adesão mudam (aviso 'loja' — utils/tempo_real_listas.py). -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="seccao-vinti4">
    <div class="flex items-center justify-between gap-3 mb-1">
      <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Pagamento com cartão (vinti4)</h2>
      <span v-if="d?.adesao" data-teste="vinti4-estado"
            :class="['px-2 py-0.5 rounded-lg text-[11px] font-bold', COR[d.adesao.estado] || 'bg-zinc-800 text-zinc-400']">
        {{ d.adesao.estado_nome }}
      </span>
    </div>
    <p class="text-xs text-zinc-600 mb-5">
      Para aceitar cartões online, a loja precisa do seu próprio contrato com a SISP (vinti4). O dinheiro das vendas com
      cartão vai direto para a tua conta — a Bendi não toca nele. Sem contrato, vendes com dinheiro ou transferência.
    </p>

    <!-- tarifário V.02 e cláusulas 4 e 6 do contrato MD050.02 — o que a loja deve saber antes de aderir -->
    <details class="mb-5 rounded-xl border border-zinc-800" data-teste="vinti4-custos">
      <summary class="px-4 py-3 text-sm text-zinc-300 cursor-pointer select-none">Custos e prazos da SISP</summary>
      <ul class="px-4 pb-4 space-y-2 text-xs text-zinc-400 list-disc list-inside">
        <li>A SISP desconta a comissão dela em cada venda com cartão: <span class="text-zinc-200">0,70% + IVA</span> nos
            cartões vinti4 e <span class="text-zinc-200">2,5%</span> nos cartões internacionais. Recebes o valor da venda
            já sem essa comissão.</li>
        <li>Esta comissão é da SISP e é diferente da comissão ou mensalidade da Bendi. Os valores "líquidos" que vês na
            Bendi só descontam a comissão da Bendi, não a da SISP.</li>
        <li>O dinheiro chega à tua conta <span class="text-zinc-200">no próprio dia</span> nos cartões vinti4 e
            <span class="text-zinc-200">4 dias úteis</span> depois nos cartões internacionais.</li>
        <li>Se um cliente reclamar no banco que não recebeu a encomenda ou o serviço, ou se a venda for fraudulenta, a SISP
            pode debitar esse valor da tua conta. Entrega sempre o que vendes e guarda a prova de entrega.</li>
        <li>Não podes cobrar ao cliente nenhum valor extra por pagar com cartão. A SISP pode pedir uma garantia bancária,
            conforme o volume de vendas.</li>
      </ul>
    </details>

    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>
    <p v-else-if="!d" class="text-xs text-red-400">{{ erroGeral || 'Não foi possível carregar.' }}</p>

    <template v-else>
      <p v-if="d.simulado" class="mb-4 text-[11px] text-amber-400/90" data-teste="vinti4-simulado">
        Por agora os pagamentos com cartão na Bendi são simulados. Podes já tratar da adesão.
      </p>

      <!-- estado da adesão -->
      <div v-if="d.adesao" class="mb-5 rounded-xl bg-zinc-800/50 p-4 text-sm space-y-1" data-teste="vinti4-adesao">
        <p class="text-zinc-200">{{ TEXTO[d.adesao.estado === 'pedida' && d.adesao.modo === 'contrato' ? 'pedida_contrato' : d.adesao.estado] }}</p>
        <p v-if="d.adesao.motivo" class="text-xs text-amber-400">Motivo: {{ d.adesao.motivo }}</p>
        <p v-if="d.adesao.pos_id" class="text-xs text-zinc-500">
          POS ID {{ d.adesao.pos_id }} · Merchant ID {{ d.adesao.merchant_id }} · chave {{ d.adesao.chave_definida ? 'guardada' : 'em falta' }}
        </p>
      </div>

      <!-- dois caminhos: pedir a adesão pela Bendi, ou já ter contrato com a SISP -->
      <div v-if="!d.adesao" class="mb-5">
        <p class="text-xs font-bold text-zinc-400 mb-2">Já tens contrato vinti4 com a SISP?</p>
        <div class="inline-flex rounded-xl bg-zinc-800 p-1 gap-1" role="tablist">
          <button v-for="o in MODOS" :key="o.v" type="button" role="tab" :aria-selected="modo === o.v"
            @click="modo = o.v" :data-teste="`vinti4-modo-${o.v}`"
            :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                     modo === o.v ? 'bg-zinc-600 text-white' : 'text-zinc-400 hover:text-zinc-200']">{{ o.t }}</button>
        </div>
      </div>

      <!-- requisitos -->
      <div v-if="!d.adesao || d.adesao.estado === 'pedida'" class="mb-5">
        <p class="text-xs font-bold text-zinc-400 mb-2">{{ modoAtual === 'contrato' ? 'O que precisas' : 'O que a SISP pede' }}</p>
        <ul class="space-y-1.5" data-teste="vinti4-requisitos">
          <li v-for="r in requisitosAtuais" :key="r.chave" class="flex items-start gap-2 text-sm" :data-req="r.chave">
            <font-awesome-icon :icon="['fas', r.ok ? 'circle-check' : 'circle-xmark']"
                               :class="['mt-0.5 flex-shrink-0', r.ok ? 'text-green-500' : 'text-zinc-600']" />
            <span class="min-w-0 flex-1">
              <span :class="r.ok ? 'text-zinc-300' : 'text-zinc-100'">{{ r.titulo }}</span>
              <span v-if="r.chave === 'comprovativo' && d.comprovativo && r.ok" class="ml-1 text-[11px] text-zinc-500">
                ({{ d.comprovativo.estado === 'aprovado' ? 'aprovado' : 'enviado — a Bendi vai verificar' }})
              </span>
              <span v-if="!r.ok" class="block text-[11px] text-zinc-500">{{ r.ajuda }}</span>
              <!-- o comprovativo envia-se aqui mesmo (fica nos Documentos da loja, privado) -->
              <span v-if="r.chave === 'comprovativo' && !r.ok" class="mt-2 flex flex-wrap items-center gap-2" data-teste="vinti4-comprovativo">
                <input ref="comprovativo" type="file" accept="application/pdf,image/jpeg,image/png" @change="escolherComprovativo"
                  class="text-xs text-zinc-400 file:mr-2 file:px-3 file:py-1.5 file:rounded-lg file:border-0 file:bg-zinc-700 file:text-zinc-100 file:text-xs" />
                <button type="button" @click="enviarComprovativo" :disabled="!comprovativo || aEnviarComp" data-teste="vinti4-comprovativo-enviar"
                  class="px-3 py-1.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 disabled:opacity-40 text-zinc-100 text-xs font-semibold transition">
                  {{ aEnviarComp ? 'A enviar…' : 'Enviar' }}
                </button>
                <span v-if="erroComp" class="w-full text-[11px] text-red-400">{{ erroComp }}</span>
              </span>
            </span>
          </li>
        </ul>
      </div>

      <!-- ficha de adesão (só para quem pede a adesão pela Bendi) -->
      <details v-if="modoAtual === 'pedido'" class="mb-5 rounded-xl border border-zinc-800" data-teste="vinti4-ficha">
        <summary class="px-4 py-3 text-sm text-zinc-300 cursor-pointer select-none">Dados para a ficha de adesão da SISP</summary>
        <div class="px-4 pb-4 space-y-3">
          <p class="text-[11px] text-zinc-500">
            Copia estes dados para a ficha "Pedido de adesão ao serviço de pagamento online na web" e entrega-a na SISP
            com a licença comercial (ou certidão comercial) e o documento de identificação de quem assina.
          </p>
          <dl class="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-1.5 text-xs">
            <template v-for="f in d.ficha" :key="f.campo">
              <dt class="text-zinc-500">{{ f.campo }}</dt>
              <dd class="sm:col-span-2 break-words" :class="f.valor ? 'text-zinc-200' : 'text-amber-400'">{{ f.valor || 'em falta' }}</dd>
            </template>
          </dl>
          <button type="button" @click="copiar" class="text-xs text-red-400 hover:text-red-300" data-teste="vinti4-copiar">
            {{ copiado ? 'Copiado ✓' : 'Copiar tudo' }}
          </button>
        </div>
      </details>

      <button v-if="!d.adesao && modo === 'pedido'" type="button" @click="pedir('pedir')" :disabled="!d.pode_pedir || aGuardar" data-teste="vinti4-pedir"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold transition">
        Já entreguei o pedido na SISP
      </button>
      <button v-else-if="!d.adesao" type="button" @click="pedir('contrato')" :disabled="!d.pode_contrato || aGuardar" data-teste="vinti4-contrato"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold transition">
        Continuar e pôr as credenciais
      </button>

      <!-- credenciais -->
      <template v-else>
        <button v-if="!editar" type="button" @click="abrir" data-teste="vinti4-credenciais"
          class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-semibold transition">
          {{ d.adesao.pos_id ? 'Alterar credenciais' : 'Pôr as credenciais da SISP' }}
        </button>
        <form v-else @submit.prevent="guardar" class="space-y-4" data-teste="vinti4-form">
          <p class="text-[11px] text-zinc-500">
            São os dados que a SISP te envia depois de aprovar a adesão. Ao guardar, o cartão fica parado até a Bendi
            os validar; recebes um email.
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-pos">POS ID</label>
              <input id="v4-pos" v-model="form.pos_id" autocomplete="off" maxlength="40" data-teste="vinti4-pos"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono focus:outline-none focus:border-red-500 transition" />
              <p v-if="erros.pos_id" class="mt-1 text-xs text-red-400">{{ erros.pos_id }}</p>
            </div>
            <div>
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-merchant">Merchant ID</label>
              <input id="v4-merchant" v-model="form.merchant_id" autocomplete="off" maxlength="40" data-teste="vinti4-merchant"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono focus:outline-none focus:border-red-500 transition" />
              <p v-if="erros.merchant_id" class="mt-1 text-xs text-red-400">{{ erros.merchant_id }}</p>
            </div>
            <div class="sm:col-span-2">
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-chave">Chave (posAutCode)</label>
              <input id="v4-chave" v-model="form.chave" type="password" autocomplete="off" maxlength="200" data-teste="vinti4-chave"
                :placeholder="d.adesao.chave_definida ? 'guardada — cola de novo para mudar' : ''"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono placeholder-zinc-600 focus:outline-none focus:border-red-500 transition" />
              <p v-if="erros.chave" class="mt-1 text-xs text-red-400">{{ erros.chave }}</p>
              <p v-else class="mt-1 text-[11px] text-zinc-600">Fica cifrada e nunca é mostrada — nem a ti, nem à equipa da Bendi.</p>
            </div>
            <div v-if="d.pede_password" class="sm:col-span-2">
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-password">A tua password (para confirmar)</label>
              <input id="v4-password" v-model="form.password" type="password" autocomplete="current-password" data-teste="vinti4-password"
                class="w-full sm:w-72 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
              <p v-if="erros.password" class="mt-1 text-xs text-red-400">{{ erros.password }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button type="submit" :disabled="aGuardar" data-teste="vinti4-guardar"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold transition">
              {{ aGuardar ? 'A guardar…' : 'Guardar credenciais' }}
            </button>
            <button type="button" @click="editar = false" class="text-sm text-zinc-400 hover:text-zinc-200">Cancelar</button>
          </div>
        </form>

        <!-- Portal do Comerciante (opcional): a Bendi pergunta à SISP pelos pagamentos que ficaram sem resposta -->
        <div v-if="d.adesao.pos_id" class="mt-5 pt-4 border-t border-zinc-800" data-teste="vinti4-portal">
          <p class="text-xs text-zinc-400">
            Portal do Comerciante: <span class="text-zinc-200">{{ d.adesao.portal_definido ? `ligado (${d.adesao.portal_id})` : 'não indicado' }}</span>
          </p>
          <p class="text-[11px] text-zinc-500 mt-0.5">
            Opcional. Com ele confirmamos sozinhos os pagamentos em que o cliente não voltou da página da SISP.
            Os estornos (reembolsos) fazes tu nesse portal.
          </p>
          <button v-if="!editarPortal" type="button" @click="abrirPortal" data-teste="vinti4-portal-abrir"
            class="mt-2 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">
            {{ d.adesao.portal_definido ? 'Alterar' : 'Indicar o acesso' }}
          </button>
          <form v-else @submit.prevent="guardarPortal" class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-portal-id">Portal ID</label>
              <input id="v4-portal-id" v-model="portal.portal_id" autocomplete="off" maxlength="60" data-teste="vinti4-portal-id"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono focus:outline-none focus:border-red-500" />
              <p v-if="erros.portal_id" class="mt-1 text-xs text-red-400">{{ erros.portal_id }}</p>
            </div>
            <div>
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-portal-pw">Password do portal</label>
              <input id="v4-portal-pw" v-model="portal.portal_password" type="password" autocomplete="off" maxlength="200" data-teste="vinti4-portal-password"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono focus:outline-none focus:border-red-500" />
              <p v-if="erros.portal_password" class="mt-1 text-xs text-red-400">{{ erros.portal_password }}</p>
              <p v-else class="mt-1 text-[11px] text-zinc-600">Fica cifrada e nunca é mostrada. Deixa os dois vazios para apagar.</p>
            </div>
            <div v-if="d.pede_password" class="sm:col-span-2">
              <label class="text-xs text-zinc-500 mb-1 block" for="v4-portal-conf">A tua password (para confirmar)</label>
              <input id="v4-portal-conf" v-model="portal.password" type="password" autocomplete="current-password"
                class="w-full sm:w-72 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
              <p v-if="erros.password" class="mt-1 text-xs text-red-400">{{ erros.password }}</p>
            </div>
            <div class="sm:col-span-2 flex items-center gap-3">
              <button type="submit" :disabled="aGuardar" data-teste="vinti4-portal-guardar"
                class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
                {{ aGuardar ? 'A guardar…' : 'Guardar acesso' }}
              </button>
              <button type="button" @click="editarPortal = false" class="text-sm text-zinc-400 hover:text-zinc-200">Cancelar</button>
            </div>
          </form>
        </div>
      </template>
      <p v-if="erroGeral" class="mt-3 text-xs text-red-400" data-teste="vinti4-erro">{{ erroGeral }}</p>
      <p v-if="guardado" class="mt-3 text-xs text-green-500" data-teste="vinti4-guardado">{{ guardado }}</p>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { ouvirListas } from '@/utils/tempoRealEncomendas'

const COR = {
  pedida: 'bg-sky-500/15 text-sky-400', por_validar: 'bg-amber-500/15 text-amber-300', teste: 'bg-violet-500/15 text-violet-300',
  ativa: 'bg-green-500/15 text-green-400', suspensa: 'bg-red-500/15 text-red-400',
}
const TEXTO = {
  pedida: 'Pedido entregue na SISP. Quando a SISP aprovar, põe aqui as credenciais que te enviarem.',
  pedida_contrato: 'Põe aqui as credenciais do teu contrato vinti4 (POS ID, Merchant ID e chave).',
  por_validar: 'Credenciais recebidas — a Bendi vai validá-las com a SISP.',
  teste: 'Em testes com a SISP. O cartão ainda não aparece aos clientes.',
  ativa: 'Ativo: os clientes podem pagar com cartão e o dinheiro vai direto para a tua conta.',
  suspensa: 'Suspenso: o cartão não aparece aos clientes.',
}

const MODOS = [{ v: 'pedido', t: 'Ainda não' }, { v: 'contrato', t: 'Sim, já tenho' }]

export default {
  name: 'SeccaoVinti4',

  props: {
    lojaId: { type: [String, Number], required: true },
  },

  emits: ['alterado'],

  computed: {
    // depois de escolher o caminho, manda o da adesão; antes, o que o dono escolheu
    modoAtual () { return this.d?.adesao?.modo || this.modo },
    requisitosAtuais () {
      return (this.modoAtual === 'contrato' ? this.d?.requisitos_contrato : this.d?.requisitos) || []
    },
  },

  data () {
    return {
      COR, TEXTO, MODOS,
      modo: 'pedido', comprovativo: null, aEnviarComp: false, erroComp: '',
      carregando: true, d: null, editar: false, aGuardar: false, guardado: '', copiado: false,
      form: { pos_id: '', merchant_id: '', chave: '', password: '' }, erros: {}, erroGeral: '',
      editarPortal: false, portal: { portal_id: '', portal_password: '', password: '' },
    }
  },

  async created () {
    this.pararTempoReal = ouvirListas('loja', () => this.recarregar(), { lojaId: this.lojaId })
    try {
      this.d = (await api.get(`/app/loja/${this.lojaId}/vinti4/`)).data
    } catch (e) { this.erroGeral = e.response?.data?.detail || '' }
    finally { this.carregando = false }
  },

  beforeUnmount () { this.pararTempoReal?.() },

  methods: {
    // em silêncio: guardar o NIF ou os contactos, ou a Bendi aprovar um documento, atualiza os requisitos sem refresh
    async recarregar () {
      if (this.aGuardar) return
      try { this.d = (await api.get(`/app/loja/${this.lojaId}/vinti4/`)).data } catch { /* fica o que estava */ }
    },

    abrir () {
      const a = this.d.adesao || {}
      this.form = { pos_id: a.pos_id || '', merchant_id: a.merchant_id || '', chave: '', password: '' }
      this.erros = {}; this.erroGeral = ''; this.guardado = ''
      this.editar = true
    },

    async pedir (acao) {
      this.aGuardar = true; this.erroGeral = ''; this.guardado = ''
      try {
        this.d = (await api.post(`/app/loja/${this.lojaId}/vinti4/`, { acao })).data
        this.$emit('alterado')
        if (acao === 'contrato') this.abrir()         // segue logo para as credenciais
        else this.guardado = 'Registado ✓'
      } catch (e) { this.erroGeral = e.response?.data?.detail || 'Não foi possível registar.' }
      finally { this.aGuardar = false }
    },

    escolherComprovativo (e) {
      this.comprovativo = e.target.files?.[0] || null
      this.erroComp = ''
      if (this.comprovativo && this.comprovativo.size > 10 * 1024 * 1024) {
        this.erroComp = 'O ficheiro tem mais de 10 MB.'
        this.comprovativo = null
        e.target.value = ''
      }
    },

    // vai para os Documentos da loja (privado; a Bendi aprova-o antes de ligar o cartão)
    async enviarComprovativo () {
      if (!this.comprovativo) return
      this.aEnviarComp = true; this.erroComp = ''
      const corpo = new FormData()
      corpo.append('tipo', 'contrato_sisp')
      corpo.append('ficheiro', this.comprovativo)
      try {
        await api.post(`/app/loja/${this.lojaId}/documentos/`, corpo)
        this.comprovativo = null
        await this.recarregar()
        this.$emit('alterado')
      } catch (e) { this.erroComp = e.response?.data?.detail || 'Não foi possível enviar o ficheiro.' }
      finally { this.aEnviarComp = false }
    },

    async guardar () {
      this.aGuardar = true; this.erros = {}; this.erroGeral = ''; this.guardado = ''
      try {
        this.d = (await api.put(`/app/loja/${this.lojaId}/vinti4/`, this.form)).data
        this.editar = false
        this.guardado = 'Guardado ✓ — enviámos-te um email a confirmar.'
        this.$emit('alterado')
      } catch (e) {
        const r = e.response?.data
        if (r && typeof r === 'object' && !r.detail) this.erros = r
        else this.erroGeral = r?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false; this.form.password = '' }
    },

    abrirPortal () {
      this.portal = { portal_id: this.d.adesao?.portal_id || '', portal_password: '', password: '' }
      this.erros = {}; this.erroGeral = ''; this.guardado = ''
      this.editarPortal = true
    },

    async guardarPortal () {
      this.aGuardar = true; this.erros = {}; this.erroGeral = ''; this.guardado = ''
      try {
        this.d = (await api.post(`/app/loja/${this.lojaId}/vinti4/`, { acao: 'portal', ...this.portal })).data
        this.editarPortal = false
        this.guardado = 'Acesso ao portal guardado ✓'
      } catch (e) {
        const r = e.response?.data
        if (r && typeof r === 'object' && !r.detail) this.erros = r
        else this.erroGeral = r?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false; this.portal.password = ''; this.portal.portal_password = '' }
    },

    async copiar () {
      try {
        await navigator.clipboard.writeText(this.d.ficha.map(f => `${f.campo}: ${f.valor || ''}`).join('\n'))
        this.copiado = true
        setTimeout(() => { this.copiado = false }, 2000)
      } catch { /* sem acesso à área de transferência */ }
    },
  },
}
</script>
