<template>
  <div class="min-h-screen bg-slate-100">
    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-xl">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-lg font-black text-white shadow-lg">
            P
          </div>

          <div class="min-w-0">
            <h1 class="truncate text-lg font-black text-slate-950 sm:text-xl">
              {{ posNome || 'POS Bendi' }}
            </h1>
            <p class="truncate text-xs font-semibold text-slate-500 sm:text-sm">
              {{ posCodigo || 'Sistema POS' }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-4">
          <!-- Info utilizador -->
          <div class="hidden items-center gap-2 sm:flex">
            <!-- Badge de membro de equipa -->
            <span
              v-if="isMembro"
              class="rounded-xl bg-blue-100 px-2 py-1 text-xs font-black text-blue-700"
            >
              {{ membroPapelLabel }}
            </span>

            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-black text-slate-700">
              {{ userInitial }}
            </div>

            <span class="max-w-[140px] truncate text-sm font-bold text-slate-700">
              {{ userName }}
            </span>
          </div>

          <!-- Botão configuração (só para conta principal) -->
          <button
            v-if="!isMembro && !soLeitura"
            type="button"
            @click="abrirConfiguracao"
            class="rounded-2xl p-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
            title="Configurar POS"
            :disabled="!posId"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>

          <button
            v-if="!soLeitura"
            type="button"
            @click="logout"
            class="rounded-2xl p-2 text-red-600 transition hover:bg-red-50"
            title="Sair"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Navegação -->
    <nav
      v-if="posId"
      class="sticky top-[73px] z-30 border-b border-slate-200 bg-white/90 backdrop-blur-xl"
    >
      <div class="mx-auto max-w-7xl px-4">
        <div class="flex gap-2 overflow-x-auto py-3 scrollbar-hide">
          <button
            v-for="tab in tabsVisiveis"
            :key="tab.id"
            type="button"
            @click="abrirAba(tab.id)"
            :class="[
              'flex shrink-0 items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-black transition',
              activeTab === tab.id
                ? 'bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950'
            ]"
          >
            <font-awesome-icon :icon="['fas', tab.icon]" class="w-4 h-4" />
            <span>{{ tab.label }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- Conteúdo -->
    <main class="mx-auto max-w-7xl p-4 sm:p-6">
      <!-- Admin a ver o POS (Admin → POS → Ver POS): o servidor recusa qualquer alteração -->
      <section v-if="soLeitura || verAdminExpirou" data-teste="banner-ver-admin" role="status"
               class="mb-5 flex items-start gap-3 rounded-[2rem] border border-sky-200 bg-sky-50 p-4 text-sm text-sky-800 shadow-sm">
        <font-awesome-icon :icon="['fas', 'eye']" class="mt-0.5 h-4 w-4 shrink-0" />
        <div class="min-w-0 flex-1">
          <p class="font-black">Estás a ver como admin — só leitura</p>
          <p v-if="verAdminExpirou" class="mt-0.5 text-xs font-semibold" data-teste="ver-admin-expirou">
            A sessão de leitura terminou. Abre outra vez o POS a partir do Admin → POS.
          </p>
          <p v-else class="mt-0.5 text-xs font-semibold">
            Vês o POS como o dono o vê. Nada pode ser alterado daqui; este acesso fica registado.
          </p>
          <p v-if="currentPOS?.suspenso" class="mt-1 text-xs font-bold text-red-700" data-teste="ver-admin-suspenso">
            Este POS está suspenso. {{ currentPOS.suspenso_motivo }}
          </p>
        </div>
      </section>

      <!-- Barra de estado do POS (só para conta principal) -->
      <section
        v-if="posId && !isMembro"
        class="mb-5 rounded-[2rem] border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div
              :class="[
                'inline-flex w-fit items-center rounded-2xl px-4 py-2 text-sm font-black',
                modoBadgeClass
              ]"
            >
              {{ modoLabel }}
            </div>

            <div class="min-w-0">
              <p class="text-sm font-black text-slate-950">
                {{ modoDescription }}
              </p>

              <p class="mt-1 truncate text-xs font-semibold text-slate-500">
                <span v-if="lojaVinculada">
                  Loja vinculada: {{ lojaVinculada.nome }}
                </span>
                <span v-else>
                  Nenhuma loja vinculada. Este POS trabalha apenas com produtos próprios.
                </span>
              </p>
            </div>
          </div>

          <div v-if="!soLeitura" class="flex flex-wrap gap-2">
            <button
              type="button"
              @click="abrirConfiguracao"
              class="h-10 rounded-2xl bg-slate-950 px-4 text-sm font-black text-white transition hover:bg-slate-800"
            >
              Configurar POS
            </button>

            <button
              v-if="lojaVinculada"
              type="button"
              @click="desconectarLoja"
              :disabled="savingConfig"
              class="h-10 rounded-2xl bg-red-50 px-4 text-sm font-black text-red-700 transition hover:bg-red-100 disabled:opacity-60"
            >
              Desconectar loja
            </button>
          </div>
        </div>
      </section>

      <!-- loja vinculada suspensa: o POS funciona, mas sem os produtos da loja -->
      <section
        v-if="posId && !currentPOS?.suspenso && currentPOS?.loja_suspensa"
        class="rounded-[2rem] border border-amber-200 bg-amber-50 p-4 shadow-sm flex items-start gap-3"
      >
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mt-0.5 text-amber-500" />
        <div>
          <p class="text-sm font-black text-amber-800">
            A loja "{{ currentPOS.loja_vinculada?.nome }}" foi suspensa pela plataforma
          </p>
          <p class="mt-0.5 text-xs font-semibold text-amber-700">
            Os produtos da loja estão indisponíveis para venda até a loja ser reactivada.
            {{ currentPOS.modo === 'integrado'
              ? 'Este POS só vende produtos da loja — muda para o modo híbrido para vender produtos próprios.'
              : 'Os produtos próprios do POS continuam disponíveis.' }}
            As contas já abertas podem ser fechadas normalmente.
          </p>
        </div>
      </section>

      <!-- faixa da subscrição (dono): grátis a acabar, em atraso… -->
      <section
        v-if="posId && !isMembro && avisoSub && !currentPOS?.suspenso && activeTab !== 'subscricao'"
        :class="['mb-5 flex flex-wrap items-center gap-3 rounded-[2rem] border p-4 shadow-sm',
                 ['vence', 'sem_plano'].includes(avisoSub.tipo) ? 'border-amber-200 bg-amber-50' : 'border-red-200 bg-red-50']"
        role="alert"
      >
        <font-awesome-icon :icon="['fas', 'credit-card']" :class="['vence', 'sem_plano'].includes(avisoSub.tipo) ? 'text-amber-500' : 'text-red-500'" />
        <p :class="['min-w-0 flex-1 text-sm font-bold', ['vence', 'sem_plano'].includes(avisoSub.tipo) ? 'text-amber-800' : 'text-red-700']">
          {{ avisoSub.texto }}
        </p>
        <button type="button" @click="abrirAba('subscricao')"
          class="h-10 rounded-2xl bg-slate-950 px-4 text-sm font-black text-white transition hover:bg-slate-800">
          {{ avisoSub.tipo === 'sem_plano' ? 'Escolher plano' : 'Ver subscrição' }}
        </button>
      </section>

      <!-- faturação: dados fiscais por preencher / lembrete de faturar (components/fiscal) -->
      <AvisoFaturacao v-if="posId && !isMembro && currentPOS?.fiscal" class="mb-5" tema="claro"
                      :fiscal="currentPOS.fiscal" :chave="`pos-${posId}`" :pode-editar="!soLeitura" @preencher="abrirConfiguracao" />

      <!-- POS suspenso pela plataforma (a aba Subscrição continua aberta ao dono, para pagar; o Histórico também,
           para registar as faturas das vendas já feitas) -->
      <section
        v-if="posId && currentPOS?.suspenso && !abertaSuspenso && !soLeitura"
        class="rounded-[2rem] border border-red-200 bg-red-50 p-6 text-center shadow-sm"
      >
        <font-awesome-icon :icon="['fas', 'ban']" class="text-3xl text-red-500" />
        <h3 class="mt-2 text-lg font-black text-red-800">Este POS está suspenso</h3>
        <p class="mt-1 text-sm font-semibold text-red-700">
          {{ currentPOS.suspenso_motivo || 'Suspenso pela plataforma.' }}
        </p>
        <p v-if="suspensoPorSubscricao && !isMembro" class="mt-3 text-xs font-semibold text-red-600/80">
          Paga a subscrição e o POS volta a funcionar logo.
        </p>
        <p v-else-if="suspensoPorSubscricao" class="mt-3 text-xs font-semibold text-red-600/80">
          A subscrição do POS está por pagar. Fala com o responsável do POS.
        </p>
        <p v-else class="mt-3 text-xs font-semibold text-red-600/80">
          As vendas, mesas e produtos estão bloqueados até a suspensão ser levantada. Contacta o suporte da plataforma.
        </p>
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <button v-if="suspensoPorSubscricao && !isMembro" type="button" @click="abrirAba('subscricao')"
            class="h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800">
            Pagar subscrição
          </button>
          <button v-if="podeHistorico" type="button" @click="abrirAba('historico')" data-teste="suspenso-historico"
            class="h-11 rounded-2xl border border-red-200 bg-white px-5 text-sm font-black text-red-800 transition hover:bg-red-100">
            Histórico
          </button>
          <button v-if="podeHistorico" type="button" @click="abrirAba('faturacao')" data-teste="suspenso-faturacao"
            class="h-11 rounded-2xl border border-red-200 bg-white px-5 text-sm font-black text-red-800 transition hover:bg-red-100">
            Faturação
          </button>
        </div>
        <p v-if="podeHistorico" class="mt-2 text-[11px] font-semibold text-red-600/70">
          As faturas das vendas já feitas continuam a poder ser registadas.
        </p>
      </section>

      <!-- Área principal -->
      <section
        v-else-if="posId"
        class="rounded-[2rem] border border-slate-200 bg-white p-3 shadow-sm sm:p-5"
      >
        <component
          :is="currentTabComponent"
          :key="`${currentTabComponent}-${posId}-${componentRefreshKey}`"
          :pos-id="posId"
          :permissoes="permissoes"
          :is-membro="isMembro"
          @alterado="onSubscricaoAlterada"
          @ver-subscricao="abrirAba('subscricao')"
        />
      </section>

      <!-- Loading -->
      <section
        v-else-if="!posLoaded"
        class="rounded-[2rem] border border-slate-200 bg-white p-10 text-center shadow-sm"
      >
        <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
        <p class="font-bold text-slate-600">A carregar dados do POS...</p>
      </section>

      <!-- Onboarding (só conta principal; nunca ao admin a ver — a faixa explica) -->
      <section
        v-else-if="!soLeitura"
        class="rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl text-slate-500">
          <font-awesome-icon :icon="['fas', 'receipt']" />
        </div>

        <h2 class="mt-5 text-2xl font-black text-slate-950">
          Configura o teu primeiro POS
        </h2>

        <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          Escolhe se queres usar o POS sozinho ou integrado com uma loja Bendi.
        </p>

        <div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            type="button"
            @click="abrirOnboarding"
            class="inline-flex h-12 items-center justify-center rounded-2xl bg-slate-950 px-6 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
          >
            Escolher configuração e plano
          </button>
        </div>
      </section>
    </main>

    <!-- Onboarding -->
    <OnboardingModal
      v-if="showOnboardingModal"
      :lojas="lojas"
      :onboarding-data="onboardingData"
      :loading="creatingPos"
      @completed="handleOnboardingCompleted"
      @create-pos="handleOnboardingCreatePOS"
      @close="handleOnboardingClose"
    />

    <!-- Modal Configuração (só conta principal) -->
    <div
      v-if="showConfigModal && !isMembro"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharConfiguracao"
    >
      <div class="w-full max-w-2xl overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white p-5">
          <div>
            <h3 class="text-xl font-black text-slate-950">Configuração do POS</h3>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              Define se o POS trabalha sozinho, com loja Bendi ou em modo híbrido.
            </p>
          </div>

          <button
            type="button"
            @click="fecharConfiguracao"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </header>

        <form class="max-h-[65vh] space-y-5 overflow-y-auto p-5 sm:max-h-[calc(100vh-14rem)]" @submit.prevent="guardarConfiguracao">
          <div
            v-if="configError"
            class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
          >
            {{ configError }}
          </div>

          <div
            v-if="configSuccess"
            class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
          >
            {{ configSuccess }}
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Nome do POS</label>
            <input
              v-model.trim="configForm.nome"
              type="text"
              placeholder="Ex: POS Principal"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Loja Bendi</label>
            <select
              v-model="configForm.loja_id"
              data-teste="config-loja"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            >
              <option value="">Sem loja vinculada</option>
              <option v-for="loja in lojas" :key="loja.id" :value="loja.id">
                {{ loja.nome }}
              </option>
            </select>
            <p v-if="configForm.modo === 'standalone' && lojaVinculada" data-teste="config-aviso-standalone" class="mt-2 text-xs font-semibold leading-5 text-amber-700">
              Em standalone o POS desliga-se de {{ lojaVinculada.nome }} e passa a usar só os seus produtos.
              Se estava incluído no plano Loja + POS da loja, passa a ter o seu próprio plano.
            </p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Modo de operação</label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label
                v-for="modoOption in modoOptions"
                :key="modoOption.value"
                :class="[
                  'cursor-pointer rounded-[1.25rem] border-2 p-4 transition',
                  configForm.modo === modoOption.value
                    ? 'border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <input v-model="configForm.modo" type="radio" :value="modoOption.value" class="hidden" />
                <p class="text-sm font-black">{{ modoOption.label }}</p>
                <p
                  :class="[
                    'mt-2 text-xs font-semibold leading-5',
                    configForm.modo === modoOption.value ? 'text-slate-300' : 'text-slate-500'
                  ]"
                >
                  {{ modoOption.description }}
                </p>
              </label>
            </div>
          </div>

          <div>
            <label for="pos-iva" class="mb-2 block text-sm font-black text-slate-700">Taxa de IVA (%)</label>
            <input
              id="pos-iva"
              v-model.trim="configForm.percentagem_iva"
              type="text"
              inputmode="decimal"
              placeholder="Ex: 15"
              class="h-12 w-full max-w-[160px] rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
            <p class="mt-1.5 text-xs font-semibold text-slate-500">
              Os preços do POS já incluem IVA. Esta taxa só serve para o Mapa de IVA dos relatórios.
            </p>
          </div>

          <!-- Dados fiscais: guardam-se à parte (PATCH /api/pos/<id>/fiscal/) -->
          <SeccaoDadosFiscais v-if="currentPOS?.fiscal" tema="claro"
                              :fiscal="currentPOS.fiscal" :url="`/api/pos/${posId}/fiscal/`" @guardado="fiscalGuardado" />
        </form>

        <div class="grid grid-cols-2 gap-3 border-t border-slate-200 bg-slate-50 p-5">
          <button
            type="button"
            @click="fecharConfiguracao"
            class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
          >
            Cancelar
          </button>

          <button
            type="button"
            @click="guardarConfiguracao"
            :disabled="savingConfig"
            class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span v-if="!savingConfig">Guardar</span>
            <span v-else class="flex items-center gap-2">
              <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
              A guardar...
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AvisoFaturacao from '@/components/fiscal/AvisoFaturacao.vue'
import SeccaoDadosFiscais from '@/components/fiscal/SeccaoDadosFiscais.vue'
import api, { POS_ACCESS, POS_REFRESH, terminarSessao, verAdminPOS, EVENTO_VER_ADMIN_EXPIROU } from '@/services/api'

