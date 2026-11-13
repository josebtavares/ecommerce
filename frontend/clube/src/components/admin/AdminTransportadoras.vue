<!-- AdminTransportadoras.vue — Admin → Definições → Transportadoras: a lista que as lojas escolhem no envio com
     código de rastreio. O link de rastreio leva {codigo} no sítio do código (vazio = sem rastreio online).
     Backend: GET/POST /app/admin/transportadoras/, PATCH /app/admin/transportadoras/<id>/ (utils/envios.py). -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="admin-transportadoras">
    <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Transportadoras</h3>
    <p class="text-xs text-zinc-500 mt-1">
      As lojas escolhem uma destas (ou "Outra") ao enviar por correio. O link de rastreio leva
      <code class="text-zinc-300">{codigo}</code> no sítio do código — o cliente carrega e segue a encomenda.
    </p>

    <p v-if="erro" class="mt-4 text-sm text-red-400" role="alert">{{ erro }}</p>

    <div class="mt-5 space-y-2">
      <div v-for="t in lista" :key="t.id" class="rounded-xl bg-zinc-800/50 p-3" :data-teste="`transportadora-${t.id}`">
        <template v-if="editar === t.id">
          <div class="grid gap-2">
            <input v-for="c in CAMPOS" :key="c.k" v-model="form[c.k]" :maxlength="c.max" :placeholder="c.ph"
                   class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
          </div>
          <div class="flex justify-end gap-2 mt-3">
            <button type="button" @click="editar = null" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200">Cancelar</button>
            <button type="button" @click="guardar(t)" :disabled="aGuardar"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-40">Guardar</button>
          </div>
        </template>
        <div v-else class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-semibold" :class="t.ativa ? 'text-zinc-200' : 'text-zinc-500 line-through'">{{ t.nome }}</p>
            <p class="text-[11px] text-zinc-500 truncate">{{ t.url_rastreio || 'Sem rastreio online' }}{{ t.contacto ? ' · ' + t.contacto : '' }}</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <button type="button" @click="alternar(t)" :disabled="aGuardar"
                    class="px-2.5 py-1 rounded-lg text-[11px] font-semibold transition"
                    :class="t.ativa ? 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600' : 'bg-green-500/15 text-green-300 hover:bg-green-500/25'">
              {{ t.ativa ? 'Desligar' : 'Ligar' }}
            </button>
            <button type="button" @click="abrirEditar(t)" class="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-zinc-700 text-zinc-300 hover:bg-zinc-600">
              Editar
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="nova" class="mt-4 rounded-xl border border-zinc-700 p-3">
      <div class="grid gap-2">
            <input v-for="c in CAMPOS" :key="c.k" v-model="form[c.k]" :maxlength="c.max" :placeholder="c.ph"
                   class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
          </div>
      <div class="flex justify-end gap-2 mt-3">
        <button type="button" @click="nova = false" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200">Cancelar</button>
        <button type="button" @click="criar" :disabled="aGuardar" data-teste="transportadora-criar"
                class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-40">Adicionar</button>
      </div>
    </div>
    <button v-else type="button" @click="abrirNova" class="mt-4 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">
      + Adicionar transportadora
    </button>
  </div>
</template>

<script>
import api from '@/services/api'

// nome, link e contacto — os mesmos ao editar e ao adicionar
const CAMPOS = [
  { k: 'nome', ph: 'Nome (ex.: DHL)', max: 80 },
  { k: 'url_rastreio', ph: 'https://…{codigo}… (opcional)', max: 300 },
  { k: 'contacto', ph: 'Contacto (opcional)', max: 200 },
]

export default {
  name: 'AdminTransportadoras',
  data () {
    return { CAMPOS, lista: [], erro: '', editar: null, nova: false, aGuardar: false, form: {} }
  },
  created () { this.carregar() },
  methods: {
    async carregar () {
      try { this.lista = (await api.get('/app/admin/transportadoras/')).data } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar as transportadoras.'
      }
    },
    msg (e) {
      const d = e.response?.data
      return d?.detail || (d && Object.values(d).flat()[0]) || 'Não foi possível guardar.'
    },
    abrirEditar (t) { this.nova = false; this.erro = ''; this.form = { nome: t.nome, url_rastreio: t.url_rastreio, contacto: t.contacto }; this.editar = t.id },
    abrirNova () { this.editar = null; this.erro = ''; this.form = { nome: '', url_rastreio: '', contacto: '' }; this.nova = true },
    async guardar (t) {
      this.aGuardar = true; this.erro = ''
      try {
        Object.assign(t, (await api.patch(`/app/admin/transportadoras/${t.id}/`, this.form)).data)
        this.editar = null
      } catch (e) { this.erro = this.msg(e) } finally { this.aGuardar = false }
    },
    async alternar (t) {
      this.aGuardar = true; this.erro = ''
      try {
        Object.assign(t, (await api.patch(`/app/admin/transportadoras/${t.id}/`, { ativa: !t.ativa })).data)
      } catch (e) { this.erro = this.msg(e) } finally { this.aGuardar = false }
    },
    async criar () {
      this.aGuardar = true; this.erro = ''
      try {
        this.lista.push((await api.post('/app/admin/transportadoras/', this.form)).data)
        this.nova = false
      } catch (e) { this.erro = this.msg(e) } finally { this.aGuardar = false }
    },
  },
}
</script>
