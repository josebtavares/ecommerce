<template>
  <!-- Onde fica a morada: em Cabo Verde escolhe-se o concelho; fora dele escreve-se a cidade. O código postal é
       opcional. Pagar com cartão pede o concelho/cidade (3DS da SISP — backend utils/geografia.py). -->
  <div class="grid gap-3" :class="colunas ? 'sm:grid-cols-2' : ''" data-teste="campo-localizacao">
    <label class="block">
      <span v-if="rotulos" class="text-xs mb-1 block" :class="classeRotulo">País</span>
      <select :value="valor.pais" @change="mudar('pais', $event.target.value)" :class="classeCampo"
              autocomplete="country" aria-label="País" data-teste="localizacao-pais">
        <option v-for="p in PAISES" :key="p.iso2" :value="p.iso2">{{ p.nome }}</option>
      </select>
    </label>
    <label v-if="emCaboVerde" class="block">
      <span v-if="rotulos" class="text-xs mb-1 block" :class="classeRotulo">Concelho</span>
      <select :value="valor.concelho" @change="mudar('concelho', $event.target.value)" :class="classeCampo"
              aria-label="Concelho" data-teste="localizacao-concelho">
        <option value="">{{ rotulos ? 'Escolhe o concelho' : 'Concelho' }}</option>
        <optgroup v-for="ilha in ilhas" :key="ilha.nome" :label="ilha.nome">
          <option v-for="c in ilha.concelhos" :key="c.codigo" :value="c.codigo">{{ c.nome }}</option>
        </optgroup>
      </select>
    </label>
    <label v-else class="block">
      <span v-if="rotulos" class="text-xs mb-1 block" :class="classeRotulo">Cidade</span>
      <input :value="valor.cidade" @input="mudar('cidade', $event.target.value)" maxlength="60" :class="classeCampo"
             autocomplete="address-level2" :placeholder="rotulos ? '' : 'Cidade'" aria-label="Cidade"
             data-teste="localizacao-cidade" />
    </label>
    <label v-if="comCodigoPostal" class="block" :class="colunas ? 'sm:col-span-2' : ''">
      <span v-if="rotulos" class="text-xs mb-1 block" :class="classeRotulo">Código postal <span class="opacity-70">(opcional)</span></span>
      <input :value="valor.codigo_postal" @input="mudar('codigo_postal', $event.target.value)" maxlength="16"
             :class="classeCampo" autocomplete="postal-code" :placeholder="rotulos ? '' : 'Código postal (opcional)'"
             aria-label="Código postal" data-teste="localizacao-codigo-postal" />
    </label>
  </div>
</template>

<script>
import { PAISES, concelhosPorIlha } from '@/utils/geografia'

export default {
  name: 'CampoLocalizacao',
  props: {
    // { pais, concelho, cidade, codigo_postal }
    modelValue:      { type: Object, required: true },
    classeCampo:     { type: [String, Array, Object], default: '' },
    classeRotulo:    { type: [String, Array, Object], default: '' },
    rotulos:         { type: Boolean, default: true },
    colunas:         { type: Boolean, default: true },
    comCodigoPostal: { type: Boolean, default: true },
  },
  emits: ['update:modelValue'],
  data () {
    return { PAISES }
  },
  computed: {
    valor () {
      const v = this.modelValue || {}
      return { pais: v.pais || 'CV', concelho: v.concelho || '', cidade: v.cidade || '', codigo_postal: v.codigo_postal || '' }
    },
    emCaboVerde () { return this.valor.pais === 'CV' },
    ilhas () { return concelhosPorIlha() },
  },
  methods: {
    mudar (campo, valor) {
      const novo = { ...this.valor, [campo]: valor }
      if (campo === 'pais') {          // mudar de país: o concelho e a cidade de antes já não servem
        novo.concelho = ''
        novo.cidade = ''
      }
      this.$emit('update:modelValue', novo)
    },
  },
}
</script>
