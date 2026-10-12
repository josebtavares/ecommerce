import { reactive } from 'vue'
import api from '@/services/api'

// Verificação ao vivo de username/email (GET /app/utilizador/disponivel/).
// estado: null | 'a_verificar' | 'disponivel' | 'indisponivel'
// O servidor volta a validar ao gravar — isto só avisa mais cedo.
export function criarVerificador (campo) {
  const v = reactive({
    estado: null,
    motivo: '',
    sugestoes: [],
    _timer: null,
    _ultimo: '',

    // `atual`: o valor que a própria conta já tem (perfil) — não é verificado
    verificar (valor, atual = '') {
      clearTimeout(v._timer)
      const limpo = String(valor || '').trim()
      v.estado = null
      v.motivo = ''
      v.sugestoes = []
      v._ultimo = limpo

      if (!limpo) return
      if (atual && limpo.toLowerCase() === String(atual).trim().toLowerCase()) return
      if (campo === 'username' && limpo.length < 3) return
      if (campo === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(limpo)) return

      // esperar 400ms depois de parar de escrever
      v._timer = setTimeout(async () => {
        v.estado = 'a_verificar'
        try {
          const { data } = await api.get('/app/utilizador/disponivel/', { params: { [campo]: limpo } })
          if (v._ultimo !== limpo) return          // entretanto mudou o texto
          const r = data[campo] || {}
          v.estado    = r.disponivel ? 'disponivel' : 'indisponivel'
          v.motivo    = r.motivo || ''
          v.sugestoes = r.sugestoes || []
        } catch {
          // se a verificação falhar não bloqueia — o servidor valida ao gravar
          if (v._ultimo === limpo) v.estado = null
        }
      }, 400)
    },

    get bloqueia () {
      return v.estado === 'indisponivel'
    },
  })
  return v
}
