<template>
  <div
    class="fixed inset-0 z-[60] flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
    @click.self="$emit('close')"
  >
    <div class="flex max-h-[95vh] w-full max-w-lg flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]"
         role="dialog" aria-modal="true" aria-labelledby="pagamento-titulo">

      <!-- Header -->
      <header class="shrink-0 border-b border-slate-200 p-5 sm:p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 id="pagamento-titulo" class="text-2xl font-black text-slate-950">Finalizar pagamento</h2>
            <p class="mt-1 text-sm font-semibold text-slate-500">Conta #{{ conta.id }}</p>
          </div>
          <button
            type="button"
            @click="$emit('close')"
            aria-label="Fechar"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </div>
      </header>

      <!-- Body -->
      <section class="min-h-0 flex-1 overflow-y-auto p-5 sm:p-6">

        <!-- Total -->
        <div class="rounded-[1.5rem] bg-slate-950 p-5 text-white shadow-lg shadow-slate-950/20">
          <div class="space-y-1 text-sm font-bold text-slate-300">
            <div class="flex justify-between"><span>Artigos</span><span>{{ money(c2v(subtotalC)) }}</span></div>
            <div v-if="taxaC" class="flex justify-between">
              <span>Taxa de serviço ({{ conta.taxa_servico_percentagem }}%)</span><span>{{ money(c2v(taxaC)) }}</span>
            </div>
            <div v-if="descontoC" class="flex justify-between text-emerald-300"><span>Desconto</span><span>−{{ money(c2v(descontoC)) }}</span></div>
            <div v-if="gorjetaC" class="flex justify-between"><span>Gorjeta</span><span>{{ money(c2v(gorjetaC)) }}</span></div>
          </div>
          <div class="mt-3 flex items-center justify-between gap-4 border-t border-white/15 pt-3">
            <p class="text-sm font-bold text-slate-300">Total a pagar</p>
            <p class="text-3xl font-black tracking-tight" data-teste="total-pagar">{{ money(c2v(totalC)) }}</p>
          </div>
        </div>

        <!-- Erro -->
        <div v-if="error" class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700" role="alert">
          {{ error }}
        </div>

        <!-- Desconto e gorjeta -->
        <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div v-if="podeDarDescontos">
            <label for="pag-desconto" class="mb-2 block text-sm font-black text-slate-700">Desconto</label>
            <div class="flex gap-2">
              <input id="pag-desconto" v-model.trim="descontoTexto" type="text" inputmode="decimal" placeholder="0"
                     class="h-12 min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10" />
              <div class="flex shrink-0 overflow-hidden rounded-2xl border border-slate-200" role="group" aria-label="Tipo de desconto">
                <button v-for="t in ['valor', 'pct']" :key="t" type="button" @click="descontoTipo = t" :aria-pressed="descontoTipo === t"
                        :class="['h-12 w-12 text-sm font-black transition', descontoTipo === t ? 'bg-slate-950 text-white' : 'bg-white text-slate-600 hover:bg-slate-50']">
                  {{ t === 'pct' ? '%' : '$' }}
                </button>
              </div>
            </div>
            <input v-if="descontoC" v-model.trim="descontoMotivo" type="text" maxlength="200" placeholder="Motivo do desconto (opcional)"
                   aria-label="Motivo do desconto"
                   class="mt-2 h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white" />
          </div>
          <div :class="podeDarDescontos ? '' : 'sm:col-span-2'">
            <label for="pag-gorjeta" class="mb-2 block text-sm font-black text-slate-700">Gorjeta <span class="font-semibold text-slate-400">(opcional)</span></label>
            <input id="pag-gorjeta" v-model.trim="gorjetaTexto" type="text" inputmode="decimal" placeholder="0"
                   class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10" />
          </div>
        </div>

        <!-- Métodos -->
        <div class="mt-5">
          <p class="mb-3 block text-sm font-black text-slate-700">Método de pagamento</p>

          <div class="grid grid-cols-2 gap-3">
            <button
              v-for="metodo in opcoes"
              :key="metodo.value"
              type="button"
              @click="escolherMetodo(metodo.value)"
              :aria-pressed="metodoSelecionado === metodo.value"
              :class="[
                'rounded-[1.25rem] border-2 p-3 text-left transition sm:p-4',
                metodo.value === 'dividida' ? 'col-span-2' : '',
                metodoSelecionado === metodo.value
                  ? 'border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                  : 'border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50'
              ]"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <font-awesome-icon :icon="['fas', metodo.icon]" class="text-xl" />
                  <p class="mt-2 text-sm font-black">{{ metodo.label }}</p>
                  <p :class="['mt-1 text-xs font-semibold', metodoSelecionado === metodo.value ? 'text-slate-300' : 'text-slate-500']">
                    {{ metodo.descricao }}
                  </p>
                </div>
                <div v-if="metodoSelecionado === metodo.value"
                     class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-xs font-black text-white">
                  <font-awesome-icon :icon="['fas', 'check']" />
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- Conta dividida -->
        <div v-if="metodoSelecionado === 'dividida'" class="mt-4 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-teste="partes">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-black text-slate-700">Pessoas</span>
              <button type="button" @click="mudarPessoas(-1)" :disabled="partes.length <= 2" aria-label="Menos uma pessoa"
                      class="h-9 w-9 rounded-xl bg-white text-lg font-black text-slate-700 shadow-sm disabled:opacity-40">−</button>
              <span class="w-6 text-center text-base font-black text-slate-950" aria-live="polite">{{ partes.length }}</span>
              <button type="button" @click="mudarPessoas(1)" :disabled="partes.length >= 20" aria-label="Mais uma pessoa"
                      class="h-9 w-9 rounded-xl bg-white text-lg font-black text-slate-700 shadow-sm disabled:opacity-40">+</button>
            </div>
            <button type="button" @click="dividirIgual" class="h-9 rounded-xl bg-white px-3 text-xs font-black text-slate-700 shadow-sm hover:bg-slate-100">
              Partes iguais
            </button>
          </div>

          <div class="mt-3 space-y-2">
            <div v-for="(p, i) in partes" :key="i" class="grid grid-cols-[auto_1fr_1fr] items-center gap-2">
              <span class="w-14 text-xs font-black text-slate-500">Pessoa {{ i + 1 }}</span>
              <input v-model.trim="p.valor" type="text" inputmode="decimal" :aria-label="`Valor da pessoa ${i + 1}`"
                     class="h-11 min-w-0 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold outline-none focus:border-slate-950" />
              <select v-model="p.metodo" :aria-label="`Método da pessoa ${i + 1}`"
                      class="h-11 min-w-0 rounded-xl border border-slate-200 bg-white px-2 text-sm font-bold text-slate-700 outline-none focus:border-slate-950">
                <option v-for="m in metodosPagamento" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
          </div>

          <p :class="['mt-3 text-sm font-black', faltaC === 0 ? 'text-emerald-700' : 'text-red-700']" aria-live="polite">
            <template v-if="faltaC === 0">As partes somam o total.</template>
            <template v-else-if="faltaC > 0">Falta dividir {{ money(c2v(faltaC)) }}.</template>
            <template v-else>As partes passam {{ money(c2v(-faltaC)) }} do total.</template>
          </p>
        </div>

        <!-- NIF -->
        <div class="mt-5">
          <label for="pag-nif" class="mb-2 block text-sm font-black text-slate-700">
            NIF do cliente
            <span class="font-semibold text-slate-400">(opcional)</span>
          </label>
          <input
            id="pag-nif"
            v-model.trim="nifCliente"
            type="text"
            inputmode="numeric"
            placeholder="Ex: 123456789"
            maxlength="20"
            class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
          />
        </div>
      </section>

      <!-- Footer -->
      <footer class="grid shrink-0 grid-cols-2 gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:p-6">
        <button
          type="button"
          @click="$emit('close')"
          :disabled="processando"
          class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Cancelar
        </button>

        <button
          type="button"
          @click="confirmarPagamento"
          :disabled="!podeConfirmar || processando"
          class="flex h-12 items-center justify-center rounded-2xl bg-emerald-600 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
        >
          <span v-if="!processando">Confirmar {{ money(c2v(totalC)) }}</span>
          <span v-else class="flex items-center gap-2">
            <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
            A processar...
          </span>
        </button>
      </footer>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro, lerCentavos } from '@/utils/dinheiro'
