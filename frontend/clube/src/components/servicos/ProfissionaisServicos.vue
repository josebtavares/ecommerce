<template>
  <!-- Backoffice → Serviços → Profissionais: fichas, conta ligada, horário semanal e ausências -->
  <div class="space-y-4" data-teste="profissionais">
    <div class="flex flex-wrap items-center gap-3">
      <p class="text-sm text-zinc-400 flex-1 min-w-[200px]">
        {{ activos }} profissional(is) activo(s)<template v-if="limites.profissionais"> · o teu plano inclui até {{ limites.profissionais }}</template>
      </p>
      <button v-if="podeGerir" type="button" @click="abrir(null)" :disabled="!!(limites.profissionais && activos >= limites.profissionais)"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">+ Novo profissional</button>
    </div>

    <div class="grid sm:grid-cols-2 gap-3">
      <div v-for="p in profissionais" :key="p.id" :data-teste="`prof-${p.id}`"
           :class="['bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-3', !p.ativo && 'opacity-60']">
        <div class="flex items-center gap-3">
          <img v-if="p.foto" :src="p.foto" alt="" class="w-12 h-12 rounded-full object-cover flex-shrink-0" />
          <div v-else class="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0 text-sm font-bold text-zinc-400">
            {{ p.nome.charAt(0) }}</div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-zinc-100 truncate">{{ p.nome }}
              <span v-if="!p.ativo" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">inactivo</span></p>
            <p class="text-[11px] text-zinc-500 truncate">
              {{ p.membro ? `Conta: ${p.membro.nome} (${p.membro.role})` : 'Sem conta — a agenda é gerida pela loja' }}</p>
          </div>
          <button v-if="podeGerir" type="button" @click="abrir(p)" :aria-label="`Editar ${p.nome}`"
            class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Editar</button>
        </div>
        <p class="text-xs text-zinc-400">{{ resumoHorario(p) }}</p>
        <p class="text-[11px] text-zinc-500">{{ p.servicos.length }} serviço(s)</p>
      </div>
    </div>

    <!-- editar -->
    <div v-if="form" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="fechar">
      <div role="dialog" :aria-label="form.id ? 'Editar profissional' : 'Novo profissional'"
           class="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-2xl p-5 w-full sm:max-w-xl max-h-[92vh] overflow-y-auto space-y-5">
        <h3 class="text-base font-bold text-zinc-100">{{ form.id ? form.nome : 'Novo profissional' }}</h3>
        <div v-if="form.id" class="flex gap-1 bg-zinc-800/60 rounded-xl p-1" role="tablist">
          <button v-for="a in ABAS" :key="a.k" type="button" role="tab" :aria-selected="aba === a.k" @click="aba = a.k"
            :class="['flex-1 px-3 py-1.5 rounded-lg text-xs font-semibold', aba === a.k ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400']">{{ a.t }}</button>
        </div>

        <!-- ficha -->
        <form v-if="aba === 'ficha'" @submit.prevent="guardar" class="space-y-4">
          <div v-if="form.id" class="flex items-center gap-3">
            <img v-if="form.foto" :src="form.foto" alt="" class="w-14 h-14 rounded-full object-cover" />
            <div v-else class="w-14 h-14 rounded-full bg-zinc-800"></div>
            <label class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 cursor-pointer">
              {{ form.foto ? 'Mudar foto' : 'Pôr foto' }}<input type="file" accept="image/*" class="sr-only" @change="enviarFoto" /></label>
            <button v-if="form.foto" type="button" @click="tirarFoto" class="text-xs text-zinc-500 hover:text-zinc-300">Tirar</button>
          </div>
          <label class="block"><span class="text-xs text-zinc-500">Nome (o que os clientes vêem)</span>
            <input v-model="form.nome" maxlength="100" required :class="[CAMPO, 'mt-1']" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Descrição (opcional)</span>
            <input v-model="form.descricao" maxlength="300" :class="[CAMPO, 'mt-1']" placeholder="ex.: Especialista em coloração" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Conta da equipa (opcional)</span>
            <select v-model="form.membro_id" :class="[CAMPO, 'mt-1']">
              <option :value="null">Sem conta</option>
              <option v-for="m in equipa.filter(m => !m.ligado || m.id === form.membro_original)" :key="m.id" :value="m.id">{{ m.nome }} ({{ m.role }})</option>
            </select>
            <span class="text-[11px] text-zinc-500">Com conta, a pessoa vê a sua agenda no backoffice e recebe os avisos das suas marcações.</span>
          </label>
          <fieldset>
            <legend class="text-xs text-zinc-500 mb-1">Serviços que faz</legend>
            <div class="flex flex-wrap gap-2">
              <label v-for="s in servicos" :key="s.id"
                :class="['px-3 py-1.5 rounded-lg border text-xs cursor-pointer select-none',
                         form.servicos.includes(s.id) ? 'border-red-500 bg-red-500/10 text-zinc-100' : 'border-zinc-700 text-zinc-400']">
                <input type="checkbox" :value="s.id" v-model="form.servicos" class="sr-only" />{{ s.nome }}
              </label>
              <p v-if="!servicos.length" class="text-xs text-zinc-500">Ainda não há serviços.</p>
            </div>
          </fieldset>
          <label v-if="form.id" class="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" v-model="form.ativo" class="accent-red-600" /> Activo (recebe marcações)</label>
          <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
          <ListaMarcacoes v-if="conflitos.length" :marcacoes="conflitos" titulo="Marcações futuras deste profissional (reatribui-as ou cancela-as na Agenda):" />
          <div class="flex flex-wrap gap-2">
            <button type="submit" :disabled="aGuardar" class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
              {{ form.id ? 'Guardar' : 'Criar profissional' }}</button>
            <button type="button" @click="fechar" class="px-4 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm">Fechar</button>
            <button v-if="form.id" type="button" @click="apagar" :disabled="aGuardar" class="w-full sm:w-auto px-4 py-2.5 text-red-400 text-sm">Apagar</button>
          </div>
        </form>

        <!-- horário -->
        <div v-else-if="aba === 'horario'" class="space-y-3" data-teste="horario">
          <label class="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" v-model="seguirLoja" class="accent-red-600" /> Segue o horário da loja</label>
          <template v-if="!seguirLoja">
            <div v-for="(nome, d) in DIAS" :key="d" class="flex flex-wrap items-center gap-2">
              <span class="w-20 text-xs font-semibold text-zinc-300">{{ nome }}</span>
              <template v-for="(b, i) in blocosDe(d)" :key="i">
                <input v-model="b.inicio" type="time" step="900" :aria-label="`${nome} início`" class="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100" />
                <span class="text-zinc-500 text-xs">–</span>
                <input v-model="b.fim" type="time" step="900" :aria-label="`${nome} fim`" class="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100" />
                <button type="button" @click="tirarBloco(b)" :aria-label="`Tirar bloco de ${nome}`" class="text-zinc-500 hover:text-red-400 text-xs px-1">✕</button>
              </template>
              <span v-if="!blocosDe(d).length" class="text-xs text-zinc-600">Folga</span>
              <button type="button" @click="porBloco(d)" class="text-xs text-sky-300 hover:text-sky-200">+ bloco</button>
            </div>
          </template>
          <p v-else class="text-xs text-zinc-500">Trabalha sempre que a loja está aberta. Desliga para definir dias e horas próprios.</p>
          <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
          <ListaMarcacoes v-if="foraHorario.length" :marcacoes="foraHorario" titulo="Atenção: estas marcações ficam fora do novo horário (continuam marcadas):" />
          <p v-if="okMsg" class="text-sm text-green-400" role="status">{{ okMsg }}</p>
          <button type="button" @click="guardarHorario" :disabled="aGuardar"
            class="w-full px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">Guardar horário</button>
        </div>

        <!-- ausências -->
        <div v-else class="space-y-3" data-teste="ausencias">
          <div v-for="a in ausencias" :key="a.id" class="flex items-center gap-2 rounded-xl bg-zinc-800/50 px-3 py-2">
            <p class="flex-1 text-xs text-zinc-300">{{ textoAusencia(a) }}<span v-if="a.motivo" class="text-zinc-500"> · {{ a.motivo }}</span></p>
            <button type="button" @click="apagarAusencia(a)" class="text-xs text-zinc-500 hover:text-red-400">Tirar</button>
          </div>
          <p v-if="!ausencias.length" class="text-xs text-zinc-500">Sem folgas nem férias marcadas.</p>
          <form @submit.prevent="criarAusencia" class="grid grid-cols-2 gap-2 pt-2 border-t border-zinc-800">
            <label class="block"><span class="text-xs text-zinc-500">De</span>
              <input v-model="novaAus.de" type="date" required :class="[CAMPO, 'mt-1']" /></label>
            <label class="block"><span class="text-xs text-zinc-500">Até (inclusive)</span>
              <input v-model="novaAus.ate" type="date" :min="novaAus.de" :class="[CAMPO, 'mt-1']" /></label>
            <label class="block col-span-2"><span class="text-xs text-zinc-500">Motivo (opcional)</span>
              <input v-model="novaAus.motivo" maxlength="200" :class="[CAMPO, 'mt-1']" placeholder="ex.: Férias, Doente" /></label>
            <button type="submit" :disabled="aGuardar" class="col-span-2 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">Marcar ausência</button>
          </form>
          <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
          <ListaMarcacoes v-if="afetadas.length" :marcacoes="afetadas"
            titulo="Estas marcações caem na ausência — remarca-as, reatribui-as ou cancela-as na Agenda:" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { CAMPO, DIAS, hora, diaDe, rotuloDia } from '@/utils/servicos'
