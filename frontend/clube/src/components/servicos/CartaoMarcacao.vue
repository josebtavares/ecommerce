<template>
  <!-- uma marcação do cliente: a mesma na página /minhas-marcacoes e no separador Marcações do perfil -->
  <button type="button" :data-teste="`minha-${m.id}`"
    class="w-full text-left rounded-2xl border p-4 flex gap-3 items-center"
    :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-400'">
    <div class="w-14 text-center flex-shrink-0">
      <p class="text-[10px] uppercase text-zinc-500">{{ DIAS_CURTOS[diaSemana(diaDe(m.inicio))] }}</p>
      <p class="text-xl font-black leading-none">{{ diaDe(m.inicio).slice(8) }}</p>
      <p class="text-[10px] text-zinc-500">{{ MESES_CURTOS[Number(diaDe(m.inicio).slice(5, 7)) - 1] }}</p>
    </div>
    <div class="flex-1 min-w-0">
      <p class="font-semibold truncate">{{ m.servico_nome }} · {{ hora(m.inicio) }}</p>
      <p class="text-xs text-zinc-500 truncate">{{ m.loja_nome }} · com {{ m.profissional_nome }}</p>
      <p class="text-xs mt-0.5" :class="corEstadoCliente(m)">{{ textoEstadoCliente(m) }}</p>
    </div>
    <span v-if="m.por_ler" class="min-w-[20px] h-5 px-1.5 rounded-full bg-red-600 text-white text-[11px] font-bold flex items-center justify-center" aria-label="Mensagens por ler">{{ m.por_ler }}</span>
  </button>
</template>

<script setup>
import { DIAS_CURTOS, MESES_CURTOS, diaDe, diaSemana, hora, textoEstadoCliente, corEstadoCliente } from '@/utils/servicos'

defineProps({ m: { type: Object, required: true }, isDark: { type: Boolean, default: true } })
</script>
