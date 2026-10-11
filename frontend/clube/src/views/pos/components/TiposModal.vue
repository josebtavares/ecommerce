<!-- TiposModal.vue — tipos de produto do POS
     Globais (só leitura) + tipos próprios do POS (criar/editar/desactivar).
     Os tipos do POS servem os produtos próprios do POS; não aparecem na loja Bendi. -->
<template>
  <div class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
       @click.self="$emit('close')">
    <div class="flex max-h-[95vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
      <header class="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
        <div>
          <h3 class="text-xl font-black text-slate-950">{{ form ? (form.id ? 'Editar tipo' : 'Novo tipo') : 'Tipos de produto' }}</h3>
          <p class="mt-1 text-sm font-semibold text-slate-500">
            {{ form ? 'Define os atributos dos produtos deste tipo.' : 'Atributos dos produtos próprios do POS (tamanho, cor, sabor…).' }}
          </p>
        </div>
        <button type="button" @click="form ? (form = null) : $emit('close')"
          class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950">
          {{ form ? '←' : '×' }}
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-5">
        <!-- ── LISTA ── -->
        <template v-if="!form">
          <div v-if="loading" class="space-y-2">
            <div v-for="n in 4" :key="n" class="h-16 animate-pulse rounded-2xl bg-slate-100"></div>
          </div>
          <p v-else-if="erro" class="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{{ erro }}</p>
          <template v-else>
            <div v-for="grupo in grupos" :key="grupo.key" class="mb-5">
              <p class="mb-2 text-[11px] font-black uppercase tracking-wider text-slate-400">{{ grupo.label }}</p>
              <p v-if="!grupo.itens.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-4 text-center text-xs font-semibold text-slate-400">
                {{ grupo.key === 'pos' ? 'Ainda não criaste tipos próprios.' : 'Sem tipos.' }}
              </p>
              <div v-for="t in grupo.itens" :key="t.id"
                   class="mb-2 flex items-start gap-3 rounded-2xl border border-slate-200 p-3">
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-black capitalize text-slate-900">{{ t.nome }}</p>
                  <div class="mt-1.5 flex flex-wrap gap-1">
                    <span v-for="a in t.atributos_schema" :key="a.nome"
                          :class="['rounded-lg px-2 py-0.5 text-[11px] font-bold',
                                   a.variante ? 'bg-amber-100 text-amber-800' : a.tipo === 'choices' ? 'bg-blue-50 text-blue-700' : 'bg-slate-100 text-slate-600']">
                      <font-awesome-icon v-if="a.variante" :icon="['fas', 'boxes-stacked']" title="Stock por opção" class="mr-1" />{{ a.nome }}
                      <span v-if="a.tipo === 'choices'" class="opacity-60">({{ (a.opcoes || []).join(', ') }})</span>
                    </span>
                    <span v-if="!t.atributos_schema.length" class="text-[11px] text-slate-400">Sem atributos</span>
                  </div>
                </div>
                <div v-if="t.editavel" class="flex flex-shrink-0 gap-1">
                  <button type="button" @click="editar(t)" class="h-8 rounded-xl bg-slate-100 px-3 text-xs font-black text-slate-700 hover:bg-slate-200">Editar</button>
                  <button type="button" @click="desactivar(t)" class="h-8 rounded-xl bg-red-50 px-3 text-xs font-black text-red-700 hover:bg-red-100">Remover</button>
                </div>
              </div>
            </div>
          </template>
        </template>

        <!-- ── FORMULÁRIO ── -->
        <div v-else class="space-y-4" @keydown.enter.prevent>
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Nome *</label>
            <input v-model.trim="form.nome" type="text" placeholder="Ex: bebidas, sobremesas, t-shirts"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none focus:border-slate-950 focus:bg-white" />
          </div>

          <div class="flex items-center justify-between">
            <label class="text-sm font-black text-slate-700">Atributos</label>
            <button type="button" @click="form.atributos_schema.push(novoAtributo())"
              class="h-9 rounded-xl bg-slate-100 px-3 text-xs font-black text-slate-700 hover:bg-slate-200">+ Atributo</button>
          </div>

          <p v-if="!form.atributos_schema.length" class="rounded-2xl border border-dashed border-slate-200 py-5 text-center text-xs font-semibold text-slate-400">
            Sem atributos. Adiciona, por exemplo, "tamanho" com as opções pequeno/grande.
          </p>

          <div v-for="(a, i) in form.atributos_schema" :key="a._k" class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex items-end gap-2">
              <div class="flex-1">
                <label class="mb-1 block text-[11px] font-bold text-slate-500">Nome</label>
                <input v-model.trim="a.nome" placeholder="ex: tamanho"
                  class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-slate-950" />
              </div>
              <div class="w-32">
                <label class="mb-1 block text-[11px] font-bold text-slate-500">Tipo</label>
                <select v-model="a.tipo" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-2 text-sm outline-none focus:border-slate-950">
                  <option value="choices">Escolha</option>
                  <option value="texto">Texto</option>
                  <option value="numero">Número</option>
                </select>
              </div>
              <button type="button" @click="form.atributos_schema.splice(i, 1)"
                class="h-10 w-10 flex-shrink-0 rounded-xl bg-red-50 text-lg font-black text-red-600 hover:bg-red-100">×</button>
            </div>

            <template v-if="a.tipo === 'choices'">
              <div class="flex flex-wrap gap-1.5">
                <span v-for="(op, oi) in a.opcoes" :key="op"
                      class="flex items-center gap-1 rounded-lg bg-blue-100 px-2 py-1 text-xs font-bold text-blue-800">
                  {{ op }}
                  <button type="button" @click="a.opcoes.splice(oi, 1)" class="hover:text-red-600">×</button>
                </span>
              </div>
              <input v-model="a._nova" @keydown.enter.prevent="adicionarOpcao(a)" @keydown="e => e.key === ',' && (e.preventDefault(), adicionarOpcao(a))"
                placeholder="Escreve uma opção e carrega Enter…"
                class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-slate-950" />

              <label :class="['flex cursor-pointer items-start gap-2.5 rounded-xl border p-3 transition',
                              a.variante ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white']">
                <input v-model="a.variante" type="checkbox" class="mt-0.5 h-4 w-4 accent-amber-500" />
                <span>
                  <span class="block text-xs font-black text-slate-800"><font-awesome-icon :icon="['fas', 'boxes-stacked']" class="mr-1 text-amber-600" />Stock por opção</span>
                  <span class="block text-[11px] font-semibold text-slate-500">
                    Cada opção tem stock próprio (ex.: tamanho). Desliga para preferências (ex.: com/sem gelo).
                  </span>
                </span>
              </label>
            </template>

            <label class="flex items-center gap-2 text-xs font-bold text-slate-600">
              <input v-model="a.obrigatorio" type="checkbox" class="h-4 w-4 accent-slate-950" />
              Obrigatório
            </label>
          </div>

          <p v-if="erroForm" class="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{{ erroForm }}</p>
        </div>
      </div>

      <footer class="grid grid-cols-2 gap-3 border-t border-slate-200 p-5">
        <template v-if="!form">
          <button type="button" @click="$emit('close')"
            class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 hover:bg-slate-50">Fechar</button>
          <button type="button" @click="novo"
            class="h-12 rounded-2xl bg-slate-950 text-sm font-black text-white hover:bg-slate-800">+ Novo tipo</button>
        </template>
        <template v-else>
          <button type="button" @click="form = null"
            class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" @click="guardar" :disabled="saving"
            class="h-12 rounded-2xl bg-slate-950 text-sm font-black text-white hover:bg-slate-800 disabled:opacity-60">
            {{ saving ? 'A guardar…' : 'Guardar tipo' }}
          </button>
        </template>
      </footer>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'

