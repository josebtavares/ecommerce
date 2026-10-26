<template>
  <!-- Backups da base de dados (só super-admin) — Views/backupView.py, utils/backups.py -->
  <div class="space-y-5 max-w-4xl" data-teste="admin-backups">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Backups da base de dados</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Cópia completa de todos os dados da plataforma, guardada fora do Railway</p>
      </div>
      <button type="button" @click="fazer" :disabled="aFazer || resumo.a_correr" data-teste="backup-fazer"
        class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition flex items-center gap-2">
        <font-awesome-icon :icon="['fas', aFazer ? 'spinner' : 'database']" :spin="aFazer" class="w-4 h-4" />
        {{ aFazer ? 'A fazer o backup…' : 'Fazer backup agora' }}
      </button>
    </div>

    <p v-if="mensagem" :class="['text-sm', mensagem.erro ? 'text-red-400' : 'text-green-400']" role="status">{{ mensagem.texto }}</p>

    <div v-if="loading" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>

    <template v-else>
      <!-- resumo (não depende dos filtros) -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" data-teste="backup-resumo">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Último backup</p>
          <p :class="['text-sm font-bold mt-1', atrasado ? 'text-amber-400' : 'text-zinc-100']">
            {{ resumo.ultimo_ok ? quando(resumo.ultimo_ok) : 'Nenhum' }}
          </p>
          <p v-if="atrasado" class="text-[11px] text-amber-400/80 mt-0.5">Há mais de 1 dia</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Próximo automático</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ quando(resumo.proximo_automatico) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Guardados</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ resumo.guardados }} · {{ tamanho(resumo.espaco) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Onde</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ resumo.armazenamento }}</p>
        </div>
      </div>
      <p class="text-xs text-zinc-500">
        Ficam {{ resumo.retencao }}; os mais antigos apagam-se sozinhos. Se um backup falhar, os super-admins recebem um email.
        Repor um backup não se faz aqui (apagava os dados atuais): pede-se ao suporte técnico, que o testa primeiro numa cópia.
      </p>

      <!-- ensaio de reposição: o worker repõe um backup numa base temporária e confere-o -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex flex-wrap items-center gap-x-4 gap-y-3" data-teste="backup-ensaio">
        <font-awesome-icon :icon="['fas', ensaioIcone]" :spin="ensaio.em_curso"
          :class="['w-5 h-5 shrink-0', ensaio.em_curso ? 'text-zinc-400' : !ultimoEnsaio ? 'text-zinc-500' : ultimoEnsaio.ok ? 'text-green-400' : 'text-red-400']" />
        <div class="min-w-0 flex-1 basis-56">
          <p class="text-sm font-semibold text-zinc-100">Ensaio de reposição</p>
          <p v-if="ensaio.em_curso" class="text-xs text-zinc-400 mt-0.5">A repor o backup numa base temporária e a conferir…</p>
          <p v-else-if="!ultimoEnsaio" class="text-xs text-zinc-500 mt-0.5">Ainda nenhum backup foi reposto para confirmar que serve.</p>
          <p v-else class="text-xs mt-0.5 break-words" :class="ultimoEnsaio.ok ? 'text-zinc-400' : 'text-red-400'">
            {{ quando(ultimoEnsaio.quando) }} · {{ ultimoEnsaio.backup }} ·
            <template v-if="ultimoEnsaio.ok">reposto e conferido: {{ ultimoEnsaio.tabelas }} tabelas, {{ numero(ultimoEnsaio.linhas) }} linhas, {{ segundos(ultimoEnsaio.total_s) }}</template>
            <template v-else>falhou: {{ ultimoEnsaio.erro }}</template>
          </p>
          <p class="text-[11px] text-zinc-500 mt-0.5">
            Automático de {{ ensaio.cada_dias }} em {{ ensaio.cada_dias }} dias<template v-if="ensaio.proximo"> (próximo {{ quando(ensaio.proximo) }})</template>.
            Usa uma base temporária — a da plataforma não é tocada.
          </p>
        </div>
        <button type="button" @click="ensaiar" :disabled="ensaio.em_curso || aEnsaiar || !resumo.guardados" data-teste="backup-ensaiar"
          class="w-full sm:w-auto px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-xs font-semibold text-zinc-200 disabled:opacity-40 transition">
          Testar reposição agora
        </button>
      </div>

      <!-- fotos e vídeos: cópia incremental do storage das lojas (utils/backup_media.py) -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-3" data-teste="backup-media">
        <div class="flex flex-wrap items-center gap-x-4 gap-y-3">
          <font-awesome-icon :icon="['fas', media.em_curso ? 'spinner' : 'images']" :spin="media.em_curso"
            :class="['w-5 h-5 shrink-0', media.em_curso || !ultimaCopia ? 'text-zinc-500' : ultimaCopia.estado === 'ok' ? 'text-green-400' : 'text-red-400']" />
          <div class="min-w-0 flex-1 basis-56">
            <p class="text-sm font-semibold text-zinc-100">Fotos e vídeos</p>
            <p v-if="media.em_curso" class="text-xs text-zinc-400 mt-0.5">A copiar o que é novo…</p>
            <p v-else-if="!ultimaCopia" class="text-xs text-zinc-500 mt-0.5">Ainda não foram copiados.</p>
            <template v-else>
              <p class="text-xs text-zinc-400 mt-0.5 break-words">
                {{ quando(ultimaCopia.quando) }} · na cópia: {{ numero(ultimaCopia.ficheiros) }} ficheiros, {{ tamanho(ultimaCopia.bytes) }}
                <span class="text-zinc-500">({{ numero(ultimaCopia.copiados) }} novos<template v-if="ultimaCopia.guardados_apagados">, {{ numero(ultimaCopia.guardados_apagados) }} apagados guardados</template>)</span>
              </p>
              <p v-if="ultimaCopia.estado === 'erro'" class="text-xs text-red-400 mt-0.5 break-words whitespace-pre-line line-clamp-4">{{ ultimaCopia.erro }}</p>
            </template>
          </div>
          <button type="button" @click="copiarMedia" :disabled="media.em_curso || aCopiar" data-teste="backup-media-copiar"
            class="w-full sm:w-auto px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-xs font-semibold text-zinc-200 disabled:opacity-40 transition">
            Copiar agora
          </button>
        </div>
        <div v-if="ultimaCopia" data-teste="backup-espaco">
          <div class="flex flex-wrap justify-between gap-x-3 text-[11px] text-zinc-500">
            <span>Espaço dos backups: <b :class="acimaLimite ? 'text-amber-400' : 'text-zinc-300'">{{ tamanho(ultimaCopia.bytes_total) }}</b> de {{ tamanho(media.gratis_bytes) }} grátis</span>
            <span>aviso por email aos {{ tamanho(media.limite_bytes) }}</span>
          </div>
          <div class="mt-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden" role="progressbar" :aria-valuenow="percentagemEspaco" aria-valuemin="0" aria-valuemax="100" aria-label="Espaço usado do limite grátis">
            <div :class="['h-full rounded-full', acimaLimite ? 'bg-amber-400' : 'bg-green-500']" :style="{ width: Math.max(1, percentagemEspaco) + '%' }"></div>
          </div>
        </div>
        <p class="text-[11px] text-zinc-500">
          Todos os dias depois do backup da base (próxima {{ quando(media.proxima) }}); só copia o que é novo ou mudou.
          O que as lojas apagam fica guardado {{ media.apagados_dias }} dias<template v-if="ultimaCopia && ultimaCopia.bytes_apagados"> ({{ tamanho(ultimaCopia.bytes_apagados) }})</template>.
          Repor ficheiros: <code class="text-zinc-400">manage.py backup_media --repor</code> (docs/REPOR_BACKUP.md).
        </p>
      </div>

      <!-- filtros da lista -->
      <form @submit.prevent="carregarLista(0)" class="flex flex-wrap items-center gap-2" data-teste="backup-filtros">
        <input v-model.trim="fl.q" type="search" placeholder="Ficheiro ou quem pediu" aria-label="Pesquisar backups" data-teste="backup-q"
          class="flex-1 min-w-[180px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
        <select v-model="fl.tipo" @change="carregarLista(0)" aria-label="Tipo" data-teste="backup-tipo" :class="SELECT">
          <option value="">Manuais e automáticos</option><option value="automatico">Só automáticos</option><option value="manual">Só manuais</option>
        </select>
        <select v-model="fl.estado" @change="carregarLista(0)" aria-label="Estado" data-teste="backup-estado" :class="SELECT">
          <option value="">Os que existem</option><option value="ok">Disponíveis</option><option value="erro">Falhados</option>
          <option value="apagado">Apagados pela retenção</option><option value="todos">Todos (com apagados)</option>
        </select>
        <span class="flex items-center gap-1 whitespace-nowrap">
          <label class="text-[11px] text-zinc-500">De <input type="date" v-model="fl.de" @change="carregarLista(0)" :max="fl.ate || hoje" aria-label="Data inicial" data-teste="backup-de" :class="DATA" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="date" v-model="fl.ate" @change="carregarLista(0)" :min="fl.de" :max="hoje" aria-label="Data final" data-teste="backup-ate" :class="DATA" /></label>
        </span>
        <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        <button v-if="comFiltros" type="button" @click="limpar" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200" data-teste="backup-limpar">Limpar</button>
      </form>
      <p v-if="erroLista" class="text-xs text-red-400">{{ erroLista }}</p>
      <p v-else class="text-xs text-zinc-500" data-teste="backup-contagem">{{ lista.count }} backup(s){{ comFiltros ? ' com estes filtros' : '' }}</p>

      <!-- lista -->
      <div :class="['bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800 transition', aCarregar && 'opacity-60']" data-teste="backup-lista">
        <p v-if="!lista.results.length" class="p-6 text-sm text-zinc-500 text-center">
          {{ comFiltros ? 'Nenhum backup com estes filtros.' : 'Ainda não há backups.' }}
        </p>
        <div v-for="b in lista.results" :key="b.id" class="p-4 flex flex-wrap items-center gap-x-4 gap-y-2" data-teste="backup-linha">
          <font-awesome-icon :icon="['fas', b.apagado_em ? 'trash-can' : ICONE[b.estado]]" :spin="b.estado === 'a_correr'"
            :class="['w-4 h-4 shrink-0', b.apagado_em ? 'text-zinc-600' : COR[b.estado]]" />
          <div class="min-w-0 flex-1">
            <p :class="['text-sm font-semibold', b.apagado_em ? 'text-zinc-500' : 'text-zinc-100']">
              {{ quando(b.criado_em) }}
              <span :class="['ml-2 px-2 py-0.5 rounded-md text-[11px] font-bold',
                             b.tipo === 'manual' ? 'bg-sky-500/10 text-sky-300' : 'bg-zinc-800 text-zinc-400']">
                {{ b.tipo === 'manual' ? 'Manual' : 'Automático' }}
              </span>
            </p>
            <p class="text-xs text-zinc-500 mt-0.5 break-all">
              <template v-if="b.estado === 'ok'">{{ tamanho(b.tamanho) }} · {{ b.duracao_s }} s</template>
              <template v-else-if="b.estado === 'a_correr'">A correr…</template>
              <span v-else class="text-red-400">Falhou: {{ b.erro }}</span>
              <template v-if="b.pedido_por"> · por {{ b.pedido_por }}</template>
              <template v-if="b.descargas"> · descarregado {{ b.descargas }}×</template>
              <template v-if="b.apagado_em"> · apagado em {{ quando(b.apagado_em) }}</template>
              <span v-if="b.ensaio_ok === true" class="text-green-400"> · reposição testada</span>
              <span v-else-if="b.ensaio_ok === false" class="text-red-400"> · o ensaio de reposição falhou</span>
            </p>
          </div>
          <button v-if="b.disponivel" type="button" @click="descarregar(b)" :disabled="aDescarregar === b.id"
            class="px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-xs font-semibold text-zinc-200 disabled:opacity-40 transition flex items-center gap-1.5">
            <font-awesome-icon :icon="['fas', 'download']" class="w-3 h-3" /> Descarregar
          </button>
        </div>
      </div>
      <PaginacaoLista :count="lista.count" :limit="LIMITE" :offset="offset" @ir="carregarLista" />

      <!-- registo de descargas -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-3" data-teste="backup-descargas">
        <div>
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Registo de descargas</h3>
          <p class="text-xs text-zinc-500 mt-1">Cada backup tem os dados pessoais de todos os utilizadores: fica registado quem o descarregou.</p>
        </div>
        <form @submit.prevent="carregarDescargas(0)" class="flex flex-wrap items-center gap-2" data-teste="descargas-filtros">
          <input v-model.trim="fd.q" type="search" placeholder="Nome, email, IP ou ficheiro" aria-label="Pesquisar descargas" data-teste="descargas-q"
            class="flex-1 min-w-[180px] px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
        <span class="flex items-center gap-1 whitespace-nowrap">
          <label class="text-[11px] text-zinc-500">De <input type="date" v-model="fd.de" @change="carregarDescargas(0)" :max="fd.ate || hoje" aria-label="Data inicial das descargas" data-teste="descargas-de" :class="DATA" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="date" v-model="fd.ate" @change="carregarDescargas(0)" :min="fd.de" :max="hoje" aria-label="Data final das descargas" data-teste="descargas-ate" :class="DATA" /></label>
        </span>
          <button type="submit" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-bold">Procurar</button>
          <button v-if="fd.q || fd.de || fd.ate" type="button" @click="limparDescargas" class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-zinc-200">Limpar</button>
        </form>
        <p v-if="erroDescargas" class="text-xs text-red-400">{{ erroDescargas }}</p>
        <p v-else-if="!descargas.results.length" class="text-xs text-zinc-500">
          {{ fd.q || fd.de || fd.ate ? 'Nenhuma descarga com estes filtros.' : 'Ainda ninguém descarregou um backup.' }}
        </p>
        <ul v-else class="space-y-1.5" data-teste="descargas-lista">
          <li v-for="d in descargas.results" :key="d.id" class="text-xs text-zinc-400 break-all">
            <span class="text-zinc-200">{{ quando(d.quando) }}</span> · {{ d.por || '—' }}<template v-if="d.email"> ({{ d.email }})</template> · {{ d.backup }}
            <span v-if="d.ip" class="text-zinc-600"> · IP {{ d.ip }}</span>
          </li>
        </ul>
        <PaginacaoLista :count="descargas.count" :limit="LIMITE" :offset="dOffset" @ir="carregarDescargas" />
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

