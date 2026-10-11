<!-- views/loja/LojaPublica.vue — wrapper dinâmico de templates -->
<template>
  <div>
    <div v-if="loadingTemplate" class="min-h-screen bg-zinc-950 flex items-center justify-center">
      <svg class="animate-spin h-10 w-10 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </div>

    <component
      v-else-if="templateComponent"
      :is="templateComponent"
      :tema="temaActivo"
      @toggle-dark="onToggleDark"
    />

    <div v-else class="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-zinc-400">
      <p class="text-2xl font-bold mb-2">Loja não encontrada</p>
      <button @click="$router.back()" class="text-red-400 hover:text-red-300 text-sm">← Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import { getTemplate, TEMPLATE_COMPONENTS } from '@/config/lojaTemplates'
import { DEMO_ID, ativarLojaDemo } from '@/utils/demoLoja'

const FALLBACK_ID   = 'classico'
const FALLBACK_TEMA = { id: FALLBACK_ID, corPrimaria: '#dc2626', corSecundaria: '#1c1c1e', darkMode: true }

export default {
  name: 'LojaPublica',

  setup () {
    const route             = useRoute()
    const loadingTemplate   = ref(true)
    const templateComponent = ref(null)
    const temaActivo        = ref(null)
    let darkModeBase        = true   // modo por defeito da loja (BD)

    // /loja/demo — loja fictícia para o preview do "Criar loja" (utils/demoLoja.js)
    if (route.params.id === DEMO_ID) ativarLojaDemo()

    async function resolveTemplate (lojaId) {
      loadingTemplate.value   = true
      templateComponent.value = null

      try {
        // ── 1. Cache local (resposta imediata enquanto a API carrega) ──────────
        const cacheKey = `loja_template_${lojaId}`
        const cached_  = localStorage.getItem(cacheKey)
        const cached   = cached_ ? JSON.parse(cached_) : null

        let templateId    = cached?.templateId    ?? FALLBACK_ID
        let corPrimaria   = cached?.corPrimaria   ?? FALLBACK_TEMA.corPrimaria
        let corSecundaria = cached?.corSecundaria ?? FALLBACK_TEMA.corSecundaria
        let darkModeDB    = cached?.darkMode      ?? true

        // ── 2. Fonte de verdade: API ──────────────────────────────────────────
        const { data } = await api.get(`/app/loja/${lojaId}/`)
        templateId    = data.template_id    || templateId
        corPrimaria   = data.cor_primaria   || corPrimaria
        corSecundaria = data.cor_secundaria || corSecundaria
        darkModeDB    = data.dark_mode      !== undefined ? data.dark_mode : darkModeDB

        // ── 3. Actualiza cache ────────────────────────────────────────────────
        localStorage.setItem(cacheKey, JSON.stringify({
          templateId, corPrimaria, corSecundaria, darkMode: darkModeDB,
        }))

        // ── 4. Preferência dark/light do VISITANTE ────────────────────────────
        // Só vale enquanto o modo por defeito da loja for o mesmo de quando a
        // escolheu; se o dono mudar o modo no backoffice, a mudança prevalece.
        darkModeBase = darkModeDB
        let darkMode = darkModeDB
        const pref = lerPrefDark(lojaId)
        if (pref && pref.base === darkModeDB) darkMode = pref.valor

        // ── 4b. Modo preview do backoffice (?preview=1&tpl=…&c1=…&c2=…&dark=…) ─
        // Só altera o que é mostrado — nada é guardado na BD nem na cache.
        const q = route.query
        if (q.preview) {
          const cor = v => (typeof v === 'string' && /^#?[0-9a-f]{6}$/i.test(v) ? '#' + v.replace('#', '') : null)
          if (q.tpl && TEMPLATE_COMPONENTS[q.tpl]) templateId = q.tpl
          corPrimaria   = cor(q.c1) || corPrimaria
          corSecundaria = cor(q.c2) || corSecundaria
          if (q.dark !== undefined) darkMode = q.dark === '1'
        }

        temaActivo.value = { id: templateId, corPrimaria, corSecundaria, darkMode }

        // ── 5. Carrega componente ─────────────────────────────────────────────
        // Tenta TEMPLATE_COMPONENTS primeiro (novo mapa directo),
        // depois cai em getTemplate() para compatibilidade com código legado.
        const loader = TEMPLATE_COMPONENTS?.[templateId]
          ?? getTemplate(templateId)?.component
          ?? TEMPLATE_COMPONENTS?.[FALLBACK_ID]

        if (!loader) throw new Error(`Loader não encontrado para template: ${templateId}`)

        const mod = await loader()
        templateComponent.value = mod.default

      } catch (e) {
        console.error('Erro ao carregar template da loja:', e)

        // Fallback: carrega o clássico directamente
        try {
          const fallbackLoader = TEMPLATE_COMPONENTS?.[FALLBACK_ID]
            ?? getTemplate(FALLBACK_ID)?.component
          const mod = await fallbackLoader()
          templateComponent.value = mod.default
          temaActivo.value = { ...FALLBACK_TEMA }
        } catch (e2) {
          console.error('Erro ao carregar template fallback:', e2)
          // templateComponent fica null → mostra "Loja não encontrada"
        }
      } finally {
        loadingTemplate.value = false
        // em preview dentro de um iframe, avisa o backoffice que já pode enviar o tema
        if (route.query.preview && window.parent !== window) {
          window.parent.postMessage({ type: 'preview-pronto' }, window.location.origin)
        }
      }
    }

    function lerPrefDark (lojaId) {
      try {
        const p = JSON.parse(localStorage.getItem(`user_dark_${lojaId}`))
        return p && typeof p.valor === 'boolean' ? p : null
      } catch { return null }   // formato antigo ('true'/'false') é ignorado
    }

    // Utilizador togglou dark/light — guarda preferência local
    function onToggleDark (novoValor) {
      const lojaId = route.params.id
      if (!route.query.preview) {
        localStorage.setItem(`user_dark_${lojaId}`, JSON.stringify({ valor: novoValor, base: darkModeBase }))
      }
      if (temaActivo.value) {
        temaActivo.value = { ...temaActivo.value, darkMode: novoValor }
      }
    }

    // Preview ao vivo: o backoffice (janela pai) envia cores/modo sem recarregar
    function onPreviewMessage (e) {
      if (e.origin !== window.location.origin || e.data?.type !== 'tema-preview') return
      if (!route.query.preview || !temaActivo.value) return
      const { corPrimaria, corSecundaria, darkMode } = e.data
      temaActivo.value = {
        ...temaActivo.value,
        ...(corPrimaria   && { corPrimaria }),
        ...(corSecundaria && { corSecundaria }),
        ...(typeof darkMode === 'boolean' && { darkMode }),
      }
    }

    onMounted(() => {
      resolveTemplate(route.params.id)
      window.addEventListener('message', onPreviewMessage)
    })
    onUnmounted(() => window.removeEventListener('message', onPreviewMessage))
    watch(() => route.params.id, id => { if (id) resolveTemplate(id) })

    return { loadingTemplate, templateComponent, temaActivo, onToggleDark }
  },
}
</script>
