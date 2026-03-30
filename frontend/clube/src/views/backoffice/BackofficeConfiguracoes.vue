<template>
  <div class="space-y-6 max-w-2xl">

    <!-- Info da loja -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
      <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-5">Informações da loja</h2>

      <!-- Banner + Logo upload -->
      <div class="relative mb-6">
        <div class="h-28 rounded-xl overflow-hidden bg-zinc-800 cursor-pointer group relative"
             @click="$refs.bannerInput.click()">
          <img v-if="bannerPreview" :src="bannerPreview" class="w-full h-full object-cover" />
          <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
            <span class="text-white text-xs font-medium">Alterar banner</span>
          </div>
        </div>
        <input ref="bannerInput" type="file" accept="image/*" class="hidden" @change="onBanner" />

        <div class="absolute -bottom-4 left-4 cursor-pointer group" @click="$refs.logoInput.click()">
          <img v-if="logoPreview" :src="logoPreview"
               class="w-16 h-16 rounded-xl object-cover border-4 border-zinc-900 shadow-lg group-hover:ring-2 group-hover:ring-red-500 transition" />
          <div v-else class="w-16 h-16 rounded-xl bg-zinc-700 border-4 border-zinc-900 flex items-center justify-center">
            <span class="text-xl font-bold text-zinc-400">{{ form.nome?.charAt(0) }}</span>
          </div>
        </div>
        <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onLogo" />
      </div>

      <div class="mt-6 space-y-4">
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Nome da loja</label>
          <input v-model="form.nome" type="text"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   focus:outline-none focus:border-red-500 transition" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Descrição</label>
          <textarea v-model="form.descricao" rows="3"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   focus:outline-none focus:border-red-500 transition resize-none"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Categoria</label>
            <input v-model="form.categoria" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Localização</label>
            <input v-model="form.localizacao" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>
      </div>
    </div>

    <!-- Entrega -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
      <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-5">Entrega & Takeaway</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl">
          <div>
            <p class="text-sm font-medium text-zinc-200">Entrega ao domicílio</p>
            <p class="text-xs text-zinc-500">Activar entrega para os clientes</p>
          </div>
          <button @click="form.entrega_ativa = !form.entrega_ativa"
            :class="['w-11 h-6 rounded-full transition-colors relative', form.entrega_ativa ? 'bg-red-600' : 'bg-zinc-700']">
            <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', form.entrega_ativa ? 'left-5.5 translate-x-0.5' : 'left-0.5']" style="transition: left 0.2s"></span>
          </button>
        </div>
        <div class="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl">
          <div>
            <p class="text-sm font-medium text-zinc-200">Takeaway / Levantamento</p>
            <p class="text-xs text-zinc-500">Clientes podem levantar na loja</p>
          </div>
          <button @click="form.levantamento_ativo = !form.levantamento_ativo"
            :class="['w-11 h-6 rounded-full transition-colors relative', form.levantamento_ativo ? 'bg-red-600' : 'bg-zinc-700']">
            <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow', form.levantamento_ativo ? 'left-5.5' : 'left-0.5']" style="transition: left 0.2s"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- Opções de entrega -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Opções de entrega</h2>
        <button @click="novaOpcao = true"
          class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition">
          + Adicionar
        </button>
      </div>

      <div v-if="opcoesEntrega.length === 0" class="text-zinc-600 text-sm text-center py-4">
        Sem opções configuradas.
      </div>
      <div v-else class="space-y-2">
        <div v-for="op in opcoesEntrega" :key="op.id"
             class="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl">
          <div>
            <p class="text-sm font-medium text-zinc-200">{{ op.nome }}</p>
            <p class="text-xs text-zinc-500">{{ op.tempo_estimado }} · {{ op.area_cobertura }}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm font-bold" :class="op.preco == 0 ? 'text-green-400' : 'text-red-400'">
              {{ op.preco == 0 ? 'Grátis' : formatPrice(op.preco) }}
            </span>
            <button @click="eliminarOpcao(op)"
              class="w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Form nova opção -->
      <div v-if="novaOpcao" class="mt-4 p-4 bg-zinc-800/50 rounded-xl space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Nome</label>
            <input v-model="formOpcao.nome" type="text" placeholder="Ex: Standard"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Preço</label>
            <input v-model.number="formOpcao.preco" type="number" step="0.01" min="0" placeholder="0.00"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Tempo estimado</label>
            <input v-model="formOpcao.tempo_estimado" type="text" placeholder="30-45 min"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Área de cobertura</label>
            <input v-model="formOpcao.area_cobertura" type="text" placeholder="Lisboa"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>
        <div class="flex gap-2">
          <button @click="novaOpcao = false" class="flex-1 py-2 rounded-lg border border-zinc-700 text-zinc-400 text-xs font-semibold transition hover:text-zinc-200">Cancelar</button>
          <button @click="criarOpcao" class="flex-1 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition">Criar opção</button>
        </div>
      </div>
    </div>

    <!-- Guardar info loja -->
    <button @click="guardarLoja" :disabled="loadingSave"
      :class="[
        'w-full py-3 rounded-xl font-bold text-sm transition flex items-center justify-center gap-2',
        loadingSave ? 'bg-red-700 cursor-not-allowed opacity-70' : 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/20'
      ]">
      <span v-if="loadingSave" class="flex items-center gap-2">
        <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
          <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
        </svg>
        A guardar…
      </span>
      <span v-else>Guardar configurações</span>
    </button>
  </div>
