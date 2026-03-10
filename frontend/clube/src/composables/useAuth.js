import { ref } from 'vue'
import { useRouter } from 'vue-router'

const user = ref(getUserFromStorage())

function getUserFromStorage () {
  const userData = localStorage.getItem('user')
  return userData ? JSON.parse(userData) : null
}

export function useAuth () {
  const router = useRouter()

  function isAuthenticated () {
    return !!localStorage.getItem('access_token')
  }

  function logout () {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    user.value = null
    router.push({ name: 'Login' })
  }

  return {
    user,
    isAuthenticated,
    logout
  }
}