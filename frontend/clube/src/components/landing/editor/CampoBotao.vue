<!-- CampoBotao.vue — texto e destino de um botão da landing page (editor). Vazio = sem botão.
     Destinos: atalhos (loja, criar loja, entrar, criar conta, secções) ou um link escrito à mão. -->
<template>
  <div class="rounded-xl border border-zinc-800 p-3 space-y-2" :data-teste="'campo-botao-' + nome">
    <p class="text-xs font-semibold text-zinc-300">{{ rotulo }}</p>
    <input :value="modelValue?.texto || ''" @input="mudar('texto', $event.target.value)" maxlength="40" placeholder="Texto (vazio = sem botão)"
           class="campo" :data-teste="'botao-texto-' + nome" />
    <select :value="escolha" @change="escolher($event.target.value)" class="campo" :data-teste="'botao-destino-' + nome">
      <option v-for="d in DESTINOS" :key="d.link" :value="d.link">{{ d.nome }}</option>
      <option value="__outro">Outro link…</option>
    </select>
    <input v-if="escolha === '__outro'" :value="modelValue?.link || ''" @input="mudar('link', $event.target.value.trim())" maxlength="300"
           placeholder="/caminho ou https://…" class="campo" :data-teste="'botao-link-' + nome" />
  </div>
</template>

<script>
export const DESTINOS = [
  { link: '/Home', nome: 'Loja Bende (página inicial)' },
  { link: '/loja/criar', nome: 'Criar loja' },
  { link: '#criar-conta', nome: 'Janela: criar conta' },
  { link: '#entrar', nome: 'Janela: entrar' },
  { link: '#clientes', nome: 'Secção: Para clientes' },
  { link: '#lojas', nome: 'Secção: Para lojas' },
  { link: '#planos', nome: 'Secção: Planos e preços' },
  { link: '#tutoriais', nome: 'Secção: Tutoriais' },
  { link: '#faq', nome: 'Secção: Perguntas frequentes' },
  { link: '#app', nome: 'Secção: Baixar a app' },
  { link: '#contactos', nome: 'Secção: Contactos' },
]

export default {
  name: 'CampoBotao',
  props: {
    modelValue: { type: Object, default: null },
    rotulo: { type: String, default: 'Botão' },
    nome: { type: String, default: 'botao' },
  },
  emits: ['update:modelValue'],
  data () { return { DESTINOS, manual: false } },
  computed: {
    escolha () {
      const l = this.modelValue?.link || '/Home'
      return !this.manual && DESTINOS.some(d => d.link === l) ? l : '__outro'
    },
  },
  methods: {
    // botão sem texto = sem botão (o painel manda null ao gravar)
    mudar (campo, v) {
      this.$emit('update:modelValue', { texto: this.modelValue?.texto || '', link: this.modelValue?.link ?? '/Home', [campo]: v })
    },
    escolher (v) {
      this.manual = v === '__outro'
      if (!this.manual) this.mudar('link', v)
      else this.mudar('link', '')
    },
  },
}
</script>

<style scoped>
.campo { width: 100%; padding: 0.5rem 0.75rem; border-radius: 0.6rem; font-size: 0.85rem; background: #18181b; border: 1px solid #3f3f46; color: #f4f4f5; }
.campo:focus { outline: none; border-color: #ef4444; }
</style>
