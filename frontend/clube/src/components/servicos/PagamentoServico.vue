<template>
  <!-- Pagamento de uma marcação, igual ao checkout das encomendas (contrato SISP, cl.3):
       cartão → página segura da SISP com as marcas aceites; quem vende (contactos e políticas da loja);
       e "Li e aceito os Termos e a Política de devoluções" (fica em Marcacao.termos_aceites_em). -->
  <div class="space-y-3" data-teste="pagamento-servico">
    <div v-if="cartao" class="rounded-xl border px-4 py-3 text-xs leading-relaxed" :class="caixa" data-teste="servico-cartao">
      <MarcasCartao pequeno class="mb-2" />
      <p class="flex items-start gap-2">
        <font-awesome-icon :icon="['fas', 'lock']" class="w-3 h-3 mt-0.5 flex-shrink-0 text-green-500" />
        <span>Pagas na página segura da SISP (vinti4, 3-D Secure), diretamente a <b>{{ loja?.nome || nomeLoja }}</b>.
          Os dados do cartão são introduzidos só na SISP: nem a Bendi nem a loja os veem.
          Valores em escudos (CVE), sem custos adicionais.</span>
      </p>
    </div>

    <div v-if="loja" class="rounded-xl border px-4 py-3" :class="caixa">
      <LojaVendedor :loja="loja" :isDark="isDark" compacto />
    </div>

    <label v-if="termos" class="flex items-start gap-2.5 text-xs leading-relaxed cursor-pointer"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-600'" data-teste="aceitar-termos">
      <input :checked="modelValue" @change="$emit('update:modelValue', $event.target.checked)" type="checkbox"
             class="mt-0.5 w-4 h-4 flex-shrink-0" :style="{ accentColor: cor }" />
      <span>
        Li e aceito os <router-link to="/termos" target="_blank" class="font-semibold hover:underline" :style="{ color: cor }">Termos de Serviço</router-link>
        e a <router-link to="/devolucoes" target="_blank" class="font-semibold hover:underline" :style="{ color: cor }">Política de devoluções</router-link>.
      </span>
    </label>
  </div>
</template>

<script>
import api from '@/services/api'
import LojaVendedor from '@/components/loja/LojaVendedor.vue'
import MarcasCartao from '@/components/pagamento/MarcasCartao.vue'

// a mesma loja não se pede outra vez ao abrir outro serviço
const LOJAS = new Map()

export default {
  name: 'PagamentoServico',
  components: { LojaVendedor, MarcasCartao },
  props: {
    lojaId:     { type: [String, Number], required: true },
    nomeLoja:   { type: String, default: '' },
    cartao:     { type: Boolean, default: false },   // paga-se já, com cartão
    termos:     { type: Boolean, default: true },    // pedir a aceitação (as já aceites não pedem outra vez)
    modelValue: { type: Boolean, default: false },
    isDark:     { type: Boolean, default: true },
    cor:        { type: String, default: '#dc2626' },
  },
  emits: ['update:modelValue'],
  data () {
    return { loja: LOJAS.get(String(this.lojaId)) || null }
  },
  computed: {
    caixa () { return this.isDark ? 'border-zinc-800 bg-zinc-950/40 text-zinc-400' : 'border-gray-200 bg-gray-50 text-zinc-600' },
  },
  async created () {
    if (this.loja) return
    try {
      const { data } = await api.get(`/app/loja/${this.lojaId}/`)
      LOJAS.set(String(this.lojaId), data)
      this.loja = data
    } catch { /* sem o "Vendido por" o resto continua */ }
  },
}
</script>
