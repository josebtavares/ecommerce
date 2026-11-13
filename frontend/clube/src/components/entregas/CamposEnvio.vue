<template>
  <!-- Tipo da opção de entrega (local / envio por transportadora) e, no envio, a transportadora e as ilhas.
       As mudanças saem em @mudar (o pai faz Object.assign na opção) — backend utils/envios.py. -->
  <div class="space-y-3" data-teste="campos-envio">
    <div class="grid grid-cols-2 gap-2">
      <button v-for="t in TIPOS" :key="t.valor" type="button" @click="mudarTipo(t.valor)"
              :data-teste="`opcao-tipo-${t.valor}`"
              :class="['px-3 py-2 rounded-lg border text-left transition',
                       opcao.tipo === t.valor ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <p class="text-xs font-semibold text-zinc-200"><font-awesome-icon :icon="['fas', t.icone]" class="mr-1.5 text-zinc-400" />{{ t.titulo }}</p>
        <p class="text-[10px] text-zinc-500 mt-0.5">{{ t.texto }}</p>
      </button>
    </div>

    <template v-if="opcao.tipo === 'envio'">
      <div>
        <label class="text-[10px] text-zinc-500 mb-1 block">Transportadora</label>
        <select :value="valorTransportadora" @change="mudarTransportadora($event.target.value)"
                data-teste="opcao-transportadora"
                class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition">
          <option value="" disabled>Escolhe a transportadora</option>
          <option v-for="t in transportadoras" :key="t.id" :value="String(t.id)">{{ t.nome }}</option>
          <option value="outra">Outra…</option>
        </select>
        <input v-if="valorTransportadora === 'outra'" :value="opcao.transportadora_outra" @input="set({ transportadora_outra: $event.target.value })" type="text" maxlength="80"
               placeholder="Nome da transportadora" data-teste="opcao-transportadora-outra"
               class="mt-2 w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition" />
      </div>
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="text-[10px] text-zinc-500">Ilhas para onde envias com este preço</label>
          <button type="button" @click="todasMenosAMinha" class="text-[10px] text-red-400 hover:text-red-300">
            {{ ilhaLoja ? 'Todas menos ' + ilhaLoja : 'Todas' }}
          </button>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <button v-for="ilha in ILHAS" :key="ilha" type="button" @click="alternarIlha(ilha)"
                  :data-teste="`opcao-ilha-${ilha}`"
                  :class="['px-2.5 py-1 rounded-full text-[11px] font-semibold transition',
                           (opcao.ilhas || []).includes(ilha) ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
            {{ ilha }}
          </button>
        </div>
        <p v-if="!(opcao.ilhas || []).length" class="text-[10px] text-red-400 mt-1">Escolhe pelo menos uma ilha.</p>
        <p class="text-[10px] text-zinc-600 mt-1">Preços diferentes por ilha? Cria uma opção de envio para cada grupo de ilhas.</p>
      </div>
      <p class="text-[10px] text-zinc-500">
        <font-awesome-icon :icon="['fas', 'circle-info']" class="mr-1" />
        O envio só aceita pagamentos antecipados (cartão ou transferência). Ao enviar indicas o código de rastreio.
      </p>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { ILHAS, ilhaDoConcelho } from '@/utils/geografia'

const TIPOS = [
  { valor: 'local', titulo: 'Entrega local', texto: 'Com os condutores da loja', icone: 'truck' },
  { valor: 'envio', titulo: 'Envio', texto: 'Correios / transportadora', icone: 'box' },
]

let cache = null      // a lista muda pouco: um pedido por página

export default {
  name: 'CamposEnvio',
  props: {
    // { tipo, transportadora_id, transportadora_outra, ilhas }
    opcao:         { type: Object, required: true },
    concelhoLoja:  { type: String, default: '' },
  },
  emits: ['mudar'],
  data () {
    return { ILHAS, TIPOS, transportadoras: [], escolheuOutra: false }
  },
  computed: {
    ilhaLoja () { return ilhaDoConcelho(this.concelhoLoja) },
    valorTransportadora () {
      if (this.opcao.transportadora_id) return String(this.opcao.transportadora_id)
      return (this.escolheuOutra || (this.opcao.transportadora_outra || '').trim()) ? 'outra' : ''
    },
  },
  async created () {
    if (!this.opcao.tipo || !Array.isArray(this.opcao.ilhas)) {
      this.set({ tipo: this.opcao.tipo || 'local', ilhas: Array.isArray(this.opcao.ilhas) ? this.opcao.ilhas : [] })
    }
    try {
      cache = cache || api.get('/app/transportadoras/').then(r => r.data)
      this.transportadoras = await cache
    } catch {
      cache = null
    }
  },
  methods: {
    set (patch) { this.$emit('mudar', patch) },
    mudarTipo (tipo) {
      if (tipo === 'local') {
        this.set({ tipo, transportadora_id: null, transportadora_outra: '', ilhas: [] })
      } else {
        this.set({ tipo, ilhas: (this.opcao.ilhas || []).length ? this.opcao.ilhas : this.semAMinha() })
      }
    },
    mudarTransportadora (v) {
      this.escolheuOutra = v === 'outra'
      this.set({ transportadora_id: v && v !== 'outra' ? Number(v) : null,
                 ...(v !== 'outra' ? { transportadora_outra: '' } : {}) })
    },
    alternarIlha (ilha) {
      const atual = new Set(this.opcao.ilhas || [])
      atual.has(ilha) ? atual.delete(ilha) : atual.add(ilha)
      this.set({ ilhas: ILHAS.filter(i => atual.has(i)) })
    },
    semAMinha () { return ILHAS.filter(i => i !== this.ilhaLoja) },
    todasMenosAMinha () { this.set({ ilhas: this.semAMinha() }) },
  },
}
</script>
