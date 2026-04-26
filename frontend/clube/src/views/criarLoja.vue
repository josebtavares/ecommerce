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
      <div>
        <h1 class="text-base font-bold text-zinc-100">Criar loja</h1>
        <p class="text-xs text-zinc-500">Passo {{ step }} de 3</p>
      </div>
    </div>

    <!-- Utilizador nao verificado -->
    <div v-if="!user.verificado" class="max-w-lg mx-auto px-6 py-16 text-center">
      <div class="w-16 h-16 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-zinc-100 mb-2">Conta não verificada</h2>
      <p class="text-zinc-400 text-sm">A tua conta precisa de ser verificada pelo administrador antes de poderes criar uma loja.</p>
      <button @click="$router.back()" class="mt-6 px-6 py-2.5 rounded-xl bg-zinc-800 text-zinc-300 text-sm font-semibold hover:bg-zinc-700 transition">
        Voltar
      </button>
    </div>

    <div v-else class="max-w-2xl mx-auto px-6 py-8">

      <!-- Progress bar -->
      <div class="flex items-center gap-2 mb-8">
        <div v-for="s in 3" :key="s" class="flex items-center gap-2 flex-1">
          <div :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all flex-shrink-0',
            step > s ? 'bg-green-500 text-white' :
            step === s ? 'bg-red-600 text-white' :
            'bg-zinc-800 text-zinc-500'
          ]">
            <svg v-if="step > s" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else>{{ s }}</span>
          </div>
          <div class="flex-1 text-xs" :class="step >= s ? 'text-zinc-300' : 'text-zinc-600'">
            {{ ['Informação básica', 'Visual', 'Configurações'][s-1] }}
          </div>
          <div v-if="s < 3" :class="['h-px flex-1 max-w-8', step > s ? 'bg-green-500' : 'bg-zinc-700']"></div>
        </div>
      </div>

      <!-- ═══ PASSO 1 — INFO BÁSICA ═══ -->
      <div v-if="step === 1" class="space-y-5">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Informação básica</h2>

          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Nome da loja *</label>
            <input v-model="form.nome" type="text" placeholder="ex: Restaurante do João"
              class="w-full px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
          </div>

          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Descrição</label>
            <textarea v-model="form.descricao" rows="3" placeholder="Descreve a tua loja..."
              class="w-full px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     placeholder-zinc-500 focus:outline-none focus:border-red-500 transition resize-none"></textarea>
          </div>

          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Categoria *</label>
            <div v-if="loadingCats" class="flex gap-2">
              <div v-for="n in 5" :key="n" class="h-8 w-24 bg-zinc-800 rounded-xl animate-pulse"></div>
            </div>
            <div v-else class="flex flex-wrap gap-2">
              <button v-for="cat in categorias" :key="cat.id"
                @click="form.categoria = cat.nome; autoSelecionarTemplate(cat.nome)"
                :class="[
                  'px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5',
                  form.categoria === cat.nome
                    ? 'bg-red-600 text-white'
                    : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                ]">
                {{ cat.icon }} {{ cat.nome }}
              </button>
            </div>
          </div>

          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Localização</label>
            <input v-model="form.localizacao" type="text" placeholder="ex: Lisboa, Portugal"
              class="w-full px-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>
      </div>

      <!-- ═══ PASSO 2 — VISUAL ═══ -->
      <div v-if="step === 2" class="space-y-5">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-5">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Visual da loja</h2>

          <!-- Preview -->
          <div class="relative rounded-xl overflow-hidden bg-zinc-800 h-32">
            <img v-if="bannerPreview" :src="bannerPreview" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-zinc-600 text-sm">Banner</div>
            <div class="absolute bottom-3 left-3 flex items-center gap-3">
              <div class="w-14 h-14 rounded-xl bg-zinc-900 border-2 border-zinc-700 overflow-hidden flex items-center justify-center">
                <img v-if="logoPreview" :src="logoPreview" class="w-full h-full object-cover" />
                <span v-else class="text-zinc-500 text-xs">Logo</span>
              </div>
              <div>
                <p class="text-sm font-bold text-white drop-shadow">{{ form.nome || 'Nome da loja' }}</p>
                <p class="text-xs text-zinc-300 capitalize">{{ categoriaLabel }}</p>
              </div>
            </div>
          </div>

          <!-- Logo -->
          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Logo</label>
            <div class="flex items-center gap-3">
              <div class="w-16 h-16 rounded-xl bg-zinc-800 border border-zinc-700 overflow-hidden flex items-center justify-center flex-shrink-0">
                <img v-if="logoPreview" :src="logoPreview" class="w-full h-full object-cover" />
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <label class="flex-1 px-4 py-2.5 bg-zinc-800 border border-dashed border-zinc-600 rounded-xl text-sm text-zinc-400 cursor-pointer hover:border-zinc-500 transition text-center">
                {{ form.logo ? form.logo.name : 'Clica para fazer upload' }}
                <input type="file" accept="image/*" class="hidden" @change="onLogo" />
              </label>
            </div>
          </div>

          <!-- Banner -->
          <div>
            <label class="text-xs text-zinc-500 mb-1.5 block">Banner</label>
            <label class="flex items-center justify-center px-4 py-4 bg-zinc-800 border border-dashed border-zinc-600 rounded-xl text-sm text-zinc-400 cursor-pointer hover:border-zinc-500 transition">
              {{ form.banner ? form.banner.name : 'Clica para fazer upload do banner (recomendado: 1200×300)' }}
              <input type="file" accept="image/*" class="hidden" @change="onBanner" />
            </label>
          </div>

          <!-- Cores -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-zinc-500 mb-1.5 block">Cor primária</label>
              <div class="flex items-center gap-2">
                <input type="color" v-model="form.cor_primaria"
                  class="w-10 h-10 rounded-lg cursor-pointer border border-zinc-700 bg-zinc-800 p-0.5" />
                <span class="text-xs text-zinc-400 font-mono">{{ form.cor_primaria }}</span>
              </div>
              <p class="text-[10px] text-zinc-600 mt-1">Botões, destaques, badges</p>
            </div>
            <div>
              <label class="text-xs text-zinc-500 mb-1.5 block">Cor secundária</label>
              <div class="flex items-center gap-2">
                <input type="color" v-model="form.cor_secundaria"
                  class="w-10 h-10 rounded-lg cursor-pointer border border-zinc-700 bg-zinc-800 p-0.5" />
                <span class="text-xs text-zinc-400 font-mono">{{ form.cor_secundaria }}</span>
              </div>
              <p class="text-[10px] text-zinc-600 mt-1">Fundos, backgrounds</p>
            </div>
          </div>

          <!-- Preview das cores -->
          <div class="flex items-center gap-3">
            <div class="flex-1 h-6 rounded-lg" :style="{ backgroundColor: form.cor_primaria }"></div>
            <div class="flex-1 h-6 rounded-lg border border-zinc-700" :style="{ backgroundColor: form.cor_secundaria }"></div>
            <p class="text-xs text-zinc-600">Preview cores</p>
          </div>

          <!-- ── TEMPLATE ── -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs text-zinc-500">Template da loja</label>
              <span v-if="form.categoria" class="text-[10px] text-zinc-600">
                Sugeridos para <span class="text-zinc-400 capitalize">{{ form.categoria }}</span>
              </span>
            </div>
            <p class="text-[10px] text-zinc-600 mb-3">
              Podes mudar a qualquer altura no backoffice → Aparência.
            </p>

            <!-- Filtro rápido — só aparece se há mais de 3 templates -->
            <div v-if="todosTemplates.length > 3" class="flex gap-2 overflow-x-auto pb-2 mb-3 scrollbar-hide">
              <button @click="filtroTemplate = null"
                :class="['px-3 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                         filtroTemplate === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
                Todos
              </button>
              <button v-for="cat in categoriasFiltroTemplate" :key="cat.value"
                @click="filtroTemplate = cat.value"
                :class="['px-3 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap capitalize',
                         filtroTemplate === cat.value ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
                {{ cat.label }}
              </button>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="t in templatesFiltrados" :key="t.id"
                   @click="form.template_id = t.id"
                   :class="['relative rounded-xl border-2 p-3 cursor-pointer transition-all',
                            form.template_id === t.id
                              ? 'border-red-500 bg-red-500/10'
                              : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600']">
                <!-- Check -->
                <div v-if="form.template_id === t.id"
                     class="absolute top-2 right-2 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div class="text-3xl text-center mb-2">{{ t.preview }}</div>
                <p class="text-xs font-bold text-center"
                   :class="form.template_id === t.id ? 'text-zinc-100' : 'text-zinc-300'">
                  {{ t.nome }}
                </p>
                <p class="text-[10px] text-center mt-0.5 line-clamp-2 leading-relaxed"
                   :class="form.template_id === t.id ? 'text-zinc-300' : 'text-zinc-500'">
                  {{ t.descricao }}
                </p>
                <!-- Tags de categoria -->
                <div class="flex flex-wrap justify-center gap-1 mt-2">
                  <span v-for="cat in t.categorias" :key="cat"
                        class="px-1.5 py-0.5 bg-zinc-900/80 text-zinc-600 text-[9px] rounded capitalize">
                    {{ cat === 'todos' ? 'genérico' : cat }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ PASSO 3 — CONFIGURAÇÕES ═══ -->
      <div v-if="step === 3" class="space-y-5">

        <!-- Entrega e levantamento -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Tipo de serviço</h2>
          <div class="grid grid-cols-2 gap-3">
            <button @click="form.entrega_ativa = !form.entrega_ativa"
              :class="['p-4 rounded-xl border-2 transition-all text-left',
                       form.entrega_ativa ? 'border-red-500 bg-red-500/10' : 'border-zinc-700']">
              <p class="text-2xl mb-2">🚚</p>
              <p class="text-sm font-semibold text-zinc-200">Entrega ao domicílio</p>
              <p class="text-xs mt-1" :class="form.entrega_ativa ? 'text-red-400' : 'text-zinc-500'">
                {{ form.entrega_ativa ? 'Activado' : 'Desactivado' }}
              </p>
            </button>
            <button @click="form.levantamento_ativo = !form.levantamento_ativo"
              :class="['p-4 rounded-xl border-2 transition-all text-left',
                       form.levantamento_ativo ? 'border-red-500 bg-red-500/10' : 'border-zinc-700']">
              <p class="text-2xl mb-2">🏪</p>
              <p class="text-sm font-semibold text-zinc-200">Levantamento em loja</p>
              <p class="text-xs mt-1" :class="form.levantamento_ativo ? 'text-red-400' : 'text-zinc-500'">
                {{ form.levantamento_ativo ? 'Activado' : 'Desactivado' }}
              </p>
            </button>
          </div>
        </div>

        <!-- Métodos de pagamento -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4">
          <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Métodos de pagamento</h2>
          <div class="grid grid-cols-3 gap-3">
            <button v-for="m in metodosPagamento" :key="m.tipo"
              @click="toggleMetodo(m.tipo)"
              :class="['p-3 rounded-xl border-2 transition-all text-center',
                       form.metodos_pagamento.includes(m.tipo) ? 'border-red-500 bg-red-500/10' : 'border-zinc-700']">
              <p class="text-xl mb-1">{{ m.icon }}</p>
              <p class="text-xs font-semibold text-zinc-300">{{ m.label }}</p>
            </button>
          </div>
        </div>

        <!-- Opções de entrega -->
        <div v-if="form.entrega_ativa" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Opções de entrega</h2>
            <button @click="adicionarOpcao"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 transition">
              + Adicionar
            </button>
          </div>
          <div class="space-y-3">
            <div v-for="(op, idx) in form.opcoes_entrega" :key="idx"
                 class="bg-zinc-800/60 rounded-xl p-4 space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div class="col-span-2">
                  <label class="text-[10px] text-zinc-500 mb-1 block">Nome</label>
                  <input v-model="op.nome" type="text" placeholder="ex: Standard"
                    class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition" />
                </div>
                <div>
                  <label class="text-[10px] text-zinc-500 mb-1 block">Preço (€)</label>
                  <input v-model="op.preco" type="number" min="0" step="0.5" placeholder="0.00"
                    class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition" />
                </div>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex-1">
                  <label class="text-[10px] text-zinc-500 mb-1 block">Tempo estimado</label>
                  <input v-model="op.tempo_estimado" type="text" placeholder="ex: 30-45 min"
                    class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition" />
                </div>
                <button @click="form.opcoes_entrega.splice(idx, 1)"
                  class="mt-4 w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div v-if="form.opcoes_entrega.length === 0"
                 class="text-center py-4 text-xs rounded-xl border border-dashed"
                 :class="form.entrega_ativa ? 'border-red-500/50 text-red-400/70 bg-red-500/5' : 'border-zinc-700 text-zinc-600'">
              {{ form.entrega_ativa ? '⚠️ Obrigatório — adiciona pelo menos uma opção de entrega' : 'Sem opções de entrega.' }}
            </div>
          </div>
        </div>

        <!-- Aviso validacao entrega -->
        <div v-if="avisoEntrega" class="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 flex items-start gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-sm text-red-400">{{ avisoEntrega }}</p>
        </div>

        <!-- Resumo do template escolhido -->
        <div v-if="templateEscolhido" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-3">
          <span class="text-2xl flex-shrink-0">{{ templateEscolhido.preview }}</span>
          <div class="flex-1 min-w-0">
            <p class="text-xs text-zinc-500">Template seleccionado</p>
            <p class="text-sm font-bold text-zinc-200">{{ templateEscolhido.nome }}</p>
          </div>
          <button @click="step = 2"
            class="text-xs text-red-400 hover:text-red-300 transition flex-shrink-0">
            Alterar →
          </button>
        </div>

        <!-- Aviso de aprovação -->
        <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-2xl p-4 flex items-start gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p class="text-sm font-semibold text-yellow-400">Aprovação necessária</p>
            <p class="text-xs text-yellow-400/70 mt-0.5">A tua loja ficará pendente até ser aprovada pelo administrador. Receberás uma notificação quando for activada.</p>
          </div>
        </div>
      </div>

      <!-- Erro -->
      <p v-if="erro" class="text-xs text-red-400 bg-red-500/10 rounded-xl px-4 py-3 mt-4">{{ erro }}</p>

      <!-- Navegação entre passos -->
      <div class="flex gap-3 mt-6">
        <button v-if="step > 1" @click="step--"
          class="flex-1 py-3 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
          ← Anterior
        </button>
        <button v-if="step < 3" @click="avancar"
          :disabled="!podeAvancar"
          :class="['flex-1 py-3 rounded-xl text-sm font-bold transition',
                   podeAvancar ? 'bg-red-600 hover:bg-red-500 text-white' : 'bg-zinc-700 text-zinc-500 cursor-not-allowed']">
          Próximo →
        </button>
        <button v-if="step === 3" @click="submeter"
          :disabled="loading || !podeCriar"
          :class="['flex-1 py-3 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                   !podeCriar ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' :
                   loading ? 'bg-red-700 opacity-70 cursor-not-allowed text-white' :
                   'bg-red-600 hover:bg-red-500 text-white']">
          <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
            <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
          </svg>
          {{ loading ? 'A criar...' : 'Criar loja' }}
        </button>
      </div>
    </div>

    <!-- Sucesso -->
    <div v-if="sucesso"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 max-w-sm w-full p-8 text-center space-y-4">
        <div class="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div class="text-4xl">{{ templateEscolhido?.preview || '🏪' }}</div>
        <h2 class="text-xl font-extrabold text-zinc-100">Loja criada!</h2>
        <p class="text-zinc-400 text-sm">
          A tua loja está pendente de aprovação com o template
          <span class="text-zinc-200 font-semibold">{{ templateEscolhido?.nome }}</span>.
          O administrador irá activá-la em breve.
        </p>
        <button @click="$router.push('/')"
          class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-sm transition">
          Voltar ao início
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { TEMPLATES, getTemplatesSugeridos } from '@/config/lojaTemplates'

