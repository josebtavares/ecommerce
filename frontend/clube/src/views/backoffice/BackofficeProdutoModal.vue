<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('close')">
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 sticky top-0 bg-zinc-900 z-10">
        <h2 class="text-base font-bold text-zinc-100">{{ produto ? 'Editar produto' : 'Novo produto' }}</h2>
        <button @click="$emit('close')" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="guardar" class="p-6 space-y-6">

        <!-- ══ PRODUTO OU CONJUNTO ══ -->
        <div>
          <div class="grid grid-cols-2 gap-1 p-1 rounded-xl bg-zinc-800" role="tablist">
            <button type="button" role="tab" :aria-selected="!conjunto.ativo" @click="conjunto.ativo = false"
              :class="['py-2 rounded-lg text-xs font-semibold transition', !conjunto.ativo ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200']">
              Produto
            </button>
            <button type="button" role="tab" :aria-selected="conjunto.ativo" @click="ligarConjunto"
              :class="['py-2 rounded-lg text-xs font-semibold transition', conjunto.ativo ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200']">
              Conjunto · menu, pack
            </button>
          </div>
          <p v-if="conjunto.ativo" class="text-[11px] text-zinc-500 mt-2 leading-relaxed">
            Um conjunto junta produtos que já vendes (ex.: hambúrguer + batata + bebida). Defines o preço do conjunto;
            ao vender, sai do stock de cada produto — o conjunto não tem stock próprio.
          </p>
        </div>

        <!-- ══ IMAGENS ══ -->
        <div>
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Imagens do produto</p>

          <!-- Grid de imagens existentes + nova imagem principal -->
          <div class="flex flex-wrap gap-3">

            <!-- Imagem principal -->
            <div class="relative group cursor-pointer flex-shrink-0"
                 @click="$refs.fileInput.click()">
              <div class="w-24 h-24 rounded-xl overflow-hidden border-2 border-dashed transition"
                   :class="previewUrl ? 'border-zinc-600' : 'border-zinc-700 hover:border-zinc-500'">
                <img v-if="previewUrl" :src="previewUrl" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-zinc-800 flex flex-col items-center justify-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span class="text-[10px] text-zinc-600">Principal</span>
                </div>
              </div>
              <!-- Overlay editar -->
              <div v-if="previewUrl"
                   class="absolute inset-0 rounded-xl bg-black/50 opacity-0 group-hover:opacity-100
                          flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                </svg>
              </div>
              <span class="absolute -top-1 -left-1 px-1.5 py-0.5 bg-red-600 text-white text-[9px] font-bold rounded">
                Principal
              </span>
            </div>
            <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />

            <!-- Imagens adicionais existentes (a editar) -->
            <div v-for="(img, idx) in imagensExistentes" :key="'ex-' + img.id"
                 class="relative group flex-shrink-0">
              <div class="w-24 h-24 rounded-xl overflow-hidden border-2 border-zinc-700">
                <img :src="img.url" class="w-full h-full object-cover" />
              </div>
              <!-- Botão remover -->
              <button type="button" @click="removerImagemExistente(img.id)"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-600 hover:bg-red-500
                       flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <span class="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[9px] text-zinc-500 whitespace-nowrap">
                #{{ idx + 1 }}
              </span>
            </div>

            <!-- Novas imagens a adicionar (pré-visualização) -->
            <div v-for="(img, idx) in novasImagens" :key="'new-' + idx"
                 class="relative group flex-shrink-0">
              <div class="w-24 h-24 rounded-xl overflow-hidden border-2 border-emerald-700/50">
                <img :src="img.preview" class="w-full h-full object-cover" />
              </div>
              <button type="button" @click="removerNovaImagem(idx)"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-600 hover:bg-red-500
                       flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <!-- Badge novo -->
              <span class="absolute -top-1 -left-1 px-1.5 py-0.5 bg-emerald-600 text-white text-[9px] font-bold rounded">
                Nova
              </span>
            </div>

            <!-- Botão adicionar mais imagens -->
            <div class="cursor-pointer flex-shrink-0" @click="$refs.fileInputAdicional.click()">
              <div class="w-24 h-24 rounded-xl border-2 border-dashed border-zinc-700 hover:border-zinc-500
                          bg-zinc-800/50 flex flex-col items-center justify-center gap-1 transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span class="text-[10px] text-zinc-500">Adicionar</span>
              </div>
            </div>
            <input ref="fileInputAdicional" type="file" accept="image/*" multiple class="hidden"
                   @change="onImagensAdicionaisChange" />
          </div>

          <p class="text-[10px] text-zinc-600 mt-2">
            A primeira imagem é a principal. Clica em × para remover. Podes adicionar várias fotos do mesmo produto.
          </p>
        </div>

        <!-- ══ CAMPOS BASE ══ -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block">Nome *</label>
            <input v-model="form.nome" required type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Preço *</label>
            <input v-model="form.preco" required type="number" step="1" min="0"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">SKU</label>
            <input v-model="form.sku" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Tipo de produto</label>
            <select v-model="form.tipo_id" @change="onTipoChange"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition">
              <option value="">— Sem tipo —</option>
              <optgroup v-if="tiposGlobais.length" label="Globais">
                <option v-for="t in tiposGlobais" :key="t.id" :value="t.id">{{ t.nome }}</option>
              </optgroup>
              <optgroup v-if="tiposLoja.length" label="Da tua loja">
                <option v-for="t in tiposLoja" :key="t.id" :value="t.id">{{ t.nome }}</option>
              </optgroup>
            </select>
          </div>

          <!-- Categorias M2M -->
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-2 block">
              Categorias
              <span class="text-zinc-600 ml-1">· um produto pode pertencer a várias</span>
            </label>
            <div v-if="form.categoria_ids.length > 0" class="flex flex-wrap gap-1.5 mb-2">
              <span v-for="id in form.categoria_ids" :key="id"
                    class="flex items-center gap-1 px-2 py-0.5 bg-red-600/20 text-red-400 text-xs rounded-lg border border-red-500/30">
                <font-awesome-icon :icon="['fas', categoriaIcone(id)]" class="w-3 h-3" /> {{ categoriaLabel(id) }}
                <button type="button" @click="removerCategoria(id)" class="hover:text-white transition">×</button>
              </span>
            </div>
            <div class="flex flex-wrap gap-1.5 mb-2">
              <button v-for="cat in categoriasDaLoja" :key="cat.id" type="button"
                @click="toggleCategoria(cat.id)"
                :class="['px-2.5 py-1 rounded-lg text-xs font-semibold transition border',
                         form.categoria_ids.includes(cat.id)
                           ? 'bg-red-600/20 border-red-500/50 text-red-400'
                           : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200']">
                <font-awesome-icon :icon="['fas', iconeCategoriaProduto(cat.icone, cat.nome)]" class="w-3 h-3 mr-0.5" /> {{ cat.nome }}
              </button>
            </div>
            <div class="flex items-center gap-2 mt-2">
              <input v-model="novaCategoriaNome" type="text" placeholder="Criar nova categoria..."
                @keydown.enter.prevent="criarEAdicionarCategoria"
                class="flex-1 px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100
                       placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
              <button type="button" @click="criarEAdicionarCategoria"
                :disabled="!novaCategoriaNome.trim()"
                class="px-3 py-1.5 rounded-xl bg-zinc-700 hover:bg-zinc-600 text-zinc-300 text-xs font-semibold
                       transition disabled:opacity-40">
                + Criar
              </button>
            </div>
          </div>

          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block">Descrição</label>
            <textarea v-model="form.descricao" rows="3"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition resize-none"></textarea>
          </div>
          <div class="flex items-center gap-3">
            <input v-model="form.destaque" type="checkbox" id="destaque"
              class="w-4 h-4 rounded border-zinc-600 text-red-600 focus:ring-red-500" />
            <label for="destaque" class="text-sm text-zinc-300">Produto em destaque</label>
          </div>
          <div class="flex items-center gap-3">
            <input v-model="form.ativo" type="checkbox" id="ativo"
              class="w-4 h-4 rounded border-zinc-600 text-red-600 focus:ring-red-500" />
            <label for="ativo" class="text-sm text-zinc-300">Produto activo</label>
          </div>
        </div>

        <!-- ══ ATRIBUTOS DINÂMICOS ══ -->
        <div v-if="!conjunto.ativo && tipoSelecionado && schemaNormalizado.length > 0">
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            Atributos
            <span class="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 rounded text-[10px] font-medium capitalize">
              {{ tipoSelecionado.nome }}
            </span>
          </p>
          <div class="space-y-4">
            <div v-for="attr in schemaNormalizado" :key="attr.nome">
              <label class="text-xs text-zinc-500 mb-2 block capitalize flex items-center gap-1">
                {{ attr.nome }}
                <span v-if="attr.obrigatorio" class="text-red-500">*</span>
                <span v-if="attr.tipo === 'choices'" class="text-zinc-600 ml-1">· selecciona um ou mais</span>
              </label>

              <!-- ── CHOICES: checkboxes para múltiplos valores ── -->
              <div v-if="attr.tipo === 'choices'" class="flex flex-wrap gap-2">
                <button v-for="opcao in attr.opcoes" :key="opcao"
                  type="button"
                  @click="toggleAtributoChoice(attr.nome, opcao)"
                  :class="[
                    'px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border',
                    isAtributoSelected(attr.nome, opcao)
                      ? 'bg-red-600 border-red-500 text-white'
                      : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-zinc-100'
                  ]">
                  <font-awesome-icon v-if="isAtributoSelected(attr.nome, opcao)" :icon="['fas', 'check']" class="mr-1" />
                  {{ opcao }}
                </button>

                <!-- Indicador do que está selecionado -->
                <div v-if="Array.isArray(form.atributos[attr.nome]) && form.atributos[attr.nome].length > 0"
                    class="w-full mt-1 text-[10px] text-zinc-500">
                  Seleccionados: <span class="text-zinc-300">{{ form.atributos[attr.nome].join(', ') }}</span>
                </div>
                <div v-else-if="attr.obrigatorio" class="w-full mt-1 text-[10px] text-yellow-600">
                  Selecciona pelo menos uma opção
                </div>
              </div>

              <!-- NÚMERO -->
              <input v-else-if="attr.tipo === 'numero'"
                v-model="form.atributos[attr.nome]"
                type="number" step="any" :required="attr.obrigatorio" :placeholder="attr.nome"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />

              <!-- TEXTO -->
              <input v-else
                v-model="form.atributos[attr.nome]"
                type="text" :required="attr.obrigatorio" :placeholder="attr.nome"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />
            </div>
          </div>
        </div>

        <!-- ══ PRODUTOS DO CONJUNTO ══ -->
        <div v-if="conjunto.ativo" class="space-y-3">
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <font-awesome-icon :icon="['fas', 'layer-group']" /> Produtos do conjunto
          </p>
          <p v-if="aCarregarCatalogo" class="text-xs text-zinc-500">A carregar os produtos da loja…</p>
          <ConjuntoEditor v-else v-model="conjunto.linhas" v-model:grupos="conjunto.grupos"
            :catalogo="catalogoConjunto" :preco-conjunto="form.preco" />
        </div>

        <!-- ══ STOCK POR VARIAÇÃO ══ -->
        <div v-if="!conjunto.ativo && atributosVariante.length" class="space-y-3">
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <font-awesome-icon :icon="['fas', 'boxes-stacked']" /> Stock por variação
            <span class="px-1.5 py-0.5 bg-amber-500/10 text-amber-300 rounded text-[10px] font-medium normal-case">
              {{ atributosVariante.join(' × ') }}
            </span>
          </p>

          <p v-if="!combinacoesForm.length" class="text-xs text-zinc-500 leading-relaxed px-3 py-3 border border-dashed border-zinc-800 rounded-xl">
            Selecciona as opções de {{ atributosVariante.join(' / ') }} acima para definires o stock de cada combinação.
          </p>
          <VariantesGrelhaForm v-else
            v-model:ativo="grelha.ativo" v-model:linhas="grelha.linhas"
            :atributos="atributosVarianteComOpcoes" :preco-produto="form.preco"
            :stock-total-antigo="produto && !produto.stock_por_variante ? (produto.stock?.quantidade ?? 0) : null" />
        </div>

        <!-- só aviso: guarda-se na mesma (utils/prontidao.js) -->
        <p v-if="faltasForm.length" data-teste="produto-faltas"
           class="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-xl px-3 py-2">
          Podes guardar assim, mas falta {{ faltasForm.join(', ') }}<template v-if="faltasForm.includes('descrição')">
          (pelo menos {{ descricaoMin }} caracteres)</template>. Produtos completos vendem melhor e a loja precisa de
          pelo menos um para ser publicada.
        </p>

        <p v-if="erroGuardar" class="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl px-3 py-2">{{ erroGuardar }}</p>

        <!-- ══ ACTIONS ══ -->
        <div class="flex gap-3 pt-2 border-t border-zinc-800">
          <button type="button" @click="$emit('close')"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 hover:text-zinc-200 text-sm font-semibold transition">
            Cancelar
          </button>
          <button type="submit" :disabled="loading"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     loading ? 'bg-red-700 cursor-not-allowed opacity-70' : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ loading ? 'A guardar...' : (produto ? 'Guardar alterações' : 'Criar produto') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'
