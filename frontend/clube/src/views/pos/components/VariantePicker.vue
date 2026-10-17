<!-- VariantePicker.vue — escolher opções (tamanho, cor, gelo…) ao adicionar um produto à conta.
     Mesmas regras do card online (utils/variantes.js): opções esgotadas riscadas,
     stock e preço da combinação escolhida. Pensado para toque. -->
<template>
  <div class="fixed inset-0 z-[70] flex items-end justify-center bg-black/50 backdrop-blur-sm sm:items-center sm:p-4"
       @click.self="$emit('close')">
    <div class="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
      <header class="flex items-start gap-3 border-b border-slate-200 p-5">
        <img v-if="produto.imagem_url" :src="produto.imagem_url" class="h-14 w-14 flex-shrink-0 rounded-2xl object-cover" />
        <div class="min-w-0 flex-1">
          <h3 class="truncate text-lg font-black text-slate-950">{{ produto.nome }}</h3>
          <p class="text-lg font-black text-slate-950">
            <span v-if="precoDesde" class="text-xs font-bold text-slate-400">desde </span>{{ money(precoUnitario) }}
          </p>
        </div>
        <button type="button" @click="$emit('close')"
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 hover:bg-slate-200">×</button>
      </header>

      <div class="flex-1 space-y-5 overflow-y-auto p-5">
        <div v-for="a in atributos" :key="a.nome">
          <p class="mb-2 text-xs font-black uppercase tracking-wider text-slate-500">
            {{ a.nome }} <span v-if="a.obrigatorio || a.variante" class="text-red-500">*</span>
          </p>
          <div class="flex flex-wrap gap-2">
            <button v-for="op in a.opcoes" :key="op" type="button"
              @click="escolher(a.nome, op)"
              :disabled="estado(a.nome, op) === 'esgotada'"
              :class="[
                'relative min-h-[48px] min-w-[64px] overflow-hidden rounded-2xl border-2 px-4 text-sm font-black transition',
                escolhas[a.nome] === op
                  ? 'border-slate-950 bg-slate-950 text-white'
                  : estado(a.nome, op) === 'esgotada'
                    ? 'cursor-not-allowed border-slate-100 bg-slate-50 text-slate-300'
                    : estado(a.nome, op) === 'esgotada_combo'
                      ? 'border-dashed border-slate-300 bg-white text-slate-400'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-400'
              ]">
              {{ op }}
              <span v-if="escolhas[a.nome] !== op && estado(a.nome, op) !== 'disponivel'"
                    class="pointer-events-none absolute inset-0 flex items-center justify-center">
                <span class="absolute h-0.5 w-full rotate-[20deg] bg-slate-300"></span>
              </span>
            </button>
          </div>
        </div>

        <!-- Stock -->
        <div class="flex items-center gap-2 text-sm font-bold">
          <span :class="['h-2.5 w-2.5 rounded-full', corStock]"></span>
          <span :class="poucas ? 'text-amber-600' : 'text-slate-500'">{{ textoStock }}</span>
        </div>

        <!-- Quantidade -->
        <div class="flex items-center justify-between rounded-2xl bg-slate-50 p-3">
          <span class="text-sm font-black text-slate-700">Quantidade</span>
          <div class="flex items-center gap-3">
            <button type="button" @click="qty > 1 && qty--" :disabled="qty <= 1"
              class="h-12 w-12 rounded-2xl bg-white text-xl font-black text-slate-700 shadow-sm disabled:opacity-40">−</button>
            <span class="w-8 text-center text-xl font-black text-slate-950">{{ qty }}</span>
            <button type="button" @click="qty < maxQty && qty++" :disabled="qty >= maxQty"
              class="h-12 w-12 rounded-2xl bg-white text-xl font-black text-slate-700 shadow-sm disabled:opacity-40">+</button>
          </div>
        </div>
      </div>

      <footer class="border-t border-slate-200 p-5">
        <p v-if="emFalta.length" class="mb-3 text-center text-xs font-bold text-amber-600">Escolhe: {{ emFalta.join(', ') }}</p>
        <button type="button" @click="confirmar" :disabled="!pode || adding"
          class="h-14 w-full rounded-2xl bg-slate-950 text-base font-black text-white shadow-lg transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40">
          {{ adding ? 'A adicionar…' : `Adicionar · ${money(precoUnitario * qty)}` }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import {
  usaVariantes, atributosVariante, estadoOpcao, escolherOpcao, varianteEscolhida,
  variantesPorEscolher, stockCompativel, intervaloPreco, opcoesDoProduto,
} from '@/utils/variantes'

export default {
  name: 'VariantePicker',
  props: {
    produto: { type: Object, required: true },
    adding:  { type: Boolean, default: false },
  },
  emits: ['close', 'confirmar'],

  data () {
    return { escolhas: {}, qty: 1 }
  },

  computed: {
    atributos () { return opcoesDoProduto(this.produto) },
    comVariantes () { return usaVariantes(this.produto) },
    nomesVariante () { return this.comVariantes ? atributosVariante(this.produto) : [] },
    variante () { return this.comVariantes ? varianteEscolhida(this.produto, this.escolhas) : null },

    emFalta () {
      const obrig = this.atributos.filter(a => a.obrigatorio && !this.escolhas[a.nome]).map(a => a.nome)
      const vars = this.comVariantes ? variantesPorEscolher(this.produto, this.escolhas) : []
      return [...new Set([...vars, ...obrig])]
    },

    stockTotal () { return Number(this.produto.stock ?? 0) },

    maxQty () {
      if (this.comVariantes) return this.variante ? this.variante.quantidade : 1
      return this.produto.controlar_stock ? this.stockTotal : 99
    },

    pode () {
      if (this.emFalta.length) return false
      if (this.comVariantes) return !!this.variante && this.variante.quantidade >= this.qty
      return !this.produto.controlar_stock || this.stockTotal >= this.qty
    },

    intervalo () { return this.comVariantes ? intervaloPreco(this.produto, this.escolhas) : null },
    precoUnitario () {
      if (this.variante) return Number(this.variante.preco_efetivo)
      if (this.intervalo) return this.intervalo.min
      return Number(this.produto.preco)
    },
    precoDesde () { return !this.variante && !!this.intervalo && this.intervalo.min !== this.intervalo.max },

    poucas () {
      const s = this.comVariantes ? this.variante?.quantidade : (this.produto.controlar_stock ? this.stockTotal : null)
      return s !== null && s !== undefined && s > 0 && s <= 5
    },

    textoStock () {
      if (this.comVariantes) {
        if (this.variante) {
          const q = this.variante.quantidade
          return q <= 0 ? 'Esta combinação está esgotada' : q <= 5 ? `Só restam ${q}` : `${q} em stock`
        }
        return `${stockCompativel(this.produto, this.escolhas)} disponíveis · escolhe ${variantesPorEscolher(this.produto, this.escolhas).join(' e ')}`
      }
      if (!this.produto.controlar_stock) return 'Disponível'
      return this.stockTotal <= 0 ? 'Sem stock' : this.poucas ? `Só restam ${this.stockTotal}` : `${this.stockTotal} em stock`
    },

    corStock () {
      if (this.comVariantes && this.variante && this.variante.quantidade <= 0) return 'bg-red-500'
      return this.poucas ? 'bg-amber-500' : 'bg-emerald-500'
    },
  },

  watch: {
    maxQty (m) { if (this.qty > m) this.qty = Math.max(1, m) },
  },

  methods: {
    estado (nome, op) {
      if (!this.nomesVariante.includes(nome)) return 'disponivel'
      return estadoOpcao(this.produto, this.escolhas, nome, op)
    },

    escolher (nome, op) {
      if (this.escolhas[nome] === op) {
        const n = { ...this.escolhas }
        delete n[nome]
        this.escolhas = n
      } else if (this.nomesVariante.includes(nome)) {
        if (this.estado(nome, op) === 'esgotada') return
        this.escolhas = escolherOpcao(this.produto, this.escolhas, nome, op)
      } else {
        this.escolhas = { ...this.escolhas, [nome]: op }
      }
    },

    confirmar () {
      if (!this.pode) return
      this.$emit('confirmar', { atributos: { ...this.escolhas }, quantidade: this.qty })
    },

    money (v) {
      return formatarDinheiro(Number(v || 0))
    },
  },
}
</script>
