<template>
  <!-- Selo "Aberta · fecha às 22:00" / "Fechada · abre amanhã às 08:00" no cabeçalho da loja.
       Herda a cor do texto do template (como o "Guardar loja"); clicar mostra o horário da semana.
       Lojas sem horário (abertas 24h) não mostram nada. -->
  <div v-if="atual && atual.ativo" ref="raiz" class="estado-loja">
    <button type="button" class="estado-loja__pilula" :aria-expanded="aberto ? 'true' : 'false'"
            aria-haspopup="dialog" :title="atual.texto" @click.stop="alternar">
      <span class="estado-loja__ponto" :class="atual.aberta ? 'is-aberta' : 'is-fechada'" aria-hidden="true"></span>
      <span class="estado-loja__texto">{{ atual.texto }}</span>
      <svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true" class="estado-loja__seta" :class="{ 'is-rodada': aberto }">
        <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <!-- no body: os cabeçalhos dos templates cortam o que sai deles (overflow hidden) -->
    <Teleport to="body">
      <div v-if="aberto" class="estado-loja__painel" :style="posicao"
           role="dialog" aria-label="Horário da loja" @click.stop>
        <p v-if="atual.aviso" class="estado-loja__aviso">{{ atual.aviso }}</p>
        <template v-if="atual.semana?.length">
          <p class="estado-loja__titulo">Horário</p>
          <ul>
            <li v-for="d in atual.semana" :key="d.dia" :class="{ 'is-hoje': d.dia === atual.hoje }">
              <span class="estado-loja__dia">{{ d.nome }}<small v-if="d.dia === atual.hoje"> · hoje</small></span>
              <span class="estado-loja__horas">{{ horasDoDia(d) }}</span>
            </li>
          </ul>
        </template>
        <template v-if="atual.excecoes?.length">
          <p class="estado-loja__titulo estado-loja__titulo--sep">Dias especiais</p>
          <ul>
            <li v-for="e in atual.excecoes" :key="e.inicio">
              <span class="estado-loja__dia">{{ e.texto.split(': ')[0] }}<small v-if="e.mensagem" class="estado-loja__msg"> · {{ e.mensagem }}</small></span>
              <span class="estado-loja__horas">{{ e.texto.split(': ')[1] }}</span>
            </li>
          </ul>
        </template>
        <p v-if="atual.ultima_encomenda" class="estado-loja__nota">
          Aceita encomendas até {{ atual.ultima_encomenda }} min antes de fechar.
        </p>
        <p v-if="!atual.aberta" class="estado-loja__nota">
          <template v-if="atual.fora_horario === 'agendar' && atual.abre_em">
            Podes encomendar já — a loja prepara a tua encomenda quando abrir.
          </template>
          <template v-else>Esta loja só aceita encomendas dentro do horário.</template>
        </p>
      </div>
    </Teleport>
  </div>
</template>

<script>
import api from '@/services/api'
import { horasDoDia } from './horario'

const LARGURA = 280
const MARGEM = 16

