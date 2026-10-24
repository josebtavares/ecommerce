<template>
  <!-- Posição partilhada com o carrinho — ver assets/loja-acoes.css -->
  <div :class="['loja-acoes-slot loja-acoes-slot--perfil z-20 text-white', !isDark && 'text-zinc-800']">
    <NotificacaoSino :isDark="isDark" />
    <button @click="toggle" :aria-label="autenticado ? 'Perfil' : 'Entrar ou criar conta'"
      :title="autenticado ? 'Perfil' : 'Entrar ou criar conta'"
      class="loja-acao-btn"
      :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
      <font-awesome-icon :icon="['fas', 'user']"
        class="text-[15px]"
        :class="isDark ? 'text-white' : 'text-zinc-700'" />
    </button>

    <!-- Backdrop -->
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                leave-active-class="transition duration-150" leave-to-class="opacity-0">
      <div v-if="isOpen" class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" @click="toggle"></div>
    </transition>

    <!-- Drawer — dark/light -->
    <transition enter-active-class="transition duration-300" enter-from-class="translate-x-full"
                leave-active-class="transition duration-200" leave-to-class="translate-x-full">
      <div v-if="isOpen"
           class="fixed top-0 right-0 w-full max-w-sm md:max-w-lg h-screen flex flex-col z-50 shadow-2xl overflow-hidden"
           :class="isDark
             ? 'bg-zinc-950 border-l border-zinc-800'
             : 'bg-white border-l border-gray-200'">

        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b flex-shrink-0"
             :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <div class="flex items-center gap-3">
            <div class="relative group/avatar cursor-pointer" @click="triggerFileSelect">
              <img :src="previewUrl" alt="avatar"
                   class="w-16 h-16 rounded-full object-cover border-2 transition"
                   :class="isDark ? 'border-zinc-700 group-hover/avatar:border-red-500' : 'border-gray-300 group-hover/avatar:border-red-400'" />
              <div class="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover/avatar:opacity-100
                          transition flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="hidden" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <p class="font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ data.username }}</p>
                <span v-if="data.verificado" title="Verificado" class="px-1.5 py-0.5 bg-green-500/15 text-green-400 text-[10px] rounded font-bold"><font-awesome-icon :icon="['fas', 'circle-check']" /></span>
              </div>
              <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ data.email }}</p>
            </div>
          </div>
          <button @click="toggle"
            class="w-8 h-8 rounded-full flex items-center justify-center transition"
            :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
                 :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b flex-shrink-0 overflow-x-auto perfil-tabs"
             :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
            :class="[
              'flex-1 px-3 py-3 text-xs font-semibold whitespace-nowrap transition border-b-2',
              activeTab === tab.key
                ? 'border-red-500 text-red-500'
                : isDark
                  ? 'border-transparent text-zinc-500 hover:text-zinc-300'
                  : 'border-transparent text-zinc-400 hover:text-zinc-700'
            ]">
            {{ tab.label }}
          </button>
        </div>

        <!-- Conteúdo scrollável -->
        <div class="flex-1 overflow-y-auto p-5">

          <!-- ═══ TAB: DADOS PESSOAIS ═══ -->
          <div v-if="activeTab === 'dados'">
            <h3 class="text-sm font-bold uppercase tracking-wider mb-4"
                :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Informações pessoais</h3>
            <div class="space-y-3">
              <div v-for="field in profileFields" :key="field.key">
                <label class="text-xs mb-1 block" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ field.label }}</label>
                <input v-model="form[field.key]" :type="field.type || 'text'"
                  @input="verificarCampo(field.key)"
                  class="w-full px-3 py-2 rounded-lg text-sm border transition focus:outline-none focus:border-red-500"
                  :class="isDark
                    ? 'bg-zinc-900 border-zinc-700 text-zinc-100'
                    : 'bg-gray-50 border-gray-300 text-zinc-900'" />
                <EstadoDisponibilidade v-if="verificadores[field.key]" :verificador="verificadores[field.key]" :isDark="isDark"
                  @usar="v => { form[field.key] = v; verificarCampo(field.key) }" />
              </div>
              <p v-if="profileError" class="text-xs text-red-400">{{ profileError }}</p>
            </div>
            <button @click="saveProfile" :disabled="loadingProfile"
              class="w-full mt-5 py-2.5 rounded-xl font-bold text-sm text-white transition-all flex items-center justify-center gap-2"
              :class="loadingProfile ? 'bg-red-700 opacity-70 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5'">
              <svg v-if="loadingProfile" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              {{ loadingProfile ? 'A guardar…' : 'Guardar alterações' }}
            </button>
          </div>

          <!-- ═══ TAB: PASSWORD ═══ -->
          <div v-if="activeTab === 'password'">
            <h3 class="text-sm font-bold uppercase tracking-wider mb-4"
                :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Alterar password</h3>
            <div class="space-y-3">
              <!-- contas criadas com Google ainda não têm password: definem uma sem pedir a actual -->
              <p v-if="!temPassword" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                Entras com o Google. Define uma password para poderes entrar também com email.
              </p>
              <div v-else>
                <label class="text-xs mb-1 block" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Password actual</label>
                <div class="relative">
                  <input v-model="formPassword.atual" :type="verPassword ? 'text' : 'password'" autocomplete="current-password"
                    class="w-full px-3 pr-10 py-2 rounded-lg text-sm border transition focus:outline-none focus:border-red-500"
                    :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-gray-50 border-gray-300 text-zinc-900'" />
                  <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
                </div>
              </div>
              <div>
                <label class="text-xs mb-1 block" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Nova password</label>
                <div class="relative">
                  <input v-model="formPassword.password" :type="verPassword ? 'text' : 'password'" autocomplete="new-password"
                    class="w-full px-3 pr-10 py-2 rounded-lg text-sm border transition focus:outline-none focus:border-red-500"
                    :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-gray-50 border-gray-300 text-zinc-900'" />
                  <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
                </div>
                <PasswordForca :password="formPassword.password" :isDark="isDark" />
              </div>
              <div>
                <label class="text-xs mb-1 block" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Confirmar password</label>
                <div class="relative">
                  <input v-model="formPassword.confirm" :type="verPassword ? 'text' : 'password'" autocomplete="new-password"
                    class="w-full px-3 pr-10 py-2 rounded-lg text-sm border transition focus:outline-none focus:border-red-500"
                    :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-gray-50 border-gray-300 text-zinc-900'" />
                  <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
                </div>
              </div>
              <p v-if="passwordError" class="text-xs text-red-400">{{ passwordError }}</p>
            </div>
            <button @click="savePassword" :disabled="loadingPassword"
              class="w-full mt-5 py-2.5 rounded-xl font-bold text-sm text-white transition-all flex items-center justify-center gap-2"
              :class="loadingPassword ? 'bg-red-700 opacity-70 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5'">
              <svg v-if="loadingPassword" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              {{ loadingPassword ? 'A guardar…' : 'Alterar password' }}
            </button>
          </div>

          <!-- ═══ TAB: ENCOMENDAS ═══ -->
          <div v-if="activeTab === 'encomendas'">
            <div class="flex flex-wrap items-center justify-between gap-2 mb-4">
              <h3 class="text-sm font-bold uppercase tracking-wider"
                  :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Histórico de encomendas</h3>
              <div class="flex items-center gap-2">
                <button type="button" @click="isOpen = false; $router.push('/minhas-marcacoes')" data-teste="link-marcacoes"
                  :class="[botaoAtalho, 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors']">
                  <font-awesome-icon :icon="['fas', 'calendar-check']" class="text-red-500" /> Marcações
                </button>
                <button type="button" @click="isOpen = false; $router.push('/perfil/reembolsos')" data-teste="link-reembolsos"
                  :class="[botaoAtalho, 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors']">
                  <font-awesome-icon :icon="['fas', 'rotate-left']" class="text-red-500" /> Reembolsos
                </button>
              </div>
            </div>

            <div v-if="loadingEncomendas" class="flex justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </div>

            <div v-else-if="encomendas.length === 0" class="text-center py-8 text-sm"
                 :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Ainda não tens encomendas.
            </div>

            <div v-else class="space-y-3">
              <div v-for="enc in encomendas" :key="enc.id"
                   class="rounded-xl border overflow-hidden transition-all"
                   :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-gray-50 border-gray-200'">

                <button @click="toggleEncomenda(enc.id)"
                  class="w-full flex items-center justify-between p-4 text-left transition"
                  :class="isDark ? 'hover:bg-zinc-800/50' : 'hover:bg-gray-100'">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-xs font-bold" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">#{{ enc.id }}</span>
                      <span class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">· {{ enc.loja_nome }}</span>
                    </div>
                    <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ formatDate(enc.data_criacao) }}</span>
                      <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(enc.status)]">
                        {{ enc.status }}
                      </span>
                      <EstadoReembolso v-if="enc.reembolso" :estado="enc.reembolso.estado" :valor="enc.reembolso.valor" :metodo="enc.reembolso.metodo" />
                    </div>
                    <p v-if="enc.agendada_texto && !['concluido', 'cancelado'].includes(enc.status)"
                       class="text-[11px] font-semibold mt-1" :class="isDark ? 'text-amber-300' : 'text-amber-700'">
                      {{ enc.agendamento_origem === 'cliente' ? 'Agendada para' : 'Preparada a partir de' }} {{ enc.agendada_texto }}
                    </p>
                  </div>
                  <div class="flex items-center gap-3 flex-shrink-0 ml-2">
                    <span class="text-sm font-bold text-red-500">{{ formatPrice(enc.valor_total) }}</span>
                    <svg :class="['h-4 w-4 transition-transform', expandedEncomenda === enc.id ? 'rotate-180' : '', isDark ? 'text-zinc-500' : 'text-zinc-400']"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                <div v-if="expandedEncomenda === enc.id"
                     class="border-t px-4 pb-4 pt-3 space-y-4"
                     :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
                  <div v-if="loadingDetalhe === enc.id" class="flex justify-center py-4">
                    <svg class="animate-spin h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                  </div>
                  <template v-else-if="detalhesEncomenda[enc.id]">
                    <div>
                      <p class="text-xs font-bold uppercase tracking-wider mb-2"
                         :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Produtos</p>
                      <div class="space-y-2">
                        <div v-for="item in detalhesEncomenda[enc.id].itens" :key="item.id"
                             class="flex items-center gap-3">
                          <img v-if="item.produto?.ficheiro_url" :src="item.produto.ficheiro_url"
                               class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                          <div v-else class="w-10 h-10 rounded-lg flex-shrink-0"
                               :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                          <div class="flex-1 min-w-0">
                            <p class="text-sm truncate" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ item.produto?.nome }}</p>
                            <p v-if="item.componentes?.length" class="text-[11px] leading-snug" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                              Inclui: {{ item.componentes.map(c => (c.grupo ? c.grupo + ': ' : '') + c.quantidade + '× ' + c.nome).join(', ') }}
                            </p>
                            <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">x{{ item.quantidade }} · {{ formatPrice(item.preco) }} un.
                              <span v-if="item.qtd_reembolsada" class="text-sky-500 font-semibold">· {{ item.qtd_reembolsada }} reembolsada{{ item.qtd_reembolsada > 1 ? 's' : '' }}</span>
                            </p>
                            <div v-if="temAtributos(item.atributos)" class="flex flex-wrap gap-1 mt-1">
                              <span v-for="(val, key) in formatarAtributos(item.atributos)" :key="key"
                                    class="px-1.5 py-0.5 text-[10px] rounded capitalize"
                                    :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-gray-200 text-zinc-600'">
                                {{ key }}: <span class="font-medium">{{ val }}</span>
                              </span>
                            </div>
                          </div>
                          <span class="text-sm font-bold flex-shrink-0"
                                :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ formatPrice(item.subtotal) }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="border-t pt-3 space-y-2"
                         :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
                      <div class="flex items-center justify-between text-xs">
                        <span :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Tipo de entrega</span>
                        <span :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
                          <font-awesome-icon :icon="['fas', detalhesEncomenda[enc.id].tipo_entrega === 'entrega' ? 'truck' : 'store']" class="mr-1" />
                          {{ detalhesEncomenda[enc.id].tipo_entrega === 'entrega' ? 'Entrega ao domicílio' : 'Takeaway' }}
                        </span>
                      </div>
                      <div v-if="detalhesEncomenda[enc.id].morada_entrega" class="flex items-start justify-between text-xs gap-2">
                        <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Morada</span>
                        <span class="text-right" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ detalhesEncomenda[enc.id].morada_entrega }}</span>
                      </div>
                      <div v-if="detalhesEncomenda[enc.id].notas" class="flex items-start justify-between text-xs gap-2">
                        <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Notas</span>
                        <span class="text-right italic" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ detalhesEncomenda[enc.id].notas }}</span>
                      </div>
                    </div>
                    <div class="border-t pt-3 flex items-center justify-between"
                         :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
                      <span class="text-sm font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Total</span>
                      <span class="text-base font-bold text-red-500">{{ formatPrice(detalhesEncomenda[enc.id].valor_total) }}</span>
                    </div>
                    <div v-if="detalhesEncomenda[enc.id].valor_a_pagar && Number(detalhesEncomenda[enc.id].valor_a_pagar) !== Number(detalhesEncomenda[enc.id].valor_total)"
                         class="flex items-center justify-between text-xs">
                      <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">A pagar na entrega (sem os artigos esgotados)</span>
                      <span class="font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ formatPrice(detalhesEncomenda[enc.id].valor_a_pagar) }}</span>
                    </div>
                    <!-- fatura que a loja emitiu no e-Fatura e registou (backend utils/fiscal.py) -->
                    <div v-if="['pago', 'preparando', 'enviado', 'concluido'].includes(enc.status)" data-teste="fatura-cliente"
                         class="flex items-center justify-between gap-2 text-xs">
                      <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Fatura</span>
                      <span v-if="detalhesEncomenda[enc.id].fatura" class="flex items-center gap-2">
                        <span class="font-semibold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ detalhesEncomenda[enc.id].fatura.numero }}</span>
                        <a v-if="detalhesEncomenda[enc.id].fatura.pdf_url" :href="detalhesEncomenda[enc.id].fatura.pdf_url"
                           target="_blank" rel="noopener" class="font-semibold text-red-500 hover:text-red-400 underline">
                          <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Descarregar
                        </a>
                      </span>
                      <span v-else :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">A loja ainda não registou a fatura</span>
                    </div>
                    <!-- chat: conversa própria desta encomenda (o condutor da entrega também a vê) -->
                    <button type="button" @click="falarSobreEncomenda(enc)"
                      class="w-full py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-2"
                      :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
                      <font-awesome-icon :icon="['fas', 'comment-dots']" /> Falar com a loja sobre esta encomenda
                    </button>
                    <!-- cancelar / pedir reembolso / acompanhar o pedido -->
                    <AcoesEncomenda :encomenda="detalhesEncomenda[enc.id]" :isDark="isDark"
                      @atualizada="recarregarEncomenda(enc)" @navegar="isOpen = false" />
                  </template>
                </div>
              </div>

              <div class="pt-2 text-center">
                <button v-if="temMais" @click="carregarMais" :disabled="loadingMais"
                  class="px-4 py-2 rounded-xl text-xs transition disabled:opacity-50"
                  :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200' : 'bg-gray-100 hover:bg-gray-200 text-zinc-500 hover:text-zinc-700'">
                  <span v-if="loadingMais">A carregar...</span>
                  <span v-else>Ver mais ({{ encomendaTotal - encomendas.length }} restantes)</span>
                </button>
                <p v-else-if="encomendas.length > 0" class="text-xs"
                   :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
                  Todas as encomendas carregadas
                </p>
              </div>
            </div>
          </div>

          <!-- ═══ TAB: FAVORITOS ═══ -->
          <FavoritosPerfil v-if="activeTab === 'favoritos'" :isDark="isDark" @fechar="isOpen = false" />

          <!-- ═══ TAB: LOJAS ═══ -->
          <div v-if="activeTab === 'lojas'">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold uppercase tracking-wider"
                  :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">As minhas lojas</h3>
              <button @click="goToCreateStore"
                class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold text-white transition">
                + Nova loja
              </button>
            </div>

            <div v-if="loadingLojas" class="flex justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </div>

            <div v-else-if="lojas.length === 0" class="text-center py-8 text-sm"
                 :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Ainda não tens lojas.<br/>
              <button @click="goToCreateStore" class="text-red-500 hover:text-red-400 mt-2 text-sm">
                Criar a primeira loja →
              </button>
            </div>

            <div v-else class="space-y-3">
              <div v-for="loja in lojas" :key="loja.id"
                   class="rounded-xl border overflow-hidden transition cursor-pointer group"
                   :class="isDark
                     ? 'bg-zinc-900 border-zinc-800 hover:border-red-500/30'
                     : 'bg-gray-50 border-gray-200 hover:border-red-400/50'"
                   @click="goToBackoffice(loja.id)">
                <div class="flex items-center gap-3 p-3">
                  <img v-if="loja.logo_url" :src="loja.logo_url" class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                  <div v-else class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                       :class="isDark ? 'bg-zinc-700' : 'bg-gray-200'">
                    <span class="text-sm font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ loja.nome.charAt(0) }}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-semibold text-sm truncate transition"
                       :class="isDark ? 'text-zinc-100 group-hover:text-red-400' : 'text-zinc-900 group-hover:text-red-500'">
                      {{ loja.nome }}
                    </p>
                    <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ loja.categoria }} · {{ loja.minha_role }}</p>
                  </div>
                  <svg class="h-4 w-4 flex-shrink-0 transition"
                       :class="isDark ? 'text-zinc-600 group-hover:text-red-500' : 'text-gray-300 group-hover:text-red-400'"
                       fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Footer — logout -->
        <div class="border-t p-4 flex-shrink-0"
             :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <div class="grid grid-cols-2 gap-2 mb-2">
            <button type="button" @click="isOpen = false; $router.push('/mensagens')"
              class="py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-1.5"
              :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
              <font-awesome-icon :icon="['fas', 'comments']" /> Mensagens
            </button>
            <button type="button" @click="isOpen = false; contactarSuporte()"
              class="py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-1.5"
              :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
              <font-awesome-icon :icon="['fas', 'headset']" /> Suporte
            </button>
          </div>
          <button v-if="data.is_staff" @click="$router.push('/admin'); isOpen = false"
            class="w-full py-2 text-xs text-purple-400 hover:text-purple-300 transition">
            <font-awesome-icon :icon="['fas', 'gear']" class="mr-1" /> Painel de Admin
          </button>
          <button @click="$emit('log_out')"
            class="w-full py-2.5 rounded-xl border text-sm font-semibold transition flex items-center justify-center gap-2"
            :class="isDark
              ? 'border-zinc-700 hover:border-red-500 hover:text-red-500 text-zinc-400'
              : 'border-gray-300 hover:border-red-400 hover:text-red-500 text-zinc-500'">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Terminar sessão
          </button>
        </div>

      </div>
    </transition>
  </div>
