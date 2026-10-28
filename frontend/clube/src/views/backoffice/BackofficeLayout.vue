<template>
  <div class="min-h-screen bg-zinc-950 flex relative">

    <!-- ═══ OVERLAY MOBILE ═══ -->
    <div v-if="sidebarAberta"
         class="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
         @click="sidebarAberta = false" />

    <!-- ═══ SIDEBAR ═══ -->
    <aside :class="[
      'fixed lg:sticky lg:top-0 lg:h-screen lg:self-start inset-y-0 left-0 z-40 w-72 bg-zinc-900 border-r border-zinc-800 flex flex-col',
      'transition-transform duration-300 ease-in-out',
      sidebarAberta ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]">

      <!-- Loja info -->
      <div class="p-5 border-b border-zinc-800 flex items-center justify-between flex-shrink-0">
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
      <nav class="flex-1 min-h-0 p-4 space-y-1 overflow-y-auto">
        <p class="text-xs font-semibold text-zinc-600 uppercase tracking-wider px-3 mb-2">Gestão</p>
        <BackofficeSidebarItem
          v-for="item in navItems" :key="item.key"
          :icon="item.icon" :label="item.label"
          :active="activeSection === item.key"
          :badge="item.key === 'mensagens' ? naoLidasChat : item.key === 'devolucoes' ? devolucoesPorResponder : 0"
          @click="navegarPara(item.key)"
        />
        <div v-if="navItems.length === 0 && !loadingLoja"
             class="px-3 py-4 text-xs text-zinc-600 text-center">
          Sem permissões nesta loja.
        </div>
      </nav>

      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800 space-y-1 flex-shrink-0">
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
          <BotaoTema :isDark="isDark" @alternar="alternarTema" />
          <NotificacaoSino />
          <span class="text-xs text-zinc-600 hidden sm:block">{{ user.username }}</span>
        </div>
      </header>

      <!-- Admin a ver a loja (Admin → Lojas → Ver backoffice): o servidor recusa qualquer alteração -->
      <div v-if="modoAdmin || verAdminExpirou" data-teste="banner-ver-admin" role="status"
           class="mx-4 lg:mx-6 mt-4 px-4 py-3 rounded-xl border border-sky-500/30 bg-sky-500/10 text-sky-300 text-sm flex items-center gap-3">
        <font-awesome-icon :icon="['fas', 'eye']" class="w-4 h-4 flex-shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="font-semibold">Estás a ver como admin — só leitura</p>
          <p v-if="verAdminExpirou" class="text-xs opacity-80 mt-0.5" data-teste="ver-admin-expirou">
            A sessão de leitura terminou. Abre outra vez a loja a partir do Admin → Lojas.
          </p>
          <p v-else class="text-xs opacity-80 mt-0.5">
            Vês o backoffice como o dono o vê. Nada pode ser alterado daqui; este acesso fica registado.
          </p>
        </div>
      </div>

      <!-- Estado da loja (pendente / fechada / suspensa) -->
      <div v-if="loja && loja.estado && loja.estado !== 'ativa'"
           :class="['mx-4 lg:mx-6 mt-4 px-4 py-3 rounded-xl border text-sm flex flex-col sm:flex-row sm:items-center gap-3', avisoEstado.classe]">
        <font-awesome-icon :icon="['fas', avisoEstado.icone]" class="w-4 h-4 flex-shrink-0 hidden sm:block" />
        <div class="flex-1 min-w-0">
          <p class="font-semibold">{{ avisoEstado.titulo }}</p>
          <p class="text-xs opacity-80 mt-0.5">{{ avisoEstado.texto }}</p>
          <p v-if="loja.estado_motivo" class="text-xs opacity-80 mt-0.5">Motivo: {{ loja.estado_motivo }}</p>
        </div>
        <button v-if="loja.estado === 'fechada' && podeFecharLoja" @click="reabrirLoja" :disabled="aMudarEstado"
          class="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-bold transition flex-shrink-0">
          <font-awesome-icon :icon="['fas', 'store']" class="mr-1.5" />Reabrir loja
        </button>
        <button v-if="suspensaPorSubscricao && permissoes.includes('ver_subscricao')" @click="navegarPara('subscricao')"
          class="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition flex-shrink-0">
          <font-awesome-icon :icon="['fas', 'credit-card']" class="mr-1.5" />Pagar subscrição
        </button>
      </div>

      <!-- Subscrição em atraso / a vencer (a loja continua a funcionar) -->
      <div v-if="avisoSub && (avisoSub.tipo !== 'suspensa' || avisoSub.servicos) && loja?.estado === 'ativa'" role="alert"
           :class="['mx-4 lg:mx-6 mt-4 px-4 py-3 rounded-xl border text-sm flex flex-col sm:flex-row sm:items-center gap-3',
                    avisoSub.tipo === 'atraso' ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-amber-500/10 border-amber-500/30 text-amber-200']">
        <font-awesome-icon :icon="['fas', avisoSub.tipo === 'atraso' ? 'triangle-exclamation' : 'clock']" class="w-4 h-4 flex-shrink-0 hidden sm:block" />
        <p class="flex-1 min-w-0">{{ avisoSub.texto }}</p>
        <button v-if="activeSection !== 'subscricao'" @click="navegarPara('subscricao')"
          class="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-900 text-xs font-bold transition flex-shrink-0">
          Ver subscrição
        </button>
      </div>

      <!-- Faturação: dados fiscais por preencher / lembrete de faturar (components/fiscal) -->
      <AvisoFaturacao v-if="loja?.fiscal" class="mx-4 lg:mx-6 mt-4" :fiscal="loja.fiscal" :chave="`loja-${lojaId}`"
                      :pode-editar="permissoes.includes('gerir_dados_fiscais')" @preencher="navegarPara('configuracoes')" />

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
      <!-- pb-24: espaço para o balão do chat (canto inferior direito) não tapar o fim do conteúdo -->
      <main v-else class="flex-1 overflow-auto p-4 pb-24 lg:p-6 lg:pb-24">
        <BackofficeDashboard     v-if="activeSection === 'dashboard'"      :loja-id="lojaId" />
        <ModuloRelatorios        v-else-if="activeSection === 'relatorios'"    :key="'rel' + lojaId"
                                 :base="`/app/loja/${lojaId}/relatorios`" :prefixo="`loja-${lojaId}`" />
        <BackofficeEncomendas    v-else-if="activeSection === 'encomendas'"    :loja-id="lojaId" @ver-reembolso="abrirReembolso"
                                 :regime-fiscal="loja?.fiscal?.regime_fiscal || ''" />
        <BackofficeDevolucoes    v-else-if="activeSection === 'devolucoes'"    :loja-id="lojaId"
                                 :reembolso-id="$route.params.ficha || null" @contagem="devolucoesPorResponder = $event" />
        <BackofficeProdutos      v-else-if="activeSection === 'produtos'"      :loja-id="lojaId" />
        <BackofficeInventario    v-else-if="activeSection === 'inventario'"    :loja-id="lojaId" />
        <BackofficeConfiguracoes v-else-if="activeSection === 'configuracoes'" :loja-id="lojaId" :loja="loja"
                                 :pode-fechar="podeFecharLoja" :pode-fiscal="permissoes.includes('gerir_dados_fiscais')"
                                 @updated="fetchLoja" />
        <BackofficeStaff         v-else-if="activeSection === 'staff'"         :loja-id="lojaId" />
        <BackofficeSubscricao    v-else-if="activeSection === 'subscricao'"    :loja-id="lojaId" @alterado="fetchLoja" />
        <BackofficeTipos         v-else-if="activeSection === 'tipos'"         :loja-id="lojaId" />
        <BackofficeAvaliacoes    v-else-if="activeSection === 'avaliacoes'"    :loja-id="lojaId" />
        <BackofficeEntregas      v-else-if="activeSection === 'entregas'"      :loja-id="lojaId" :minha-role="role" />
        <BackofficeCategorias    v-else-if="activeSection === 'categorias'"    :loja-id="lojaId" />
        <BackofficeTemplates     v-else-if="activeSection === 'templates'"     :loja-id="lojaId" />
        <BackofficeMensagens     v-else-if="activeSection === 'mensagens'"     :loja-id="lojaId" />
        <BackofficeFaturacao     v-else-if="activeSection === 'faturacao'"     :loja-id="lojaId"
                                 @ver-subscricao="navegarPara('subscricao')" />
        <BackofficeServicos      v-else-if="activeSection === 'servicos'"      :loja-id="lojaId"
                                 :so-agenda="!permissoes.includes('gerir_marcacoes')"
                                 @ver-subscricao="navegarPara('subscricao')" />
      </main>
    </div>

  </div>