import ListaMarcacoes from './ListaMarcacoes.vue'

const ABAS = [{ k: 'ficha', t: 'Ficha' }, { k: 'horario', t: 'Horário' }, { k: 'ausencias', t: 'Folgas e férias' }]

export default {
  name: 'ProfissionaisServicos',
  components: { ListaMarcacoes },
  props: {
    lojaId: { type: [String, Number], required: true },
    profissionais: { type: Array, default: () => [] },
    equipa: { type: Array, default: () => [] },
    limites: { type: Object, default: () => ({}) },
    servicos: { type: Array, default: () => [] },
    podeGerir: { type: Boolean, default: false },
  },
  emits: ['alterado'],
  data () {
    return { form: null, aba: 'ficha', erro: '', okMsg: '', aGuardar: false, conflitos: [], blocos: [], seguirLoja: true,
             foraHorario: [], ausencias: [], afetadas: [], novaAus: { de: '', ate: '', motivo: '' }, CAMPO, DIAS, ABAS }
  },
  computed: {
    activos () { return this.profissionais.filter(p => p.ativo).length },
  },
  methods: {
    base () { return `/app/loja/${this.lojaId}/servicos/profissionais/` },
    resumoHorario (p) {
      if (!p.horario.length) return 'Horário da loja'
      const dias = [...new Set(p.horario.map(h => h.dia_semana))]
      return dias.map(d => `${DIAS[d].slice(0, 3)} ${p.horario.filter(h => h.dia_semana === d).map(h => `${h.inicio}–${h.fim}`).join(', ')}`).join(' · ')
    },
    abrir (p) {
      this.erro = ''; this.okMsg = ''; this.aba = 'ficha'; this.conflitos = []; this.foraHorario = []; this.afetadas = []
      this.form = p
        ? { ...p, membro_id: p.membro?.id || null, membro_original: p.membro?.id || null, servicos: [...p.servicos] }
        : { id: null, nome: '', descricao: '', membro_id: null, servicos: this.servicos.filter(s => s.ativo).map(s => s.id), ativo: true }
      this.blocos = (p?.horario || []).map(h => ({ ...h }))
      this.seguirLoja = !this.blocos.length
      this.novaAus = { de: '', ate: '', motivo: '' }
      if (p) this.carregarAusencias()
    },
    fechar () { this.form = null },
    async guardar () {
      this.erro = ''; this.conflitos = []; this.aGuardar = true
      const f = this.form
      const corpo = { nome: f.nome, descricao: f.descricao, membro_id: f.membro_id, servicos: f.servicos }
      try {
        if (f.id) {
          corpo.ativo = f.ativo
          const { data } = await api.patch(`${this.base()}${f.id}/`, corpo)
          Object.assign(this.form, { ...data, membro_id: data.membro?.id || null, membro_original: data.membro?.id || null })
          this.okMsg = 'Guardado.'
        } else {
          const { data } = await api.post(this.base(), corpo)
          this.abrir(data)
          this.aba = 'horario'
        }
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
        this.conflitos = e.response?.data?.marcacoes || []
      } finally { this.aGuardar = false }
    },
    async apagar () {
      if (!confirm(`Apagar ${this.form.nome}?\n\nSe já tiver marcações, fica só inactivo.`)) return
      this.erro = ''; this.conflitos = []
      try {
        const { data } = await api.delete(`${this.base()}${this.form.id}/`)
        if (data.desativado) alert(data.detail)
        this.form = null
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível apagar.'
        this.conflitos = e.response?.data?.marcacoes || []
      }
    },
    async enviarFoto (ev) {
      const f = ev.target.files?.[0]
      ev.target.value = ''
      if (!f) return
      const fd = new FormData()
      fd.append('ficheiro', f)
      try {
        const { data } = await api.post(`${this.base()}${this.form.id}/foto/`, fd)
        this.form.foto = data.foto
        this.$emit('alterado')
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível enviar a foto.' }
    },
    async tirarFoto () {
      const { data } = await api.delete(`${this.base()}${this.form.id}/foto/`)
      this.form.foto = data.foto
      this.$emit('alterado')
    },
    blocosDe (d) { return this.blocos.filter(b => b.dia_semana === d) },
    porBloco (d) {
      const ult = this.blocosDe(d).slice(-1)[0]
      this.blocos.push(ult ? { dia_semana: d, inicio: ult.fim, fim: ult.fim < '22:00' ? '22:00' : '23:45' } : { dia_semana: d, inicio: '09:00', fim: '18:00' })
    },
    tirarBloco (b) { this.blocos = this.blocos.filter(x => x !== b) },
    async guardarHorario () {
      this.erro = ''; this.okMsg = ''; this.foraHorario = []; this.aGuardar = true
      try {
        const blocos = this.seguirLoja ? [] : this.blocos.map(b => ({ dia_semana: b.dia_semana, inicio: b.inicio.slice(0, 5), fim: b.fim.slice(0, 5) }))
        const { data } = await api.put(`${this.base()}${this.form.id}/horario/`, { blocos })
        this.blocos = data.horario.map(h => ({ ...h }))
        this.seguirLoja = !this.blocos.length
        this.foraHorario = data.fora_do_horario
        this.okMsg = 'Horário guardado.'
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar o horário.'
      } finally { this.aGuardar = false }
    },
    textoAusencia (a) {
      const di = diaDe(a.inicio), df = diaDe(a.fim)
      if (hora(a.inicio) === '00:00' && hora(a.fim) === '00:00') {
        const ultimo = new Date(df + 'T12:00:00'); ultimo.setDate(ultimo.getDate() - 1)
        const u = ultimo.toISOString().slice(0, 10)
        return u === di ? rotuloDia(di) : `${rotuloDia(di)} a ${rotuloDia(u)}`
      }
      return `${rotuloDia(di)} ${hora(a.inicio)} – ${di === df ? '' : rotuloDia(df) + ' '}${hora(a.fim)}`
    },
    async carregarAusencias () {
      this.ausencias = (await api.get(`${this.base()}${this.form.id}/ausencias/`)).data
    },
    async criarAusencia () {
      this.erro = ''; this.afetadas = []; this.aGuardar = true
      try {
        const { data } = await api.post(`${this.base()}${this.form.id}/ausencias/`,
          { de: this.novaAus.de, ate: this.novaAus.ate || this.novaAus.de, motivo: this.novaAus.motivo })
        this.afetadas = data.afetadas
        this.novaAus = { de: '', ate: '', motivo: '' }
        await this.carregarAusencias()
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível marcar a ausência.'
      } finally { this.aGuardar = false }
    },
    async apagarAusencia (a) {
      await api.delete(`/app/loja/${this.lojaId}/servicos/ausencias/${a.id}/`)
      await this.carregarAusencias()
      this.$emit('alterado')
    },
  },
}
</script>