import api from '@/services/api'

// valores em centavos (inteiros) para as somas baterem certo
const paraCentavos = lerCentavos

export default {
  name: 'PagamentoModal',

  props: {
    conta: {
      type: Object,
      required: true
    },
    posId: {
      type: [Number, String],
      required: true
    },
    podeDarDescontos: {
      type: Boolean,
      default: true
    }
  },

  emits: ['close', 'pago'],

  data() {
    return {
      metodoSelecionado: null,
      nifCliente:        '',
      processando:       false,
      error:             '',
      descontoTexto:     '',
      descontoTipo:      'valor',
      descontoMotivo:    '',
      gorjetaTexto:      '',
      partes:            [],

      metodosPagamento: [
        { value: 'dinheiro',      label: 'Dinheiro',      descricao: 'Pagamento em numerário',     icon: 'money-bill-wave' },
        { value: 'cartao',        label: 'Cartão',         descricao: 'Débito ou crédito',          icon: 'credit-card' },
        { value: 'mbway',         label: 'MBWay',          descricao: 'Pagamento via MBWay',        icon: 'mobile-screen-button' },
        { value: 'transferencia', label: 'Transferência',  descricao: 'Transferência bancária',     icon: 'building-columns' },
      ]
    }
  },

  computed: {
    opcoes() {
      return [...this.metodosPagamento,
        { value: 'dividida', label: 'Dividir a conta', descricao: 'Cada pessoa paga uma parte, com o seu método', icon: 'users' }]
    },
    subtotalC() { return Math.round(Number(this.conta.subtotal || 0) * 100) },
    taxaC() { return Math.round(Number(this.conta.taxa_servico_valor || 0) * 100) },
    descontoC() {
      if (!this.podeDarDescontos) return 0
      const v = paraCentavos(this.descontoTexto)
      if (Number.isNaN(v)) return NaN
      if (this.descontoTipo === 'pct') return Math.round((this.subtotalC + this.taxaC) * v / 10000)
      return v
    },
    gorjetaC() { return paraCentavos(this.gorjetaTexto) },
    totalC() {
      const d = Number.isNaN(this.descontoC) ? 0 : this.descontoC
      const g = Number.isNaN(this.gorjetaC) ? 0 : this.gorjetaC
      return Math.max(0, this.subtotalC + this.taxaC + g - d)
    },
    faltaC() {
      const soma = this.partes.reduce((s, p) => s + (paraCentavos(p.valor) || 0), 0)
      return this.totalC - soma
    },
    erroValores() {
      if (Number.isNaN(this.descontoC)) return 'O desconto não é um número válido.'
      if (this.descontoTipo === 'pct' && paraCentavos(this.descontoTexto) > 10000) return 'O desconto não pode passar de 100%.'
      if (this.descontoC > this.subtotalC + this.taxaC) return 'O desconto não pode ser maior do que a conta.'
      if (Number.isNaN(this.gorjetaC)) return 'A gorjeta não é um número válido.'
      if (this.metodoSelecionado === 'dividida') {
        if (this.partes.some(p => Number.isNaN(paraCentavos(p.valor)) || paraCentavos(p.valor) <= 0)) {
          return 'Cada pessoa tem de pagar um valor maior do que zero.'
        }
      }
      return ''
    },
    podeConfirmar() {
      if (!this.metodoSelecionado || this.erroValores) return false
      if (this.metodoSelecionado === 'dividida') return this.faltaC === 0
      return true
    }
  },

  watch: {
    // o total mudou (desconto/gorjeta) → volta a dividir em partes iguais
    totalC() {
      if (this.metodoSelecionado === 'dividida') this.dividirIgual()
    },
    erroValores(v) {
      this.error = v
    }
  },

  methods: {
    c2v(c) {
      return (c || 0) / 100
    },

    escolherMetodo(valor) {
      this.metodoSelecionado = valor
      if (valor === 'dividida' && this.partes.length === 0) {
        this.partes = [{ valor: '', metodo: 'dinheiro' }, { valor: '', metodo: 'dinheiro' }]
        this.dividirIgual()
      }
    },

    mudarPessoas(delta) {
      const n = Math.min(20, Math.max(2, this.partes.length + delta))
      while (this.partes.length < n) this.partes.push({ valor: '', metodo: 'dinheiro' })
      this.partes.splice(n)
      this.dividirIgual()
    },

    // partes iguais ao centavo; o que sobra da divisão vai para as primeiras pessoas
    dividirIgual() {
      const n = this.partes.length
      if (!n) return
      const base = Math.floor(this.totalC / n)
      const resto = this.totalC - base * n
      this.partes.forEach((p, i) => { p.valor = this.c2v(base + (i < resto ? 1 : 0)).toFixed(2).replace('.', ',') })
    },

    async confirmarPagamento() {
      if (!this.podeConfirmar || this.processando) return

      this.processando = true
      this.error       = ''

      const corpo = {
        metodo_pagamento: this.metodoSelecionado,
        nif_cliente:      this.nifCliente || '',
        gorjeta:          this.c2v(this.gorjetaC).toFixed(2),
      }
      if (this.descontoC) {
        corpo.desconto_valor = this.c2v(this.descontoC).toFixed(2)
        corpo.desconto_motivo = this.descontoMotivo
      }
      if (this.metodoSelecionado === 'dividida') {
        corpo.partes = this.partes.map(p => ({ valor: this.c2v(paraCentavos(p.valor)).toFixed(2), metodo: p.metodo }))
      }

      try {
        await api.post(`/api/pos/${this.posId}/contas/${this.conta.id}/fechar/`, corpo)
        this.$emit('pago')
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao processar pagamento.'
      } finally {
        this.processando = false
      }
    },

    money(value) {
      return formatarDinheiro(Number(value || 0))
    }
  }
}
</script>
