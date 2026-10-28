<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100">

    <!-- Header -->
    <div class="sticky top-0 z-20 bg-zinc-950/90 backdrop-blur border-b border-zinc-800 px-6 py-4 flex items-center gap-4">
      <button @click="$router.back()"
        class="w-9 h-9 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-lg font-bold text-zinc-100">Checkout</h1>
      <span v-if="loja" class="text-sm text-zinc-500">· {{ loja.nome }}</span>
      <BotaoTema class="ml-auto" :isDark="isDark" @alternar="alternarTema" />
    </div>

    <!-- Loading inicial -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <svg class="animate-spin h-8 w-8 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </div>

    <!-- Carrinho vazio -->
    <div v-else-if="itens.length === 0" class="flex flex-col items-center justify-center h-64 text-center">
      <p class="text-zinc-400 text-lg font-semibold mb-2">O carrinho está vazio</p>
      <button @click="$router.back()" class="text-red-400 hover:text-red-300 text-sm">← Voltar</button>
    </div>

    <div v-else class="max-w-4xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">

      <!-- ═══ COLUNA ESQUERDA ═══ -->
      <div class="lg:col-span-2 space-y-6">

        <!-- TIPO DE ENTREGA -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Como queres receber?</h2>
          <div class="grid grid-cols-2 gap-3">
            <button @click="tipoEntrega = 'entrega'" :disabled="!loja?.entrega_ativa"
              :class="['p-4 rounded-xl border-2 transition-all text-left',
                       tipoEntrega === 'entrega' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600',
                       !loja?.entrega_ativa ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer']">
              <div class="flex items-center gap-3 mb-2">
                <div :class="['w-4 h-4 rounded-full border-2 flex items-center justify-center',
                              tipoEntrega === 'entrega' ? 'border-red-500' : 'border-zinc-600']">
                  <div v-if="tipoEntrega === 'entrega'" class="w-2 h-2 rounded-full bg-red-500"></div>
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </div>
              <p class="text-sm font-semibold text-zinc-200">Entrega ao domicílio</p>
              <p class="text-xs text-zinc-500 mt-0.5">Recebe em casa</p>
              <p v-if="!loja?.entrega_ativa" class="text-xs text-red-500 mt-1">Indisponível</p>
            </button>

            <button @click="tipoEntrega = 'levantamento'" :disabled="!loja?.levantamento_ativo"
              :class="['p-4 rounded-xl border-2 transition-all text-left',
                       tipoEntrega === 'levantamento' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600',
                       !loja?.levantamento_ativo ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer']">
              <div class="flex items-center gap-3 mb-2">
                <div :class="['w-4 h-4 rounded-full border-2 flex items-center justify-center',
                              tipoEntrega === 'levantamento' ? 'border-red-500' : 'border-zinc-600']">
                  <div v-if="tipoEntrega === 'levantamento'" class="w-2 h-2 rounded-full bg-red-500"></div>
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <p class="text-sm font-semibold text-zinc-200">Takeaway</p>
              <p class="text-xs text-zinc-500 mt-0.5">Levanta na loja</p>
              <p v-if="!loja?.levantamento_ativo" class="text-xs text-red-500 mt-1">Indisponível</p>
            </button>
          </div>
        </div>

        <!-- OPÇÕES DE ENTREGA -->
        <div v-if="tipoEntrega === 'entrega'" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Opção de entrega</h2>
          <div v-if="opcoesEntrega.length === 0" class="text-zinc-500 text-sm">Sem opções disponíveis.</div>
          <div v-else class="space-y-3">
            <button v-for="opcao in opcoesEntrega" :key="opcao.id"
              @click="opcaoEntregaId = opcao.id"
              :class="['w-full p-4 rounded-xl border-2 transition-all flex items-center justify-between text-left',
                       opcaoEntregaId === opcao.id ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
              <div class="flex items-center gap-3">
                <div :class="['w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                              opcaoEntregaId === opcao.id ? 'border-red-500' : 'border-zinc-600']">
                  <div v-if="opcaoEntregaId === opcao.id" class="w-2 h-2 rounded-full bg-red-500"></div>
                </div>
                <div>
                  <p class="text-sm font-semibold text-zinc-200">{{ opcao.nome }}</p>
                  <p v-if="opcao.tempo_estimado" class="text-xs text-zinc-500">{{ opcao.tempo_estimado }}</p>
                </div>
              </div>
              <span class="text-sm font-bold flex-shrink-0" :class="opcao.preco == 0 ? 'text-green-400' : 'text-red-400'">
                {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
              </span>
            </button>
          </div>
        </div>

        <!-- MORADA -->
        <div v-if="tipoEntrega === 'entrega'" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Morada de entrega</h2>
          <textarea v-model="moradaEntrega" rows="3"
            placeholder="Rua, número, andar, código postal, cidade..."
            class="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition resize-none"></textarea>
          <p v-if="moradaPerfil && moradaEntrega !== moradaPerfil" class="text-xs text-zinc-500 mt-2 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            </svg>
            Perfil: {{ moradaPerfil }}
            <button @click="moradaEntrega = moradaPerfil" class="text-red-400 hover:text-red-300 underline">usar</button>
          </p>
        </div>

        <!-- QUANDO (o cliente escolhe dia e hora, se a loja deixar) -->
        <EscolherHora v-if="loja?.agendamento?.ativo && tipoEntrega && !(lojaFechada && !aceitaAgendar)"
          ref="escolherHora" v-model="agendarPara" :loja-id="lojaId" :tipo-entrega="tipoEntrega"
          :texto-asap="lojaFechada ? `Quando a loja abrir — ${quandoAbre(loja.horario)}` : 'Assim que a loja preparar'" />

        <!-- NOTAS -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Notas <span class="text-zinc-600 font-normal normal-case">(opcional)</span>
          </h2>
          <textarea v-model="notas" rows="2"
            placeholder="Instruções especiais, alergias, preferências..."
            class="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition resize-none"></textarea>
        </div>

        <!-- MÉTODO DE PAGAMENTO -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Método de pagamento</h2>

          <!-- Loading métodos -->
          <div v-if="loadingMetodos" class="space-y-3">
            <div v-for="n in 3" :key="n" class="h-16 bg-zinc-800 rounded-xl animate-pulse"></div>
          </div>

          <!-- Sem métodos -->
          <div v-else-if="metodosPagamento.length === 0"
               class="text-center py-6 text-zinc-500 text-sm border border-dashed border-zinc-700 rounded-xl">
            Esta loja não tem métodos de pagamento configurados.
          </div>

          <!-- Lista de métodos -->
          <div v-else class="space-y-3">
            <button v-for="metodo in metodosPagamento" :key="metodo.tipo"
              @click="metodoPagamento = metodo.tipo"
              :class="['w-full p-4 rounded-xl border-2 transition-all flex items-center gap-3 text-left',
                       metodoPagamento === metodo.tipo ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
              <div :class="['w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                            metodoPagamento === metodo.tipo ? 'border-red-500' : 'border-zinc-600']">
                <div v-if="metodoPagamento === metodo.tipo" class="w-2 h-2 rounded-full bg-red-500"></div>
              </div>
              <span :class="['w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                             metodoPagamento === metodo.tipo ? 'bg-red-500/15 text-red-400' : 'bg-zinc-800 text-zinc-400']">
                <font-awesome-icon :icon="['fas', metodo.icon]" class="w-4 h-4" />
              </span>
              <div class="flex-1">
                <p class="text-sm font-semibold text-zinc-200">{{ metodo.label }}</p>
                <p class="text-xs text-zinc-500">{{ metodo.descricao }}</p>
              </div>
              <!-- pago online pelo fornecedor da plataforma (backend app/pagamentos) -->
              <span v-if="metodosOnline.includes(metodo.tipo)"
                    class="text-[10px] text-green-400 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded font-semibold">
                Online
              </span>
            </button>
          </div>
        </div>

      </div>

      <!-- ═══ COLUNA DIREITA — Resumo ═══ -->
      <div class="lg:col-span-1">
        <div class="sticky top-24 bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Resumo do pedido</h2>

          <!-- Loja -->
          <div v-if="loja" class="flex items-center gap-3 mb-4 pb-4 border-b border-zinc-800">
            <img v-img v-if="loja.logo_url" :src="$miniatura(loja.logo_url)" :alt="loja.nome"
                 class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
            <div v-else class="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-zinc-400">{{ loja.nome.charAt(0) }}</span>
            </div>
            <div>
              <p class="text-sm font-semibold text-zinc-200">{{ loja.nome }}</p>
              <p class="text-xs text-zinc-500">{{ loja.categoria }}</p>
            </div>
          </div>

          <!-- Itens -->
          <div class="space-y-3 mb-4">
            <div v-for="item in itens" :key="item.id" class="flex items-center gap-3">
              <img v-img v-if="item.produto?.ficheiro_url" :src="$miniatura(item.produto.ficheiro_url)"
                   class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
              <div v-else class="w-10 h-10 rounded-lg bg-zinc-800 flex-shrink-0"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-zinc-200 truncate">{{ item.produto?.nome }}</p>
                <p v-if="item.produto?.inclui" class="text-[11px] text-zinc-500 leading-snug line-clamp-2">{{ item.produto.inclui }}</p>
                <p v-if="item.escolhas_texto" class="text-[11px] text-red-400 leading-snug">{{ item.escolhas_texto }}</p>
                <p class="text-xs text-zinc-500">x{{ item.quantidade }}</p>
                <p v-if="item.variante && item.quantidade > (item.variante.ativo ? item.variante.quantidade_disponivel : 0)"
                   class="text-[11px] text-amber-500 mt-0.5">
                  <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mr-0.5" /> {{ (item.variante.ativo ? item.variante.quantidade_disponivel : 0) > 0
                        ? `Só restam ${item.variante.quantidade_disponivel} desta combinação — ajusta no carrinho.`
                        : 'Esta combinação esgotou — remove-a do carrinho.' }}
                </p>
                <div v-if="temAtributos(item.atributos)" class="flex flex-wrap gap-1 mt-1">
                  <span v-for="(val, key) in formatarAtributos(item.atributos)" :key="key"
                        class="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-[10px] rounded capitalize">
                    {{ key }}: <span class="text-zinc-300 font-medium">{{ val }}</span>
                  </span>
                </div>
              </div>
              <span class="text-xs font-bold text-zinc-300 flex-shrink-0">
                {{ formatPrice(parseFloat(item.preco_unitario ?? item.produto?.preco ?? 0) * item.quantidade) }}
              </span>
            </div>
          </div>

          <!-- Totais -->
          <div class="border-t border-zinc-800 pt-4 space-y-2">
            <div class="flex justify-between text-sm text-zinc-400">
              <span>Subtotal</span>
              <span>{{ formatPrice(subtotal) }}</span>
            </div>
            <div v-if="tipoEntrega === 'entrega' && opcaoSelecionada" class="flex justify-between text-sm text-zinc-400">
              <span>Entrega · {{ opcaoSelecionada.nome }}</span>
              <span :class="opcaoSelecionada.preco == 0 ? 'text-green-400' : ''">
                {{ opcaoSelecionada.preco == 0 ? 'Grátis' : formatPrice(opcaoSelecionada.preco) }}
              </span>
            </div>
            <div v-if="tipoEntrega === 'levantamento'" class="flex justify-between text-sm text-zinc-400">
              <span>Takeaway</span>
              <span class="text-green-400">Grátis</span>
            </div>
            <div class="flex justify-between text-base font-bold text-zinc-100 pt-2 border-t border-zinc-800">
              <span>Total</span>
              <span class="text-red-400">{{ formatPrice(total) }}</span>
            </div>
          </div>

          <!-- Validações -->
          <div v-if="!podeConfirmar && tipoEntrega" class="mt-3 space-y-1">
            <p v-if="tipoEntrega === 'entrega' && !opcaoEntregaId" class="text-xs text-yellow-500 flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Selecciona uma opção de entrega
            </p>
            <p v-if="tipoEntrega === 'entrega' && !moradaEntrega.trim()" class="text-xs text-yellow-500 flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Introduz a morada de entrega
            </p>
          </div>

          <!-- Loja fechada (horário) -->
          <div v-if="lojaFechada" role="status"
            :class="['mt-4 rounded-xl px-3 py-2.5 text-xs leading-relaxed border',
                     aceitaAgendar ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-red-500/10 border-red-500/30 text-red-300']">
            <p class="font-bold mb-0.5">A loja está fechada</p>
            <p v-if="aceitaAgendar && agendarPara">
              Não faz mal: a tua encomenda fica agendada para <b>{{ textoAgendada }}</b>.
            </p>
            <p v-else-if="aceitaAgendar">
              Podes encomendar já: a loja prepara a tua encomenda a partir de <b>{{ quandoAbre(loja.horario) }}</b>.
            </p>
            <p v-else>
              Só aceita encomendas dentro do horário<template v-if="quandoAbre(loja.horario)"> — abre {{ quandoAbre(loja.horario) }}</template>.
              O carrinho fica guardado.
            </p>
          </div>

          <!-- Quem vende (contactos e políticas da loja) -->
          <div v-if="loja" class="mt-4 rounded-xl border border-zinc-800 bg-zinc-950/40 px-4 py-3">
            <LojaVendedor :loja="loja" :isDark="true" compacto />
          </div>

          <!-- Aceitar os termos (fica registado na encomenda: termos_aceites_em) -->
          <label class="mt-4 flex items-start gap-2.5 text-xs text-zinc-400 leading-relaxed cursor-pointer" data-teste="aceitar-termos">
            <input v-model="aceitaTermos" type="checkbox" class="mt-0.5 w-4 h-4 flex-shrink-0 accent-red-600" />
            <span>
              Li e aceito os <router-link to="/termos" target="_blank" class="font-semibold text-red-400 hover:underline">Termos de Serviço</router-link>
              e a <router-link to="/devolucoes" target="_blank" class="font-semibold text-red-400 hover:underline">Política de devoluções</router-link>.
            </span>
          </label>

          <!-- Erro -->
          <p v-if="erro" class="text-xs text-red-400 mt-3 bg-red-500/10 rounded-lg px-3 py-2">{{ erro }}</p>

          <!-- Botão confirmar -->
          <button @click="confirmarEncomenda"
            :disabled="loadingConfirmar || !podeConfirmar"
            :class="['w-full mt-5 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2',
                     !podeConfirmar ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' :
                     loadingConfirmar ? 'bg-red-700 cursor-not-allowed opacity-70 text-white' :
                     'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5 shadow-lg shadow-red-600/20 text-white']">
            <svg v-if="loadingConfirmar" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            <span v-if="loadingConfirmar && redirecionando">A redirecionar…</span>
            <span v-else-if="loadingConfirmar">A processar…</span>
            <span v-else-if="agendarPara">Encomendar para {{ textoAgendada }} · {{ formatPrice(total) }}</span>
            <span v-else-if="lojaFechada && aceitaAgendar">Encomendar para {{ quandoAbre(loja.horario) }} · {{ formatPrice(total) }}</span>
            <span v-else>Confirmar Encomenda · {{ formatPrice(total) }}</span>
          </button>

          <p class="text-xs text-zinc-600 text-center mt-3">
            Pagamento simulado para testes
          </p>
        </div>
      </div>
    </div>

    <!-- página escrita em escuro: no tema claro o tema-claro.css troca as cores (utils/tema.js) -->
    <SiteRodape :isDark="true" :temaEscuro="isDark" />
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'
import { formatarAtributos, temAtributos } from '@/utils/atributos'
import { iconePagamento } from '@/utils/icones'
import { quandoAbre } from '@/components/horario/horario'
import EscolherHora from '@/components/horario/EscolherHora.vue'
import { temaPainel } from '@/utils/tema'
import BotaoTema from '@/components/BotaoTema.vue'
import LojaVendedor from '@/components/loja/LojaVendedor.vue'
import SiteRodape from '@/components/paginas/SiteRodape.vue'
import { seguirPagamento } from '@/utils/pagamentoOnline'

