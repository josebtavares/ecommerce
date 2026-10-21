<template>
  <!-- Cartão de um serviço (home e pesquisa): abre a página de marcação com o serviço escolhido -->
  <router-link :to="{ path: `/loja/${s.loja.id}/servicos`, query: { servico: s.id } }" :data-teste="`servico-card-${s.id}`"
    class="group flex flex-col rounded-2xl border overflow-hidden transition"
    :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-red-500/50' : 'bg-white border-stone-200 hover:border-red-400 hover:shadow-md'">
    <div class="aspect-[4/3] flex items-center justify-center overflow-hidden" :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'">
      <img v-if="s.imagem" :src="s.imagem" alt="" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition" />
      <font-awesome-icon v-else :icon="['fas', 'calendar-check']" class="text-3xl" :class="isDark ? 'text-zinc-600' : 'text-stone-400'" />
    </div>
    <div class="p-3 flex-1 flex flex-col">
      <p class="font-semibold text-sm leading-tight" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ s.nome }}</p>
      <p class="text-xs mt-0.5" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ duracaoTexto(s.duracao_min) }} · <b>{{ s.preco_texto }}</b></p>
      <div class="flex items-center gap-1.5 mt-auto pt-2">
        <img v-if="s.loja.logo" :src="s.loja.logo" alt="" class="w-5 h-5 rounded-md object-cover" />
        <p class="text-[11px] truncate" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ s.loja.nome }}<template v-if="s.loja.localizacao"> · {{ s.loja.localizacao }}</template></p>
      </div>
    </div>
  </router-link>
</template>

<script>
import { duracaoTexto } from '@/utils/servicos'

export default {
  name: 'ServicoCard',
  props: { s: { type: Object, required: true }, isDark: { type: Boolean, default: true } },
  methods: { duracaoTexto },
}
</script>