import POSMesas from './POSMesas.vue'
import POSPedidos from './POSPedidos.vue'
import POSHistorico from './POSHistorico.vue'
import POSProdutos from './POSProdutos.vue'
import POSEquipa from './POSEquipa.vue'
import POSSubscricao from './POSSubscricao.vue'
import POSPainel from './POSPainel.vue'
import POSFaturacao from './POSFaturacao.vue'
import POSRelatorios from './POSRelatorios.vue'
import OnboardingModal from './components/OnboardingModal.vue'

export default {
  name: 'POSDashboard',

  components: {
    AvisoFaturacao, SeccaoDadosFiscais,
    POSMesas,
    POSPedidos,
    POSHistorico,
    POSProdutos,
    POSEquipa,
    POSSubscricao,
    POSPainel,
    POSFaturacao,
    POSRelatorios,
    OnboardingModal
  },

  data() {
    return {
      // admin a ver este POS (Admin → POS → Ver POS): só leitura e nada se grava no localStorage
      // (é a sessão do POS do próprio admin)
      soLeitura: !!verAdminPOS(),
      verAdminExpirou: !!verAdminPOS()?.expirou,
      abaGuardada: '',     // a última aba usada neste aparelho (abre-se em /pos/dashboard sem aba)

      posId: null,
      posNome: '',
      posCodigo: '',
      modo: 'standalone',
      lojaVinculada: null,
      currentPOS: null,

      // Sessão
      tipoSessao: 'principal',   // 'principal' | 'membro'
      userName: '',
      userInitial: '',
      permissoes: null,
      membroPapel: '',

      posLoaded: false,
      creatingPos: false,
      savingConfig: false,

      lojas: [],
      onboardingData: null,
      showOnboardingModal: false,

      showConfigModal: false,
      configError: '',
      configSuccess: '',

      componentRefreshKey: 0,

      configForm: {
        nome: '',
        loja_id: '',
        modo: 'standalone'
      },

      // Todas as tabs possíveis
      allTabs: [
        { id: 'painel',   label: 'Painel',    icon: 'chart-line',      apenasNaoMembro: false },
        { id: 'mesas',    label: 'Mesas',     icon: 'utensils',        apenasNaoMembro: false },
        { id: 'pedidos',  label: 'Pedidos',   icon: 'cart-shopping',   apenasNaoMembro: false },
        { id: 'produtos', label: 'Produtos',  icon: 'box',             apenasNaoMembro: false },
        { id: 'historico',label: 'Histórico', icon: 'clock-rotate-left', apenasNaoMembro: false },
        { id: 'relatorios', label: 'Relatórios', icon: 'file-lines',   apenasNaoMembro: false },
        { id: 'faturacao', label: 'Faturação', icon: 'file-invoice',   apenasNaoMembro: false },
        { id: 'equipa',   label: 'Equipa',    icon: 'users',           apenasNaoMembro: true  },
        { id: 'subscricao', label: 'Subscrição', icon: 'credit-card',  apenasNaoMembro: true  },
      ],

      // faixa da subscrição (só o dono) — GET /api/pos/<id>/subscricao/
      avisoSub: null,

      modoOptions: [
        {
          value: 'standalone',
          label: 'Standalone',
          description: 'Usa apenas produtos próprios do POS.'
        },
        {
          value: 'integrado',
          label: 'Integrado',
          description: 'Usa apenas produtos da loja Bendi.'
        },
        {
          value: 'hibrido',
          label: 'Híbrido',
          description: 'Usa produtos próprios e produtos da loja.'
        }
      ]
    }
  },

  computed: {
    // Sessão membro de equipa?
    isMembro() {
      return this.tipoSessao === 'membro'
    },

    // Papel legível do membro
    membroPapelLabel() {
      const labels = {
        gerente:   'Gerente',
        empregado: 'Empregado',
        cozinha:   'Cozinha',
        caixa:     'Caixa',
      }
      return labels[this.membroPapel] || this.membroPapel
    },

    // Tabs filtradas por tipo de sessão e permissões
    tabsVisiveis() {
      return this.allTabs.filter(tab => {
        // Tab exclusiva de não-membro
        if (tab.apenasNaoMembro && this.isMembro) return false

        // Filtrar por permissões do membro
        if (this.isMembro && this.permissoes) {
          if (['historico', 'painel', 'relatorios', 'faturacao'].includes(tab.id) && !this.permissoes.pode_ver_relatorios) return false
          if (tab.id === 'produtos'  && !this.permissoes.pode_gerir_produtos)  return false
        }

        return true
      })
    },

    // a aba vem do endereço (/pos/dashboard/<aba>): um refresh ou o voltar do browser mantêm-na
    activeTab() {
      const visiveis = this.tabsVisiveis.map(t => t.id)
      const pedida = this.$route.params.aba
      if (visiveis.includes(pedida)) return pedida
      if (visiveis.includes(this.abaGuardada)) return this.abaGuardada
      return !this.isMembro ? 'painel' : 'mesas'
    },

    currentTabComponent() {
      const map = {
        mesas:    'POSMesas',
        pedidos:  'POSPedidos',
        produtos: 'POSProdutos',
        historico:'POSHistorico',
        painel:   'POSPainel',
        relatorios: 'POSRelatorios',
        equipa:   'POSEquipa',
        subscricao: 'POSSubscricao',
        faturacao: 'POSFaturacao',
      }
      return map[this.activeTab] || 'POSMesas'
    },

    podeHistorico() {
      return !this.isMembro || Boolean(this.permissoes?.pode_ver_relatorios)
    },
    // num POS suspenso só abrem a Subscrição (dono, para pagar), o Histórico e a Faturação (faturas das vendas já feitas)
    abertaSuspenso() {
      return (this.activeTab === 'subscricao' && !this.isMembro) || (['historico', 'faturacao'].includes(this.activeTab) && this.podeHistorico)
    },

    // suspenso por falta de pagamento (o dono paga na aba Subscrição e o POS volta logo)
    suspensoPorSubscricao() {
      return Boolean(this.currentPOS?.suspenso && (this.currentPOS.suspenso_motivo || '').startsWith('Subscrição por pagar'))
    },

    modoLabel() {
      return { standalone: 'Standalone', integrado: 'Integrado', hibrido: 'Híbrido' }[this.modo] || 'Standalone'
    },

    modoDescription() {
      if (this.modo === 'integrado') return 'O POS usa apenas produtos da loja Bendi vinculada.'
      if (this.modo === 'hibrido')   return 'O POS usa produtos próprios e produtos da loja Bendi.'
      return 'O POS usa apenas produtos próprios, sem depender de uma loja.'
    },

    modoBadgeClass() {
      return {
        standalone: 'bg-purple-50 text-purple-700',
        integrado:  'bg-blue-50 text-blue-700',
        hibrido:    'bg-emerald-50 text-emerald-700',
      }[this.modo] || 'bg-purple-50 text-purple-700'
    }
  },

  watch: {
    activeTab(aba) {
      if (this.soLeitura) return
      try { localStorage.setItem('pos_aba', aba) } catch { /* sem storage */ }
    },
    // sem aba, aba que não existe ou que este membro não vê → a aba certa no endereço
    $route() { this.acertarEndereco() },
    tabsVisiveis() { this.acertarEndereco() },
    // standalone = sem loja: escolher uma loja passa a integrado; escolher standalone tira a loja
    'configForm.loja_id'(id) {
      if (id && this.configForm.modo === 'standalone') this.configForm.modo = 'integrado'
    },
    'configForm.modo'(modo) {
      if (modo === 'standalone') this.configForm.loja_id = ''
    },
  },

  beforeUnmount() {
    window.removeEventListener(EVENTO_VER_ADMIN_EXPIROU, this.aoExpirarVer)
  },

  async created() {
    this.aoExpirarVer = () => { this.verAdminExpirou = true }
    window.addEventListener(EVENTO_VER_ADMIN_EXPIROU, this.aoExpirarVer)
    this.loadSessao()
    this.escolherAbaInicial()
    this.loadLojasFromStorage()
    this.loadOnboardingData()
    await this.loadPOSData()
  },

  methods: {
    // ── SESSÃO ──────────────────────────────────────────────────────
    // O tipo de sessão vem do TOKEN activo (claim tipo_sessao), não de chaves guardadas
    // que podem ter ficado de outra sessão (ex.: entrou na Bendi depois de usar o POS).
    tipoSessaoDoToken() {
      // o POS tem sessão própria (services/api.js) — dono ou membro, quem diz é o token
      try {
        const token = localStorage.getItem(POS_ACCESS) || ''
        const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
        return payload.tipo_sessao === 'membro' ? 'membro' : 'principal'
      } catch {
        return localStorage.getItem('tipo_sessao') || 'principal'
      }
    },

    loadSessao() {
      if (this.soLeitura) {     // como o dono vê (o nome chega com /api/pos/meus/)
        this.tipoSessao = 'principal'
        this.permissoes = null
        return
      }
      this.tipoSessao = this.tipoSessaoDoToken()
      localStorage.setItem('tipo_sessao', this.tipoSessao)

      if (this.tipoSessao === 'membro') {
        // Sessão de membro de equipa
        const membro = JSON.parse(localStorage.getItem('pos_membro') || '{}')
        const pos    = JSON.parse(localStorage.getItem('pos_membro_pos') || '{}')

        this.userName    = membro.nome || 'Membro'
        this.userInitial = (membro.nome || 'M').charAt(0).toUpperCase()
        this.membroPapel = membro.papel || ''
        this.permissoes  = JSON.parse(localStorage.getItem('pos_membro_permissoes') || 'null')

        // Definir POS diretamente (membro entra sempre no POS associado)
        if (pos?.id) {
          this.posId       = pos.id
          this.posNome     = pos.nome || 'POS'
          this.posCodigo   = pos.codigo_pos || ''
          this.modo        = pos.modo || 'standalone'
          this.lojaVinculada = pos.loja_vinculada || null
          this.posLoaded   = true
        }
      } else {
        // Sessão de conta principal (nome definitivo chega com /api/pos/meus/)
        const user = JSON.parse(localStorage.getItem('pos_user') || '{}') || {}
        this.setUtilizador(user)
        this.permissoes  = null
      }
    },

    escolherAbaInicial() {
      try { this.abaGuardada = localStorage.getItem('pos_aba') || '' } catch { /* sem storage */ }
      this.acertarEndereco()
    },

    abrirAba(aba) {
      if (aba !== this.$route.params.aba) this.$router.push({ name: 'POSDashboard', params: { aba } })
    },

    acertarEndereco() {
      if (this.$route.name !== 'POSDashboard') return
      if (this.$route.params.aba !== this.activeTab) {
        this.$router.replace({ name: 'POSDashboard', params: { aba: this.activeTab }, query: this.$route.query })
      }
    },

    setUtilizador(user) {
      this.userName    = user?.nome || user?.first_name || user?.username || 'Utilizador'
      this.userInitial = this.userName.charAt(0).toUpperCase()
    },

    // ── LOJAS / ONBOARDING ──────────────────────────────────────────
    loadLojasFromStorage() {
      try {
        this.lojas = JSON.parse(localStorage.getItem('pos_lojas') || '[]')
      } catch {
        this.lojas = []
      }
    },

    loadOnboardingData() {
      try {
        this.onboardingData = JSON.parse(localStorage.getItem('pos_onboarding_data') || 'null')
      } catch {
        this.onboardingData = null
      }
    },

    // o dono pode ter mudado as permissões, o papel ou o POS depois do login do membro
    async atualizarMembro() {
      try {
        const { data } = await api.get('/api/pos/membro/me/')
        localStorage.setItem('pos_membro', JSON.stringify(data.membro))
        localStorage.setItem('pos_membro_pos', JSON.stringify(data.pos))
        localStorage.setItem('pos_membro_permissoes', JSON.stringify(data.permissoes))
        this.loadSessao()          // tabsVisiveis acerta a aba, se a aberta deixou de ser permitida
      } catch { /* fica o que veio do login — o servidor confere as permissões na mesma */ }
    },

    // ── CARREGAR POS ────────────────────────────────────────────────
    async loadPOSData() {
      // Membro já tem POS carregado em loadSessao()
      if (this.isMembro) return this.atualizarMembro()

      if (this.soLeitura) {
        try {
          const { data } = await api.get('/api/pos/meus/')
          this.setUtilizador(data.user)
          this.lojas = data.lojas || []
        } catch { /* fica sem o nome do dono */ }
        await this.carregarDetalhePOS(verAdminPOS().pos)
        this.posLoaded = true
        return
      }

      try {
        // Fonte de verdade: o servidor. O localStorage só guarda a última escolha.
        const { data } = await api.get('/api/pos/meus/')
        const lista = data.pos || []

        this.setUtilizador(data.user)
        localStorage.setItem('pos_user', JSON.stringify(data.user))
        this.lojas = data.lojas || []
        localStorage.setItem('pos_lojas', JSON.stringify(this.lojas))
        localStorage.setItem('pos_existentes', JSON.stringify(lista))
        this.onboardingData = { tem_lojas: this.lojas.length > 0, lojas: this.lojas }

        const anterior = JSON.parse(localStorage.getItem('pos_selected') || 'null')
        const pos = lista.find(p => p.id === anterior?.id) || lista[0] || null

        if (pos) {
          await this.carregarDetalhePOS(pos.id)
        } else {
          // a conta não tem POS → só aqui faz sentido propor criar um
          localStorage.removeItem('pos_selected')
          localStorage.removeItem('pos_id')
          this.showOnboardingModal = true
        }
      } catch (error) {
        console.error('Erro ao carregar POS:', error)
        // sem resposta do servidor NÃO se propõe criar um POS (evita duplicados)
      } finally {
        this.posLoaded = true
      }
    },

    async carregarDetalhePOS(posId) {
      try {
        const { data } = await api.get(`/api/pos/${posId}/`)
        this.setCurrentPOS(data)
      } catch (error) {
        console.error('Erro ao carregar detalhe do POS:', error)
        if (this.soLeitura) return
        const posSelecionado = JSON.parse(localStorage.getItem('pos_selected') || 'null')
        if (posSelecionado?.id) this.setCurrentPOS(posSelecionado)
      }
    },

    setCurrentPOS(pos) {
      this.currentPOS    = pos
      this.posId         = pos.id
      this.posNome       = pos.nome || 'POS Principal'
      this.posCodigo     = pos.codigo_pos || ''
      this.modo          = pos.modo || 'standalone'
      this.lojaVinculada = pos.loja_vinculada || null

      if (this.soLeitura) {
        this.componentRefreshKey += 1
        this.carregarAvisoSub()
        return
      }
      localStorage.setItem('pos_selected',  JSON.stringify(pos))
      localStorage.setItem('pos_id',        String(pos.id))
      localStorage.setItem('pos_precisa_onboarding', 'false')

      const posExistentes = JSON.parse(localStorage.getItem('pos_existentes') || '[]')
      const updated = posExistentes.length
        ? posExistentes.map(item => item.id === pos.id ? { ...item, ...pos } : item)
        : [pos]
      localStorage.setItem('pos_existentes', JSON.stringify(updated))

      this.showOnboardingModal = false
      this.componentRefreshKey += 1
      this.carregarAvisoSub()
    },

    // ── SUBSCRIÇÃO ──────────────────────────────────────────────────
    async carregarAvisoSub() {
      if (this.isMembro || !this.posId) return
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/subscricao/`)
        this.avisoSub = data.aviso
      } catch {
        this.avisoSub = null
      }
    },

    async onSubscricaoAlterada(dados) {
      this.avisoSub = dados?.aviso || null
      // pagou e a suspensão levantou: volta a ler o POS (desbloqueia as outras abas)
      if (this.currentPOS?.suspenso && dados && !dados.suspenso) {
        const { data } = await api.get(`/api/pos/${this.posId}/`)
        this.currentPOS = data
        localStorage.setItem('pos_selected', JSON.stringify(data))
      }
    },

    // ── ONBOARDING ──────────────────────────────────────────────────
    abrirOnboarding() {
      this.loadLojasFromStorage()
      this.loadOnboardingData()
      this.showOnboardingModal = true
    },

    handleOnboardingClose()           { this.showOnboardingModal = false },
    handleOnboardingCompleted(pos)    { pos?.id ? this.setCurrentPOS(pos) : this.loadPOSData() },
    async handleOnboardingCreatePOS(payload) { await this.criarPOSComPayload(payload) },

    // ── CRIAR POS ───────────────────────────────────────────────────
    async criarPOSComPayload(payload = {}) {
      if (this.creatingPos) return
      this.creatingPos = true
      try {
        const body = { nome: payload.nome || 'POS Principal', modo: payload.modo || 'standalone' }
        if (payload.loja_id) body.loja_id = payload.loja_id
        if (payload.plano_id) body.plano_id = payload.plano_id
        for (const k of ['nif', 'regime_fiscal', 'declaracao_fiscal']) if (payload[k]) body[k] = payload[k]
        const { data } = await api.post('/api/pos/criar/', body)
        this.setCurrentPOS(data)
      } catch (error) {
        console.error('Erro ao criar POS:', error)
        alert(error.response?.data?.detail || 'Erro ao criar POS.')
      } finally {
        this.creatingPos = false
      }
    },

    fiscalGuardado (pos) {
      this.currentPOS = pos
      localStorage.setItem('pos_selected', JSON.stringify(pos))
    },

    // ── CONFIGURAÇÃO ────────────────────────────────────────────────
    async abrirConfiguracao() {
      if (!this.posId) { this.abrirOnboarding(); return }

      this.configError   = ''
      this.configSuccess = ''

      // Recarregar lojas do backend (URL correta)
      try {
        const { data } = await api.get('/app/loja/minhas/')
        // o POS só pode usar lojas aprovadas (activas ou fechadas pelo dono) — como o backend
        const vinculaveis = (data.results || data).filter(l => ['ativa', 'fechada'].includes(l.estado))
        this.lojas = vinculaveis
        localStorage.setItem('pos_lojas', JSON.stringify(vinculaveis))
      } catch (error) {
        console.error('Erro ao recarregar lojas:', error)
        this.loadLojasFromStorage()
      }

      this.configForm = {
        nome:    this.posNome || 'POS Principal',
        loja_id: this.lojaVinculada?.id || '',
        modo:    this.modo || 'standalone',
        percentagem_iva: this.currentPOS?.percentagem_iva ?? '0.00'
      }

      this.showConfigModal = true
    },

    fecharConfiguracao() {
      this.showConfigModal = false
      this.configError     = ''
      this.configSuccess   = ''
    },

    async guardarConfiguracao() {
      if (!this.posId || this.savingConfig) return

      this.configError   = ''
      this.configSuccess = ''

      if (['integrado', 'hibrido'].includes(this.configForm.modo) && !this.configForm.loja_id) {
        this.configError = 'Para usar modo integrado ou híbrido, escolhe uma loja Bendi.'
        return
      }
      const iva = Number(String(this.configForm.percentagem_iva ?? '').replace(',', '.'))
      if (String(this.configForm.percentagem_iva ?? '').trim() === '' || !Number.isFinite(iva) || iva < 0 || iva > 100) {
        this.configError = 'A taxa de IVA vai de 0 a 100%.'
        return
      }

      this.savingConfig = true

      try {
        // standalone = sem loja: mesmo com uma loja escolhida, desliga-a
        if (this.configForm.modo !== 'standalone' && this.configForm.loja_id) {
          const { data } = await api.post(`/api/pos/${this.posId}/conectar-loja/`, {
            loja_id: this.configForm.loja_id,
            modo:    this.configForm.modo
          })
          this.setCurrentPOS(data.pos || data)
        } else {
          const { data } = await api.post(`/api/pos/${this.posId}/desconectar-loja/`)
          this.setCurrentPOS(data.pos || data)
        }

        const alteracoes = {}
        if (this.configForm.nome && this.configForm.nome !== this.posNome) alteracoes.nome = this.configForm.nome
        if (iva !== Number(this.currentPOS?.percentagem_iva || 0)) alteracoes.percentagem_iva = iva.toFixed(2)
        if (Object.keys(alteracoes).length) {
          const { data } = await api.patch(`/api/pos/${this.posId}/`, alteracoes)
          this.setCurrentPOS(data)
        }

        this.configSuccess = 'Configuração guardada com sucesso.'
        setTimeout(() => this.fecharConfiguracao(), 700)

      } catch (error) {
        console.error('Erro ao guardar configuração:', error)
        this.configError = error.response?.data?.detail || 'Erro ao guardar configuração do POS.'
      } finally {
        this.savingConfig = false
      }
    },

    async desconectarLoja() {
      if (!confirm('Desconectar este POS da loja Bendi? O POS passará para modo standalone.')) return
      this.savingConfig = true
      try {
        const { data } = await api.post(`/api/pos/${this.posId}/desconectar-loja/`)
        this.setCurrentPOS(data.pos || data)
      } catch (error) {
        alert(error.response?.data?.detail || 'Erro ao desconectar loja.')
      } finally {
        this.savingConfig = false
      }
    },

    // ── LOGOUT ──────────────────────────────────────────────────────
    logout() {
      if (!confirm('Tem a certeza que quer sair?')) return

      // sai só do POS (dono ou membro) — a sessão Bendi que exista no browser não é tocada
      terminarSessao(POS_ACCESS, POS_REFRESH)
      const keys = [
        'tipo_sessao', POS_ACCESS, POS_REFRESH,
        'pos_membro', 'pos_membro_pos', 'pos_membro_permissoes',
        'pos_user', 'pos_lojas', 'pos_existentes', 'pos_selected',
        'pos_id', 'pos_tem_lojas', 'pos_precisa_onboarding', 'pos_onboarding_data',
      ]
      keys.forEach(k => localStorage.removeItem(k))

      this.$router.push('/pos/login')
    }
  }
}
</script>