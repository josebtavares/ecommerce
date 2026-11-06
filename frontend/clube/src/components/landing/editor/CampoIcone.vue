<!-- CampoIcone.vue — ícone de um cartão (nome do Font Awesome, ex.: "truck-fast"), com sugestões e pré-visualização. -->
<template>
  <div>
    <div class="flex items-center gap-2">
      <span class="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0 text-red-400">
        <font-awesome-icon :icon="['fas', valido ? modelValue : 'circle-check']" />
      </span>
      <input :value="modelValue" @input="$emit('update:modelValue', $event.target.value.trim().toLowerCase())" maxlength="40"
             placeholder="ícone (ex.: truck-fast)" class="campo flex-1" data-teste="campo-icone" />
      <button type="button" @click="aberto = !aberto" class="px-2.5 py-2 rounded-lg bg-zinc-800 text-xs text-zinc-300 hover:bg-zinc-700">
        {{ aberto ? 'Fechar' : 'Escolher' }}</button>
    </div>
    <p v-if="modelValue && !valido" class="mt-1 text-[11px] text-amber-400">Ícone desconhecido — aparece um genérico.</p>
    <div v-if="aberto" class="mt-2 grid grid-cols-8 gap-1">
      <button v-for="i in SUGESTOES" :key="i" type="button" :title="i" @click="$emit('update:modelValue', i); aberto = false"
              class="h-9 rounded-lg flex items-center justify-center"
              :class="i === modelValue ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'">
        <font-awesome-icon :icon="['fas', i]" />
      </button>
    </div>
  </div>
</template>

<script>
import { findIconDefinition } from '@fortawesome/fontawesome-svg-core'

const SUGESTOES = ['store', 'shop', 'cart-shopping', 'bag-shopping', 'truck-fast', 'motorcycle', 'box', 'credit-card',
  'money-bill-wave', 'cash-register', 'file-invoice', 'receipt', 'chart-line', 'chart-pie', 'calendar-check', 'calendar-days',
  'clock', 'scissors', 'utensils', 'mobile-screen', 'laptop', 'qrcode', 'magnifying-glass', 'star', 'heart', 'thumbs-up',
  'shield-halved', 'lock', 'headset', 'comments', 'bell', 'users', 'user-tie', 'gift', 'tag', 'percent', 'location-dot',
  'map', 'globe', 'bolt', 'rocket', 'circle-check', 'hand-holding-dollar', 'warehouse', 'boxes-stacked', 'camera', 'image', 'video']

export default {
  name: 'CampoIcone',
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  data () { return { aberto: false, SUGESTOES } },
  computed: {
    valido () { return !!this.modelValue && !!findIconDefinition({ prefix: 'fas', iconName: this.modelValue }) },
  },
}
</script>

<style scoped>
.campo { padding: 0.5rem 0.75rem; border-radius: 0.6rem; font-size: 0.85rem; background: #18181b; border: 1px solid #3f3f46; color: #f4f4f5; min-width: 0; }
.campo:focus { outline: none; border-color: #ef4444; }
</style>
