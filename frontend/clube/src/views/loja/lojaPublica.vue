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
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import { getTemplate } from '@/config/lojaTemplates'

export default {
  name: 'LojaPublica',

  setup () {
    const route             = useRoute()
    const loadingTemplate   = ref(true)
    const templateComponent = ref(null)
    const temaActivo        = ref(null)

    async function resolveTemplate (lojaId) {
      loadingTemplate.value = true
      try {
        // 1. Cache do template/cores da loja
        const cacheKey = `loja_template_${lojaId}`
        const cached   = localStorage.getItem(cacheKey)

        let templateId    = cached ? JSON.parse(cached).templateId    : 'classico'
        let corPrimaria   = cached ? JSON.parse(cached).corPrimaria   : '#dc2626'
        let corSecundaria = cached ? JSON.parse(cached).corSecundaria : '#1c1c1e'
        let darkModeDefault = cached ? JSON.parse(cached).darkMode    : true

        // 2. Fonte de verdade: BD
        const { data } = await api.get(`/app/loja/${lojaId}/`)
        templateId      = data.template_id    || templateId
        corPrimaria     = data.cor_primaria   || corPrimaria
        corSecundaria   = data.cor_secundaria || corSecundaria
        darkModeDefault = data.dark_mode      !== undefined ? data.dark_mode : darkModeDefault

        // 3. Actualiza cache do template
        localStorage.setItem(cacheKey, JSON.stringify({
          templateId, corPrimaria, corSecundaria, darkMode: darkModeDefault
        }))

        // 4. Preferência de dark/light do UTILIZADOR para esta loja (tem prioridade)
        const userDarkKey = `user_dark_${lojaId}`
        const userDark    = localStorage.getItem(userDarkKey)
        const darkMode    = userDark !== null ? userDark === 'true' : darkModeDefault

        temaActivo.value = { id: templateId, corPrimaria, corSecundaria, darkMode }

        // 5. Carrega componente lazy
        const config = getTemplate(templateId)
        const mod    = await config.component()
        templateComponent.value = mod.default

      } catch (e) {
        console.error('Erro ao carregar template:', e)
        try {
          const mod = await import('@/views/loja/templates/TemplateClassico.vue')
          templateComponent.value = mod.default
          temaActivo.value = { id: 'classico', corPrimaria: '#dc2626', corSecundaria: '#1c1c1e', darkMode: true }
        } catch (e2) { console.error(e2) }
      } finally {
        loadingTemplate.value = false
      }
    }

    // Utilizador clicou no toggle — guarda preferência no localStorage
    function onToggleDark (novoValor) {
      const lojaId     = route.params.id
      const userDarkKey = `user_dark_${lojaId}`
      localStorage.setItem(userDarkKey, String(novoValor))
      if (temaActivo.value) {
        temaActivo.value = { ...temaActivo.value, darkMode: novoValor }
      }
    }

    onMounted(() => resolveTemplate(route.params.id))
    watch(() => route.params.id, id => resolveTemplate(id))

    return { loadingTemplate, templateComponent, temaActivo, onToggleDark }
  }
}
</script>