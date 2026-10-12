<template>
  <!-- coração: guarda/retira dos favoritos. variante "imagem" = redondo sobre a foto do card;
       "pilula" = coração + texto, herda a cor do texto do template (cabeçalho da loja) -->
  <!-- dentro de cards que já são <button> usa-se elemento="span" (botão dentro de botão não é HTML válido) -->
  <component :is="elemento" v-if="idValido" :type="elemento === 'button' ? 'button' : null"
          :role="elemento === 'button' ? null : 'button'" :tabindex="elemento === 'button' ? null : 0"
          @keydown.enter.stop.prevent="alternar" @keydown.space.stop.prevent="alternar"
          :aria-label="activo ? `Retirar ${rotulo} dos favoritos` : `Guardar ${rotulo} nos favoritos`"
          :title="activo ? 'Retirar dos favoritos' : 'Guardar nos favoritos'"
          :aria-pressed="activo ? 'true' : 'false'"
          :class="['fav-btn inline-flex items-center justify-center rounded-full transition-transform active:scale-90',
                   variante === 'imagem' ? 'fav-btn--imagem' : '',
                   variante === 'pilula' ? 'fav-btn--pilula' : '',
                   pulsar ? 'fav-btn--pulsar' : '']"
          :style="variante === 'pilula' ? null : { width: tamanho + 'px', height: tamanho + 'px' }"
          @click.stop.prevent="alternar">
    <svg viewBox="0 0 24 24" :width="Math.round(tamanho * 0.55)" :height="Math.round(tamanho * 0.55)" aria-hidden="true">
      <path d="M12 21s-7.5-4.6-9.6-9.2C1 8.6 3 5 6.6 5c2 0 3.4 1.1 4.4 2.4C12 6.1 13.4 5 15.4 5 19 5 21 8.6 21.6 11.8 19.5 16.4 12 21 12 21z"
            :fill="activo ? '#ef4444' : 'none'" :stroke="activo ? '#ef4444' : corContorno" stroke-width="2" stroke-linejoin="round" />
    </svg>
    <span v-if="variante === 'pilula'">{{ activo ? 'Loja guardada' : 'Guardar loja' }}</span>
  </component>
</template>

<script>
import { favoritos, eFavorito, alternarFavorito, garantirFavoritos } from '@/services/favoritos'

export default {
  name: 'BotaoFavorito',
  props: {
    tipo:     { type: String, default: 'produto' },          // produto | loja
    id:       { type: [Number, String], default: null },
    variante: { type: String, default: 'imagem' },           // imagem | simples | pilula
    tamanho:  { type: Number, default: 34 },
    isDark:   { type: Boolean, default: true },
    elemento: { type: String, default: 'button' },         // button | span
  },

  data () {
    return { favoritos, pulsar: false }
  },

  computed: {
    // a pré-visualização de templates usa ids fictícios — sem coração
    idValido () { return /^\d+$/.test(String(this.id ?? '')) },
    activo () { return eFavorito(this.tipo, this.id) },   // o Set dentro de reactive() é seguido pelo Vue
    rotulo () { return this.tipo === 'loja' ? 'a loja' : 'o produto' },
    corContorno () {
      if (this.variante === 'imagem') return '#ffffff'
      if (this.variante === 'pilula') return 'currentColor'
      return this.isDark ? '#a1a1aa' : '#52525b'
    },
  },

  mounted () { garantirFavoritos() },

  methods: {
    async alternar () {
      const ok = await alternarFavorito(this.tipo, this.id)
      if (ok && this.activo) {
        this.pulsar = true
        setTimeout(() => { this.pulsar = false }, 350)
      }
    },
  },
}
</script>

<style scoped>
.fav-btn { cursor: pointer; flex-shrink: 0; }
.fav-btn--imagem { background: rgba(0, 0, 0, .38); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.fav-btn--imagem:hover { background: rgba(0, 0, 0, .55); }
.fav-btn--pilula {
  gap: 7px; padding: 7px 14px 7px 11px; font-size: 13px; font-weight: 600; line-height: 1;
  color: inherit; border: 1px solid color-mix(in srgb, currentColor 35%, transparent);
  background: color-mix(in srgb, currentColor 6%, transparent);
}
.fav-btn--pilula:hover { background: color-mix(in srgb, currentColor 12%, transparent); }
.fav-btn--pulsar { animation: fav-pulsar .35s ease-out; }
@keyframes fav-pulsar { 0% { transform: scale(1); } 45% { transform: scale(1.25); } 100% { transform: scale(1); } }
</style>