export default {
  name: 'CriarLoja',

  data () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      step: 1,
      loading: false,
      erro: '',
      sucesso: false,
      user,
      filtroTemplate: null,

      form: {
        nome:               '',
        descricao:          '',
        categoria:          '',
        localizacao:        '',
        logo:               null,
        banner:             null,
        cor_primaria:       '#ef4444',
        cor_secundaria:     '#ffffff',
        template_id:        'classico',
        entrega_ativa:      false,
        levantamento_ativo: true,
        metodos_pagamento:  ['dinheiro'],
        opcoes_entrega:     [],
      },

      logoPreview:   null,
      bannerPreview: null,
      loadingCats:   false,
      categorias:    [],

      metodosPagamento: [
        { tipo: 'dinheiro',      icon: '💵', label: 'Dinheiro'      },
        { tipo: 'mbway',         icon: '📱', label: 'MBWay'         },
        { tipo: 'cartao',        icon: '💳', label: 'Cartão'        },
        { tipo: 'flutterwave',   icon: '🌍', label: 'Flutterwave'   },
        { tipo: 'transferencia', icon: '🏦', label: 'Transferência' },
        { tipo: 'mobile_money',  icon: '📲', label: 'Mobile Money'  },
      ],

      categoriasFiltroTemplate: [
        { value: 'todos',       label: 'Genéricos'   },
        { value: 'restaurante', label: 'Restaurante' },
        { value: 'moda',        label: 'Moda'        },
        { value: 'tecnologia',  label: 'Tecnologia'  },
      ],
    }
  },

  computed: {
    todosTemplates () { return TEMPLATES },

    templatesFiltrados () {
      if (this.filtroTemplate) {
        return TEMPLATES.filter(t =>
          t.categorias.includes('todos') || t.categorias.includes(this.filtroTemplate)
        )
      }
      // sem filtro manual: mostra sugeridos para a categoria, senão todos
      return this.form.categoria
        ? getTemplatesSugeridos(this.form.categoria)
        : TEMPLATES
    },

    templateEscolhido () {
      return TEMPLATES.find(t => t.id === this.form.template_id) || null
    },

    categoriaLabel () {
      const cat = this.categorias.find(c => c.nome === this.form.categoria)
      return cat ? `${cat.icon} ${cat.nome}` : ''
    },

    podeAvancar () {
      if (this.step === 1) return this.form.nome.trim() && this.form.categoria
      if (this.step === 2) return true
      return false
    },

    podeCriar () {
      if (this.form.metodos_pagamento.length === 0) return false
      if (this.form.entrega_ativa && this.form.opcoes_entrega.filter(o => o.nome.trim()).length === 0) return false
      if (!this.form.entrega_ativa && !this.form.levantamento_ativo) return false
      return true
    },

    avisoEntrega () {
      if (this.form.entrega_ativa && this.form.opcoes_entrega.filter(o => o.nome.trim()).length === 0)
        return 'Com entrega ao domicílio activa tens de adicionar pelo menos uma opção de entrega.'
      if (!this.form.entrega_ativa && !this.form.levantamento_ativo)
        return 'Tens de activar pelo menos um tipo de serviço (entrega ou levantamento).'
      return null
    },
  },

  async created () {
    await this.fetchCategorias()
  },

  methods: {
    async fetchCategorias () {
      this.loadingCats = true
      try {
        const { data } = await api.get('/app/categorias/')
        this.categorias = data
      } catch (e) { console.error(e) }
      finally { this.loadingCats = false }
    },

    // Quando muda categoria no passo 1, pré-selecciona o primeiro template sugerido
    autoSelecionarTemplate (categoriaNome) {
      const sugeridos = getTemplatesSugeridos(categoriaNome)
      // só muda se ainda estiver no default ou se for genérico
      const actualTemplate = TEMPLATES.find(t => t.id === this.form.template_id)
      if (!actualTemplate || actualTemplate.categorias.includes('todos')) {
        // selecciona o primeiro sugerido que não seja genérico, senão o primeiro
        const especifico = sugeridos.find(t => !t.categorias.includes('todos'))
        if (especifico) this.form.template_id = especifico.id
      }
    },

    avancar () {
      if (!this.podeAvancar) return
      this.erro = ''
      this.step++
    },

    onLogo (e) {
      const file = e.target.files[0]
      if (!file) return
      this.form.logo = file
      this.logoPreview = URL.createObjectURL(file)
    },

    onBanner (e) {
      const file = e.target.files[0]
      if (!file) return
      this.form.banner = file
      this.bannerPreview = URL.createObjectURL(file)
    },

    toggleMetodo (tipo) {
      const idx = this.form.metodos_pagamento.indexOf(tipo)
      if (idx >= 0) this.form.metodos_pagamento.splice(idx, 1)
      else this.form.metodos_pagamento.push(tipo)
    },

    adicionarOpcao () {
      this.form.opcoes_entrega.push({ nome: '', preco: 0, tempo_estimado: '' })
    },

    async submeter () {
      if (!this.podeCriar) return
      this.loading = true
      this.erro = ''
      try {
        const fd = new FormData()
        fd.append('nome',               this.form.nome.trim())
        fd.append('descricao',          this.form.descricao)
        fd.append('categoria',          this.form.categoria)
        fd.append('localizacao',        this.form.localizacao)
        fd.append('cor_primaria',       this.form.cor_primaria)
        fd.append('cor_secundaria',     this.form.cor_secundaria)
        fd.append('template_id',        this.form.template_id)
        fd.append('entrega_ativa',      this.form.entrega_ativa)
        fd.append('levantamento_ativo', this.form.levantamento_ativo)

        if (this.form.logo)   fd.append('logo',   this.form.logo)
        if (this.form.banner) fd.append('banner', this.form.banner)

        this.form.metodos_pagamento.forEach(m => fd.append('metodos_pagamento', m))

        if (this.form.opcoes_entrega.length > 0) {
          fd.append('opcoes_entrega', JSON.stringify(
            this.form.opcoes_entrega.filter(o => o.nome.trim())
          ))
        }

        await api.post('/app/loja/criar/', fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.sucesso = true
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao criar a loja. Tenta novamente.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>