</template>

<script setup>
import { formatarDinheiro } from '@/utils/dinheiro'
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import { DEFAULT_UTILIZADOR } from '@/services/media'
import { useAsyncAction } from '@/composables/useAsyncAction'
import { toast } from 'vue3-toastify'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import FavoritosPerfil from '@/components/favoritos/FavoritosPerfil.vue'
import PasswordForca from '@/components/forms/PasswordForca.vue'
import BotaoVerPassword from '@/components/forms/BotaoVerPassword.vue'
import EstadoDisponibilidade from '@/components/forms/EstadoDisponibilidade.vue'
import AcoesEncomenda from '@/components/reembolsos/AcoesEncomenda.vue'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import { criarVerificador } from '@/services/disponibilidade'
import { estaAutenticado, pedirLogin } from '@/services/sessao'
import { contactarLoja, contactarSuporte } from '@/services/chat'
import { passwordValida } from '@/utils/password'
import { formatarAtributos, temAtributos } from '@/utils/atributos'

const props = defineProps({
  data:   { type: Object,  default: () => ({}) },
  isDark: { type: Boolean, default: true },       // ← prop nova, default true = comportamento original
})
defineEmits(['log_out'])

const router     = useRouter()
const route      = useRoute()
const isOpen     = ref(false)
const fileInput  = ref(null)
const previewUrl = ref('')
const activeTab  = ref('dados')