</template>

<script>
import { defineAsyncComponent } from 'vue'
import api, { capturarVerAdmin, verAdmin, EVENTO_VER_ADMIN_EXPIROU } from '@/services/api'
import BackofficeSidebarItem    from './BackofficeSidebarItem.vue'
import { chat } from '@/services/chat'
import NotificacaoSino          from '@/components/notificacao/notificacaoSino.vue'
import AvisoFaturacao           from '@/components/fiscal/AvisoFaturacao.vue'
import { EVENTO_REEMBOLSO, EVENTO_RELIGADO } from '@/composables/useTempoRealReembolsos'
import { COM_FICHA, enderecoCerto } from '@/utils/ficha'
import { temaPainel } from '@/utils/tema'
import BotaoTema from '@/components/BotaoTema.vue'

// cada módulo é um ficheiro à parte: só se descarrega quando se abre
const BackofficeDashboard      = defineAsyncComponent(() => import('./BackofficeDashboard.vue'))
const BackofficeEncomendas     = defineAsyncComponent(() => import('./BackofficeEncomendas.vue'))
const BackofficeProdutos       = defineAsyncComponent(() => import('./BackofficeProdutos.vue'))
const BackofficeInventario     = defineAsyncComponent(() => import('./BackofficeInventario.vue'))
const BackofficeConfiguracoes  = defineAsyncComponent(() => import('./BackofficeConfiguracoes.vue'))
const BackofficeStaff          = defineAsyncComponent(() => import('./BackofficeStaff.vue'))
const BackofficeTipos          = defineAsyncComponent(() => import('./BackofficeTipos.vue'))
const BackofficeAvaliacoes     = defineAsyncComponent(() => import('./BackofficeAvaliacoes.vue'))
const BackofficeEntregas       = defineAsyncComponent(() => import('./BackofficeEntregas.vue'))
const BackofficeCategorias     = defineAsyncComponent(() => import('./BackofficeCategorias.vue'))
const BackofficeTemplates      = defineAsyncComponent(() => import('./BackofficeTemplates.vue'))
const BackofficeMensagens      = defineAsyncComponent(() => import('./BackofficeMensagens.vue'))
const BackofficeSubscricao     = defineAsyncComponent(() => import('./BackofficeSubscricao.vue'))
const BackofficeDevolucoes     = defineAsyncComponent(() => import('./BackofficeDevolucoes.vue'))
const BackofficeServicos       = defineAsyncComponent(() => import('./BackofficeServicos.vue'))
const BackofficeFaturacao      = defineAsyncComponent(() => import('./BackofficeFaturacao.vue'))
const ModuloRelatorios         = defineAsyncComponent(() => import('@/components/relatorios/ModuloRelatorios.vue'))