let k = 0

export default {
  name: 'TiposModal',
  props: { posId: { type: [Number, String], required: true } },
  emits: ['close', 'alterado'],

  data () {
    return { tipos: [], loading: true, erro: '', form: null, saving: false, erroForm: '' }
  },

  computed: {
    grupos () {
      return [
        { key: 'pos',    label: 'Deste POS',          itens: this.tipos.filter(t => t.origem === 'pos') },
        { key: 'global', label: 'Globais (só leitura)', itens: this.tipos.filter(t => t.origem === 'global') },
      ]
    },
  },

  created () { this.carregar() },

  methods: {
    async carregar () {
      this.loading = true
      this.erro = ''
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/tipos/`, { params: { para: 'pos' } })
        this.tipos = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao carregar tipos.'
      } finally {
        this.loading = false
      }
    },

    novoAtributo () {
      return { _k: ++k, nome: '', tipo: 'choices', opcoes: [], obrigatorio: false, variante: false, _nova: '' }
    },

    novo () {
      this.erroForm = ''
      this.form = { id: null, nome: '', atributos_schema: [this.novoAtributo()] }
    },

    editar (t) {
      this.erroForm = ''
      this.form = {
        id: t.id, nome: t.nome,
        atributos_schema: (t.atributos_schema || []).map(a => ({ ...a, opcoes: [...(a.opcoes || [])], _k: ++k, _nova: '' })),
      }
    },

    adicionarOpcao (a) {
      const v = String(a._nova || '').replace(',', '').trim()
      if (v && !a.opcoes.includes(v)) a.opcoes.push(v)
      a._nova = ''
    },

    async guardar () {
      this.erroForm = ''
      // aproveita opções escritas e não confirmadas com Enter
      this.form.atributos_schema.forEach(a => { if (a.tipo === 'choices' && a._nova) this.adicionarOpcao(a) })
      if (!this.form.nome) { this.erroForm = 'O nome é obrigatório.'; return }
      const semNome = this.form.atributos_schema.find(a => !a.nome)
      if (semNome) { this.erroForm = 'Todos os atributos precisam de nome.'; return }
      const semOpcoes = this.form.atributos_schema.find(a => a.tipo === 'choices' && !a.opcoes.length)
      if (semOpcoes) { this.erroForm = `"${semOpcoes.nome}" precisa de pelo menos uma opção.`; return }

      const body = {
        nome: this.form.nome,
        atributos_schema: this.form.atributos_schema.map(({ nome, tipo, opcoes, obrigatorio, variante }) => ({
          nome, tipo, opcoes: tipo === 'choices' ? opcoes : [], obrigatorio, variante: tipo === 'choices' && variante,
        })),
      }
      this.saving = true
      try {
        if (this.form.id) await api.patch(`/api/pos/${this.posId}/tipos/${this.form.id}/`, body)
        else await api.post(`/api/pos/${this.posId}/tipos/`, body)
        toast.success('Tipo guardado.')
        this.form = null
        await this.carregar()
        this.$emit('alterado')
      } catch (e) {
        const d = e.response?.data
        this.erroForm = d?.detail || (d && Object.values(d).flat()[0]) || 'Erro ao guardar.'
      } finally {
        this.saving = false
      }
    },

    async desactivar (t) {
      if (!confirm(`Remover o tipo "${t.nome}"? Os produtos que o usam mantêm-no.`)) return
      try {
        await api.delete(`/api/pos/${this.posId}/tipos/${t.id}/`)
        await this.carregar()
        this.$emit('alterado')
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Erro ao remover.')
      }
    },
  },
}
</script>