const tabs = [
  { key: 'dados',      label: 'Perfil'     },
  { key: 'password',   label: 'Password'   },
  { key: 'encomendas', label: 'Encomendas' },
  { key: 'favoritos',  label: 'Favoritos'  },
  { key: 'lojas',      label: 'Lojas'      },
]

const profileFields = [
  { key: 'first_name', label: 'Primeiro nome' },
  { key: 'last_name',  label: 'Apelido'       },
  { key: 'username',   label: 'Username'      },
  { key: 'email',      label: 'Email', type: 'email' },
  { key: 'telefone',   label: 'Telefone'      },
  { key: 'morada',     label: 'Morada'        },
]

const form         = ref({ first_name: '', last_name: '', username: '', email: '', telefone: '', morada: '' })
const formPassword = ref({ atual: '', password: '', confirm: '' })
const verPassword  = ref(false)
// contas Google sem password não têm "password actual" — o servidor diz (tem_password)
const temPassword  = ref(props.data?.tem_password !== false)
const passwordError = ref('')

const { loading: loadingProfile,  wrap: wrapProfile  } = useAsyncAction()
const { loading: loadingPassword, wrap: wrapPassword } = useAsyncAction()

const encomendas        = ref([])
const loadingEncomendas = ref(false)
const expandedEncomenda = ref(null)
const detalhesEncomenda = ref({})
const loadingDetalhe    = ref(null)
const encomendaOffset   = ref(0)
const encomendaLimit    = ref(6)
const encomendaTotal    = ref(0)
const loadingMais       = ref(false)
const temMais = computed(() => encomendas.value.length < encomendaTotal.value)
// atalhos da aba Encomendas (Marcações, Reembolsos) com ar de botão
const botaoAtalho = computed(() => props.isDark
  ? 'bg-zinc-800 border-zinc-700 text-zinc-200 hover:bg-zinc-700 hover:border-zinc-600'
  : 'bg-white border-gray-200 text-zinc-700 hover:bg-gray-50 hover:border-gray-300 shadow-sm')

