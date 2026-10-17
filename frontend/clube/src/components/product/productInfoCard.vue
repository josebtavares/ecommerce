<template>
  <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
              leave-active-class="transition duration-150" leave-to-class="opacity-0">
    <div v-if="produto"
         class="fixed inset-0 z-50 flex items-center justify-center p-4"
         :class="isDark ? 'bg-black/80' : 'bg-black/50'"
         style="backdrop-filter: blur(4px)"
         @click.self="$emit('close')">

      <div class="relative w-full max-w-2xl md:max-w-4xl max-h-[90vh] rounded-2xl overflow-hidden shadow-2xl border flex flex-col md:flex-row"
           :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">

        <!-- ══ PAINEL ESQUERDO — slider de imagens ══ -->
        <div class="relative md:w-1/2 md:flex-shrink-0 h-64 md:h-auto overflow-hidden">

          <!-- Imagem actual -->
          <div class="relative w-full h-full cursor-pointer group"
               @click="todasImagens[imagemActiva]?.url && !todasImagens[imagemActiva]?.video && (imagemFullscreen = true)">
            <!-- vídeo do produto: toca com controlos (é o único vídeo no ecrã) -->
            <video v-if="todasImagens[imagemActiva]?.video" :key="todasImagens[imagemActiva].url"
                   :src="todasImagens[imagemActiva].url" :poster="todasImagens[imagemActiva].poster"
                   class="w-full h-full object-cover" autoplay muted loop playsinline controls></video>
            <img v-else :src="todasImagens[imagemActiva]?.url || defaultImg" :alt="produto.nome"
                 class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />

            <!-- Overlay hover -->
            <div v-if="todasImagens[imagemActiva]?.url && !todasImagens[imagemActiva]?.video"
                 class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity
                        flex flex-col items-center justify-center gap-2">
              <div class="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <span class="text-white text-xs font-medium opacity-80">Ver imagem completa</span>
            </div>

            <!-- Sem imagem -->
            <div v-if="!todasImagens[imagemActiva]?.url"
                 class="w-full h-full flex items-center justify-center"
                 :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16" :class="isDark ? 'text-zinc-600' : 'text-gray-300'"
                   fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>

            <!-- Badge destaque -->
            <span v-if="produto.destaque"
                  class="absolute top-3 left-3 px-2 py-1 bg-red-600 text-white text-xs font-bold rounded">
              <font-awesome-icon :icon="['fas', 'star']" class="mr-1" />Destaque
            </span>

            <!-- Botão fechar (mobile) -->
            <button @click.stop="$emit('close')"
              class="absolute top-3 right-3 md:hidden w-8 h-8 rounded-full bg-black/50 hover:bg-black/70
                     flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <!-- Setas de navegação (só se houver >1 imagem) -->
            <button v-if="todasImagens.length > 1"
              @click.stop="prevImagem"
              class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70
                     flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button v-if="todasImagens.length > 1"
              @click.stop="nextImagem"
              class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70
                     flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <!-- Thumbnails das imagens (só desktop, na base) -->
          <div v-if="todasImagens.length > 1"
               class="hidden md:flex absolute bottom-0 left-0 right-0 gap-1.5 p-2 bg-black/40 backdrop-blur-sm overflow-x-auto">
            <button v-for="(img, idx) in todasImagens" :key="idx"
              @click.stop="imagemActiva = idx"
              class="w-10 h-10 flex-shrink-0 rounded-lg overflow-hidden border-2 transition"
              :class="imagemActiva === idx ? 'border-white' : 'border-transparent opacity-60 hover:opacity-100'">
              <img :src="img.poster || (img.video ? defaultImg : img.url) || defaultImg" :alt="'Imagem ' + (idx+1)" class="w-full h-full object-cover" />
            </button>
          </div>

          <!-- Dots de paginação (mobile) -->
          <div v-if="todasImagens.length > 1"
               class="md:hidden absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
            <button v-for="(img, idx) in todasImagens" :key="idx"
              @click.stop="imagemActiva = idx"
              class="w-2 h-2 rounded-full transition"
              :class="imagemActiva === idx ? 'bg-white' : 'bg-white/40'"></button>
          </div>
        </div>

        <!-- ══ PAINEL DIREITO — informações ══ -->
        <div class="md:w-1/2 flex flex-col overflow-y-auto max-h-[calc(90vh-256px)] md:max-h-[90vh]">

          <!-- Header com botão fechar (desktop) -->
          <div class="flex items-center justify-between px-6 pt-5 pb-2 flex-shrink-0">
            <div class="flex items-center gap-2">
              <img v-if="loja?.logo_url" :src="loja.logo_url" :alt="loja.nome"
                   class="w-5 h-5 rounded object-cover" />
              <button v-if="mostrarBotaoLoja" @click="visitarLoja"
                class="text-xs font-medium transition hover:underline underline-offset-2"
                :class="isDark ? 'text-zinc-400 hover:text-red-400' : 'text-zinc-500 hover:text-red-500'">
                {{ loja?.nome }}
              </button>
              <span v-else class="text-xs font-medium" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ loja?.nome }}</span>
              <span :class="isDark ? 'text-zinc-700' : 'text-gray-300'">·</span>
              <span class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ produto.categoria }}</span>
            </div>
            <button @click="$emit('close')"
              class="hidden md:flex w-8 h-8 rounded-full items-center justify-center transition flex-shrink-0"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                   fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Conteúdo scrollável -->
          <div class="px-6 pb-6 flex-1 overflow-y-auto">

            <!-- Nome e preço -->
            <div class="flex items-start gap-3 mb-1">
              <h2 class="flex-1 text-2xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ produto.nome }}</h2>
              <BotaoFavorito tipo="produto" :id="produto.id" variante="simples" :tamanho="38" :isDark="isDark"
                             :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'" />
            </div>
            <p class="text-2xl font-bold text-red-500 mb-4">
              <span v-if="precoDesde" class="text-sm font-semibold opacity-70 mr-1">desde</span>{{ formatPrice(precoUnitario) }}
            </p>

            <!-- Descrição -->
            <p class="text-sm leading-relaxed mb-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
              {{ produto.descricao || 'Sem descrição.' }}
            </p>

            <!-- ══ CONJUNTO: o que inclui (menu, pack) ══ -->
            <div v-if="eConjunto" class="mb-4 rounded-xl border p-3" :class="isDark ? 'border-zinc-800 bg-zinc-900/60' : 'border-gray-200 bg-gray-50'">
              <template v-if="produto.componentes?.length">
              <p class="text-xs font-semibold uppercase tracking-wider mb-2" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Inclui</p>
              <ul class="space-y-2">
                <li v-for="c in produto.componentes" :key="c.id" class="flex items-center gap-3">
                  <img v-if="c.imagem" :src="c.imagem" :alt="c.nome" class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                  <span v-else class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold"
                        :class="isDark ? 'bg-zinc-800 text-zinc-500' : 'bg-gray-200 text-zinc-400'">{{ c.nome.charAt(0) }}</span>
                  <span class="flex-1 min-w-0 text-sm" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">
                    <b>{{ c.quantidade }}×</b> {{ c.nome }}
                    <span v-if="c.variante" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'"> · {{ c.variante }}</span>
                  </span>
                </li>
              </ul>
              </template>
              <p v-if="poupanca > 0" class="mt-3 text-xs font-semibold text-green-500">
                Em separado custaria {{ formatPrice(produto.conjunto.preco_componentes) }} — poupas {{ formatPrice(poupanca) }}
              </p>
            </div>

            <!-- ══ CONJUNTO: escolhas do cliente (ex.: bebida) ══ -->
            <EscolhasConjunto v-if="eConjunto && temEscolhas(produto)" v-model="escolhas"
                              :grupos="produto.grupos" :componentes="produto.componentes" :isDark="isDark" class="mb-4" />

            <!-- ══ CHOICES: só as opções disponíveis no produto ══ -->
            <div v-if="!eConjunto && atributosChoices.length > 0" class="space-y-4 mb-4">
              <div v-for="attr in atributosChoices" :key="attr.nome">
                <p class="text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1"
                   :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                  <span class="capitalize">{{ attr.nome }}</span>
                  <span v-if="attr.obrigatorio" class="text-red-500">*</span>
                </p>
                <div class="flex flex-wrap gap-2">
                  <button v-for="opcao in attr.opcoesDisponiveis" :key="opcao"
                    @click="toggleSeleccao(attr.nome, opcao)"
                    :disabled="estado(attr.nome, opcao) === 'esgotada'"
                    :title="tituloOpcao(attr.nome, opcao)"
                    :class="[
                      'px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border relative overflow-hidden',
                      seleccoes[attr.nome] === opcao
                        ? 'bg-red-600 border-red-500 text-white'
                        : estado(attr.nome, opcao) === 'esgotada'
                          ? (isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-600 cursor-not-allowed' : 'bg-gray-50 border-gray-200 text-zinc-300 cursor-not-allowed')
                          : estado(attr.nome, opcao) === 'esgotada_combo'
                            ? (isDark ? 'bg-zinc-900 border-dashed border-zinc-700 text-zinc-500 hover:text-zinc-300' : 'bg-gray-50 border-dashed border-gray-300 text-zinc-400 hover:text-zinc-600')
                            : isDark
                              ? 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-zinc-100'
                              : 'bg-gray-100 border-gray-300 text-zinc-600 hover:border-gray-400 hover:text-zinc-900'
                    ]">
                    {{ opcao }}
                    <!-- risco diagonal: esgotado (total ou com as escolhas actuais) -->
                    <span v-if="seleccoes[attr.nome] !== opcao && ['esgotada', 'esgotada_combo'].includes(estado(attr.nome, opcao))"
                          class="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <span class="absolute w-full h-px rotate-[25deg] opacity-50"
                            :class="isDark ? 'bg-zinc-500' : 'bg-gray-400'"></span>
                    </span>
                  </button>

                  <!-- Opções do schema global mas não disponíveis no produto (desativadas) -->
                  <button v-for="opcao in attr.opcoesIndisponiveis" :key="'dis-' + opcao"
                    disabled
                    class="px-3 py-1.5 rounded-xl text-xs font-semibold border cursor-not-allowed relative overflow-hidden"
                    :class="isDark
                      ? 'bg-zinc-900 border-zinc-800 text-zinc-600'
                      : 'bg-gray-50 border-gray-200 text-zinc-300'">
                    <span>{{ opcao }}</span>
                    <!-- Linha diagonal a indicar indisponível -->
                    <span class="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <span class="absolute w-full h-px rotate-[25deg] opacity-40"
                            :class="isDark ? 'bg-zinc-600' : 'bg-gray-300'"></span>
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Atributos texto/número (informativos, não seleccionáveis) -->
            <div v-if="atributosVisiveis.length > 0" class="grid grid-cols-2 gap-2 mb-4">
              <div v-for="(item, idx) in atributosVisiveis" :key="idx"
                   class="rounded-lg px-3 py-2"
                   :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
                <p class="text-xs capitalize" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ item.key }}</p>
                <p class="text-sm font-medium" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ item.val }}</p>
              </div>
            </div>

            <!-- Stock -->
            <div class="flex items-center gap-2 mb-4">
              <div :class="['w-2 h-2 rounded-full', corStock]"></div>
              <span class="text-sm" :class="[isDark ? 'text-zinc-400' : 'text-zinc-500', poucasUnidades && 'text-amber-500 font-semibold']">
                {{ textoStock }}
              </span>
            </div>

            <!-- Aviso obrigatórios -->
            <p v-if="obrigatoriosPorPreencher.length > 0 && stock > 0"
               class="text-xs text-yellow-500 mb-4 flex items-center gap-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Selecciona: {{ obrigatoriosPorPreencher.join(', ') }}
            </p>

            <!-- Quantidade -->
            <div class="flex items-center gap-4 mb-5">
              <span class="text-sm font-medium" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Quantidade:</span>
              <div class="flex items-center gap-3">
                <button @click="qty > 1 && qty--" :disabled="qty <= 1 || loading"
                  class="w-8 h-8 rounded-lg flex items-center justify-center transition disabled:opacity-40"
                  :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                       fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M20 12H4" />
                  </svg>
                </button>
                <span class="text-lg font-bold w-8 text-center" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ qty }}</span>
                <button @click="qty < maxQty && qty++" :disabled="qty >= maxQty || loading"
                  class="w-8 h-8 rounded-lg flex items-center justify-center transition disabled:opacity-40"
                  :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                       fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>
              <span class="text-sm font-bold ml-auto" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
                Total: {{ formatPrice(precoUnitario * qty) }}
              </span>
            </div>

            <!-- Botão adicionar -->
            <button @click="addToCart"
              :disabled="stock === 0 || loading || !podeAdicionar"
              :class="[
                'w-full py-3 rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2',
                stock === 0 || !podeAdicionar
                  ? 'bg-zinc-700 cursor-not-allowed opacity-60'
                  : loading
                    ? 'bg-red-700 cursor-not-allowed opacity-80'
                    : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5 shadow-lg shadow-red-600/20'
              ]">
              <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              <span v-if="loading">A adicionar…</span>
              <span v-else-if="stock === 0">Sem stock</span>
              <span v-else-if="varianteSelecionadaEsgotada">Combinação esgotada</span>
              <span v-else class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Adicionar ao carrinho
              </span>
            </button>

            <!-- chat: abre a conversa com a loja já com este produto (visitante → convite a entrar) -->
            <button type="button" @click="perguntarLoja"
              class="mt-2 w-full py-2.5 rounded-xl text-sm font-semibold border transition-colors flex items-center justify-center gap-2"
              :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400'">
              <font-awesome-icon :icon="['fas', 'comment-dots']" /> Perguntar à loja
            </button>
          </div>
        </div>

        <!-- ══ FULLSCREEN IMAGEM ══ -->
        <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 scale-95"
                    leave-active-class="transition duration-150" leave-to-class="opacity-0 scale-95">
          <div v-if="imagemFullscreen"
               class="absolute inset-0 z-10 flex flex-col rounded-2xl overflow-hidden"
               :class="isDark ? 'bg-zinc-950/98' : 'bg-white/98'">
            <div class="flex items-center gap-3 px-4 py-3 border-b flex-shrink-0"
                 :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <button @click="imagemFullscreen = false"
                class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-gray-100 hover:bg-gray-200 text-zinc-700'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                Voltar
              </button>
              <span class="text-sm truncate" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ produto.nome }}</span>
              <span class="ml-auto text-xs" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
                {{ imagemActiva + 1 }} / {{ todasImagens.length }}
              </span>
            </div>
            <div class="flex-1 flex items-center justify-center p-4 overflow-hidden relative">
              <img :src="todasImagens[imagemActiva]?.url || defaultImg" :alt="produto.nome"
                   class="max-w-full max-h-full object-contain rounded-xl" />
              <button v-if="todasImagens.length > 1" @click.stop="prevImagem"
                class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/70
                       flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button v-if="todasImagens.length > 1" @click.stop="nextImagem"
                class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/70
                       flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </transition>

      </div>
    </div>
  </transition>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api'