</template>

<script>
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'

export default {
  name: 'BackofficeConfiguracoes',
  props: {
    lojaId: [String, Number],
    loja:   { type: Object, default: null },
  },
  emits: ['updated'],

  setup () {
    const { loading: loadingSave, wrap } = useAsyncAction()
    return { loadingSave, wrap }
  },

  data () {
    return {
      form: { nome: '', descricao: '', categoria: '', localizacao: '', entrega_ativa: false, levantamento_ativo: false },
      logoFicheiro: null,
      bannerFicheiro: null,
      logoPreview: '',
      bannerPreview: '',
      opcoesEntrega: [],
      novaOpcao: false,
      formOpcao: { nome: '', preco: 0, tempo_estimado: '', area_cobertura: '' },
    }
  },

  watch: {
    loja: { immediate: true, handler (l) { if (l) this.initForm(l) } },
  },

  async created () { await this.fetchOpcoes() },

  methods: {
    formatPrice (val) { return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0) },

    initForm (l) {
      this.form = {
        nome:               l.nome              || '',
        descricao:          l.descricao         || '',
        categoria:          l.categoria         || '',
        localizacao:        l.localizacao       || '',
        entrega_ativa:      l.entrega_ativa      || false,
        levantamento_ativo: l.levantamento_ativo || false,
      }
      this.logoPreview   = l.logo_url   || ''
      this.bannerPreview = l.banner_url || ''
    },

    onLogo (e)   { const f = e.target.files[0]; if (f) { this.logoFicheiro = f;   this.logoPreview   = URL.createObjectURL(f) } },
    onBanner (e) { const f = e.target.files[0]; if (f) { this.bannerFicheiro = f; this.bannerPreview = URL.createObjectURL(f) } },

    async guardarLoja () {
      await this.wrap(async () => {
        const fd = new FormData()
        Object.entries(this.form).forEach(([k, v]) => {
          if (typeof v === 'boolean') fd.append(k, v ? 'true' : 'false')
          else if (v !== '' && v !== null) fd.append(k, v)
        })
        if (this.logoFicheiro)   fd.append('logo',   this.logoFicheiro)
        if (this.bannerFicheiro) fd.append('banner', this.bannerFicheiro)
        await api.patch(`/app/loja/${this.lojaId}/editar/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        this.$emit('updated')
      })
    },

    async fetchOpcoes () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/opcoes/`)
        this.opcoesEntrega = data.results || data
      } catch (e) { console.error(e) }
    },

    async criarOpcao () {
      try {
        await api.post(`/app/loja/${this.lojaId}/entrega/opcoes/criar/`, this.formOpcao)
        this.formOpcao = { nome: '', preco: 0, tempo_estimado: '', area_cobertura: '' }
        this.novaOpcao = false
        await this.fetchOpcoes()
      } catch (e) { console.error(e) }
    },

    async eliminarOpcao (op) {
      if (!confirm(`Eliminar opção "${op.nome}"?`)) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/entrega/opcoes/${op.id}/`)
        await this.fetchOpcoes()
      } catch (e) { console.error(e) }
    },
  }
}
</script>