import { iconeCategoriaProduto, chaveCategoriaProduto } from '@/utils/icones'
import VariantesGrelhaForm from '@/components/inventario/VariantesGrelhaForm.vue'
import { faltas, DESCRICAO_MIN } from '@/utils/prontidao'
import ConjuntoEditor, { erroConjunto, gruposDoProduto } from '@/components/conjuntos/ConjuntoEditor.vue'
import {
  combinacoesDe, mesclarLinhas, linhasDoProduto, linhasParaPayload, grelhaValida,
} from '@/utils/variantes'

export default {
  name: 'BackofficeProdutoModal',
  components: { VariantesGrelhaForm, ConjuntoEditor },
  props: {
    lojaId:  [String, Number],
    produto: { type: Object, default: null },
  },
  emits: ['close', 'saved'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      descricaoMin: DESCRICAO_MIN,
      tipos: [],
      // stock por variação: novo produto → ligado por defeito; existente → como estiver gravado
      grelha: { ativo: !this.produto || !!this.produto.stock_por_variante, linhas: linhasDoProduto(this.produto) },
      erroGuardar: '',
      // conjunto (menu, pack): produtos da loja que o compõem
      conjunto: {
        ativo: !!this.produto?.e_conjunto,
        linhas: (this.produto?.componentes || []).map(c => ({
          origem: 'loja', produto_id: c.produto_id, variante_id: c.variante_id, quantidade: c.quantidade,
          variante_livre: !!c.variante_livre,
        })),
        grupos: gruposDoProduto(this.produto),   // escolhas do cliente (ex.: bebida)
      },
      catalogoConjunto: [],
      aCarregarCatalogo: false,
      categoriasDaLoja: [],
      // Imagem principal
      ficheiro: null,
      previewUrl: '',
      // Imagens adicionais já existentes (ao editar)
      imagensExistentes: [],    // [{ id, url }] — imagens do servidor
      imagensParaEliminar: [],  // IDs a enviar ao backend para remover
      // Novas imagens adicionais (a fazer upload)
      novasImagens: [],         // [{ file, preview }]
      // Formulário
      novaCategoriaNome: '',
      form: {
        nome: '', preco: '', sku: '', descricao: '',
        tipo_id: '', destaque: false, ativo: true,
        atributos: {},
        categoria_ids: [],
      },
    }
  },

  computed: {
    faltasForm () {
      return faltas({
        temFoto: !!(this.previewUrl || this.imagensExistentes.length || this.novasImagens.length),
        descricao: this.form.descricao, preco: this.form.preco,
      })
    },
    tiposGlobais () { return this.tipos.filter(t => t.is_global) },
    tiposLoja    () { return this.tipos.filter(t => !t.is_global) },

    tipoSelecionado () {
      if (!this.form.tipo_id) return null
      return this.tipos.find(t => t.id === parseInt(this.form.tipo_id)) || null
    },

    schemaNormalizado () {
      if (!this.tipoSelecionado?.atributos_schema) return []
      return this.tipoSelecionado.atributos_schema.map(a =>
        typeof a === 'string' ? { nome: a, tipo: 'texto', opcoes: [], obrigatorio: false } : a
      )
    },

    // atributos do tipo com stock próprio por opção (ex.: tamanho, cor)
    atributosVariante () {
      return this.schemaNormalizado.filter(a => a.tipo === 'choices' && a.variante).map(a => a.nome)
    },

    // combinações calculadas a partir das opções seleccionadas — a grelha acompanha em tempo real
    combinacoesForm () {
      return combinacoesDe(this.schemaNormalizado, this.form.atributos)
    },

    atributosVarianteComOpcoes () {
      return this.atributosVariante.filter(n => this.combinacoesForm.some(c => n in c.combinacao))
    },
  },

  watch: {
    // novas combinações entram a 0; removidas saem; as quantidades já escritas mantêm-se
    combinacoesForm (combos) {
      this.grelha.linhas = mesclarLinhas(combos, this.grelha.linhas)
    },
  },

  async created () {
    await Promise.all([this.fetchTipos(), this.fetchCategorias(), this.conjunto.ativo ? this.fetchCatalogoConjunto() : null])
    if (this.produto) {
      const schemaDoProduto = this.produto?.tipo?.atributos_schema || []

      this.form = {
        nome:          this.produto.nome      || '',
        preco:         this.produto.preco     || '',
        sku:           this.produto.sku       || '',
        descricao:     this.produto.descricao || '',
        tipo_id:       this.produto.tipo?.id  || '',
        destaque:      this.produto.destaque  || false,
        ativo:         this.produto.ativo     !== false,
        atributos:     this._normalizarAtributosParaForm(this.produto.atributos || {}, schemaDoProduto),
        categoria_ids: (this.produto.categorias || []).map(c => c.id),
      }

      this.previewUrl = this.produto.ficheiro_url || ''
      this.imagensExistentes = (this.produto.imagens || []).map(img => ({
        id: img.id,
        url: img.ficheiro_url,
      }))
    }
  },

  methods: {

    // ── Normaliza atributos do servidor para o form ────────────────
    // Garante que choices ficam como array, texto/numero como string
    _normalizarAtributosParaForm (atributos, schemaInput = null) {
      const result = {}
      const schema = schemaInput || this.tipoSelecionado?.atributos_schema || []

      for (const [key, val] of Object.entries(atributos)) {
        const def = schema.find(a => (typeof a === 'string' ? a : a.nome) === key)
        const tipo = def?.tipo || 'texto'
        if (tipo === 'choices') {
          result[key] = Array.isArray(val) ? val : (val ? [String(val)] : [])
        } else {
          result[key] = Array.isArray(val) ? (val[0] || '') : (val || '')
        }
      }
      return result
    },

    // ── Gestão de choices: toggle individual ──────────────────────
    toggleAtributoChoice (nome, opcao) {
      const lista = this.form.atributos[nome]
      if (!Array.isArray(lista)) {
        this.form.atributos = { ...this.form.atributos, [nome]: [opcao] }
        return
      }
      const idx = lista.indexOf(opcao)
      const novaLista = idx >= 0
        ? lista.filter(v => v !== opcao)
        : [...lista, opcao]
      this.form.atributos = { ...this.form.atributos, [nome]: novaLista }
    },

    isAtributoSelected (nome, opcao) {
      const lista = this.form.atributos[nome]
      return Array.isArray(lista) && lista.includes(opcao)
    },

    // ── Imagem principal ──────────────────────────────────────────
    onFileChange (e) {
      const file = e.target.files[0]
      if (!file) return
      this.ficheiro   = file
      this.previewUrl = URL.createObjectURL(file)
    },

    // ── Imagens adicionais ─────────────────────────────────────────
    onImagensAdicionaisChange (e) {
      const files = Array.from(e.target.files)
      files.forEach(file => {
        this.novasImagens.push({ file, preview: URL.createObjectURL(file) })
      })
      // reset input para permitir escolher os mesmos ficheiros outra vez
      e.target.value = ''
    },

    removerImagemExistente (id) {
      this.imagensParaEliminar.push(id)
      this.imagensExistentes = this.imagensExistentes.filter(img => img.id !== id)
    },

    removerNovaImagem (idx) {
      URL.revokeObjectURL(this.novasImagens[idx].preview)
      this.novasImagens.splice(idx, 1)
    },

    // ── Tipo change ────────────────────────────────────────────────
    onTipoChange () {
      const novosAtributos = {}
      this.schemaNormalizado.forEach(attr => {
        // preservar valor anterior se existir
        const anterior = this.form.atributos[attr.nome]
        if (attr.tipo === 'choices') {
          novosAtributos[attr.nome] = Array.isArray(anterior) ? anterior : []
        } else {
          novosAtributos[attr.nome] = typeof anterior === 'string' ? anterior : ''
        }
      })
      this.form.atributos = novosAtributos
    },

    // ── Categorias ────────────────────────────────────────────────
    categoriaLabel (id) {
      const cat = this.categoriasDaLoja.find(c => c.id === id)
      return cat ? cat.nome : `#${id}`
    },
    categoriaIcone (id) {
      const cat = this.categoriasDaLoja.find(c => c.id === id)
      return iconeCategoriaProduto(cat?.icone, cat?.nome)
    },
    iconeCategoriaProduto,
    toggleCategoria (id) {
      const idx = this.form.categoria_ids.indexOf(id)
      idx >= 0 ? this.form.categoria_ids.splice(idx, 1) : this.form.categoria_ids.push(id)
    },
    removerCategoria (id) {
      this.form.categoria_ids = this.form.categoria_ids.filter(x => x !== id)
    },

    ligarConjunto () {
      this.conjunto.ativo = true
      if (!this.catalogoConjunto.length) this.fetchCatalogoConjunto()
    },

    // produtos da loja que podem entrar num conjunto (todos, página a página; sem conjuntos nem ele próprio)
    async fetchCatalogoConjunto () {
      this.aCarregarCatalogo = true
      const todos = []
      try {
        for (let offset = 0; offset < 1000; offset += 100) {
          const { data } = await api.get(`/app/loja/${this.lojaId}/produtos/`, { params: { limit: 100, offset } })
          const pagina = data.results || data
          todos.push(...pagina)
          if (!data.next_offset && data.next_offset !== 0) break
          if (pagina.length < 100) break
        }
      } catch (e) { console.error(e) }
      const video = u => /\.(mp4|webm|mov|mkv|m4v)(\?|$)/i.test(u || '')
      this.catalogoConjunto = todos
        .filter(p => !p.e_conjunto && p.id !== this.produto?.id)
        .map(p => ({
          origem: 'loja', id: p.id, nome: p.nome, preco: p.preco, ativo: p.ativo,
          imagem: p.ficheiro_poster_url || (video(p.ficheiro_url) ? null : p.ficheiro_url),
          variantes: p.stock_por_variante
            ? (p.variantes || []).map(v => ({ id: v.id, nome: Object.values(v.combinacao || {}).join(' · '), preco: v.preco_efetivo }))
            : [],
        }))
      this.aCarregarCatalogo = false
    },

    async fetchTipos () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/tipos/`)
        this.tipos = data
      } catch (e) { console.error(e) }
    },

    async fetchCategorias () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/categorias/gerir/`)
        this.categoriasDaLoja = data
      } catch (e) { console.error(e) }
    },

    async criarEAdicionarCategoria () {
      const nome = this.novaCategoriaNome.trim()
      if (!nome) return
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/categorias/criar/`, { nome, icone: chaveCategoriaProduto('', nome) })
        if (!this.categoriasDaLoja.find(c => c.id === data.id)) this.categoriasDaLoja.push(data)
        if (!this.form.categoria_ids.includes(data.id)) this.form.categoria_ids.push(data.id)
        this.novaCategoriaNome = ''
      } catch (e) { console.error(e) }
    },

    // ── GUARDAR ──────────────────────────────────────────────────
    async guardar () {
      await this.wrap(async () => {
        const fd = new FormData()

        // Campos base
        Object.entries(this.form).forEach(([k, v]) => {
          if (k === 'atributos') {
            // Normalizar: choices ficam como array, resto como valor simples
            fd.append('atributos', JSON.stringify(v))
          } else if (k === 'categoria_ids') {
            v.forEach(id => fd.append('categoria_ids', id))
          } else if (k === 'tipo_id') {
            if (v) fd.append('tipo_id', v)
          } else if (typeof v === 'boolean') {
            fd.append(k, v ? 'true' : 'false')
          } else if (v !== '' && v !== null && v !== undefined) {
            fd.append(k, v)
          }
        })

        // Imagem principal
        if (this.ficheiro) fd.append('ficheiro', this.ficheiro)

        // Imagens adicionais novas
        this.novasImagens.forEach((img, idx) => {
          fd.append(`imagens_novas[${idx}]`, img.file)
          fd.append(`imagens_ordem_nova[${idx}]`, idx)
        })

        // Imagens a eliminar
        if (this.imagensParaEliminar.length > 0) {
          fd.append('imagens_eliminar', JSON.stringify(this.imagensParaEliminar))
        }

        // Conjunto — produtos e variações escolhidas (o backend valida e grava tudo-ou-nada)
        this.erroGuardar = ''
        if (this.conjunto.ativo) {
          const erro = erroConjunto(this.conjunto.linhas, this.conjunto.grupos, this.catalogoConjunto)
          if (erro) {
            this.erroGuardar = erro
            return
          }
          fd.append('e_conjunto', 'true')
          fd.append('componentes', JSON.stringify(this.conjunto.linhas))
          fd.append('grupos', JSON.stringify(this.conjunto.grupos))
        } else if (this.produto?.e_conjunto) {
          fd.append('e_conjunto', 'false')
        }

        // Stock por variação — vai no mesmo pedido (o backend grava tudo-ou-nada)
        if (!this.conjunto.ativo && this.combinacoesForm.length) {
          if (this.grelha.ativo && !grelhaValida(this.grelha.linhas)) {
            this.erroGuardar = 'Há quantidades inválidas na grelha de stock por variação.'
            return
          }
          fd.append('stock_por_variante', this.grelha.ativo ? 'true' : 'false')
          if (this.grelha.ativo) fd.append('variantes', JSON.stringify(linhasParaPayload(this.grelha.linhas)))
        }

        try {
          if (this.produto) {
            const url = `/app/loja/${this.lojaId}/produtos/${this.produto.id}/editar/`
            const cfg = { headers: { 'Content-Type': 'multipart/form-data' } }
            try {
              await api.patch(url, fd, cfg)
            } catch (e) {
              // desactivar um produto que está dentro de conjuntos → confirmar primeiro
              if (e.response?.status !== 409 || !e.response.data?.precisa_confirmar) throw e
              if (!confirm(e.response.data.detail + '\n\nDesactivar mesmo assim?')) return
              await api.patch(url, fd, { ...cfg, params: { confirmar: 1 } })
            }
          } else {
            await api.post(`/app/loja/${this.lojaId}/produtos/criar/`, fd,
              { headers: { 'Content-Type': 'multipart/form-data' } })
          }
        } catch (e) {
          const d = e.response?.data
          this.erroGuardar = d?.detail || (d && typeof d === 'object' && Object.values(d).flat()[0]) || 'Erro ao guardar o produto.'
          return
        }
        this.$emit('saved')
      })
    },
  }
}
</script>