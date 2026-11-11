<template>
  <!-- Pagar com cartão (vinti4) pede o telefone, a morada e o concelho/cidade de quem paga (3DS da SISP).
       O backend responde { codigo: 'dados_cliente', campos: [...] }: isto pede só o que falta, grava no perfil
       (PATCH /app/utilizador/me/editar/) e avisa o pai para tentar outra vez. -->
  <div v-if="campos.length" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('fechar')" data-teste="dados-pagador">
    <form class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md shadow-2xl" @submit.prevent="guardar">
      <div class="px-6 py-4 border-b border-zinc-800">
        <h3 class="text-base font-bold text-zinc-100">Os teus dados para pagar com cartão</h3>
        <p class="text-xs text-zinc-500 mt-1">O banco pede-os para confirmar o pagamento. Ficam guardados no teu perfil.</p>
      </div>
      <div class="p-6 space-y-3">
        <label v-if="campos.includes('telefone')" class="block">
          <span class="text-xs mb-1 block text-zinc-400">Telefone</span>
          <input v-model="telefone" type="tel" autocomplete="tel" maxlength="20" :class="classeCampo" data-teste="dados-pagador-telefone" />
        </label>
        <label v-if="campos.includes('morada')" class="block">
          <span class="text-xs mb-1 block text-zinc-400">Morada</span>
          <input v-model="morada" type="text" autocomplete="street-address" maxlength="255" :class="classeCampo" data-teste="dados-pagador-morada" />
        </label>
        <CampoLocalizacao v-if="campos.includes('cidade')" v-model="localizacao" :classe-campo="classeCampo" classe-rotulo="text-zinc-400" />
        <p v-if="erro" class="text-sm text-red-400" data-teste="dados-pagador-erro">{{ erro }}</p>
      </div>
      <div class="px-6 pb-5 flex justify-end gap-2">
        <button type="button" @click="$emit('fechar')" class="px-4 py-2 rounded-xl text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200">Cancelar</button>
        <button type="submit" :disabled="aGuardar || !completo"
                class="px-4 py-2 rounded-xl text-sm font-semibold bg-red-600 hover:bg-red-500 text-white disabled:opacity-50"
                data-teste="dados-pagador-guardar">{{ aGuardar ? 'A guardar…' : 'Guardar e pagar' }}</button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'
import CampoLocalizacao from '@/components/forms/CampoLocalizacao.vue'
import { localizacaoCompleta, localizacaoDe } from '@/utils/geografia'

export default {
  name: 'DadosPagador',
  components: { CampoLocalizacao },
  props: {
    campos: { type: Array, default: () => [] },     // 'telefone' | 'morada' | 'cidade'
  },
  emits: ['guardado', 'fechar'],
  data () {
    return {
      telefone: '', morada: '', localizacao: { pais: 'CV', concelho: '', cidade: '', codigo_postal: '' },
      aGuardar: false, erro: '',
      classeCampo: 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition',
    }
  },
  computed: {
    completo () {
      return (!this.campos.includes('telefone') || this.telefone.trim().length > 0)
        && (!this.campos.includes('morada') || this.morada.trim().length > 0)
        && (!this.campos.includes('cidade') || localizacaoCompleta(this.localizacao))
    },
  },
  watch: {
    campos () { this.erro = '' },
  },
  methods: {
    async guardar () {
      if (!this.completo) return
      this.aGuardar = true; this.erro = ''
      const fd = new FormData()
      if (this.campos.includes('telefone')) fd.append('telefone', this.telefone.trim())
      if (this.campos.includes('morada')) fd.append('morada', this.morada.trim())
      if (this.campos.includes('cidade')) Object.entries(this.localizacao).forEach(([k, v]) => fd.append(k, (v || '').trim()))
      try {
        const { data } = await api.patch('/app/utilizador/me/editar/', fd)
        try {
          const user = JSON.parse(localStorage.getItem('user') || '{}')
          localStorage.setItem('user', JSON.stringify({ ...user, telefone: data.telefone ?? user.telefone,
                                                        morada: data.morada ?? user.morada, ...localizacaoDe(data) }))
        } catch (e) { /* sem localStorage: fica no servidor */ }
        this.$emit('guardado')
      } catch (e) {
        const d = e.response?.data || {}
        this.erro = [d.telefone, d.morada, d.pais, d.concelho, d.cidade, d.codigo_postal, d.detail].flat().filter(Boolean)[0]
          || 'Não foi possível guardar os teus dados.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
