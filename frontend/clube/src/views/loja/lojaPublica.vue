<!-- views/loja/LojaPublica.vue — wrapper dinâmico de templates -->
<template>
  <div>
    <div v-if="loadingTemplate" class="min-h-screen bg-zinc-950 flex items-center justify-center">
      <svg class="animate-spin h-10 w-10 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </div>

    <!-- loja fechada pelo dono (ou indisponível) -->
    <div v-else-if="indisponivel" class="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-center px-6">
      <div class="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-5">
        <font-awesome-icon :icon="['fas', indisponivel.fechada ? 'door-closed' : 'store']" class="w-6 h-6 text-zinc-500" />
      </div>
      <p class="text-xl font-bold text-zinc-100">
        {{ indisponivel.fechada ? `${indisponivel.nome || 'Esta loja'} está temporariamente fechada` : 'Loja não encontrada' }}
      </p>
      <p class="text-sm text-zinc-500 mt-2 max-w-sm">
        {{ indisponivel.fechada ? 'Volta mais tarde — a loja não está a receber encomendas de momento.' : 'O link pode estar errado ou a loja já não existe.' }}
      </p>
      <router-link to="/Home" class="mt-6 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition">
        Explorar outras lojas
      </router-link>
    </div>

    <template v-else-if="templateComponent">
      <!-- min-h-screen: enquanto o template carrega, o rodapé fica abaixo do ecrã (senão aparece no topo e "salta") -->
      <div class="min-h-screen">
        <component
          :is="templateComponent"
          :tema="temaActivo"
          @toggle-dark="onToggleDark"
        />
      </div>
      <!-- rodapé do site, igual em todos os templates (o "Vendido por" está no rodapé de cada template: LojaRodapeInfo) -->
      <SiteRodape :isDark="temaActivo?.darkMode !== false" />
    </template>

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
import SiteRodape from '@/components/paginas/SiteRodape.vue'

const FALLBACK_ID   = 'classico'
const FALLBACK_TEMA = { id: FALLBACK_ID, corPrimaria: '#dc2626', corSecundaria: '#1c1c1e', darkMode: true }

export default {
  name: 'LojaPublica',
  components: { SiteRodape },

  setup () {
    const route             = useRoute()
    const loadingTemplate   = ref(true)
    const templateComponent = ref(null)
    const temaActivo        = ref(null)
    const indisponivel      = ref(null)   // { fechada, nome } quando a API devolve 404
    let darkModeBase        = true   // modo por defeito da loja (BD)

    // /loja/demo — loja fictícia para o preview do "Criar loja" (utils/demoLoja.js)
    if (route.params.id === DEMO_ID) ativarLojaDemo()

    async function resolveTemplate (lojaId) {
      loadingTemplate.value   = true
      templateComponent.value = null
      indisponivel.value      = null

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
        document.title = `${data.nome} — Bende`
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
        // 404: loja inexistente, ou não activa (fechada/pendente/suspensa) para este visitante
        if (e.response?.status === 404) {
          indisponivel.value = { fechada: e.response.data?.estado === 'fechada', nome: e.response.data?.nome || '' }
          return
        }
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

    return { loadingTemplate, templateComponent, temaActivo, onToggleDark, indisponivel }
  },
}
</script>