const lojas       = ref([])
const loadingLojas = ref(false)

function formatPrice(val) {
  return formatarDinheiro(val || 0)
}
function formatDate(d) { return new Date(d).toLocaleDateString('pt-PT') }
function statusColor(s) {
  return {
    pendente:   'bg-yellow-500/15 text-yellow-400',
    pago:       'bg-blue-500/15 text-blue-400',
    preparando: 'bg-purple-500/15 text-purple-400',
    enviado:    'bg-indigo-500/15 text-indigo-400',
    concluido:  'bg-green-500/15 text-green-400',
    cancelado:  'bg-red-500/15 text-red-400',
  }[s] || 'bg-zinc-500/15 text-zinc-400'
}

async function toggleEncomenda(id) {
  if (expandedEncomenda.value === id) { expandedEncomenda.value = null; return }
  expandedEncomenda.value = id
  if (detalhesEncomenda.value[id]) return
  loadingDetalhe.value = id
  try {
    const { data } = await api.get(`/app/encomenda/${id}/`)
    detalhesEncomenda.value = { ...detalhesEncomenda.value, [id]: data }
  } catch (e) { console.error(e) }
  finally { loadingDetalhe.value = null }
}

// depois de cancelar: o detalhe e a linha da lista mostram o novo estado
async function recarregarEncomenda(enc) {
  try {
    const { data } = await api.get(`/app/encomenda/${enc.id}/`)
    detalhesEncomenda.value = { ...detalhesEncomenda.value, [enc.id]: data }
    Object.assign(enc, { status: data.status, reembolso: data.reembolso, valor_reembolsado: data.valor_reembolsado })
  } catch (e) { console.error(e) }
}

