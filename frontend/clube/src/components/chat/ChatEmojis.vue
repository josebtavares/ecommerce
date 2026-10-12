<template>
  <!-- seletor de emojis próprio (sem dependências nem pedidos a CDNs); no telemóvel o teclado já tem emojis -->
  <div class="w-72 rounded-xl border shadow-2xl overflow-hidden"
       :class="isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-gray-200'">
    <div class="flex border-b" :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
      <button v-for="(g, i) in grupos" :key="g.nome" type="button" :title="g.nome"
              class="flex-1 py-2 text-lg transition-colors"
              :class="i === activo ? (isDark ? 'bg-zinc-800' : 'bg-gray-100') : ''"
              @click="activo = i">{{ g.icone }}</button>
    </div>
    <div class="grid grid-cols-8 gap-0.5 p-2 max-h-52 overflow-y-auto">
      <button v-for="e in grupos[activo].emojis" :key="e" type="button"
              class="h-8 w-8 rounded-lg text-xl leading-none transition-colors"
              :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'"
              @click="$emit('escolher', e)">{{ e }}</button>
    </div>
  </div>
</template>

<script>
// Array.from respeita os emojis compostos de um só "carácter" usados aqui
const separar = s => Array.from(s.replace(/\s/g, ''))

export default {
  name: 'ChatEmojis',
  props: { isDark: { type: Boolean, default: true } },
  emits: ['escolher'],
  data () {
    return {
      activo: 0,
      grupos: [
        { nome: 'Caras', icone: '😀', emojis: separar('😀😃😄😁😆😅😂🤣😊😇🙂😉😌😍🥰😘😗😋😛😜🤪😝🤗🤭🤫🤔😐😑😶😏😒🙄😬😮😯😲😳🥺😢😭😤😠😡🤯😱😨😰😥😓😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😎🤓🧐😕😟🙁😣😖😫😩🥱') },
        { nome: 'Gestos', icone: '👍', emojis: separar('👍👎👌🤌🤏✌🤞🤟🤘🤙👈👉👆👇☝✋🤚🖐🖖👋🤝🙏👏🙌👐🤲💪✍💅🤳') },
        { nome: 'Corações', icone: '❤', emojis: separar('❤🧡💛💚💙💜🖤🤍🤎💔💕💞💓💗💖💘💝✨⭐🌟💫🔥💯✅❌⚠❓❗') },
        { nome: 'Compras', icone: '🛍', emojis: separar('🛍🛒💳💰💵🧾📦🚚🛵🏪🏬🎁🏷📱💻⌚👕👖👗👟👜🍔🍕🍰☕🍹🛠') },
      ],
    }
  },
}
</script>
