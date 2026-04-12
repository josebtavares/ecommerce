<template>
  <div class="min-h-screen bg-zinc-950 flex relative">

    <!-- ═══ OVERLAY MOBILE ═══ -->
    <div v-if="sidebarAberta"
         class="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
         @click="sidebarAberta = false" />

    <!-- ═══ SIDEBAR ═══ -->
    <aside :class="[
      'fixed lg:relative inset-y-0 left-0 z-40 w-72 bg-zinc-900 border-r border-zinc-800 flex flex-col',
      'transition-transform duration-300 ease-in-out',
      sidebarAberta ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]">

      <!-- Loja info -->
      <div class="p-5 border-b border-zinc-800 flex items-center justify-between">
        <div v-if="loadingLoja" class="flex items-center gap-3 flex-1">
          <div class="w-10 h-10 rounded-xl bg-zinc-800 animate-pulse flex-shrink-0"></div>
          <div class="flex-1 space-y-1">
            <div class="h-3 bg-zinc-800 rounded animate-pulse w-3/4"></div>
            <div class="h-2 bg-zinc-800 rounded animate-pulse w-1/2"></div>
          </div>
        </div>
        <div v-else-if="loja" class="flex items-center gap-3 flex-1 min-w-0">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-10 h-10 rounded-xl object-cover flex-shrink-0" />
          <div v-else class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center flex-shrink-0">
            <span class="text-sm font-bold text-zinc-400">{{ loja.nome?.charAt(0) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-zinc-100 truncate">{{ loja.nome }}</p>
            <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded uppercase', roleColor]">
              {{ loja.minha_role }}
            </span>
          </div>
        </div>
        <!-- Fechar sidebar no mobile -->
        <button @click="sidebarAberta = false"
          class="lg:hidden ml-2 w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Nav -->
      <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
        <p class="text-xs font-semibold text-zinc-600 uppercase tracking-wider px-3 mb-2">Gestão</p>
        <BackofficeSidebarItem
          v-for="item in navItems" :key="item.key"
          :icon="item.icon" :label="item.label"
          :active="activeSection === item.key"
          @click="navegarPara(item.key)"
        />
        <div v-if="navItems.length === 0 && !loadingLoja"
             class="px-3 py-4 text-xs text-zinc-600 text-center">
          Sem permissões nesta loja.
        </div>
      </nav>

      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800 space-y-1">
        <button @click="$router.push(`/loja/${lojaId}`)"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Ver loja pública
        </button>
        <button @click="$router.push('/Home')"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Voltar ao marketplace
        </button>
      </div>
    </aside>

    <!-- ═══ MAIN ═══ -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">

      <!-- Header -->
      <header class="bg-zinc-900 border-b border-zinc-800 px-4 lg:px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-3">
          <!-- Botão menu mobile -->
          <button @click="sidebarAberta = true"
            class="lg:hidden w-9 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div>
            <h1 class="text-base lg:text-lg font-bold text-zinc-100 leading-tight">{{ currentNavItem?.label }}</h1>
            <p class="text-xs text-zinc-500 hidden sm:block">{{ loja?.nome }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 lg:gap-3">
          <NotificacaoSino />
          <span class="text-xs text-zinc-600 hidden sm:block">{{ user.username }}</span>
        </div>
      </header>

      <!-- Sem permissão -->
      <div v-if="!loadingLoja && !temPermissao(activeSection)"
           class="flex-1 flex items-center justify-center text-center p-6">
        <div>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-zinc-700 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <p class="text-zinc-400 font-semibold">Sem permissão</p>
          <p class="text-xs text-zinc-600 mt-1">O teu role <span class="text-zinc-400">{{ loja?.minha_role }}</span> não tem acesso a esta secção.</p>
        </div>
      </div>

      <!-- Content -->
      <main v-else class="flex-1 overflow-auto p-4 lg:p-6">
        <BackofficeDashboard     v-if="activeSection === 'dashboard'"      :loja-id="lojaId" />
        <BackofficeEncomendas    v-else-if="activeSection === 'encomendas'"    :loja-id="lojaId" />
        <BackofficeProdutos      v-else-if="activeSection === 'produtos'"      :loja-id="lojaId" />
        <BackofficeInventario    v-else-if="activeSection === 'inventario'"    :loja-id="lojaId" />
        <BackofficeConfiguracoes v-else-if="activeSection === 'configuracoes'" :loja-id="lojaId" :loja="loja" @updated="fetchLoja" />
        <BackofficeStaff         v-else-if="activeSection === 'staff'"         :loja-id="lojaId" />
        <BackofficeTipos         v-else-if="activeSection === 'tipos'"         :loja-id="lojaId" />
        <BackofficeAvaliacoes    v-else-if="activeSection === 'avaliacoes'"    :loja-id="lojaId" />
        <BackofficeEntregas      v-else-if="activeSection === 'entregas'"      :loja-id="lojaId" :minha-role="role" />
        <BackofficeCategorias    v-else-if="activeSection === 'categorias'"    :loja-id="lojaId" />
      </main>
    </div>

    <!-- ═══ BOTÃO FLUTUANTE MOBILE (canto inferior esquerdo) ═══ -->
    <button @click="sidebarAberta = !sidebarAberta"
      class="fixed bottom-5 left-5 z-50 lg:hidden w-14 h-14 bg-red-600 hover:bg-red-500
             rounded-2xl shadow-2xl shadow-red-600/40 flex items-center justify-center
             transition-all duration-200 active:scale-95">
      <!-- Menu icon quando fechado -->
      <svg v-if="!sidebarAberta" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      <!-- X icon quando aberto -->
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
      <!-- Badge notificações no botão flutuante -->
      <span v-if="naoLidasCount > 0"
        class="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-yellow-400 text-zinc-900
               text-[10px] font-bold rounded-full flex items-center justify-center">
        {{ naoLidasCount > 9 ? '9+' : naoLidasCount }}
      </span>
    </button>

  </div>
</template>

<script>
import api from '@/services/api'
import BackofficeSidebarItem    from './BackofficeSidebarItem.vue'
import BackofficeDashboard      from './BackofficeDashboard.vue'
import BackofficeEncomendas     from './BackofficeEncomendas.vue'
import BackofficeProdutos       from './BackofficeProdutos.vue'
import BackofficeInventario     from './BackofficeInventario.vue'
import BackofficeConfiguracoes  from './BackofficeConfiguracoes.vue'
import BackofficeStaff          from './BackofficeStaff.vue'
import BackofficeTipos          from './BackofficeTipos.vue'
import BackofficeAvaliacoes     from './BackofficeAvaliacoes.vue'
import BackofficeEntregas       from './BackofficeEntregas.vue'
import BackofficeCategorias     from './BackofficeCategorias.vue'
import NotificacaoSino          from '@/components/notificacao/notificacaoSino.vue'

const PERMISSOES = {
  dono: [
    'ver_loja','editar_loja','apagar_loja','gerir_staff',
    'gerir_produtos','gerir_inventario','gerir_encomendas',
    'atribuir_condutor','gerir_pagamentos','gerir_entregas',
    'ver_relatorios','gerir_metodos_pagamento','gerir_opcoes_entrega','gerir_template',
  ],
  gestor: [
    'ver_loja','editar_loja','gerir_staff',
    'gerir_produtos','gerir_inventario','gerir_encomendas',
    'atribuir_condutor','gerir_pagamentos','gerir_entregas',
    'ver_relatorios','gerir_metodos_pagamento','gerir_opcoes_entrega','gerir_template',
  ],
  staff:        ['ver_loja','gerir_produtos','gerir_inventario','gerir_encomendas'],
  contabilista: ['ver_loja','gerir_pagamentos','ver_relatorios'],
  condutor:     ['gerir_entregas'],
}

const SECCOES = [
  { key: 'dashboard',     label: 'Dashboard',        icon: 'chart',     permissao: 'ver_loja'         },
  { key: 'encomendas',    label: 'Encomendas',        icon: 'order',     permissao: 'gerir_encomendas' },
  { key: 'entregas',      label: 'Entregas',          icon: 'delivery',  permissao: 'gerir_entregas'   },
  { key: 'avaliacoes',    label: 'Avaliações',        icon: 'star',      permissao: 'ver_loja'         },
  { key: 'tipos',         label: 'Tipos de Produto',  icon: 'tag',       permissao: 'gerir_produtos'   },
  { key: 'categorias',    label: 'Categorias',        icon: 'category',  permissao: 'gerir_produtos'   },
  { key: 'produtos',      label: 'Produtos',          icon: 'box',       permissao: 'gerir_produtos'   },
  { key: 'inventario',    label: 'Inventário',        icon: 'inventory', permissao: 'gerir_inventario' },
  { key: 'staff',         label: 'Staff',             icon: 'staff',     permissao: 'gerir_staff'      },
  { key: 'configuracoes', label: 'Configurações',     icon: 'settings',  permissao: 'editar_loja'      },
]

export default {
  name: 'BackofficeLayout',
  components: {
    BackofficeSidebarItem, BackofficeDashboard, BackofficeEncomendas,
    BackofficeProdutos, BackofficeInventario, BackofficeConfiguracoes,
    BackofficeStaff, BackofficeTipos, NotificacaoSino,
    BackofficeEntregas, BackofficeAvaliacoes, BackofficeCategorias,
  },

  data () {
    return {
      loja:          null,
      loadingLoja:   true,
      activeSection: 'dashboard',
      sidebarAberta: false,
      naoLidasCount: 0,
      user:          JSON.parse(localStorage.getItem('user') || '{}'),
    }
  },

  computed: {
    lojaId ()      { return this.$route.params.id },
    role ()        { return this.loja?.minha_role || '' },
    permissoes ()  { return PERMISSOES[this.role] || [] },
    navItems ()    { return SECCOES.filter(s => this.permissoes.includes(s.permissao)) },
    currentNavItem () { return SECCOES.find(n => n.key === this.activeSection) },
    roleColor () {
      const map = {
        dono:        'bg-red-500/20 text-red-400',
        gestor:      'bg-orange-500/20 text-orange-400',
        staff:       'bg-blue-500/20 text-blue-400',
        contabilista:'bg-green-500/20 text-green-400',
        condutor:    'bg-purple-500/20 text-purple-400',
      }
      return map[this.role] || 'bg-zinc-500/20 text-zinc-400'
    },
  },

  async created () {
    await this.fetchLoja()
    this.fetchNaoLidas()
  },

  methods: {
    temPermissao (seccaoKey) {
      const seccao = SECCOES.find(s => s.key === seccaoKey)
      if (!seccao) return false
      return this.permissoes.includes(seccao.permissao)
    },

    navegarPara (key) {
      this.activeSection = key
      // fecha sidebar no mobile após navegar
      this.sidebarAberta = false
    },

    async fetchLoja () {
      this.loadingLoja = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/backoffice/`)
        this.loja = data
        const primeira = SECCOES.find(s =>
          (PERMISSOES[data.minha_role] || []).includes(s.permissao)
        )
        if (primeira) this.activeSection = primeira.key
      } catch (e) {
        console.error(e)
        this.$router.push('/Home')
      } finally {
        this.loadingLoja = false
      }
    },

    async fetchNaoLidas () {
      try {
        const { data } = await api.get('/app/notificacoes/contador/')
        this.naoLidasCount = data.nao_lidas || 0
      } catch (e) { /* silencioso */ }
    },
  },
}
</script>