// visitante sem conta: o botão do perfil convida a entrar (o perfil e as encomendas pedem conta)
const autenticado = ref(estaAutenticado())

function falarSobreEncomenda(enc) {
  isOpen.value = false
  contactarLoja(enc.loja, { encomendaId: enc.id })
}

function toggle() {
  if (!autenticado.value) {
    pedirLogin('Entra ou cria conta para veres o teu perfil e as tuas encomendas.')
    return
  }
  isOpen.value = !isOpen.value
  if (isOpen.value && activeTab.value === 'encomendas') fetchEncomendas()
  if (isOpen.value && activeTab.value === 'lojas') fetchLojas()
}

watch(activeTab, (tab) => {
  if (tab === 'encomendas' && encomendas.value.length === 0) fetchEncomendas()
  if (tab === 'lojas'      && lojas.value.length === 0)      fetchLojas()
  if (tab === 'password') fetchTemPassword()
})

// o user guardado no browser pode ser de antes do tem_password — confirma no servidor
async function fetchTemPassword() {
  try {
    const { data } = await api.get('/app/utilizador/me/')
    temPassword.value = data.tem_password !== false
  } catch { /* fica o valor que já havia */ }
}

function initForm() {
  form.value = {
    first_name: props.data.first_name || '',
    last_name:  props.data.last_name  || '',
    username:   props.data.username   || '',
    email:      props.data.email      || '',
    telefone:   props.data.telefone   || '',
    morada:     props.data.morada     || '',
  }
  valoresAtuais.value = { username: form.value.username, email: form.value.email }
}

