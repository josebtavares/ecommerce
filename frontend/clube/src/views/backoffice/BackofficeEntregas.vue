<template>
  <div class="space-y-5">

    <!-- Tabs -->
    <div class="flex gap-1 bg-zinc-900 rounded-xl p-1 w-fit">
      <button v-for="tab in tabsVisiveis" :key="tab.key"
        @click="activeTab = tab.key"
        :class="['px-4 py-2 rounded-lg text-sm font-semibold transition',
                 activeTab === tab.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
        <font-awesome-icon :icon="['fas', tab.icon]" class="mr-1.5" />{{ tab.label }}
      </button>
    </div>

    <!-- ═══ TAB: ENTREGAS ═══ -->
    <div v-if="activeTab === 'entregas'">

      <!-- Filtros + limit -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <button v-for="f in filtrosEntrega" :key="f.value"
          @click="filtroEntrega = f.value; page = 1; fetchEntregas()"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition',
                   filtroEntrega === f.value ? f.active : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ f.label }}
        </button>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-xs text-zinc-500">Por página:</span>
          <select v-model="limit" @change="page = 1; fetchEntregas()"
            class="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-300 focus:outline-none focus:border-red-500">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
          <span class="text-xs text-zinc-500">{{ totalCount }} entregas</span>
        </div>
      </div>

      <div v-if="loadingEntregas" class="space-y-3">
        <div v-for="n in limit" :key="n" class="h-24 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>

      <div v-else-if="entregas.length === 0"
           class="text-center py-16 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem entregas neste estado.
      </div>

      <div v-else class="space-y-3">
        <div v-for="entrega in entregas" :key="entrega.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">

          <!-- Header -->
          <div class="p-4 flex items-start gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span class="text-sm font-bold text-zinc-200">Encomenda #{{ entrega.encomenda }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', entregaStatusColor(entrega.status)]">
                  {{ labelStatus(entrega.status) }}
                </span>
                <span v-if="entrega.opcao_entrega_nome"
                      class="px-1.5 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-400">
                  {{ entrega.opcao_entrega_nome }}
                </span>
                <span v-if="entrega.agendada_texto" data-teste="agendada"
                      class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-300">
                  <font-awesome-icon :icon="['fas', 'calendar-days']" class="mr-1" />{{ entrega.agendada_texto }}
                </span>
              </div>
              <p class="text-xs text-zinc-500">{{ entrega.data_criacao }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <p v-if="entrega.condutor_nome" class="text-xs font-semibold text-zinc-200">
                <font-awesome-icon :icon="['fas', 'car']" class="mr-1 text-zinc-500" />{{ entrega.condutor_nome }}
              </p>
              <p v-if="entrega.condutor_veiculo" class="text-[10px] text-zinc-500">{{ entrega.condutor_veiculo }}</p>
              <p v-if="!entrega.condutor_nome" class="text-xs text-zinc-600 italic">Sem condutor</p>
            </div>
          </div>

          <!-- Encomenda cancelada a meio -->
          <div v-if="entrega.status === 'cancelada'"
               class="border-t border-zinc-800 px-4 py-3 text-xs font-semibold text-red-400">
            <font-awesome-icon :icon="['fas', 'ban']" class="mr-1" />Encomenda cancelada — não entregar. Se já a levantaste, devolve-a à loja.
          </div>

          <!-- Contacto do cliente -->
          <div v-if="entrega.comprador_nome || entrega.comprador_email || entrega.comprador_telefone"
               class="border-t border-zinc-800 px-4 py-3 bg-zinc-800/30">
            <p class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Cliente</p>
            <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs">
              <span v-if="entrega.comprador_nome" class="text-zinc-300 font-semibold">
                Nome: {{ entrega.comprador_nome }}
              </span>
              <a v-if="entrega.comprador_email" :href="`mailto:${entrega.comprador_email}`"
                 class="text-zinc-300 hover:text-red-300 transition">Email: {{ entrega.comprador_email }}</a>
              <a v-if="entrega.comprador_telefone" :href="`tel:${entrega.comprador_telefone}`"
                 class="text-zinc-300 hover:text-red-300 transition">Contato: {{ entrega.comprador_telefone }}</a>
            </div>
          </div>

          <!-- Detalhe -->
          <div class="border-t border-zinc-800 px-4 py-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
            <div v-if="entrega.morada_entrega" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Morada:</span>
              <span class="text-zinc-300">{{ entrega.morada_entrega }}</span>
              <a v-if="porEntregar(entrega)" :href="linkMapa(entrega)" target="_blank" rel="noopener noreferrer"
                 class="flex-shrink-0 ml-auto font-semibold text-red-400 hover:text-red-300 whitespace-nowrap">
                <font-awesome-icon :icon="['fas', 'location-dot']" class="mr-1" />Mapa
              </a>
            </div>
            <div v-if="entrega.itens?.length" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Levar:</span>
              <span class="text-zinc-200 font-semibold">{{ entrega.itens.join(', ') }}</span>
            </div>
            <div v-if="entrega.valor_a_cobrar" data-teste="a-cobrar"
                 class="col-span-2 flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-amber-500/15 text-amber-300 font-bold">
              <span>A cobrar em dinheiro</span><span class="text-sm">{{ $dinheiro(entrega.valor_a_cobrar) }}</span>
            </div>
            <div v-else-if="entrega.pago && porEntregar(entrega)" class="col-span-2 font-semibold text-green-400">
              <font-awesome-icon :icon="['fas', 'circle-check']" class="mr-1" />Já pago — não cobrar nada
            </div>
            <div v-if="entrega.tipo_entrega" class="flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Tipo:</span>
              <span class="text-zinc-300">
                <font-awesome-icon :icon="['fas', entrega.tipo_entrega === 'entrega' ? 'truck' : 'store']" class="mr-1 text-zinc-500" />
                {{ entrega.tipo_entrega === 'entrega' ? 'Domicílio' : 'Levantamento' }}
              </span>
            </div>
            <div v-if="entrega.opcao_entrega_nome" class="flex gap-2 col-span-2">
              <span class="text-zinc-500 flex-shrink-0">Opção:</span>
              <span class="text-zinc-300 font-semibold">{{ entrega.opcao_entrega_nome }}</span>
              <span v-if="entrega.opcao_entrega_tempo" class="text-zinc-500">· {{ entrega.opcao_entrega_tempo }}</span>
              <span v-if="entrega.opcao_entrega_preco" class="text-zinc-500">
                · {{ parseFloat(entrega.opcao_entrega_preco) === 0 ? 'Gratuito' : $dinheiro(entrega.opcao_entrega_preco) }}
              </span>
            </div>
            <div v-if="entrega.metodo_pagamento" class="flex gap-2">
              <span class="text-zinc-500">Pagamento:</span>
              <span class="text-zinc-300 capitalize">
                <font-awesome-icon :icon="['fas', iconePagamento(entrega.metodo_pagamento)]" class="mr-1 text-zinc-500" />
                {{ entrega.metodo_pagamento }}
              </span>
            </div>
            <div v-if="entrega.notas" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0"><font-awesome-icon :icon="['fas', 'note-sticky']" class="mr-1" />Notas:</span>
              <span class="text-zinc-300 italic">{{ entrega.notas }}</span>
            </div>
            <div v-if="entrega.motivo_falha" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Motivo:</span>
              <span class="text-red-400">{{ entrega.motivo_falha_texto }}{{ entrega.nota_falha ? ` — ${entrega.nota_falha}` : '' }}</span>
            </div>
            <div v-if="entrega.data_entrega" class="col-span-2 text-green-400">
              <font-awesome-icon :icon="['fas', 'circle-check']" class="mr-1" />Entregue em {{ entrega.data_entrega }}
            </div>
          </div>

          <!-- Acções -->
          <div v-if="temAcoes(entrega)"
               class="border-t border-zinc-800 px-4 py-3 flex flex-wrap gap-2 items-center">
            <template v-if="isCondutor">
              <button v-if="entrega.status === 'atribuido'"
                @click="atualizarEntrega(entrega, 'a_caminho')" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'car']" class="mr-1" />A caminho
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="modalEntregue = entrega" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'check']" class="mr-1" />Marcar entregue
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="confirmarFalha(entrega)" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'xmark']" class="mr-1" />Não consegui entregar
              </button>
              <button v-if="podeFalar(entrega)" @click="falarComCliente(entrega)"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'comment-dots']" class="mr-1" />Mensagem
              </button>
            </template>
            <template v-else>
              <button @click="abrirReatribuir(entrega)"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', entrega.condutor_nome ? 'rotate-left' : 'plus']" class="mr-1" />{{ entrega.condutor_nome ? 'Reatribuir' : 'Atribuir condutor' }}
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="modalEntregue = entrega" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'check']" class="mr-1" />Concluir entrega
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="confirmarFalha(entrega)" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'xmark']" class="mr-1" />Entrega falhou
              </button>
              <button v-if="entrega.status === 'falhou' && entrega.tipo_entrega === 'entrega'" @click="abrirMorada(entrega)"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                <font-awesome-icon :icon="['fas', 'location-dot']" class="mr-1" />Corrigir morada
              </button>
            </template>
            <svg v-if="loadingAcao === entrega.id" class="animate-spin h-4 w-4 text-zinc-500 ml-auto" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Paginação -->
      <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
        <p class="text-xs text-zinc-500">
          {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
        </p>
        <div class="flex items-center gap-2">
          <button @click="irParaPagina(page - 1)" :disabled="page <= 1"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button v-for="p in paginasVisiveis" :key="p" @click="irParaPagina(p)"
            :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                     p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
            {{ p }}
          </button>
          <button @click="irParaPagina(page + 1)" :disabled="page >= totalPages"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ TAB: CALENDÁRIO ═══ -->
    <CalendarioEntregas v-if="activeTab === 'calendario'" :loja-id="lojaId" :is-condutor="isCondutor"
      :condutores="condutores" @alterado="entregas = []" />

    <!-- ═══ TAB: CONDUTORES ═══ -->
    <div v-if="activeTab === 'condutores' && !isCondutor">
      <div v-if="loadingCondutores" class="space-y-3">
        <div v-for="n in 3" :key="n" class="h-14 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>
      <div v-else-if="condutores.length === 0"
           class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem condutores. Adiciona condutores na secção de Staff.
      </div>
      <div v-else class="space-y-3">
        <div v-for="c in condutores" :key="c.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4">
          <div class="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-300 font-bold flex-shrink-0">
            {{ (c.utilizador_nome || c.utilizador_username)?.charAt(0)?.toUpperCase() || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-200">{{ c.utilizador_nome || c.utilizador_username }}</p>
            <p class="text-xs text-zinc-500">{{ c.tipo_veiculo || 'Veículo não especificado' }}</p>
            <div class="flex gap-3 mt-1">
              <a v-if="c.utilizador_email" :href="`mailto:${c.utilizador_email}`"
                 class="text-xs text-red-400 hover:text-red-300 transition"><font-awesome-icon :icon="['fas', 'envelope']" class="mr-1" />{{ c.utilizador_email }}</a>
              <a v-if="c.utilizador_telefone" :href="`tel:${c.utilizador_telefone}`"
                 class="text-xs text-red-400 hover:text-red-300 transition"><font-awesome-icon :icon="['fas', 'phone']" class="mr-1" />{{ c.utilizador_telefone }}</a>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-zinc-500">
              {{ entregasActivasDoCondutor(c.id) }} activa{{ entregasActivasDoCondutor(c.id) !== 1 ? 's' : '' }}
            </span>
            <span :class="['w-2 h-2 rounded-full', c.ativo ? 'bg-green-500' : 'bg-zinc-600']"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal reatribuir -->
    <div v-if="modalReatribuir"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalReatribuir = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md p-6 space-y-5 shadow-2xl">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold text-zinc-100">
              {{ modalReatribuir.condutor_nome ? 'Reatribuir condutor' : 'Atribuir condutor' }}
            </h3>
            <p class="text-xs text-zinc-500 mt-0.5">Encomenda #{{ modalReatribuir.encomenda }}</p>
          </div>
          <button @click="modalReatribuir = null"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="modalReatribuir.comprador_nome || modalReatribuir.comprador_email || modalReatribuir.comprador_telefone"
             class="bg-zinc-800/50 rounded-xl p-3 space-y-1 text-xs">
          <p class="text-zinc-500 font-semibold mb-1">Cliente</p>
          <p v-if="modalReatribuir.comprador_nome" class="text-zinc-300 font-semibold"><font-awesome-icon :icon="['fas', 'user']" class="mr-1 text-zinc-500" fixed-width />{{ modalReatribuir.comprador_nome }}</p>
          <a v-if="modalReatribuir.comprador_email" :href="`mailto:${modalReatribuir.comprador_email}`"
             class="text-red-400 hover:text-red-300 flex items-center gap-1"><font-awesome-icon :icon="['fas', 'envelope']" fixed-width />{{ modalReatribuir.comprador_email }}</a>
          <a v-if="modalReatribuir.comprador_telefone" :href="`tel:${modalReatribuir.comprador_telefone}`"
             class="text-red-400 hover:text-red-300 flex items-center gap-1"><font-awesome-icon :icon="['fas', 'phone']" fixed-width />{{ modalReatribuir.comprador_telefone }}</a>
          <p v-if="modalReatribuir.morada_entrega" class="text-zinc-400 mt-1"><font-awesome-icon :icon="['fas', 'location-dot']" class="mr-1" fixed-width />{{ modalReatribuir.morada_entrega }}</p>
        </div>

        <div v-if="modalReatribuir.condutor_nome"
             class="bg-zinc-800/50 rounded-xl p-3 flex items-center gap-3 text-xs">
          <span class="text-zinc-500">Actual:</span>
          <span class="text-zinc-300 font-semibold"><font-awesome-icon :icon="['fas', 'car']" class="mr-1 text-zinc-500" />{{ modalReatribuir.condutor_nome }}</span>
          <span class="text-zinc-500 ml-auto">→ será substituído</span>
        </div>

        <div class="space-y-2 max-h-64 overflow-y-auto">
          <button v-for="c in condutores" :key="c.id"
            @click="novoCondutorId = c.id"
            :disabled="bloqueado(c)"
            :class="['w-full flex items-center gap-3 p-3 rounded-xl border-2 transition text-left',
                     bloqueado(c)
                       ? 'border-zinc-700 opacity-40 cursor-not-allowed'
                       : novoCondutorId === c.id
                         ? 'border-red-500 bg-red-500/10'
                         : 'border-zinc-700 hover:border-zinc-600']">
            <div class="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-sm flex-shrink-0 text-zinc-300">
              {{ (c.utilizador_nome || c.utilizador_username)?.charAt(0)?.toUpperCase() || '?' }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-zinc-200">{{ c.utilizador_nome || c.utilizador_username }}</p>
              <p class="text-xs text-zinc-500">{{ c.tipo_veiculo || 'Veículo n/d' }}</p>
              <p v-if="c.utilizador_telefone" class="text-xs text-zinc-600"><font-awesome-icon :icon="['fas', 'phone']" class="mr-1" />{{ c.utilizador_telefone }}</p>
            </div>
            <span v-if="bloqueado(c)" class="text-[10px] text-zinc-500">actual</span>
            <div v-else-if="novoCondutorId === c.id" class="w-4 h-4 rounded-full bg-red-500 flex-shrink-0"></div>
            <span v-else-if="c.id === modalReatribuir.condutor_id_field" class="text-[10px] text-zinc-500">tentou antes</span>
          </button>
          <p v-if="condutores.filter(c => !bloqueado(c)).length === 0"
             class="text-center py-4 text-zinc-500 text-sm">Sem outros condutores disponíveis.</p>
        </div>

        <div class="flex gap-3">
          <button @click="modalReatribuir = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="confirmarReatribuicao"
            :disabled="!novoCondutorId || loadingReatribuir"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     !novoCondutorId || loadingReatribuir ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loadingReatribuir" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            Confirmar
          </button>
        </div>
      </div>
    </div>

    <!-- Corrigir a morada depois de uma falha -->
    <div v-if="modalMorada"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalMorada = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 space-y-4 shadow-2xl" role="dialog" aria-modal="true">
        <div>
          <h3 class="text-base font-bold text-zinc-100">Corrigir morada</h3>
          <p class="text-sm text-zinc-400 mt-1">Encomenda <strong>#{{ modalMorada.encomenda }}</strong>. O cliente é avisado da morada nova.</p>
        </div>
        <textarea v-model="novaMorada" rows="3" maxlength="300" aria-label="Morada de entrega"
          class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500"></textarea>
        <div class="flex gap-3">
          <button type="button" @click="modalMorada = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Voltar
          </button>
          <button type="button" @click="guardarMorada" :disabled="!novaMorada.trim() || loadingMorada"
            class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition disabled:opacity-40">
            Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- Confirmar o fecho da entrega -->
    <ConfirmarEntrega v-if="modalEntregue" :encomenda-id="modalEntregue.encomenda" :a-cobrar="modalEntregue.valor_a_cobrar"
      :is-condutor="isCondutor" :a-guardar="!!loadingAcao" @fechar="modalEntregue = null"
      @confirmar="atualizarEntrega(modalEntregue, 'entregue')" />
    <ConfirmarEntrega v-if="modalFalha" falhou :encomenda-id="modalFalha.encomenda"
      :is-condutor="isCondutor" :a-guardar="!!loadingAcao" @fechar="modalFalha = null"
      @confirmar="atualizarEntrega(modalFalha, 'falhou', $event)" />

  </div>
</template>

<script>
import api from '@/services/api'
import { iconePagamento } from '@/utils/icones'
import CalendarioEntregas from '@/components/calendario/CalendarioEntregas.vue'
import ConfirmarEntrega from '@/components/calendario/ConfirmarEntrega.vue'
import { contactarCliente } from '@/services/chat'
import { toast } from 'vue3-toastify'

const ATUALIZAR_MS = 30000

export default {
  name: 'BackofficeEntregas',
  components: { CalendarioEntregas, ConfirmarEntrega },
  props: {
    lojaId:    [String, Number],
    minhaRole: { type: String, default: '' },
  },

  data () {
    return {
      activeTab: 'entregas',
      tabs: [
        { key: 'entregas',   label: 'Entregas',   icon: 'box' },
        { key: 'calendario', label: 'Calendário', icon: 'calendar-days' },
        { key: 'condutores', label: 'Condutores', icon: 'car' },
      ],
      entregas:      [],
      totalCount:    0,
      page:          1,
      limit:         10,
      loadingEntregas:  false,
      filtroEntrega:    'todos',
      filtrosEntrega: [
        { value: 'todos',     label: 'Todas',      active: 'bg-zinc-200 text-zinc-900'        },
        { value: 'atribuido', label: 'Atribuídas', active: 'bg-blue-500/20 text-blue-400'     },
        { value: 'a_caminho', label: 'A caminho',  active: 'bg-indigo-500/20 text-indigo-400' },
        { value: 'entregue',  label: 'Entregues',  active: 'bg-green-500/20 text-green-400'   },
        { value: 'falhou',    label: 'Falhadas',   active: 'bg-red-500/20 text-red-400'       },
        { value: 'cancelada', label: 'Canceladas', active: 'bg-zinc-500/20 text-zinc-300'     },
      ],
      condutores:        [],
      loadingCondutores: false,
      modalReatribuir:   null,
      novoCondutorId:    null,
      loadingReatribuir: false,
      modalFalha:        null,
      modalEntregue:     null,
      modalMorada:       null,
      novaMorada:        '',
      loadingMorada:     false,
      loadingAcao:       null,
      atualizador:       null,
    }
  },

  computed: {
    isCondutor ()  { return this.minhaRole === 'condutor' },
    // o condutor não gere condutores
    tabsVisiveis () { return this.isCondutor ? this.tabs.filter(t => t.key !== 'condutores') : this.tabs },
    totalPages ()  { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
  },

  async created () {
    await Promise.all([this.fetchEntregas(), this.isCondutor ? null : this.fetchCondutores()])
    this.atualizador = setInterval(this.atualizarLista, ATUALIZAR_MS)
  },

  beforeUnmount () { clearInterval(this.atualizador) },

  methods: {
    iconePagamento,
    labelStatus (s) {
      const map = { atribuido: 'Atribuído', a_caminho: 'A caminho', entregue: 'Entregue', falhou: 'Falhou', cancelada: 'Cancelada' }
      return map[s] || s
    },

    entregaStatusColor (s) {
      const map = {
        atribuido: 'bg-blue-500/15 text-blue-400',
        a_caminho: 'bg-indigo-500/15 text-indigo-400',
        entregue:  'bg-green-500/15 text-green-400',
        falhou:    'bg-red-500/15 text-red-400',
      }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    entregasActivasDoCondutor (condutorId) {
      return this.entregas.filter(e =>
        e.condutor_id_field === condutorId && this.porEntregar(e)
      ).length
    },

    porEntregar (e) { return ['atribuido', 'a_caminho'].includes(e.status) },
    // o condutor só age nas que tem por entregar; a loja também pode reatribuir uma que falhou
    temAcoes (e) { return this.porEntregar(e) || (!this.isCondutor && e.status === 'falhou' && e.encomenda_status === 'preparando') },

    linkMapa (e) {
      return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(e.morada_entrega)}`
    },

    podeFalar (e) {
      return this.porEntregar(e) && e.comprador_id
    },
    falarComCliente (e) { contactarCliente(this.lojaId, e.comprador_id, e.encomenda) },

    erroAcao (e) {
      const d = e.response?.data
      toast.error(d?.detail || d?.status?.[0] || 'Não foi possível guardar. Tenta de novo.')
    },

    // entrega nova, ou cancelada entretanto, sem o condutor ter de fazer refresh
    atualizarLista () {
      const ocupado = this.modalReatribuir || this.modalFalha || this.modalEntregue || this.modalMorada || this.loadingAcao
      if (!document.hidden && !ocupado && this.activeTab === 'entregas') this.fetchEntregas(true)
    },

    irParaPagina (p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.fetchEntregas()
    },

    async fetchEntregas (silencioso = false) {
      if (!silencioso) this.loadingEntregas = true
      try {
        const params = {
          limit:  this.limit,
          offset: (this.page - 1) * this.limit,
        }
        if (this.filtroEntrega !== 'todos') params.status = this.filtroEntrega
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/lista/`, { params })
        this.entregas   = data.results || data
        this.totalCount = data.count ?? this.entregas.length
      } catch (e) { console.error(e) }
      finally { this.loadingEntregas = false }
    },

    async fetchCondutores () {
      this.loadingCondutores = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/condutores/`)
        this.condutores = data.results || data
      } catch (e) { console.error(e) }
      finally { this.loadingCondutores = false }
    },

    async atualizarEntrega (entrega, novoStatus, extra = {}) {
      this.loadingAcao = entrega.id
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${entrega.encomenda}/entrega/atualizar/`,
          { status: novoStatus, ...extra }
        )
      } catch (e) { this.erroAcao(e) }
      finally {
        this.modalEntregue = this.modalFalha = null
        await this.fetchEntregas(true)     // mesmo com erro: a entrega pode ter mudado noutro lado
        this.loadingAcao = null
      }
    },

    confirmarFalha (entrega) { this.modalFalha = entrega },

    abrirMorada (entrega) {
      this.modalMorada = entrega
      this.novaMorada  = entrega.morada_entrega || ''
    },

    async guardarMorada () {
      this.loadingMorada = true
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${this.modalMorada.encomenda}/entrega/morada/`,
          { morada: this.novaMorada }
        )
        this.modalMorada = null
        await this.fetchEntregas(true)
        toast.success('Morada corrigida. Atribui um condutor para tentar de novo.')
      } catch (e) { this.erroAcao(e) }
      finally { this.loadingMorada = false }
    },

    // depois de uma falha o mesmo condutor pode tentar de novo (ex.: a morada foi esclarecida)
    bloqueado (c) {
      const e = this.modalReatribuir
      return c.id === e.condutor_id_field && e.status !== 'falhou'
    },

    abrirReatribuir (entrega) {
      this.modalReatribuir = entrega
      this.novoCondutorId  = null
    },

    async confirmarReatribuicao () {
      if (!this.novoCondutorId || !this.modalReatribuir) return
      this.loadingReatribuir = true
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${this.modalReatribuir.encomenda}/entrega/atualizar/`,
          { condutor_id: this.novoCondutorId }
        )
        this.modalReatribuir = null
        await this.fetchEntregas(true)
      } catch (e) { this.erroAcao(e) }
      finally { this.loadingReatribuir = false }
    },
  },

  watch: {
    activeTab (tab) {
      if (tab === 'entregas'   && this.entregas.length === 0)   this.fetchEntregas()
      if (tab === 'condutores' && this.condutores.length === 0) this.fetchCondutores()
    },
  },
}
</script>