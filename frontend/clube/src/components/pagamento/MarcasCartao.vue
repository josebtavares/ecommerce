<template>
  <!-- Logótipos oficiais das marcas aceites (pacote da SISP, pasta "g"; checklist "Validação de site do
       Merchant", ponto 2: vinti4, Visa, Mastercard e Amex). O do Mastercard ID Check tem letras brancas: vai sempre num fundo escuro. -->
  <div class="flex items-center flex-wrap" :class="pequeno ? 'gap-1.5' : 'gap-2'" aria-label="Cartões aceites"
       data-teste="marcas-cartao">
    <span class="rounded-md flex items-center" :style="CLARO" :class="pequeno ? 'px-1 h-6' : 'px-1.5 h-8'">
      <img src="/img/cartoes/vinti4.png" alt="rede vinti4" :class="pequeno ? 'h-5' : 'h-7'" class="w-auto" loading="lazy" />
    </span>
    <span class="rounded-md flex items-center" :style="CLARO" :class="pequeno ? 'px-1 h-6' : 'px-1.5 h-8'">
      <img src="/img/cartoes/visa-secure.png" alt="Visa Secure" :class="pequeno ? 'h-5' : 'h-7'" class="w-auto" loading="lazy" />
    </span>
    <span class="rounded-md flex items-center" :style="ESCURO" :class="pequeno ? 'px-1 h-6' : 'px-1.5 h-8'">
      <img src="/img/cartoes/mastercard-idcheck.png" alt="Mastercard ID Check" :class="pequeno ? 'h-4' : 'h-6'" class="w-auto" loading="lazy" />
    </span>
    <span class="rounded-md flex items-center" :style="CLARO" :class="pequeno ? 'px-1 h-6' : 'px-1.5 h-8'">
      <img src="/img/cartoes/amex-safekey.png" alt="American Express SafeKey" :class="pequeno ? 'h-4' : 'h-6'" class="w-auto" loading="lazy" />
    </span>
  </div>
</template>

<script>
export default {
  name: 'MarcasCartao',
  props: { pequeno: { type: Boolean, default: false } },
  // cores fixas (não em classes zinc/stone): o tema claro troca essas paletas e o logótipo ficava ilegível
  data () {
    return { CLARO: 'background:#fff;border:1px solid #e7e5e4', ESCURO: 'background:#18181b;border:1px solid #3f3f46' }
  },
}
</script>
