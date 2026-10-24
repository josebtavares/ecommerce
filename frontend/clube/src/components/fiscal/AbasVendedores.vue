<!-- AbasVendedores.vue — fila de abas das lojas (e POS sem loja), como em Admin → Comissões, com procura.
     itens: [{ tipo, id, nome, codigo_pos?, contador }] (já ordenados: pendentes primeiro). ativo: 'loja-12' | 'pos-3' | null.
     Emite 'selecionar' com o item (ou null = "Todas"). -->
<template>
  <div class="flex items-center gap-2" data-teste="abas-vendedores">
    <input v-model.trim="procura" type="search" :placeholder="placeholder" :aria-label="placeholder" data-teste="abas-procurar"
      class="w-36 sm:w-44 flex-shrink-0 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide min-w-0" role="tablist">
      <button type="button" role="tab" :aria-selected="!ativo ? 'true' : 'false'" @click="$emit('selecionar', null)" data-teste="aba-todas"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 !ativo ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        Todas
      </button>
      <button v-for="v in visiveis" :key="v.tipo + v.id" type="button" role="tab" :aria-selected="ativo === `${v.tipo}-${v.id}` ? 'true' : 'false'"
        @click="$emit('selecionar', v)" :data-teste="`aba-${v.tipo}-${v.id}`"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 ativo === `${v.tipo}-${v.id}` ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        <span v-if="v.tipo === 'pos'" class="mr-1 text-[9px] opacity-70">POS</span>{{ v.nome }}
        <span v-if="v.contador" :title="titulo" class="ml-1.5 px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-[9px] font-bold">{{ v.contador }}</span>
      </button>
      <span v-if="procura && !visiveis.length" class="px-2 py-1.5 text-xs text-zinc-500 whitespace-nowrap">Nenhuma loja com "{{ procura }}"</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AbasVendedores',
  props: {
    itens:  { type: Array, required: true },
    ativo:  { type: String, default: null },
    titulo: { type: String, default: '' },          // tooltip do contador
    placeholder: { type: String, default: 'Procurar loja…' },
  },
  emits: ['selecionar'],
  data () {
    return { procura: '' }
  },
  computed: {
    visiveis () {
      const q = this.procura.toLowerCase()
      if (!q) return this.itens
      return this.itens.filter(v => v.nome.toLowerCase().includes(q) || (v.codigo_pos || '').toLowerCase().includes(q))
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
