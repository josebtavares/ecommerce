<!-- AdminPOS.vue — visão e suporte da plataforma sobre todos os POS
     (standalone, integrado, híbrido). O dia-a-dia é gerido pelo dono no dashboard do POS. -->
<template>
  <div class="space-y-5">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">POS</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Todos os pontos de venda da plataforma — métricas e acções de suporte.</p>
    </div>

    <!-- Resumo -->
    <div v-if="resumo" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[11px] uppercase tracking-wider text-zinc-500">Total</p>
        <p class="text-2xl font-black text-zinc-100 mt-1">{{ resumo.total }}</p>
        <p class="text-[11px] text-zinc-500 mt-1">
          {{ resumo.por_modo.standalone }} standalone · {{ resumo.por_modo.hibrido }} híbridos · {{ resumo.por_modo.integrado }} integrados
        </p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[11px] uppercase tracking-wider text-zinc-500">Activos</p>
        <p class="text-2xl font-black text-green-400 mt-1">{{ resumo.ativos }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[11px] uppercase tracking-wider text-zinc-500">Suspensos</p>
        <p class="text-2xl font-black mt-1" :class="resumo.suspensos ? 'text-red-400' : 'text-zinc-100'">{{ resumo.suspensos }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[11px] uppercase tracking-wider text-zinc-500">Vendas {{ resumo.dias }} dias</p>
        <p class="text-2xl font-black text-zinc-100 mt-1">{{ money(resumo.vendas_30d) }}</p>
      </div>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-2 items-center">
      <div class="relative flex-1 min-w-[220px]">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="filtros.q" @input="debouncedFetch" placeholder="Nome, código, dono ou loja…"
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>
      <select v-for="f in selects" :key="f.key" v-model="filtros[f.key]" @change="fetchLista(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none">
        <option v-for="o in f.opcoes" :key="o[0]" :value="o[0]">{{ o[1] }}</option>
      </select>
      <select v-model.number="limit" @change="fetchLista(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none">
        <option :value="10">10 / pág.</option>
        <option :value="20">20 / pág.</option>
        <option :value="50">50 / pág.</option>
      </select>
    </div>
    <p class="text-xs text-zinc-500 -mt-2">{{ totalCount }} POS</p>

    <!-- Lista -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>
    <p v-else-if="erro" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erro }}</p>
    <div v-else-if="!lista.length" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      Nenhum POS encontrado.
    </div>
    <div v-else class="space-y-3">
      <div v-for="p in lista" :key="p.id" @click="abrir(p)"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 hover:border-zinc-700 transition cursor-pointer group">
        <div class="flex items-center gap-3 flex-wrap">
          <div class="w-11 h-11 rounded-xl bg-zinc-800 flex items-center justify-center text-zinc-400 flex-shrink-0"><font-awesome-icon :icon="['fas', 'cash-register']" class="w-4 h-4" /></div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-sm font-bold text-zinc-200 group-hover:text-red-400 transition">{{ p.nome }}</p>
              <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-400 font-mono">{{ p.codigo_pos }}</span>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', MODOS[p.modo].cls]">{{ MODOS[p.modo].label }}</span>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', ESTADOS[p.estado].cls]">{{ ESTADOS[p.estado].label }}</span>
            </div>
            <p class="text-xs text-zinc-500 truncate mt-0.5">
              {{ p.dono?.nome }} ({{ p.dono?.username }})
              <template v-if="p.loja"> · <font-awesome-icon :icon="['fas', 'store']" class="text-zinc-600" /> {{ p.loja.nome }}</template>
              · {{ p.membros }} membros
              · última actividade {{ quando(p.ultima_atividade) }}
            </p>
          </div>
          <div class="text-right flex-shrink-0">
            <p class="text-sm font-bold text-zinc-100">{{ money(p.vendas_30d) }}</p>
            <p class="text-[11px] text-zinc-500">{{ p.contas_30d }} contas · 30d</p>
            <p v-if="p.contas_abertas" class="text-[11px] text-amber-400">{{ p.contas_abertas }} abertas</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchLista(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button v-for="n in paginasVisiveis" :key="n" @click="fetchLista(n)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition', n === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ n }}
        </button>
        <button @click="fetchLista(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </div>

    <!-- ═══ DETALHE ═══ -->
    <Teleport to="body">
      <div v-if="aberto" class="fixed inset-0 z-[150] flex justify-end bg-black/60 backdrop-blur-sm" @click.self="fechar">
        <aside class="w-full max-w-2xl h-full bg-zinc-950 border-l border-zinc-800 flex flex-col">
          <header class="flex items-start justify-between gap-3 px-5 py-4 border-b border-zinc-800">
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="text-base font-bold text-zinc-100">{{ aberto.nome }}</h3>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', MODOS[aberto.modo].cls]">{{ MODOS[aberto.modo].label }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', ESTADOS[aberto.estado].cls]">{{ ESTADOS[aberto.estado].label }}</span>
              </div>
              <p class="text-xs text-zinc-500 mt-0.5 font-mono">{{ aberto.codigo_pos }} · criado {{ data(aberto.criado_em) }}</p>
            </div>
            <button @click="fechar" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-400 flex-shrink-0">×</button>
          </header>

          <div class="flex-1 overflow-y-auto p-5 space-y-5">
            <div v-if="loadingDetalhe" class="space-y-3">
              <div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
            </div>

            <template v-else-if="d">
              <!-- Suspensão -->
              <div v-if="d.suspenso" class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-sm text-red-300">
                <b>Suspenso</b> desde {{ data(d.suspenso_em) }} — {{ d.suspenso_motivo }}
              </div>

              <!-- Info -->
              <div class="grid grid-cols-2 gap-3 text-xs">
                <div class="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
                  <p class="text-zinc-500">Dono</p>
                  <p class="text-zinc-200 font-semibold mt-0.5">{{ d.dono?.nome }}</p>
                  <p class="text-zinc-500">{{ d.dono?.email }}</p>
                </div>
                <div class="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
                  <p class="text-zinc-500">Loja ligada</p>
                  <p class="text-zinc-200 font-semibold mt-0.5">{{ d.loja?.nome || '— (standalone)' }}</p>
                  <p class="text-zinc-500">{{ d.produtos_proprios }} produtos próprios · {{ d.mesas }} mesas</p>
                </div>
              </div>

              <!-- Métricas -->
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
                  <p class="text-[11px] text-zinc-500">Vendas 30d</p>
                  <p class="text-lg font-black text-zinc-100">{{ money(d.vendas_30d) }}</p>
                </div>
                <div class="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
                  <p class="text-[11px] text-zinc-500">Contas 30d</p>
                  <p class="text-lg font-black text-zinc-100">{{ d.contas_30d }}</p>
                </div>
                <div class="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
                  <p class="text-[11px] text-zinc-500">Ticket médio</p>
                  <p class="text-lg font-black text-zinc-100">{{ money(d.ticket_medio_30d) }}</p>
                </div>
              </div>

              <!-- Vendas por dia -->
              <section v-if="d.vendas_por_dia.length" class="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
                <p class="text-xs font-bold text-zinc-400 mb-3">Vendas por dia (30 dias)</p>
                <div class="flex items-end gap-1 h-24">
                  <div v-for="v in d.vendas_por_dia" :key="v.dia" class="flex-1 bg-red-500/70 hover:bg-red-400 rounded-t transition min-w-[4px]"
                       :style="{ height: Math.max(4, Number(v.total) / maxVenda * 100) + '%' }"
                       :title="`${data(v.dia)} · ${money(v.total)} · ${v.contas} contas`"></div>
                </div>
              </section>

              <!-- Top produtos -->
              <section v-if="d.top_produtos.length" class="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
                <p class="text-xs font-bold text-zinc-400 mb-2">Mais vendidos (30 dias)</p>
                <div v-for="t in d.top_produtos" :key="t.nome" class="flex justify-between py-1.5 border-b border-zinc-800 last:border-0 text-xs">
                  <span class="text-zinc-300 truncate">{{ t.nome }}</span>
                  <span class="text-zinc-500 flex-shrink-0 ml-3">{{ t.quantidade }} un.<template v-if="t.em_menus"> ({{ t.em_menus }} em menus)</template> · {{ money(t.total) }}</span>
                </div>
              </section>

              <!-- Contas abertas -->
              <section class="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
                <p class="text-xs font-bold text-zinc-400 mb-2">Contas abertas ({{ d.contas_abertas_lista.length }})</p>
                <p v-if="!d.contas_abertas_lista.length" class="text-xs text-zinc-600">Nenhuma.</p>
                <div v-for="c in d.contas_abertas_lista" :key="c.id" class="flex items-center gap-3 py-2 border-b border-zinc-800 last:border-0 text-xs">
                  <div class="flex-1 min-w-0">
                    <p class="text-zinc-200">#{{ c.id }} · Mesa {{ c.mesa ?? '—' }} · {{ c.itens }} itens · {{ money(c.total) }}</p>
                    <p class="text-zinc-500">aberta {{ quando(c.criada_em) }}<template v-if="c.atendente"> · {{ c.atendente }}</template></p>
                  </div>
                  <button v-if="podeGerir" @click="cancelarConta(c)"
                    class="px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 font-semibold flex-shrink-0">Cancelar</button>
                </div>
              </section>

              <!-- Equipa -->
              <section class="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
                <p class="text-xs font-bold text-zinc-400 mb-2">Equipa ({{ d.equipa.length }})</p>
                <p v-if="!d.equipa.length" class="text-xs text-zinc-600">Sem membros.</p>
                <div v-for="m in d.equipa" :key="m.id" class="py-2 border-b border-zinc-800 last:border-0 text-xs">
                  <div class="flex items-center gap-3">
                    <div class="flex-1 min-w-0">
                      <p class="text-zinc-200">{{ m.nome }} <span class="text-zinc-500">@{{ m.username }}</span></p>
                      <p class="text-zinc-500 capitalize">{{ m.papel }}<template v-if="!m.ativo"> · inactivo</template></p>
                    </div>
                    <button v-if="podeGerir" @click="pwMembro = pwMembro === m.id ? null : m.id; novaPw = ''; erroPw = ''"
                      class="px-2.5 py-1 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 font-semibold flex-shrink-0">
                      Redefinir password
                    </button>
                  </div>
                  <div v-if="pwMembro === m.id" class="mt-2 p-3 rounded-lg bg-zinc-950 border border-zinc-800 space-y-2">
                    <input v-model="novaPw" type="password" autocomplete="new-password" placeholder="Nova password"
                      class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
                    <PasswordForca :password="novaPw" :isDark="true" />
                    <p v-if="erroPw" class="text-red-400">{{ erroPw }}</p>
                    <button @click="redefinirPassword(m)" :disabled="!passwordValida(novaPw)"
                      class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold disabled:bg-zinc-800 disabled:text-zinc-500">Guardar</button>
                  </div>
                </div>
              </section>

              <!-- Histórico -->
              <section v-if="d.historico.length" class="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
                <p class="text-xs font-bold text-zinc-400 mb-2">Últimas contas</p>
                <div v-for="h in d.historico" :key="h.id" class="flex justify-between py-1.5 border-b border-zinc-800 last:border-0 text-xs">
                  <span class="text-zinc-400">#{{ h.id }} · Mesa {{ h.mesa ?? '—' }} · {{ data(h.data) }}</span>
                  <span :class="h.status === 'cancelada' ? 'text-red-400' : 'text-zinc-300'">
                    {{ h.status === 'cancelada' ? 'cancelada' : `${money(h.total)} · ${h.metodo_pagamento || '—'}` }}
                  </span>
                </div>
              </section>

              <!-- Ver o POS só para leitura (super-admin) — backend utils/ver_loja.py -->
              <section v-if="podeVerPos" class="bg-zinc-900 rounded-xl border border-zinc-800 p-4 space-y-3" data-teste="admin-ver-pos">
                <p class="text-xs font-bold text-zinc-400">
                  <font-awesome-icon :icon="['fas', 'eye']" class="mr-1.5" />Dashboard do POS
                </p>
                <p class="text-xs text-zinc-500">
                  Abre o POS como o dono o vê, noutro separador e só para leitura (vendas, faturas, turnos, relatórios)
                  — também com o POS suspenso ou o dono banido. Cada acesso fica registado; dura 2 horas.
                </p>
                <button @click="verPOS" :disabled="aAbrirPOS" data-teste="btn-ver-pos"
                  class="w-full py-2.5 rounded-xl text-sm font-bold transition bg-sky-500/15 text-sky-400 hover:bg-sky-500/25 disabled:opacity-50">
                  {{ aAbrirPOS ? 'A abrir…' : 'Ver POS (só leitura)' }}
                  <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="ml-1" />
                </button>
                <div v-if="acessosAdmin.length" class="space-y-1">
                  <p class="text-[11px] text-zinc-500">Últimos acessos</p>
                  <p v-for="a in acessosAdmin" :key="a.id" class="text-[11px] text-zinc-400" data-teste="acesso-admin">
                    {{ a.quando }} · {{ a.admin }}
                  </p>
                </div>
              </section>

              <!-- Exportar dados (super-admin) — também os POS sem loja -->
              <section v-if="podeExportar" class="bg-zinc-900 rounded-xl border border-zinc-800 p-4 space-y-3" data-teste="admin-exportar-pos">
                <p class="text-xs font-bold text-zinc-400">
                  <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1.5" />Exportar dados
                </p>
                <ExportacoesLoja :base="`/app/admin/pos/${d.id}/exportacoes/`" pos />
              </section>
            </template>
          </div>

          <!-- Acções -->
          <footer v-if="d && podeGerir" class="px-5 py-4 border-t border-zinc-800 space-y-3">
            <div v-if="aSuspender" class="space-y-2">
              <textarea v-model="motivo" rows="2" maxlength="300" placeholder="Motivo da suspensão (mostrado ao dono)"
                class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500"></textarea>
              <div class="flex gap-2 justify-end">
                <button @click="aSuspender = false" class="px-4 py-2 rounded-xl text-sm text-zinc-400 hover:text-zinc-200">Cancelar</button>
                <button @click="suspender" :disabled="!motivo.trim() || acao"
                  class="px-4 py-2 rounded-xl text-sm font-bold bg-red-600 hover:bg-red-500 text-white disabled:bg-zinc-800 disabled:text-zinc-500">Confirmar suspensão</button>
              </div>
            </div>
            <div v-else class="flex gap-2 flex-wrap justify-end">
              <button v-if="d.loja" @click="desligarLoja" :disabled="acao"
                class="px-4 py-2 rounded-xl text-sm font-semibold border border-zinc-700 text-zinc-300 hover:border-zinc-500">Desligar loja</button>
              <button v-if="d.suspenso" @click="reativar" :disabled="acao"
                class="px-4 py-2 rounded-xl text-sm font-bold bg-green-600 hover:bg-green-500 text-white">Reactivar POS</button>
              <button v-else @click="aSuspender = true; motivo = ''"
                class="px-4 py-2 rounded-xl text-sm font-bold bg-red-600/15 text-red-400 hover:bg-red-600/25">Suspender POS</button>
            </div>
          </footer>
        </aside>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import PasswordForca from '@/components/forms/PasswordForca.vue'