export default {
  name: 'EstadoLoja',
  props: {
    horario: { type: Object, default: null },            // loja.horario (API pública)
    lojaId:  { type: [Number, String], default: null },  // para actualizar quando abre/fecha
  },

  data () {
    return { atual: this.horario, aberto: false, timer: null, posicao: {} }
  },

  watch: {
    horario (v) { this.atual = v; this.agendar() },
  },

  mounted () {
    this.agendar()
    document.addEventListener('click', this.fechar)
    document.addEventListener('keydown', this.esc)
    window.addEventListener('scroll', this.fechar, { passive: true })
    window.addEventListener('resize', this.fechar)
  },

  beforeUnmount () {
    clearTimeout(this.timer)
    document.removeEventListener('click', this.fechar)
    document.removeEventListener('keydown', this.esc)
    window.removeEventListener('scroll', this.fechar)
    window.removeEventListener('resize', this.fechar)
  },

  methods: {
    horasDoDia,
    fechar () { this.aberto = false },
    esc (e) { if (e.key === 'Escape') this.aberto = false },

    // painel por baixo do selo, sempre dentro do ecrã
    alternar () {
      if (this.aberto) { this.aberto = false; return }
      const r = this.$refs.raiz.getBoundingClientRect()
      const largura = Math.min(LARGURA, window.innerWidth - 2 * MARGEM)
      const left = Math.max(MARGEM, Math.min(r.left, window.innerWidth - MARGEM - largura))
      // nunca passa do fundo do ecrã (com dias especiais o painel fica comprido) — o resto faz scroll
      const altura = Math.max(180, window.innerHeight - r.bottom - 8 - MARGEM)
      this.posicao = { top: `${r.bottom + 8}px`, left: `${left}px`, width: `${largura}px`, maxHeight: `${altura}px` }
      this.aberto = true
    },

    // à hora de abrir/fechar vai buscar o estado novo (a página pode ficar aberta horas)
    agendar () {
      clearTimeout(this.timer)
      const h = this.atual
      const prox = h?.ativo && (h.aberta ? h.fecha_em : h.abre_em)
      if (!prox || !/^\d+$/.test(String(this.lojaId ?? ''))) return
      const ms = new Date(prox).getTime() - Date.now() + 1500
      if (ms <= 0 || ms > 864e5) return
      this.timer = setTimeout(this.atualizar, ms)
    },
    async atualizar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/`)
        this.atual = data.horario
        this.agendar()
      } catch (e) { /* fica o estado anterior */ }
    },
  },
}
</script>

<style scoped>
.estado-loja { display: inline-block; vertical-align: top; max-width: 100%; }
.estado-loja__pilula {
  display: inline-flex; align-items: center; gap: 7px; padding: 7px 12px 7px 11px; max-width: 100%;
  font-size: 13px; font-weight: 600; line-height: 1; color: inherit; border-radius: 999px; cursor: pointer;
  white-space: nowrap; border: 1px solid color-mix(in srgb, currentColor 35%, transparent);
  background: color-mix(in srgb, currentColor 6%, transparent);
}
.estado-loja__pilula:hover { background: color-mix(in srgb, currentColor 12%, transparent); }
.estado-loja__texto { overflow: hidden; text-overflow: ellipsis; }
.estado-loja__ponto { width: 8px; height: 8px; border-radius: 999px; flex-shrink: 0; }
.estado-loja__ponto.is-aberta  { background: #22c55e; box-shadow: 0 0 0 3px rgba(34, 197, 94, .25); }
.estado-loja__ponto.is-fechada { background: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, .25); }
.estado-loja__seta { opacity: .7; flex-shrink: 0; transition: transform .15s; }
.estado-loja__seta.is-rodada { transform: rotate(180deg); }

/* painel com cores próprias — legível em qualquer template */
.estado-loja__painel {
  position: fixed; z-index: 60; padding: 14px 16px; overflow-y: auto; overscroll-behavior: contain; border-radius: 16px; background: #fff; color: #18181b;
  text-align: left; box-shadow: 0 18px 40px rgba(0, 0, 0, .25); border: 1px solid #e4e4e7;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.estado-loja__titulo { font-size: 11px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: #71717a; margin: 0 0 8px; }
.estado-loja__painel ul { list-style: none; margin: 0; padding: 0; }
.estado-loja__painel li { display: flex; justify-content: space-between; gap: 12px; padding: 5px 0; font-size: 13px; border-top: 1px solid #f4f4f5; }
.estado-loja__painel li:first-child { border-top: 0; }
.estado-loja__painel li.is-hoje { font-weight: 700; }
.estado-loja__dia small { font-weight: 600; color: #16a34a; }
.estado-loja__horas { text-align: right; color: #3f3f46; }
.estado-loja__titulo--sep { margin-top: 12px; }
.estado-loja__aviso { margin: 0 0 10px; font-size: 13px; font-weight: 700; color: #b45309; background: #fffbeb; border-radius: 10px; padding: 8px 10px; }
.estado-loja__msg { font-weight: 500; color: #71717a; }
.estado-loja__nota { margin: 10px 0 0; font-size: 12px; line-height: 1.4; color: #52525b; background: #fafafa; border-radius: 10px; padding: 8px 10px; }
</style>
