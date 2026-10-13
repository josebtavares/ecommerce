<template>
  <div class="min-h-screen bg-zinc-950 flex relative">

    <!-- Overlay mobile -->
    <div v-if="sidebarAberta"
         class="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
         @click="sidebarAberta = false" />

    <!-- Sidebar -->
    <aside :class="[
      'fixed lg:sticky lg:top-0 lg:h-screen lg:self-start inset-y-0 left-0 z-40 bg-zinc-900 border-r border-zinc-800 flex flex-col',
      'transition-all duration-300 ease-in-out',
      // mobile: slide in/out
      sidebarAberta ? 'translate-x-0 w-64' : '-translate-x-full lg:translate-x-0',
      // desktop: colapsável
      sidebarExpandida ? 'lg:w-64' : 'lg:w-16',
    ]">

      <!-- Header sidebar -->
      <div class="flex items-center gap-3 px-4 py-5 border-b border-zinc-800 flex-shrink-0 overflow-hidden">
        <div class="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <span v-if="sidebarExpandida || sidebarAberta"
              class="text-sm font-bold text-zinc-100 truncate transition-opacity">
          Painel Admin
        </span>
        <!-- Fechar no mobile -->
        <button @click="sidebarAberta = false"
          class="lg:hidden ml-auto w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Botão colapsar (desktop) -->
      <button @click="sidebarExpandida = !sidebarExpandida"
        class="hidden lg:flex absolute -right-3 top-6 w-6 h-6 rounded-full bg-zinc-700 border border-zinc-600
               items-center justify-center hover:bg-zinc-600 transition z-10">
        <svg xmlns="http://www.w3.org/2000/svg"
             :class="['h-3 w-3 text-zinc-300 transition-transform', sidebarExpandida ? '' : 'rotate-180']"
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- Nav -->
      <nav class="flex-1 min-h-0 overflow-y-auto py-4 space-y-1 px-2">
        <button v-for="item in seccoes" :key="item.key"
          @click="navegarPara(item.key)"
          :title="!sidebarExpandida ? item.label : ''"
          :class="[
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left',
            activeSection === item.key
              ? 'bg-red-600/15 text-red-400'
              : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800'
          ]">
          <font-awesome-icon :icon="['fas', item.icon]" class="flex-shrink-0 w-4 h-4" fixed-width />
          <span v-if="(sidebarExpandida || sidebarAberta) && contador(item.key)"
                class="order-last ml-auto min-w-[20px] h-5 px-1.5 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center">{{ contador(item.key) }}</span>
          <span v-if="sidebarExpandida || sidebarAberta"
                class="text-sm font-medium truncate">{{ item.label }}</span>
        </button>
      </nav>

      <!-- Footer -->
      <div class="border-t border-zinc-800 p-3 flex-shrink-0">
        <button @click="$router.push('/Home')"
          :title="!sidebarExpandida ? 'Voltar ao site' : ''"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800">
          <font-awesome-icon :icon="['fas', 'house']" class="flex-shrink-0 w-4 h-4" fixed-width />
          <span v-if="sidebarExpandida || sidebarAberta" class="text-sm font-medium">Voltar ao site</span>
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0"
         :class="sidebarExpandida ? 'lg:ml-0' : 'lg:ml-0'">

      <!-- Header -->
      <div class="sticky top-0 z-20 bg-zinc-950/90 backdrop-blur border-b border-zinc-800 px-4 lg:px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <!-- Botão menu mobile -->
          <button @click="sidebarAberta = true"
            class="lg:hidden w-9 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div>
            <h1 class="text-base lg:text-lg font-bold text-zinc-100 leading-tight">{{ secaoActiva?.label }}</h1>
            <p class="text-xs text-zinc-500 hidden sm:block">{{ roleLabel }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 lg:gap-3">
          <NotificacaoSino />
          <div class="hidden sm:block text-right">
            <p class="text-sm font-semibold text-zinc-200">{{ user?.username }}</p>
            <p class="text-xs text-zinc-500">{{ user?.role_admin }}</p>
          </div>
          <div class="w-8 h-8 rounded-full bg-red-600/20 flex items-center justify-center flex-shrink-0">
            <span class="text-red-400 text-xs font-bold">{{ user?.username?.charAt(0)?.toUpperCase() }}</span>
          </div>
        </div>
      </div>

      <!-- Content -->
      <!-- pb-24: espaço para o balão do chat (canto inferior direito) não tapar o fim do conteúdo -->
      <div class="flex-1 overflow-auto p-4 pb-24 lg:p-6 lg:pb-24">
        <AdminDashboard    v-if="activeSection === 'dashboard'"    />
        <AdminLojas        v-else-if="activeSection === 'lojas'"        />
        <AdminUtilizadores v-else-if="activeSection === 'utilizadores'" />
        <AdminProdutos     v-else-if="activeSection === 'produtos'"     />
        <AdminEncomendas   v-else-if="activeSection === 'encomendas'"   />
        <AdminPagamentos   v-else-if="activeSection === 'pagamentos'"   />
        <AdminTipos        v-else-if="activeSection === 'tipos'"        />
        <AdminComissoes    v-else-if="activeSection === 'comissoes'"    />
        <AdminCategorias   v-else-if="activeSection === 'categorias'"   />
        <AdminRelatorios   v-else-if="activeSection === 'relatorios'"   />
        <AdminCategoriasDestaque v-else-if="activeSection === 'categorias_destaque'" />
        <AdminPaginas      v-else-if="activeSection === 'paginas'"      />
        <AdminPOS          v-else-if="activeSection === 'pos'"          />
        <AdminSuporte      v-else-if="activeSection === 'suporte_chat'" />
        <AdminDenuncias    v-else-if="activeSection === 'denuncias'"    @pendentes="n => denunciasPendentes = n" />
        <AdminPlataforma   v-else-if="activeSection === 'plataforma'"   />
      </div>
    </div>

  </div>
</template>

<script>
import AdminDashboard    from './AdminDashboard.vue'
import AdminLojas        from './AdminLojas.vue'
import AdminUtilizadores from './AdminUtilizadores.vue'
import AdminProdutos     from './AdminProdutos.vue'
import AdminEncomendas   from './AdminEncomendas.vue'
import AdminPagamentos   from './AdminPagamentos.vue'
import AdminTipos        from './AdminTipos.vue'
import AdminComissoes    from './AdminComissoes.vue'
import AdminCategorias   from './AdminCategorias.vue'
import AdminRelatorios   from './AdminRelatorios.vue'
import AdminCategoriasDestaque from './AdminCategoriasDestaque.vue'
import AdminPaginas      from './AdminPaginas.vue'
import AdminPOS          from './AdminPOS.vue'
import AdminSuporte      from './AdminSuporte.vue'
import AdminDenuncias    from './AdminDenuncias.vue'
import AdminPlataforma   from './AdminPlataforma.vue'
import api from '@/services/api'
import { chat } from '@/services/chat'
import NotificacaoSino   from '@/components/notificacao/notificacaoSino.vue'

const SECCOES = [
  // icon: nome do ícone Font Awesome (solid)
  { key: 'dashboard',    label: 'Dashboard',     icon: 'chart-pie',     permissao: 'ver_stats'           },
  { key: 'relatorios',   label: 'Relatórios',    icon: 'chart-line',    permissao: 'ver_relatorios'    },
  { key: 'categorias',   label: 'Categorias',    icon: 'tags',          permissao: 'gerir_lojas'         },
  { key: 'lojas',        label: 'Lojas',         icon: 'store',         permissao: 'gerir_lojas'         },
  { key: 'utilizadores', label: 'Utilizadores',  icon: 'users',         permissao: 'gerir_utilizadores'  },
  { key: 'produtos',     label: 'Produtos',      icon: 'box',           permissao: 'gerir_produtos'      },
  { key: 'categorias_destaque', label: 'Categorias em Destaque', icon: 'fire', permissao: 'gerir_categorias_destaque' },

  { key: 'encomendas',   label: 'Encomendas',    icon: 'bag-shopping',  permissao: 'gerir_encomendas'   },
  { key: 'pagamentos',   label: 'Pagamentos',    icon: 'credit-card',   permissao: 'gerir_pagamentos'    },
  { key: 'tipos',        label: 'Tipos Globais', icon: 'shapes',        permissao: 'gerir_tipos_globais' },
  { key: 'comissoes',    label: 'Comissões',     icon: 'coins',         permissao: 'gerir_comissoes'     },
  { key: 'paginas',      label: 'Páginas & Ajuda', icon: 'file-lines',  permissao: 'gerir_conteudo'    },
  { key: 'pos',          label: 'POS',             icon: 'cash-register', permissao: 'ver_pos'           },
  { key: 'suporte_chat', label: 'Suporte (chat)',  icon: 'headset',       permissao: 'atender_suporte'   },
  { key: 'denuncias',    label: 'Denúncias',       icon: 'flag',          permissao: 'moderar_chat'      },
  { key: 'plataforma',   label: 'Definições',      icon: 'globe',         permissao: 'gerir_plataforma'  },

]

const PERMISSOES_ADMIN = {
  superadmin:   ['ver_stats','gerir_lojas','gerir_utilizadores','gerir_produtos','gerir_encomendas','gerir_pagamentos','gerir_tipos_globais','gerir_comissoes','ver_relatorios','gerir_categorias_destaque','gerir_conteudo','ver_pos','gerir_pos','atender_suporte','moderar_chat','gerir_plataforma'],
  moderador:    ['ver_stats','gerir_lojas','gerir_produtos','gerir_encomendas','gerir_pagamentos','gerir_tipos_globais','ver_relatorios','moderar_chat'],
  suporte:      ['ver_stats','gerir_utilizadores','gerir_lojas','gerir_encomendas','gerir_pagamentos','ver_relatorios','gerir_conteudo','ver_pos','gerir_pos','atender_suporte'],
  contabilista: ['ver_stats','gerir_pagamentos','gerir_encomendas','ver_relatorios','ver_pos'],
}

export default {
  name: 'AdminLayout',
  components: {
    AdminDashboard, AdminLojas, AdminUtilizadores, AdminProdutos,
    AdminEncomendas, AdminPagamentos, AdminTipos, AdminComissoes,
    AdminCategorias, NotificacaoSino,AdminRelatorios,AdminCategoriasDestaque, AdminPaginas, AdminPOS, AdminSuporte, AdminDenuncias, AdminPlataforma,
  },

  data () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const permissoes = PERMISSOES_ADMIN[user.role_admin] || []
    const seccoes = SECCOES.filter(s => permissoes.includes(s.permissao))
    return {
      sidebarExpandida: true,
      sidebarAberta:    false,
      user,
      seccoes,
      activeSection: seccoes[0]?.key || 'dashboard',
      denunciasPendentes: 0,
    }
  },

  computed: {
    secaoActiva () { return this.seccoes.find(s => s.key === this.activeSection) },
    roleLabel () {
      const map = {
        superadmin:   'Super Administrador',
        moderador:    'Moderador',
        suporte:      'Suporte',
        contabilista: 'Contabilista',
      }
      return map[this.user?.role_admin] || ''
    },
  },

  created () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!user.is_staff || !user.role_admin) this.$router.push('/')
    // denúncias por analisar no menu (só para quem modera)
    if (this.seccoes.some(s => s.key === 'denuncias')) {
      this.carregarPendentes()
      this.temporizadorDenuncias = setInterval(this.carregarPendentes, 60000)
    }
  },

  beforeUnmount () {
    clearInterval(this.temporizadorDenuncias)
  },

  methods: {
    navegarPara (key) {
      this.activeSection = key
      this.sidebarAberta = false
    },
    // contadores no menu: mensagens do suporte por ler e denúncias por analisar
    contador (key) {
      if (key === 'suporte_chat') return chat.caixas.find(c => c.tipo === 'suporte')?.nao_lidas || 0
      if (key === 'denuncias') return this.denunciasPendentes
      return 0
    },
    async carregarPendentes () {
      try {
        const { data } = await api.get('/api/chat/denuncias/', { params: { estado: 'pendente' } })
        this.denunciasPendentes = data.pendentes
      } catch { /* sem permissão ou sem rede — o contador fica como está */ }
    },
  },
}
</script>