// ?perfil=encomendas (links das notificações, /perfil) → abre a gaveta nesse separador
watch(() => route.query.perfil, (tab) => {
  if (!tab || !autenticado.value) return
  if (tabs.some(t => t.key === tab)) activeTab.value = tab
  isOpen.value = true
  if (activeTab.value === 'encomendas') fetchEncomendas()
  const resto = { ...route.query }
  delete resto.perfil
  router.replace({ query: resto })
}, { immediate: true })

onMounted(() => {
  // o carrinho encosta-se ao grupo do perfil: sem sessão não há sino (ver assets/loja-acoes.css)
  document.documentElement.style.setProperty('--acoes-n-perfil', autenticado.value ? '2' : '1')
  previewUrl.value = props.data.foto || DEFAULT_UTILIZADOR
  initForm()
})

watch(() => props.data, () => {
  previewUrl.value = props.data.foto || DEFAULT_UTILIZADOR
  initForm()
}, { deep: true })

function triggerFileSelect() { fileInput.value?.click() }

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  previewUrl.value = URL.createObjectURL(file)
  wrapProfile(async () => {
    const fd = new FormData()
    fd.append('foto', file)
    const res = await api.put('/app/utilizador/me/editar/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (res.data.foto) previewUrl.value = res.data.foto
    toast.success('Foto actualizada!', { autoClose: 1500 })
  })
}

