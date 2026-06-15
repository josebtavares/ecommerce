<template>
  <div
    class="fixed inset-0 z-[60] flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-lg overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">

      <!-- Header -->
      <header class="border-b border-slate-200 p-5 sm:p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-2xl font-black text-slate-950">Finalizar pagamento</h2>
            <p class="mt-1 text-sm font-semibold text-slate-500">Conta #{{ conta.id }}</p>
          </div>
          <button
            type="button"
            @click="$emit('close')"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </div>
      </header>

      <!-- Body -->
      <section class="max-h-[60vh] overflow-y-auto p-5 sm:max-h-none sm:p-6">

        <!-- Total -->
        <div class="rounded-[1.5rem] bg-slate-950 p-5 text-white shadow-lg shadow-slate-950/20">
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="text-sm font-bold text-slate-300">Total a pagar</p>
              <p class="mt-1 text-3xl font-black tracking-tight">{{ money(conta.total) }}</p>
            </div>
            <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-3xl">💳</div>
          </div>
        </div>

        <!-- Erro -->
        <div
          v-if="error"
          class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
        >
          {{ error }}
        </div>

        <!-- Métodos -->
        <div class="mt-5">
          <label class="mb-3 block text-sm font-black text-slate-700">Método de pagamento</label>

          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              v-for="metodo in metodosPagamento"
              :key="metodo.value"
              type="button"
              @click="metodoSelecionado = metodo.value"
              :class="[
                'rounded-[1.25rem] border-2 p-4 text-left transition',
                metodoSelecionado === metodo.value
                  ? 'border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                  : 'border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50'
              ]"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-2xl">{{ metodo.icon }}</div>
                  <p class="mt-2 text-sm font-black">{{ metodo.label }}</p>
                  <p
                    :class="[
                      'mt-1 text-xs font-semibold',
                      metodoSelecionado === metodo.value ? 'text-slate-300' : 'text-slate-500'
                    ]"
                  >
                    {{ metodo.descricao }}
                  </p>
                </div>

                <div
                  v-if="metodoSelecionado === metodo.value"
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-xs font-black text-white"
                >
                  ✓
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- NIF -->
        <div class="mt-5">
          <label class="mb-2 block text-sm font-black text-slate-700">
            NIF do cliente
            <span class="font-semibold text-slate-400">(opcional)</span>
          </label>
          <input
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
      <footer class="grid grid-cols-2 gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:p-6">
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
          :disabled="!metodoSelecionado || processando"
          class="flex h-12 items-center justify-center rounded-2xl bg-emerald-600 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
        >
          <span v-if="!processando">Confirmar</span>
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
import api from '@/services/api'

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
    }
  },

  emits: ['close', 'pago'],

  data() {
    return {
      metodoSelecionado: null,
      nifCliente:        '',
      processando:       false,
      error:             '',

      metodosPagamento: [
        { value: 'dinheiro',      label: 'Dinheiro',      descricao: 'Pagamento em numerário',     icon: '💵' },
        { value: 'cartao',        label: 'Cartão',         descricao: 'Débito ou crédito',          icon: '💳' },
        { value: 'mbway',         label: 'MBWay',          descricao: 'Pagamento via MBWay',        icon: '📱' },
        { value: 'transferencia', label: 'Transferência',  descricao: 'Transferência bancária',     icon: '🏦' },
      ]
    }
  },

  methods: {
    async confirmarPagamento() {
      if (!this.metodoSelecionado || this.processando) return

      this.processando = true
      this.error       = ''

      try {
        await api.post(`/api/pos/${this.posId}/contas/${this.conta.id}/fechar/`, {
          metodo_pagamento: this.metodoSelecionado,
          nif_cliente:      this.nifCliente || ''
        })

        this.$emit('pago')
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao processar pagamento.'
      } finally {
        this.processando = false
      }
    },

    money(value) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(value || 0))
    }
  }
}
</script>