import { DEFAULT_PRODUTO } from '@/services/media'
import { toast } from 'vue3-toastify'
import { estaAutenticado, pedirLogin } from '@/services/sessao'
import { contactarLoja } from '@/services/chat'
import BotaoFavorito from '@/components/favoritos/BotaoFavorito.vue'
import EscolhasConjunto, { extrasDe, faltaEscolher, temEscolhas } from '@/components/conjuntos/EscolhasConjunto.vue'
import {
  usaVariantes, atributosVariante, estadoOpcao, escolherOpcao, varianteEscolhida,
  variantesPorEscolher, stockCompativel, intervaloPreco,
} from '@/utils/variantes'

export default {
  name: 'ProductInfoCard',
  components: { BotaoFavorito, EscolhasConjunto },

  props: {
    produto: { type: Object,  default: null },
    loja:    { type: Object,  default: null },
    isDark:  { type: Boolean, default: true },
  },

  emits: ['close', 'added-to-cart'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      qty: 1,
      seleccoes: {},
      escolhas: {},      // conjunto: { grupo_id: [opcao_id] }
      imagemFullscreen: false,
      imagemActiva: 0,
      defaultImg: DEFAULT_PRODUTO,
    }
  },

  computed: {
    stock () {
      // conjunto: sem stock próprio — o servidor calcula pelos componentes (null = sem limite)
      if (this.eConjunto) {
        if (this.produto.conjunto && !this.produto.conjunto.disponivel) return 0
        return this.produto.stock?.quantidade ?? 99
      }
      return this.produto?.inventario?.quantidade ?? this.produto?.stock?.quantidade ?? 0
    },

    eConjunto () { return !!this.produto?.e_conjunto },

    // conjunto mais barato do que os produtos em separado
    poupanca () {
      if (!this.eConjunto || !this.produto.conjunto) return 0
      const d = Number(this.produto.conjunto.preco_componentes) - Number(this.produto.preco)
      return d >= 0.01 ? d : 0
    },

    // ── Imagens: principal + adicionais (ordenadas) ──────────────
    todasImagens () {
      const imgs = []
      // 1. imagem principal
      if (this.produto?.ficheiro_url) {
        imgs.push({
          url: this.produto.ficheiro_url, legenda: '',
          video: /\.(mp4|webm|mov|mkv|m4v)$/i.test(this.produto.ficheiro_url),
          poster: this.produto.ficheiro_poster_url || null,
        })
      }
      // 2. imagens adicionais (do novo endpoint)
      const adicionais = this.produto?.imagens || []
      adicionais.forEach(img => {
        if (img.ficheiro_url && img.ficheiro_url !== this.produto?.ficheiro_url) {
          imgs.push({ url: img.ficheiro_url, legenda: img.legenda || '' })
        }
      })
      // fallback: sem imagens
      if (imgs.length === 0) imgs.push({ url: null, legenda: '' })
      return imgs
    },

    // ── Schema do tipo de produto (todas as opcoes globais) ────────
    schema () {
      if (!this.produto?.tipo?.atributos_schema) return []
      return this.produto.tipo.atributos_schema.map(a =>
        typeof a === 'string'
          ? { nome: a, tipo: 'texto', opcoes: [], obrigatorio: false }
          : a
      )
    },

    // ── Atributos do produto (normalizados: sempre lista) ──────────
    atributosNormalizados () {
      // Preferir campo pré-normalizado se disponível
      const norm = this.produto?.atributos_normalizados
      if (norm && typeof norm === 'object') return norm

      // Fallback: normalizar manualmente
      const raw = this.produto?.atributos || {}
      const out = {}
      for (const [k, v] of Object.entries(raw)) {
        out[k] = Array.isArray(v) ? v : (v ? [String(v)] : [])
      }
      return out
    },

    // ── Choices: para cada atributo choices do schema,
    //    separar em disponíveis (no produto) e indisponíveis ────────
    atributosChoices () {
      const disponivel = this.atributosNormalizados
      return this.schema
        .filter(a => a.tipo === 'choices' && a.opcoes?.length > 0)
        .map(a => {
          const prodValores = disponivel[a.nome] || []
          return {
            nome: a.nome,
            obrigatorio: a.obrigatorio || false,
            opcoesDisponiveis:    a.opcoes.filter(op => prodValores.includes(op)),
            opcoesIndisponiveis:  a.opcoes.filter(op => !prodValores.includes(op)),
          }
        })
        // Só mostrar se houver pelo menos alguma opção disponível
        .filter(a => a.opcoesDisponiveis.length > 0 || a.opcoesIndisponiveis.length > 0)
    },

    // ── Atributos texto/número (informativos) ─────────────────────
    atributosVisiveis () {
      const atributos = this.produto?.atributos || {}
      if (this.schema.length > 0) {
        return this.schema
          .filter(a => a.tipo !== 'choices' && atributos[a.nome])
          .map(a => ({
            key: a.nome,
            val: Array.isArray(atributos[a.nome])
              ? atributos[a.nome].join(', ')
              : atributos[a.nome]
          }))
      }
      return Object.entries(atributos)
        .filter(([, v]) => v)
        .map(([key, val]) => ({
          key,
          val: Array.isArray(val) ? val.join(', ') : val
        }))
    },

    // ── Stock por variação ────────────────────────────────────────
    comVariantes () { return usaVariantes(this.produto) },

    variante () {
      return this.comVariantes ? varianteEscolhida(this.produto, this.seleccoes) : null
    },

    varianteSelecionadaEsgotada () {
      return !!this.variante && this.variante.quantidade <= 0
    },

    // stock relevante: da combinação escolhida, ou das compatíveis com o que já está escolhido
    stockVisivel () {
      if (!this.comVariantes) return this.stock
      if (this.variante) return this.variante.quantidade
      return stockCompativel(this.produto, this.seleccoes)
    },

    // quantidade máxima no selector: só com a combinação completa escolhida
    maxQty () {
      if (!this.comVariantes) return this.stock
      return this.variante ? this.variante.quantidade : 1
    },

    poucasUnidades () {
      const s = this.comVariantes ? (this.variante?.quantidade ?? 0) : this.stock
      return s > 0 && s <= 5
    },

    textoStock () {
      if (this.eConjunto && this.produto.conjunto && !this.produto.conjunto.disponivel) return 'Indisponível de momento'
      if (this.eConjunto && this.produto.stock == null) return 'Disponível'
      if (this.stock <= 0) return 'Sem stock'
      if (!this.comVariantes) return this.poucasUnidades ? `Só restam ${this.stock}` : `${this.stock} em stock`
      if (this.variante) {
        const q = this.variante.quantidade
        if (q <= 0) return 'Esta combinação está esgotada — escolhe outra'
        return q <= 5 ? `Só restam ${q} nesta combinação` : `${q} em stock`
      }
      const falta = variantesPorEscolher(this.produto, this.seleccoes)
      return `Disponível · escolhe ${falta.join(' e ')} para ver o stock`
    },

    corStock () {
      if (this.stock <= 0 || this.varianteSelecionadaEsgotada) return 'bg-red-500'
      return this.poucasUnidades ? 'bg-amber-500' : 'bg-green-500'
    },

    precoUnitario () {
      // conjunto: preço base + extras das opções escolhidas
      if (this.eConjunto) return Number(this.produto.preco) + extrasDe(this.produto.grupos, this.escolhas)
      if (!this.comVariantes) return this.produto?.preco
      if (this.variante) return this.variante.preco_efetivo
      return this.intervalo ? this.intervalo.min : this.produto?.preco
    },

    intervalo () {
      return this.comVariantes ? intervaloPreco(this.produto, this.seleccoes) : null
    },

    // preços diferentes entre combinações ainda possíveis → "desde X"
    precoDesde () {
      return !this.variante && !!this.intervalo && this.intervalo.min !== this.intervalo.max
    },

    obrigatoriosPorPreencher () {
      if (this.eConjunto) return faltaEscolher(this.produto.grupos, this.escolhas, this.produto.componentes)
      const obrig = this.atributosChoices
        .filter(a => a.obrigatorio && !this.seleccoes[a.nome])
        .map(a => a.nome)
      // atributos-variante são sempre necessários (definem o stock)
      const variantes = this.comVariantes ? variantesPorEscolher(this.produto, this.seleccoes) : []
      return [...new Set([...obrig, ...variantes])]
    },

    podeAdicionar () {
      if (this.obrigatoriosPorPreencher.length > 0) return false
      if (this.comVariantes) return !!this.variante && this.variante.quantidade >= this.qty
      return true
    },

    mostrarBotaoLoja () {
      const rotaActual   = this.$route?.name
      const lojaIdActual = this.$route?.params?.id
      if (rotaActual === 'LojaPublica' && String(lojaIdActual) === String(this.loja?.id)) return false
      return !!this.loja?.id
    },
  },

  watch: {
    produto () {
      this.qty = 1
      this.seleccoes = {}
      this.escolhas = {}
      this.imagemFullscreen = false
      this.imagemActiva = 0
    },
    // ao trocar de combinação, a quantidade não pode passar o stock dela
    maxQty (max) {
      if (this.qty > max) this.qty = Math.max(1, max)
    },
  },

  methods: {
    temEscolhas,
    formatPrice (val) {
      return formatarDinheiro(val || 0)
    },

    toggleSeleccao (nome, opcao) {
      if (this.seleccoes[nome] === opcao) {
        const novas = { ...this.seleccoes }
        delete novas[nome]
        this.seleccoes = novas
      } else if (this.comVariantes) {
        if (this.estado(nome, opcao) === 'esgotada') return
        // larga escolhas que ficariam sem stock com esta opção
        this.seleccoes = escolherOpcao(this.produto, this.seleccoes, nome, opcao)
      } else {
        this.seleccoes = { ...this.seleccoes, [nome]: opcao }
      }
    },

    // estado de uma opção (só atributos-variante; os outros estão sempre disponíveis)
    estado (nome, opcao) {
      if (!this.comVariantes || !atributosVariante(this.produto).includes(nome)) return 'disponivel'
      return estadoOpcao(this.produto, this.seleccoes, nome, opcao)
    },

    tituloOpcao (nome, opcao) {
      const e = this.estado(nome, opcao)
      if (e === 'esgotada') return 'Esgotado'
      if (e === 'esgotada_combo') return 'Esgotado com as opções escolhidas — clica para ver outras combinações'
      return ''
    },

    prevImagem () {
      this.imagemActiva = (this.imagemActiva - 1 + this.todasImagens.length) % this.todasImagens.length
    },
    nextImagem () {
      this.imagemActiva = (this.imagemActiva + 1) % this.todasImagens.length
    },

    async addToCart () {
      if (!this.loja || !this.produto || this.stock === 0 || !this.podeAdicionar) return
      // visitante: encomendar pede conta — convida a entrar e volta depois à loja do produto
      if (!estaAutenticado()) {
        pedirLogin('Entra ou cria conta para adicionares produtos ao carrinho e encomendares.', `/loja/${this.loja.id}`)
        return
      }
      await this.wrap(async () => {
        try {
          await api.post(`/app/loja/${this.loja.id}/carrinho/adicionar/`, {
            produto_id: this.produto.id,
            quantidade: this.qty,
            atributos:  this.seleccoes,
            ...(this.eConjunto ? { escolhas: this.escolhas } : {}),
          })
        } catch (e) {
          // ex.: stock mudou entretanto ("Stock insuficiente… Disponível: 1")
          toast.error(e.response?.data?.detail || 'Não foi possível adicionar ao carrinho.')
          return
        }
        this.$emit('added-to-cart', { loja: this.loja })
        this.$emit('close')
      })
    },

    async perguntarLoja () {
      if (!this.loja || !this.produto) return
      const produto = {
        id: this.produto.id,
        nome: this.produto.nome,
        preco: this.produto.preco,
        imagem: this.todasImagens?.[0]?.url || null,
      }
      // a pré-visualização de templates não tem loja real — não abre conversa
      if (!/^\d+$/.test(String(this.loja.id))) return
      const ok = await contactarLoja(this.loja.id, { produto })
      if (ok) this.$emit('close')
    },

    visitarLoja () {
      this.$emit('close')
      this.$router.push(`/loja/${this.loja.id}`)
    },
  }
}
</script>