// username e email verificados ao vivo — o valor que a conta já tem não conta como ocupado
const verificadores = { username: criarVerificador('username'), email: criarVerificador('email') }
const valoresAtuais = ref({ username: '', email: '' })
const profileError  = ref('')

function verificarCampo(key) {
  verificadores[key]?.verificar(form.value[key], valoresAtuais.value[key])
}

async function saveProfile() {
  profileError.value = ''
  const ocupado = Object.values(verificadores).find(v => v.bloqueia)
  if (ocupado) { profileError.value = ocupado.motivo; return }

  await wrapProfile(async () => {
    const fd = new FormData()
    Object.entries(form.value).forEach(([k, v]) => { if (v) fd.append(k, v) })
    try {
      await api.put('/app/utilizador/me/editar/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    } catch (e) {
      const d = e.response?.data
      const msg = d && typeof d === 'object' && Object.values(d).flat()[0]
      profileError.value = (typeof msg === 'string' && msg) || 'Não foi possível guardar o perfil.'
      return
    }
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    Object.assign(user, form.value)
    localStorage.setItem('user', JSON.stringify(user))
    valoresAtuais.value = { username: form.value.username, email: form.value.email }
    Object.values(verificadores).forEach(v => v.verificar(''))
    toast.success('Perfil actualizado!', { autoClose: 1500 })
  })
}

async function savePassword() {
  passwordError.value = ''
  if (temPassword.value && !formPassword.value.atual) { passwordError.value = 'Introduz a password actual.'; return }
  if (!formPassword.value.password) { passwordError.value = 'Introduz a nova password.'; return }
  if (!passwordValida(formPassword.value.password)) { passwordError.value = 'A password não cumpre todos os requisitos de segurança.'; return }
  if (formPassword.value.password !== formPassword.value.confirm) { passwordError.value = 'As passwords não coincidem.'; return }
  await wrapPassword(async () => {
    const fd = new FormData()
    fd.append('password', formPassword.value.password)
    if (temPassword.value) fd.append('password_atual', formPassword.value.atual)
    try {
      await api.put('/app/utilizador/me/editar/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    } catch (e) {
      const d = e.response?.data
      passwordError.value = (d && (d.password_atual?.[0] || d.password?.[0] || d.detail)) || 'Não foi possível alterar a password.'
      return
    }
    formPassword.value = { atual: '', password: '', confirm: '' }
    verPassword.value = false
    temPassword.value = true   // a partir de agora já tem password
    toast.success('Password alterada!', { autoClose: 1500 })
  })
}

async function fetchEncomendas() {
  loadingEncomendas.value = true; encomendaOffset.value = 0
  try {
    const { data } = await api.get('/app/encomenda/', { params: { limit: encomendaLimit.value, offset: 0 } })
    encomendas.value     = data.results || data
    encomendaTotal.value = data.count ?? encomendas.value.length
    encomendaOffset.value = encomendas.value.length
  } catch (e) { console.error(e) }
  finally { loadingEncomendas.value = false }
}

async function carregarMais() {
  if (loadingMais.value || !temMais.value) return
  loadingMais.value = true
  try {
    const { data } = await api.get('/app/encomenda/', { params: { limit: encomendaLimit.value, offset: encomendaOffset.value } })
    const novas = data.results || data
    encomendas.value = [...encomendas.value, ...novas]
    encomendaOffset.value += novas.length
    encomendaTotal.value = data.count ?? encomendaTotal.value
  } catch (e) { console.error(e) }
  finally { loadingMais.value = false }
}

async function fetchLojas() {
  loadingLojas.value = true
  try {
    const { data } = await api.get('/app/loja/minhas/')
    lojas.value = data.results || data
  } catch (e) { console.error(e) }
  finally { loadingLojas.value = false }
}

function goToBackoffice(id) { router.push(`/loja/${id}/backoffice`); isOpen.value = false }
function goToCreateStore()  { router.push('/loja/criar');            isOpen.value = false }
</script>
<style scoped>
/* 5 separadores: em ecrãs estreitos deslizam na horizontal, sem barra visível */
.perfil-tabs { scrollbar-width: none; }
.perfil-tabs::-webkit-scrollbar { display: none; }
</style>