const PERMISSOES = {
  dono: [
    'ver_loja','editar_loja','apagar_loja','gerir_dados_fiscais','gerir_staff',
    'gerir_produtos','gerir_inventario','gerir_encomendas','gerir_devolucoes',
    'atribuir_condutor','gerir_pagamentos','gerir_entregas',
    'ver_relatorios','gerir_metodos_pagamento','gerir_opcoes_entrega','gerir_template',
    'ver_subscricao','pagar_subscricao','gerir_servicos','gerir_marcacoes','gerir_faturacao',
  ],
  gestor: [
    'ver_loja','editar_loja','gerir_staff',
    'gerir_produtos','gerir_inventario','gerir_encomendas','gerir_devolucoes',
    'atribuir_condutor','gerir_pagamentos','gerir_entregas',
    'ver_relatorios','gerir_metodos_pagamento','gerir_opcoes_entrega','gerir_template', 'ver_subscricao',
    'gerir_servicos','gerir_marcacoes','gerir_faturacao',
  ],
  staff:        ['ver_loja','gerir_produtos','gerir_inventario','gerir_encomendas','gerir_marcacoes'],
  contabilista: ['ver_loja','gerir_pagamentos','ver_relatorios','ver_subscricao','gerir_faturacao'],
  condutor:     ['gerir_entregas'],
}

