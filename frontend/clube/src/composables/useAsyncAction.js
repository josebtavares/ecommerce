// src/composables/useAsyncAction.js
import { ref } from 'vue'

/**
 * Devolve:
 *   loading  – ref<boolean>  ➜  indica se há uma acção em curso
 *   wrap(fn) – função que executa fn() e bloqueia cliques duplicados
 */
export function useAsyncAction () {
  const loading = ref(false)

  async function wrap (fn) {
    if (loading.value) return            // ignora se já está a executar
    loading.value = true
    try {
      return await fn()                  // corre a função recebida
    } finally {
      loading.value = false              // desbloqueia mesmo em erro
    }
  }

  return { loading, wrap }
}
