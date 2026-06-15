<template>
  <article
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
    :class="[
      'group relative min-h-[170px] overflow-hidden rounded-[1.5rem] border bg-white p-4 text-left shadow-sm transition-all duration-200',
      'hover:-translate-y-1 hover:shadow-xl focus:outline-none focus:ring-4',
      cardClasses
    ]"
  >
    <!-- Brilho decorativo -->
    <div
      :class="[
        'pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full blur-2xl transition-opacity group-hover:opacity-80',
        glowClasses
      ]"
    ></div>

    <!-- Topo: badge de status + botão editar -->
    <div class="relative flex items-start justify-between gap-3">
      <div
        :class="[
          'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide',
          badgeClasses
        ]"
      >
        <span :class="['h-2 w-2 rounded-full', dotClasses]"></span>
        {{ statusText }}
      </div>

      <!-- Botão editar: só visível se tiver permissão para gerir mesas -->
      <button
        v-if="podeGerir"
        type="button"
        class="rounded-xl p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-950"
        title="Editar mesa"
        @click.stop="$emit('editar')"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"
          />
        </svg>
      </button>

      <!-- Placeholder para manter layout quando sem permissão -->
      <div v-else class="h-7 w-7"></div>
    </div>

    <!-- Centro: número e info -->
    <div class="relative mt-5">
      <p class="truncate text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
        {{ mesa.numero }}
      </p>

      <div class="mt-2 flex flex-wrap items-center gap-2 text-xs font-bold text-slate-500">
        <span class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
          👥 {{ mesa.capacidade }} lugares
        </span>

        <span
          v-if="mesa.tem_conta_aberta"
          class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-blue-700"
        >
          🧾 Conta aberta
        </span>
      </div>
    </div>

    <!-- Rodapé: atendente + botão apagar -->
    <div class="relative mt-5 flex items-end justify-between gap-3">
      <div class="min-w-0">
        <p class="text-[11px] font-bold uppercase tracking-wide text-slate-400">Atendente</p>
        <p class="mt-1 truncate text-sm font-black text-slate-700">{{ atendenteNome }}</p>
      </div>

      <!-- Botão apagar: só visível se tiver permissão para gerir mesas -->
      <button
        v-if="podeGerir"
        type="button"
        class="rounded-xl p-2 text-red-500 transition hover:bg-red-50 hover:text-red-700"
        title="Apagar mesa"
        @click.stop="$emit('apagar')"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3m-8 0h10"
          />
        </svg>
      </button>
    </div>
  </article>
</template>

<script>
export default {
  name: 'MesaCard',

  props: {
    mesa: {
      type: Object,
      required: true
    },
    // Passado pelo POSMesas: true = pode editar/apagar
    podeGerir: {
      type: Boolean,
      default: true
    },
    // Passado pelo POSMesas: true = pode clicar para abrir
    podeAbrir: {
      type: Boolean,
      default: true
    }
  },

  emits: ['click', 'editar', 'apagar'],

  computed: {
    statusText() {
      return {
        livre:     'Livre',
        ocupada:   'Ocupada',
        reservada: 'Reservada',
        limpeza:   'Limpeza',
      }[this.mesa.status] || this.mesa.status || 'Indefinido'
    },

    atendenteNome() {
      return this.mesa.atendente_atual?.nome || 'Sem atendente'
    },

    cardClasses() {
      const base = {
        livre:     'border-emerald-200 hover:border-emerald-300 focus:ring-emerald-100',
        ocupada:   'border-blue-200 hover:border-blue-300 focus:ring-blue-100',
        reservada: 'border-amber-200 hover:border-amber-300 focus:ring-amber-100',
        limpeza:   'border-slate-200 hover:border-slate-300 focus:ring-slate-100',
      }[this.mesa.status] || 'border-slate-200 hover:border-slate-300 focus:ring-slate-100'

      // Visual de cursor desativado se não puder abrir
      return this.podeAbrir
        ? base
        : `${base} cursor-not-allowed opacity-70`
    },

    badgeClasses() {
      return {
        livre:     'bg-emerald-50 text-emerald-700',
        ocupada:   'bg-blue-50 text-blue-700',
        reservada: 'bg-amber-50 text-amber-700',
        limpeza:   'bg-slate-100 text-slate-600',
      }[this.mesa.status] || 'bg-slate-100 text-slate-600'
    },

    dotClasses() {
      return {
        livre:     'bg-emerald-500',
        ocupada:   'bg-blue-500',
        reservada: 'bg-amber-500',
        limpeza:   'bg-slate-500',
      }[this.mesa.status] || 'bg-slate-500'
    },

    glowClasses() {
      return {
        livre:     'bg-emerald-300/50',
        ocupada:   'bg-blue-300/50',
        reservada: 'bg-amber-300/50',
        limpeza:   'bg-slate-300/50',
      }[this.mesa.status] || 'bg-slate-300/50'
    },
  }
}
</script>