const SECCOES = [
  { key: 'dashboard',     label: 'Dashboard',        icon: 'chart',     permissao: 'ver_loja'         },
  { key: 'relatorios',    label: 'Relatórios',        icon: 'report',    permissao: 'ver_relatorios'   },
  { key: 'encomendas',    label: 'Encomendas',        icon: 'order',     permissao: 'gerir_encomendas' },
  { key: 'devolucoes',    label: 'Devoluções',        icon: 'refund',    permissao: 'gerir_devolucoes' },
  { key: 'faturacao',     label: 'Faturação',         icon: 'invoice',   permissao: 'gerir_faturacao'  },
  { key: 'entregas',      label: 'Entregas',          icon: 'delivery',  permissao: 'gerir_entregas'   },
  { key: 'mensagens',     label: 'Mensagens',         icon: 'chat',      permissao: null               },   // todos os membros (equipa); clientes só quem atende
  { key: 'avaliacoes',    label: 'Avaliações',        icon: 'star',      permissao: 'ver_loja'         },
  { key: 'tipos',         label: 'Tipos de Produto',  icon: 'tag',       permissao: 'gerir_produtos'   },
  { key: 'categorias',    label: 'Categorias',        icon: 'category',  permissao: 'gerir_produtos'   },
  { key: 'produtos',      label: 'Produtos',          icon: 'box',       permissao: 'gerir_produtos'   },
  { key: 'inventario',    label: 'Inventário',        icon: 'inventory', permissao: 'gerir_inventario' },
  { key: 'servicos',      label: 'Serviços',          icon: 'calendar',  permissao: 'gerir_marcacoes'  },
  { key: 'staff',         label: 'Staff',             icon: 'staff',     permissao: 'gerir_staff'      },
  { key: 'templates',     label: 'Templates',         icon: 'template',  permissao: 'gerir_template'   },
  { key: 'configuracoes', label: 'Configurações',     icon: 'settings',  permissao: 'editar_loja'      },
  { key: 'subscricao',    label: 'Subscrição',        icon: 'card',      permissao: 'ver_subscricao'   },
]