// mapa de rótulos e descrições para cada tipo de método (o ícone vem de utils/icones.js)
const METODO_INFO = {
  dinheiro:      { label: 'Dinheiro',           descricao: 'Paga ao receber / na loja' },
  mbway:         { label: 'MBWay',              descricao: 'Pagamento via MBWay' },
  cartao:        { label: 'Cartão',             descricao: 'Cartão de débito/crédito — pago online' },
  flutterwave:   { label: 'Cartão',             descricao: 'Visa, Mastercard — pago online' },
  transferencia: { label: 'Transferência',      descricao: 'Transferência bancária' },
  mobile_money:  { label: 'Mobile Money',       descricao: 'Pagamento via telemóvel' },
  paypal:        { label: 'PayPal',             descricao: 'Pagamento via PayPal' },
  stripe:        { label: 'Cartão',             descricao: 'Visa, Mastercard — pago online' },
}

// pagos online pelo fornecedor da plataforma (os outros pagam-se à loja)
const METODOS_ONLINE = ['cartao', 'mobile_money', 'mbway', 'flutterwave', 'stripe', 'paypal']

export default {
  name: 'CheckoutPage',
  mixins: [temaPainel],
  components: { BotaoTema, EscolherHora, LojaVendedor, SiteRodape },

  setup () {
    const { loading: loadingConfirmar, wrap } = useAsyncAction()
    return { loadingConfirmar, wrap }
  },

  data () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      loading:        true,
      loadingMetodos: false,
      loja:           null,
      aceitaTermos:   false,
      itens:          [],
      opcoesEntrega:  [],
      metodosPagamento: [],   // carregados da API
      tipoEntrega:    null,
      opcaoEntregaId: null,
      moradaEntrega:  user.morada || '',
      moradaPerfil:   user.morada || '',
      notas:          '',
      metodoPagamento: '',
      erro: '',
      agendarPara: null,   // null = o mais cedo possível · '' = a escolher · 'AAAA-MM-DDTHH:MM'
      redirecionando: false,
      metodosOnline: METODOS_ONLINE,
    }
  },

  computed: {
    lojaId ()           { return this.$route.params.lojaId },
    opcaoSelecionada () { return this.opcoesEntrega.find(o => o.id === this.opcaoEntregaId) || null },
    subtotal () {
      return this.itens.reduce((s, i) => s + parseFloat(i.preco_unitario ?? i.produto?.preco ?? 0) * i.quantidade, 0)
    },
    custoEntrega () {
      if (this.tipoEntrega !== 'entrega' || !this.opcaoSelecionada) return 0
      return parseFloat(this.opcaoSelecionada.preco || 0)
    },
    total () { return this.subtotal + this.custoEntrega },
    // horário da loja (utils/horarios.py no servidor) — fechada: agendar para a abertura ou não aceitar
    lojaFechada ()   { return !!(this.loja?.horario?.ativo && !this.loja.horario.aberta) },
    aceitaAgendar () { return this.loja?.horario?.fora_horario === 'agendar' && !!this.loja.horario.abre_em },
    // "14/10 às 13:30" a partir de '2026-10-14T13:30'
    textoAgendada () {
      if (!this.agendarPara) return ''
      const [d, h] = this.agendarPara.split('T')
      const [, m, dia] = d.split('-')
      return `${dia}/${m} às ${h}`
    },
    podeConfirmar () {
      if (this.lojaFechada && !this.aceitaAgendar) return false
      if (this.agendarPara === '') return false            // escolheu "dia e hora" mas ainda não a hora
      if (!this.tipoEntrega || this.itens.length === 0 || !this.metodoPagamento) return false
      if (!this.aceitaTermos) return false
      if (this.tipoEntrega === 'entrega') {
        if (!this.opcaoEntregaId) return false
        if (!this.moradaEntrega.trim()) return false
      }
      return true
    },
  },

  async created () {
    await Promise.all([
      this.fetchLoja(),
      this.fetchCarrinho(),
      this.fetchOpcoesEntrega(),
      this.fetchMetodosPagamento(),
    ])
    if (this.loja?.entrega_ativa)          this.tipoEntrega = 'entrega'
    else if (this.loja?.levantamento_ativo) this.tipoEntrega = 'levantamento'
    this.loading = false
  },

  methods: {
    formatarAtributos, temAtributos, quandoAbre,
    formatPrice (val) {
      return formatarDinheiro(val || 0)
    },

    async fetchLoja () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/`)
        this.loja = data
      } catch (e) { console.error(e) }
    },

    async fetchCarrinho () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/carrinho/`)
        this.itens = data.itens || []
      } catch (e) { console.error(e) }
    },

    async fetchOpcoesEntrega () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/opcoes/`)
        this.opcoesEntrega = data.results || data
        if (this.opcoesEntrega.length > 0) {
          const maisBara = this.opcoesEntrega.reduce((a, b) =>
            parseFloat(a.preco) <= parseFloat(b.preco) ? a : b
          )
          this.opcaoEntregaId = maisBara.id
        }
      } catch (e) { console.error(e) }
    },

    async fetchMetodosPagamento () {
      this.loadingMetodos = true
      try {
        // carrega os métodos reais da loja da API
        const { data } = await api.get(`/app/loja/${this.lojaId}/pagamento/metodos/`)
        const lista = Array.isArray(data) ? data : data.results || []
        // enriquece com ícone e descrição
        this.metodosPagamento = lista
          .filter(m => m.ativo)
          .map(m => ({
            ...m,
            ...(METODO_INFO[m.tipo] || { label: m.tipo, descricao: '' }),
            icon: iconePagamento(m.tipo),
          }))
        // pré-selecciona o primeiro método disponível
        if (this.metodosPagamento.length > 0) {
          this.metodoPagamento = this.metodosPagamento[0].tipo
        }
      } catch (e) {
        console.error(e)
        // fallback para dinheiro se a API falhar
        this.metodosPagamento = [
          { tipo: 'dinheiro', icon: iconePagamento('dinheiro'), label: 'Dinheiro', descricao: 'Paga ao receber', ativo: true },
        ]
        this.metodoPagamento = 'dinheiro'
      } finally {
        this.loadingMetodos = false
      }
    },

    async confirmarEncomenda () {
      this.erro = ''
      await this.wrap(async () => {
        // 1 — criar encomenda
        const payload = {
          tipo_entrega:   this.tipoEntrega,
          morada_entrega: this.tipoEntrega === 'entrega' ? this.moradaEntrega : '',
          notas:          this.notas,
          aceita_termos:  this.aceitaTermos,
        }
        if (this.tipoEntrega === 'entrega' && this.opcaoEntregaId) {
          payload.opcao_entrega_id = this.opcaoEntregaId
        }
        if (this.agendarPara) payload.agendar_para = this.agendarPara
        // o cliente viu o aviso "a loja está fechada — fica para a abertura"
        else if (this.lojaFechada && this.aceitaAgendar) payload.aceita_agendamento = true
        let encomenda
        try {
          ({ data: encomenda } = await api.post(`/app/loja/${this.lojaId}/encomenda/criar/`, payload))
        } catch (e) {
          // a loja fechou enquanto o cliente estava no checkout → mostra o aviso e pede para confirmar
          const d = e.response?.data
          if (d?.codigo === 'vaga_invalida') {          // a hora escolhida deixou de estar livre
            this.erro = d.detail
            this.$refs.escolherHora?.carregar()
            return
          }
          if (d?.horario && ['loja_fechada', 'confirmar_agendamento'].includes(d.codigo)) {
            this.loja = { ...this.loja, horario: d.horario }
            this.erro = d.detail
            return
          }
          // ex.: "Stock insuficiente de 'Camisola (preto · S)'. Disponível: 1."
          this.erro = e.response?.data?.detail || 'Erro ao criar a encomenda. Tenta novamente.'
          await this.fetchCarrinho()   // mostra o stock actualizado em cada item
          return
        }

        // 2 — pagar: dinheiro/transferência ficam por receber; online vai pelo fornecedor da plataforma
        // (aprovado já, ou o cliente vai à página dele e volta a /pagamento/callback)
        const { data: pag } = await api.post('/app/pagamento/iniciar/', {
          encomenda_id: encomenda.id, metodo: this.metodoPagamento,
        })
        if (seguirPagamento(pag)) {
          this.redirecionando = true
          return
        }

        // 3 — limpar carrinho e redirecionar
        window.dispatchEvent(new CustomEvent('carrinho-limpo', { detail: { lojaId: this.lojaId } }))
        this.$router.push({ name: 'EncomendaSucesso', params: { id: encomenda.id } })
      })

      if (!this.erro && !this.loadingConfirmar && !this.redirecionando && this.$route.name !== 'EncomendaSucesso') {
        this.erro = 'Erro ao processar a encomenda. Verifica os dados e tenta novamente.'
      }
    },
  }
}
</script>