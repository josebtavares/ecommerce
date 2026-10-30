<!-- AvisoConfirmarEmail.vue — "confirma o teu email" com o botão para reenviar o link (services/confirmarEmail.js).
     faixa: cartão flutuante em todas as páginas (App.vue) enquanto a conta estiver por confirmar.
     bloco: dentro de uma página (ex.: criar loja), com mais explicação. -->
<template>
  <!-- cartão no canto de baixo à esquerda: no topo ficava por baixo dos botões fixos das páginas;
       à direita fica o balão do chat -->
  <div v-if="faixa" role="status"
       class="fixed z-40 bottom-4 left-4 right-20 sm:right-auto sm:max-w-sm rounded-2xl border border-amber-200 bg-amber-50 text-amber-900 shadow-lg"
       data-teste="aviso-confirmar-email">
    <div class="p-3.5 pr-9 text-xs sm:text-sm relative">
      <button type="button" @click="$emit('fechar')" aria-label="Fechar aviso"
        class="absolute top-2 right-2 w-6 h-6 rounded-full text-amber-700 hover:bg-amber-100 hover:text-amber-900">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>
      <p class="font-bold flex items-center gap-2">
        <font-awesome-icon :icon="['fas', 'envelope']" class="text-amber-600" /> Confirma o teu email
      </p>
      <p class="mt-1 leading-snug">
        Abre o link que enviámos<template v-if="email"> para <b class="font-semibold break-all">{{ email }}</b></template>
        para poderes encomendar, marcar e criar uma loja.
      </p>
      <p v-if="mensagem" class="mt-2 font-semibold" :class="ok ? 'text-green-700' : 'text-red-700'" data-teste="aviso-confirmar-msg">{{ mensagem }}</p>
      <button v-else type="button" @click="reenviar" :disabled="aEnviar"
        class="mt-2 font-semibold underline underline-offset-2 hover:text-amber-700 disabled:opacity-60" data-teste="aviso-confirmar-reenviar">
        {{ aEnviar ? 'A enviar…' : 'Reenviar email' }}
      </button>
    </div>
  </div>

  <div v-else class="rounded-2xl border p-5 text-left"
       :class="isDark ? 'bg-zinc-900 border-amber-500/30' : 'bg-amber-50 border-amber-200'" data-teste="bloco-confirmar-email">
    <p class="text-sm font-bold" :class="isDark ? 'text-amber-300' : 'text-amber-800'">Confirma o teu email</p>
    <p class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
      <slot>Enviámos um link para <b class="break-all">{{ email || 'o teu email' }}</b>. Abre-o para confirmares que o email é teu.</slot>
      Não o encontras? Vê na pasta de spam ou pede outro.
    </p>
    <div class="mt-3 flex flex-wrap items-center gap-3">
      <button type="button" @click="reenviar" :disabled="aEnviar"
        class="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-red-600 hover:bg-red-500 disabled:opacity-60" data-teste="bloco-confirmar-reenviar">
        {{ aEnviar ? 'A enviar…' : 'Reenviar email' }}
      </button>
      <span v-if="mensagem" class="text-sm font-semibold" :class="ok ? 'text-green-600' : 'text-red-500'">{{ mensagem }}</span>
    </div>
  </div>
</template>

<script>
import { reenviarLink, atualizarGuardado, utilizadorGuardado } from '@/services/confirmarEmail'

export default {
  name: 'AvisoConfirmarEmail',
  props: {
    faixa:  { type: Boolean, default: false },
    isDark: { type: Boolean, default: false },
  },
  emits: ['fechar'],

  data () {
    return { aEnviar: false, mensagem: '', ok: false, email: utilizadorGuardado()?.email || '' }
  },

  methods: {
    async reenviar () {
      this.aEnviar = true; this.mensagem = ''
      try {
        const { data } = await reenviarLink()
        this.ok = true
        this.mensagem = data.detail || 'Email enviado.'
        if (data.email_confirmado) atualizarGuardado({ email_confirmado: true })
      } catch (e) {
        this.ok = false
        this.mensagem = e.response?.data?.detail || 'Não foi possível enviar. Tenta mais tarde.'
      } finally { this.aEnviar = false }
    },
  },
}
</script>