export default {
  name: 'BackofficeLayout',
  mixins: [temaPainel],
  components: { BotaoTema, BackofficeSubscricao,
    BackofficeSidebarItem, BackofficeDashboard, BackofficeEncomendas, ModuloRelatorios,
    BackofficeProdutos, BackofficeInventario, BackofficeConfiguracoes,
    BackofficeStaff, BackofficeTipos, NotificacaoSino, AvisoFaturacao,
    BackofficeEntregas, BackofficeAvaliacoes, BackofficeCategorias,
    BackofficeTemplates, BackofficeMensagens, BackofficeDevolucoes, BackofficeServicos, BackofficeFaturacao,
  },

  data () {
    return {
      loja:          null,
      aMudarEstado:  false,
      avisoSub:      null,    // faixa da subscrição (em atraso / a vencer)
      devolucoesPorResponder: 0,   // pedidos de reembolso à espera da loja (contador no menu)
      loadingLoja:   true,
      sidebarAberta: false,
      user:          JSON.parse(localStorage.getItem('user') || '{}'),
      verAdminExpirou: false,
    }
  },

  computed: {
    lojaId ()      { return this.$route.params.id },
    // o módulo vem do endereço (/loja/:id/backoffice/<módulo>): um refresh, o voltar do browser ou um link abrem-no.
    // Enquanto a loja (e as permissões do membro) carrega mostra-se o pedido; depois acertarEndereco corrige-o.
    activeSection () { return this.$route.params.seccao || this.$route.query.seccao || 'dashboard' },
    role ()        { return this.loja?.minha_role || '' },
    // admin a ver esta loja só para leitura (services/api.js)
    modoAdmin ()   { return !!verAdmin(this.lojaId) },
    permissoes ()  { return PERMISSOES[this.role] || [] },
    navItems ()    { return SECCOES.filter(s => this.temPermissao(s.key)) },
    // um profissional com conta vê a sua agenda mesmo sem gerir_marcacoes
    meuProfissional () { return !!this.loja?.servicos?.meu_profissional_id },
    naoLidasChat () {
      const c = chat.caixas.find(x => x.tipo === 'loja' && String(x.loja_id) === String(this.lojaId))
      return c ? c.nao_lidas : 0
    },
    podeFecharLoja () { return this.permissoes.includes('apagar_loja') },
    avisoEstado () {
      return ({
        pendente: {
          icone: 'hourglass-half', classe: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
          titulo: 'Loja à espera de aprovação',
          texto:  'Podes configurá-la e adicionar produtos. Ainda não aparece no site nem recebe encomendas.',
        },
        fechada: {
          icone: 'door-closed', classe: 'bg-zinc-800 border-zinc-700 text-zinc-300',
          titulo: 'Loja fechada',
          texto:  'Não aparece no site nem recebe encomendas novas. As encomendas em curso continuam a ser geridas aqui.',
        },
        suspensa: this.suspensaPorSubscricao ? {
          icone: 'ban', classe: 'bg-red-500/10 border-red-500/30 text-red-300',
          titulo: 'Loja suspensa — subscrição por pagar',
          texto:  'Não aparece no site nem recebe encomendas novas. Paga a fatura em atraso e a loja volta logo, sem esperar pela plataforma.',
        } : {
          icone: 'ban', classe: 'bg-red-500/10 border-red-500/30 text-red-300',
          titulo: 'Loja suspensa pela plataforma',
          texto:  'Não aparece no site nem recebe encomendas novas. As encomendas em curso continuam aqui. Contacta o suporte para a reactivar.',
        },
      })[this.loja?.estado] || {}
    },
    // suspensa automaticamente por falta de pagamento (utils/subscricoes.py MOTIVO_SUSPENSAO)
    suspensaPorSubscricao () {
      return this.loja?.estado === 'suspensa' && (this.loja.estado_motivo || '').startsWith('Subscrição por pagar')
    },
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
    capturarVerAdmin()
    await this.fetchLoja()
  },

  mounted () {
    // contador "Devoluções" no menu em tempo real (avisos do sino — composables/useTempoRealReembolsos)
    this.aoReembolso = (e) => { if (!e.detail || String(e.detail.loja_id) === String(this.lojaId)) this.fetchDevolucoes() }
    window.addEventListener(EVENTO_REEMBOLSO, this.aoReembolso)
    window.addEventListener(EVENTO_RELIGADO, this.aoReembolso)
    this.aoExpirarVer = () => { this.verAdminExpirou = true }
    window.addEventListener(EVENTO_VER_ADMIN_EXPIROU, this.aoExpirarVer)
  },

  beforeUnmount () {
    window.removeEventListener(EVENTO_REEMBOLSO, this.aoReembolso)
    window.removeEventListener(EVENTO_RELIGADO, this.aoReembolso)
    window.removeEventListener(EVENTO_VER_ADMIN_EXPIROU, this.aoExpirarVer)
  },

  watch: {
    $route () { this.acertarEndereco() },
    // outra loja no mesmo separador (ex.: o dono de várias lojas)
    lojaId (novo, antigo) { if (novo && novo !== antigo) this.fetchLoja() },
  },

  methods: {
    temPermissao (seccaoKey) {
      const seccao = SECCOES.find(s => s.key === seccaoKey)
      if (!seccao) return false
      if (seccao.permissao === null) return !!this.role      // qualquer membro (ex.: mensagens)
      if (seccao.key === 'servicos' && this.meuProfissional) return true
      return this.permissoes.includes(seccao.permissao)
    },

    abrirReembolso (id) {
      this.$router.push(`/loja/${this.lojaId}/backoffice/devolucoes/${id}`)
    },

    async fetchDevolucoes () {
      if (!(PERMISSOES[this.loja?.minha_role] || []).includes('gerir_devolucoes')) return
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/reembolsos/`, { params: { grupo: 'novos', limit: 1 } })
        this.devolucoesPorResponder = (data.contagem?.novos || 0) + (data.contagem?.dinheiro || 0)
      } catch { /* o contador não é essencial */ }
    },

    navegarPara (key) {
      // fecha sidebar no mobile após navegar
      this.sidebarAberta = false
      if (key !== this.$route.params.seccao || this.$route.params.ficha) this.$router.push(`/loja/${this.lojaId}/backoffice/${key}`)
    },

    // Só depois de a loja carregar (as permissões dependem do papel do membro):
    // sem módulo, módulo que não existe ou sem acesso → primeiro módulo permitido;
    // ficha (/encomendas/<id>) só nos módulos que a têm (utils/ficha.js);
    // links antigos (?seccao=devolucoes&reembolso=12, /devolucoes?reembolso=12) → /devolucoes/12
    acertarEndereco () {
      if (!this.loja || this.$route.name !== 'Backoffice') return
      const pedida = this.$route.params.seccao || this.$route.query.seccao
      const valida = this.temPermissao(pedida) ? pedida
        : SECCOES.find(s => s.permissao !== null && this.temPermissao(s.key))?.key
          || SECCOES.find(s => this.temPermissao(s.key))?.key
      const destino = enderecoCerto(this.$route, `/loja/${this.lojaId}/backoffice`, valida, COM_FICHA.backoffice)
      if (destino) this.$router.replace(destino)
    },

    async reabrirLoja () {
      if (!confirm('Reabrir a loja? Volta a aparecer no site e a receber encomendas.')) return
      this.aMudarEstado = true
      try {
        await api.post(`/app/loja/${this.lojaId}/reabrir/`)
        await this.fetchLoja()
      } catch (e) {
        alert(e.response?.data?.detail || 'Não foi possível reabrir a loja.')
      } finally { this.aMudarEstado = false }
    },

    async fetchAvisoSub () {
      const perms = PERMISSOES[this.loja?.minha_role] || []
      if (!perms.includes('ver_subscricao')) { this.avisoSub = null; return }
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/subscricao/`)
        // a da loja manda; senão a da subscrição de Serviços (só o módulo, a loja continua)
        this.avisoSub = data.aviso || data.servicos?.aviso || null
      } catch (e) { this.avisoSub = null }
    },

    async fetchLoja () {
      this.loadingLoja = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/backoffice/`)
        this.loja = data
        this.fetchAvisoSub()
        this.fetchDevolucoes()
        // recarregar a loja depois de guardar não muda de módulo; só corrige o endereço se o módulo
        // pedido não existir ou o membro deixar de ter acesso
        this.acertarEndereco()
      } catch (e) {
        console.error(e)
        // modo de leitura que expirou: fica cá, com a faixa a explicar
        if (!this.verAdminExpirou) this.$router.push('/Home')
      } finally {
        this.loadingLoja = false
      }
    },
  },
}
</script>