import { passwordValida } from '@/utils/password'
import ExportacoesLoja from '@/components/ExportacoesLoja.vue'
import { fichaDaRota, irParaFicha } from '@/utils/ficha'

const MODOS = {
  standalone: { label: 'Standalone', cls: 'bg-purple-500/15 text-purple-300' },
  integrado:  { label: 'Integrado',  cls: 'bg-blue-500/15 text-blue-300' },
  hibrido:    { label: 'Híbrido',    cls: 'bg-cyan-500/15 text-cyan-300' },
}
const ESTADOS = {
  ativo:    { label: 'Activo',   cls: 'bg-green-500/15 text-green-400' },
  inativo:  { label: 'Inactivo', cls: 'bg-zinc-700/60 text-zinc-400' },
  suspenso: { label: 'Suspenso', cls: 'bg-red-500/15 text-red-400' },
}

export default {
  name: 'AdminPOS',
  components: { PasswordForca, ExportacoesLoja },

  props: {
    podeExportar: { type: Boolean, default: false },   // permissão exportar_lojas (super-admin)
    podeVerPos: { type: Boolean, default: false },     // permissão ver_backoffice_lojas (super-admin)
  },

  data () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      MODOS, ESTADOS,
      podeGerir: ['superadmin', 'suporte'].includes(user.role_admin),
      lista: [], resumo: null, loading: true, erro: '',
      totalCount: 0, page: 1, limit: 20, debounceTimer: null,
      filtros: { q: '', modo: '', estado: '', loja: '', ordem: '' },
      selects: [
        { key: 'modo',   opcoes: [['', 'Todos os modos'], ['standalone', 'Standalone'], ['hibrido', 'Híbrido'], ['integrado', 'Integrado']] },
        { key: 'estado', opcoes: [['', 'Todos os estados'], ['ativo', 'Activos'], ['suspenso', 'Suspensos'], ['inativo', 'Inactivos']] },
        { key: 'loja',   opcoes: [['', 'Com ou sem loja'], ['com', 'Com loja'], ['sem', 'Sem loja']] },
        { key: 'ordem',  opcoes: [['', 'Mais recentes'], ['vendas', 'Mais vendas (30d)'], ['atividade', 'Actividade recente']] },
      ],
      aberto: null, d: null, loadingDetalhe: false,
      aSuspender: false, motivo: '', acao: false,
      pwMembro: null, novaPw: '', erroPw: '',
      acessosAdmin: [], aAbrirPOS: false,
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
    maxVenda () { return Math.max(1, ...(this.d?.vendas_por_dia || []).map(v => Number(v.total))) },
  },

  // a ficha aberta vem do endereço (/admin/pos/<id>): refresh, voltar e links das notificações
  watch: { '$route.params.ficha' () { this.carregarFicha() } },

  created () { this.fetchLista(); this.carregarFicha() },

  methods: {
    passwordValida,

    money (v) { return formatarDinheiro(Number(v || 0)) },
    data (iso) { return iso ? new Date(iso).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short', year: 'numeric' }) : '—' },
    quando (iso) {
      if (!iso) return 'nunca'
      const dias = Math.floor((Date.now() - new Date(iso)) / 86400000)
      if (dias <= 0) return 'hoje'
      if (dias === 1) return 'ontem'
      return dias < 30 ? `há ${dias} dias` : this.data(iso)
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchLista(1), 350)
    },

    async fetchLista (pagina = this.page) {
      this.page = pagina
      this.loading = true
      this.erro = ''
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        Object.entries(this.filtros).forEach(([k, v]) => { if (v) params[k] = v })
        const { data } = await api.get('/app/admin/pos/', { params })
        this.lista = data.results
        this.totalCount = data.count
        this.resumo = data.resumo
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao carregar os POS.'
      } finally {
        this.loading = false
      }
    },

    abrir (p) { irParaFicha(this.$router, this.$route, p.id) },

    async carregarFicha () {
      const id = fichaDaRota(this.$route)
      if (!id) { this.aberto = null; this.d = null; return }
      if (this.aberto?.id === id) return
      const p = this.lista.find(x => x.id === id)
      if (p) return this.abrirFicha(p)
      try {
        const { data } = await api.get(`/app/admin/pos/${id}/`)
        if (fichaDaRota(this.$route) === id) this.abrirFicha(data)
      } catch { irParaFicha(this.$router, this.$route, null, true) }   // POS que não existe
    },

    async abrirFicha (p) {
      this.aberto = p
      this.aSuspender = false
      this.pwMembro = null
      this.carregarAcessos(p)
      await this.carregarDetalhe()
    },

    async carregarAcessos (p) {
      this.acessosAdmin = []
      if (!this.podeVerPos) return
      try {
        const { data } = await api.get(`/app/admin/pos/${p.id}/ver/`)
        if (this.aberto?.id === p.id) this.acessosAdmin = data.acessos
      } catch { /* a lista não é essencial */ }
    },

    async verPOS () {
      // o separador abre-se já (no clique), senão o browser bloqueia-o como pop-up
      const separador = window.open('', '_blank')
      const p = this.aberto
      this.aAbrirPOS = true
      try {
        const { data } = await api.post(`/app/admin/pos/${p.id}/ver/`)
        const destino = `/pos/dashboard#ver_admin=${encodeURIComponent(data.token)}`
        if (separador) { separador.opener = null; separador.location = destino }
        else window.location.href = destino
        this.carregarAcessos(p)
      } catch (e) {
        separador?.close()
        toast.error(e.response?.data?.detail || 'Não foi possível abrir o POS.')
      } finally { this.aAbrirPOS = false }
    },

    async carregarDetalhe () {
      this.loadingDetalhe = true
      try {
        const { data } = await api.get(`/app/admin/pos/${this.aberto.id}/`)
        this.d = data
        this.aberto = { ...this.aberto, ...data }
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Erro ao carregar o POS.')
      } finally {
        this.loadingDetalhe = false
      }
    },

    fechar () { irParaFicha(this.$router, this.$route, null) },

    // executa uma acção, recarrega detalhe + lista e mostra o resultado
    async executar (fn, okMsg) {
      this.acao = true
      try {
        const { data } = await fn()
        toast.success(data?.detail || okMsg)
        await Promise.all([this.carregarDetalhe(), this.fetchLista()])
        return true
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível concluir a acção.')
        return false
      } finally {
        this.acao = false
      }
    },

    async suspender () {
      const ok = await this.executar(() => api.post(`/app/admin/pos/${this.d.id}/suspender/`, { motivo: this.motivo.trim() }), 'POS suspenso.')
      if (ok) this.aSuspender = false
    },

    reativar () {
      return this.executar(() => api.post(`/app/admin/pos/${this.d.id}/reativar/`), 'POS reactivado.')
    },

    desligarLoja () {
      if (!confirm(`Desligar "${this.d.nome}" da loja "${this.d.loja.nome}"? O POS passa a standalone.`)) return
      return this.executar(() => api.post(`/app/admin/pos/${this.d.id}/desligar-loja/`), 'Loja desligada.')
    },

    cancelarConta (c) {
      const motivo = window.prompt(`Cancelar a conta #${c.id} (${this.money(c.total)})? O stock é reposto e a mesa libertada.\n\nMotivo:`, '')
      if (motivo === null) return
      return this.executar(() => api.post(`/app/admin/pos/${this.d.id}/contas/${c.id}/cancelar/`, { motivo }), 'Conta cancelada.')
    },

    async redefinirPassword (m) {
      this.erroPw = ''
      try {
        const { data } = await api.post(`/app/admin/pos/${this.d.id}/membros/${m.id}/password/`, { nova_password: this.novaPw })
        toast.success(data.detail)
        this.pwMembro = null
        this.novaPw = ''
      } catch (e) {
        this.erroPw = e.response?.data?.detail || 'Erro ao redefinir.'
      }
    },
  },
}
</script>