const LIMITE = 20
const ICONE = { ok: 'circle-check', erro: 'circle-xmark', a_correr: 'spinner' }
const COR = { ok: 'text-green-400', erro: 'text-red-400', a_correr: 'text-zinc-400' }
const SELECT = 'px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200'
const DATA = 'ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]'
const FILTROS = () => ({ q: '', tipo: '', estado: '', de: '', ate: '' })

function diaLocal (d = new Date()) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default {
  name: 'AdminBackups',
  components: { PaginacaoLista },
  data () {
    return {
      loading: true, aCarregar: false, resumo: {}, aFazer: false, aDescarregar: null, mensagem: null,
      aEnsaiar: false, aCopiar: false, temporizador: null,
      lista: { count: 0, results: [] }, offset: 0, fl: FILTROS(), erroLista: '',
      descargas: { count: 0, results: [] }, dOffset: 0, fd: { q: '', de: '', ate: '' }, erroDescargas: '',
      hoje: diaLocal(), LIMITE, ICONE, COR, SELECT, DATA,
    }
  },
  computed: {
    atrasado () {
      const u = this.resumo.ultimo_ok
      return !u || Date.now() - new Date(u).getTime() > 26 * 3600 * 1000
    },
    comFiltros () { return Object.values(this.fl).some(Boolean) },
    ensaio () { return this.resumo.ensaio || {} },
    ultimoEnsaio () { return this.ensaio.ultimo },
    media () { return this.resumo.media || {} },
    ultimaCopia () { return this.media.ultima },
    percentagemEspaco () {
      const t = this.ultimaCopia?.bytes_total || 0
      return Math.min(100, Math.round(t / (this.media.gratis_bytes || 1) * 100))
    },
    acimaLimite () { return (this.ultimaCopia?.bytes_total || 0) >= (this.media.limite_bytes || Infinity) },
    ensaioIcone () {
      if (this.ensaio.em_curso) return 'spinner'
      if (!this.ultimoEnsaio) return 'flask'
      return this.ultimoEnsaio.ok ? 'circle-check' : 'circle-xmark'
    },
  },
  beforeUnmount () { clearTimeout(this.temporizador) },
  async mounted () {
    await Promise.all([this.carregarLista(0), this.carregarDescargas(0)])
    this.loading = false
  },
  methods: {
    params (f, offset) {
      const p = { limit: LIMITE, offset }
      for (const [k, v] of Object.entries(f)) if (v) p[k] = v
      return p
    },
    async carregarLista (offset = this.offset) {
      this.aCarregar = true; this.erroLista = ''
      try {
        const { data } = await api.get('/app/admin/backups/', { params: this.params(this.fl, offset) })
        // a página ficou vazia (ex.: o último da página saiu): volta uma atrás
        if (!data.results.length && offset > 0 && data.count) return this.carregarLista(Math.max(0, offset - LIMITE))
        const estava = this.resumo.ensaio?.em_curso
        const copiava = this.resumo.media?.em_curso
        this.resumo = data.resumo
        this.lista = { count: data.count, results: data.results }
        this.offset = offset
        if (estava && !data.resumo.ensaio.em_curso) {
          this.mensagem = data.resumo.ensaio.ultimo?.ok
            ? { texto: 'Ensaio de reposição concluído: o backup repõe-se sem erros.' }
            : { erro: true, texto: 'O ensaio de reposição falhou — vê o detalhe abaixo. Os super-admins recebem um email.' }
        }
        if (copiava && !data.resumo.media.em_curso) {
          const c = data.resumo.media.ultima
          this.mensagem = c?.estado === 'ok'
            ? { texto: `Cópia das fotos e vídeos concluída: ${this.numero(c.copiados)} novos.` }
            : { erro: true, texto: 'A cópia das fotos e vídeos falhou — vê o detalhe abaixo. Os super-admins recebem um email.' }
        }
        // enquanto o worker ensaia ou copia, vai vendo de 5 em 5 segundos
        clearTimeout(this.temporizador)
        if (data.resumo.ensaio.em_curso || data.resumo.media.em_curso) this.temporizador = setTimeout(() => this.carregarLista(), 5000)
      } catch (e) {
        this.erroLista = e.response?.data?.detail || 'Não foi possível carregar os backups.'
      } finally { this.aCarregar = false }
    },
    async carregarDescargas (offset = this.dOffset) {
      this.erroDescargas = ''
      try {
        const { data } = await api.get('/app/admin/backups/descargas/', { params: this.params(this.fd, offset) })
        this.descargas = data
        this.dOffset = offset
      } catch (e) {
        this.erroDescargas = e.response?.data?.detail || 'Não foi possível carregar o registo de descargas.'
      }
    },
    limpar () { this.fl = FILTROS(); this.carregarLista(0) },
    async ensaiar () {
      this.aEnsaiar = true; this.mensagem = null
      try {
        const { data } = await api.post('/app/admin/backups/ensaiar/')
        this.mensagem = { texto: `A testar a reposição de ${data.nome}…` }
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível pedir o ensaio.' }
      } finally {
        this.aEnsaiar = false
        this.carregarLista()
      }
    },
    async copiarMedia () {
      this.aCopiar = true; this.mensagem = null
      try {
        await api.post('/app/admin/backups/media/copiar/')
        this.mensagem = { texto: 'A copiar as fotos e vídeos novos…' }
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível pedir a cópia.' }
      } finally {
        this.aCopiar = false
        this.carregarLista()
      }
    },
    numero (n) { return (n || 0).toLocaleString('pt-PT') },
    segundos (s) { return s >= 60 ? `${Math.round(s / 60)} min` : `${String(s).replace('.', ',')} s` },
    limparDescargas () { this.fd = { q: '', de: '', ate: '' }; this.carregarDescargas(0) },
    async fazer () {
      this.aFazer = true; this.mensagem = null
      try {
        const { data } = await api.post('/app/admin/backups/fazer/')
        this.mensagem = data.estado === 'ok'
          ? { texto: `Backup feito (${this.tamanho(data.tamanho)}).` }
          : { erro: true, texto: `O backup falhou: ${data.erro}` }
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'O backup falhou.' }
      } finally {
        this.aFazer = false
        this.hoje = diaLocal()
        this.carregarLista(0)       // o novo vai para o topo
      }
    },
    async descarregar (b) {
      this.aDescarregar = b.id; this.mensagem = null
      try {
        const { data } = await api.post(`/app/admin/backups/${b.id}/descarregar/`)
        const a = document.createElement('a')
        a.href = data.url; a.download = data.nome; a.rel = 'noopener'
        document.body.appendChild(a); a.click(); a.remove()
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível descarregar.' }
      } finally {
        this.aDescarregar = null
        this.carregarLista()
        this.carregarDescargas(0)
      }
    },
    quando (d) {
      return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
    },
    tamanho (b) {
      if (!b) return '0 KB'
      if (b >= 1e9) return `${(b / 1e9).toFixed(1).replace('.', ',')} GB`
      return b >= 1e6 ? `${(b / 1e6).toFixed(1).replace('.', ',')} MB` : `${Math.max(1, Math.round(b / 1e3))} KB`
    },
  },
}
</script>
