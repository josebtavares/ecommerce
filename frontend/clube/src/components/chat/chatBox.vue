<template>
  <!-- Floating Chat Button -->
  <button
    @click="toggleChat"
    class="fixed bottom-6 right-6 z-40 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <font-awesome-icon :icon="['fas', isOpen ? 'times' : 'comment-dots']" size="lg" />
    <span v-if="totalUnreadCount > 0" class="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
      {{ totalUnreadCount > 99 ? '99+' : totalUnreadCount }}
    </span>
  </button>

  <!-- Chat Widget -->
  <Transition name="slide">
    <div
      v-if="isOpen"
      class="fixed bottom-0 right-0 md:right-4 md:bottom-4 w-full md:w-[800px] h-[85vh] bg-white dark:bg-gray-900 rounded-t-xl md:rounded-xl shadow-2xl flex z-50 overflow-hidden border border-gray-200 dark:border-gray-700"
    >
      <!-- Left Sidebar - Conversations -->
      <div class="w-80 bg-gray-50 dark:bg-gray-800 h-full flex flex-col border-r border-gray-200 dark:border-gray-700">
        <!-- Header with Search -->
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Mensagens</h3>

          <!-- Search Input -->
          <div class="relative">
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              class="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white"
              placeholder="Pesquisar utilizadores..."
            />
            <font-awesome-icon
              :icon="['fas', 'search']"
              class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"
            />
            <button
              v-if="searchQuery"
              @click="clearSearch"
              class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <font-awesome-icon :icon="['fas', 'times']" class="text-sm" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p class="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
          </div>
        </div>

        <!-- Search Results -->
        <div v-else-if="isSearching && searchResults.length > 0" class="flex-1 overflow-y-auto">
          <div class="p-2">
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-2 px-2">Resultados da pesquisa</p>
            <div
              v-for="user in searchResults"
              :key="`search-${user.id}`"
              class="flex items-center gap-3 p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg cursor-pointer transition-colors"
              @click="startChatWithUser(user)"
            >
              <img
                :src="getUserPhoto(user.foto)"
                :alt="user.nome"
                class="w-10 h-10 rounded-full object-cover"
                @error="handleImageError"
              />
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-900 dark:text-white truncate">{{ user.nome }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{{ user.email }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- No Search Results -->
        <div v-else-if="isSearching && searchResults.length === 0 && searchQuery" class="flex-1 flex items-center justify-center">
          <div class="text-center p-4">
            <font-awesome-icon :icon="['fas', 'user-slash']" class="text-4xl text-gray-400 mb-2" />
            <p class="text-sm text-gray-500 dark:text-gray-400">Nenhum utilizador encontrado</p>
          </div>
        </div>

        <!-- Conversations List -->
        <div v-else class="flex-1 overflow-y-auto">
          <div v-if="threads.length === 0" class="flex-1 flex items-center justify-center p-4">
            <div class="text-center">
              <font-awesome-icon :icon="['fas', 'comments']" class="text-4xl text-gray-400 mb-2" />
              <p class="text-sm text-gray-500 dark:text-gray-400">Nenhuma conversa ainda</p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Pesquise um utilizador para começar</p>
            </div>
          </div>

          <div v-else class="p-2">
            <div
              v-for="thread in threads"
              :key="`thread-${thread.id}`"
              :class="[
                'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                selectedThread?.id === thread.id
                  ? 'bg-blue-100 dark:bg-blue-900'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
              @click="selectThread(thread)"
            >
              <img
                :src="getUserPhoto(getOtherUser(thread).foto)"
                :alt="getOtherUser(thread).nome"
                class="w-12 h-12 rounded-full object-cover"
                @error="handleImageError"
              />

              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                  <p class="font-medium text-gray-900 dark:text-white truncate">
                    {{ getOtherUser(thread).nome }}
                  </p>
                  <span v-if="thread.last_msg_at" class="text-xs text-gray-500 dark:text-gray-400">
                    {{ formatTime(thread.last_msg_at) }}
                  </span>
                </div>

                <div class="flex items-center justify-between">
                  <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {{ getLastMessagePreview(thread) }}
                  </p>
                  <span v-if="thread.unread_count > 0" class="bg-blue-600 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                    {{ thread.unread_count > 99 ? '99+' : thread.unread_count }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Chat Area -->
      <div class="flex-1 h-full flex flex-col">
        <!-- Chat Header -->
        <div v-if="selectedThread" class="h-16 px-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div class="flex items-center gap-3">
            <img
              :src="getUserPhoto(getOtherUser(selectedThread).foto)"
              :alt="getOtherUser(selectedThread).nome"
              class="w-10 h-10 rounded-full object-cover"
              @error="handleImageError"
            />
            <div>
              <p class="font-semibold text-gray-900 dark:text-white">{{ getOtherUser(selectedThread).nome }}</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ getOtherUser(selectedThread).username ? `@${getOtherUser(selectedThread).username}` : 'Utilizador' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="clearCurrentChat"
              class="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
              title="Limpar conversa"
            >
              <font-awesome-icon :icon="['fas', 'trash']" />
            </button>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!selectedThread" class="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-800">
          <div class="text-center">
            <font-awesome-icon :icon="['fas', 'comment-dots']" class="text-6xl text-gray-400 mb-4" />
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Bem-vindo ao Chat</h3>
            <p class="text-gray-500 dark:text-gray-400">Selecione uma conversa ou pesquise um utilizador para começar</p>
          </div>
        </div>

        <!-- Messages Area -->
        <div v-else class="flex-1 overflow-hidden flex flex-col">
          <!-- Messages Container -->
          <div
            ref="messagesContainer"
            class="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-gray-800"
            @scroll="handleScroll"
          >
            <!-- Load More Button -->
            <div v-if="hasMoreMessages" class="text-center">
              <button
                @click="loadMoreMessages"
                :disabled="isLoadingMessages"
                class="text-blue-600 hover:text-blue-800 text-sm font-medium disabled:opacity-50"
              >
                {{ isLoadingMessages ? 'Carregando...' : 'Carregar mensagens anteriores' }}
              </button>
            </div>

            <!-- Messages -->
            <div
              v-for="message in messages"
              :key="message.id"
              :class="[
                'flex',
                isMyMessage(message) ? 'justify-end' : 'justify-start'
              ]"
              >
              <div
                :class="[
                  'max-w-xs lg:max-w-md px-4 py-2 rounded-lg',
                  isMyMessage(message)
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600'
                ]"
              >
                <p class="text-sm">{{ message.text }}</p>
                <div class="flex items-center justify-between mt-1">
                  <span class="text-xs opacity-75">
                    {{ formatTime(message.created_at) }}
                  </span>
                  <div v-if="isMyMessage(message)" class="flex items-center gap-1">
                    <font-awesome-icon
                      :icon="['fas', message.read ? 'check-double' : 'check']"
                      :class="message.read ? 'text-blue-200' : 'text-gray-300'"
                      class="text-xs"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Message Input -->
          <div class="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
            <div class="flex items-end gap-2">
              <div class="flex-1">
                <textarea
                  v-model="newMessageText"
                  @keydown="handleKeyDown"
                  ref="messageInput"
                  rows="1"
                  class="w-full resize-none bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white"
                  placeholder="Escreva uma mensagem..."
                  :disabled="isSendingMessage"
                ></textarea>
              </div>

              <button
                @click="sendMessage"
                :disabled="!newMessageText.trim() || isSendingMessage"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <font-awesome-icon
                  :icon="isSendingMessage ? ['fas', 'spinner'] : ['fas', 'paper-plane']"
                  :class="{ 'animate-spin': isSendingMessage }"
                />
                <span class="hidden sm:inline">{{ isSendingMessage ? 'Enviando...' : 'Enviar' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

// ═══════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════

// Get current user from localStorage
const getCurrentUser = () => {
  try {
    const userStr = localStorage.getItem('user')
    if (!userStr) return null
    const user = JSON.parse(userStr)
    return {
      id: Number(user.id),
      nome: user.nome,
      username: user.username,
      email: user.email,
      foto: user.foto
    }
  } catch (error) {
    console.error('Error parsing current user:', error)
    return null
  }
}

const currentUser = getCurrentUser()
console.log('Current user:', currentUser)

// UI State
const isOpen = ref(false)
const isLoading = ref(false)
const isLoadingMessages = ref(false)
const isSendingMessage = ref(false)
const isSearching = ref(false)
const hasMoreMessages = ref(false)

// Data
const threads = ref([])
const messages = ref([])
const searchResults = ref([])
const selectedThread = ref(null)

// Form data
const searchQuery = ref('')
const newMessageText = ref('')

// Refs
const messagesContainer = ref(null)
const messageInput = ref(null)

// WebSocket
let websocket = null

// ═══════════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════════

const totalUnreadCount = computed(() => {
  return threads.value.reduce((total, thread) => total + (thread.unread_count || 0), 0)
})

// ═══════════════════════════════════════════════════════════════
// METHODS
// ═══════════════════════════════════════════════════════════════

const toggleChat = () => {
  isOpen.value = !isOpen.value
}

const handleImageError = (event) => {
  event.target.src = '/default-avatar.png'
}

const getUserPhoto = (photo) => {
  if (!photo) return '/default-avatar.png'
  if (photo.startsWith('http')) return photo
  return `${process.env.VUE_APP_URL_BASE}${photo}`
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  const now = new Date()
  const diffInHours = (now - date) / (1000 * 60 * 60)

  if (diffInHours < 24) {
    return date.toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })
  } else if (diffInHours < 168) { // 7 days
    return date.toLocaleDateString('pt-PT', { weekday: 'short', hour: '2-digit', minute: '2-digit' })
  } else {
    return date.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: '2-digit' })
  }
}

const getOtherUser = (thread) => {
  if (!thread?.participants || !Array.isArray(thread.participants)) {
    console.warn('Invalid thread structure:', thread)
    return {
      id: null,
      nome: 'Utilizador',
      foto: '',
      username: '',
      email: '',
      online: false
    }
  }

  // Find participant that is NOT the current user
  const otherParticipant = thread.participants.find(participant => {
    return participant.user.id !== currentUser?.id
  })

  if (!otherParticipant) {
    console.warn('No other participant found in thread:', thread)
    return {
      id: null,
      nome: 'Utilizador',
      foto: '',
      username: '',
      email: '',
      online: false
    }
  }

  return {
    ...otherParticipant.user,
    online: otherParticipant.user.status === 'ativo' // or whatever determines online status
  }
}

const getLastMessagePreview = (thread) => {
  // You can implement this based on your needs
  // For now, just return a placeholder
  console.log('Getting last message preview for thread:', thread)
  return 'Sem mensagens ainda...'
}

const isMyMessage = (message) => {
  if (!message?.sender || !currentUser) return false
  return message.sender.id === currentUser.id
}

// ═══════════════════════════════════════════════════════════════
// API METHODS
// ═══════════════════════════════════════════════════════════════

const loadThreads = async () => {
  if (!currentUser) return

  isLoading.value = true
  try {
    const response = await api.get('/api/chat/threads/')
    threads.value = response.data || []
    console.log('Loaded threads:', threads.value)
  } catch (error) {
    console.error('Error loading threads:', error)
  } finally {
    isLoading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    isSearching.value = false
    searchResults.value = []
    return
  }

  try {
    isSearching.value = true
    const response = await api.get('/app/utilizador/pagination/', {
      params: { q: searchQuery.value.trim() }
    })
    searchResults.value = response.data.results || response.data || []
  } catch (error) {
    console.error('Error searching users:', error)
    searchResults.value = []
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  isSearching.value = false
  searchResults.value = []
}

const startChatWithUser = async (user) => {
  try {
    console.log('Starting chat with user:', user.id, user.nome)

    // Check if thread already exists with this user
    const existingThread = threads.value.find(thread => {
      return thread.participants.some(
        participant => participant.user.id === user.id
      )
    })

    if (existingThread) {
      console.log('Using existing thread:', existingThread.id)
      await selectThread(existingThread)
      return
    }

    console.log('Creating new thread with user:', user.id)
    const response = await api.post('/api/chat/threads/', {
      destinatario_id: user.id
    })

    const newThread = response.data
    console.log('New thread created:', newThread)

    threads.value.unshift(newThread)
    await selectThread(newThread)

  } catch (error) {
    console.error('Error starting chat:', error)
    alert('Erro ao iniciar conversa. Tente novamente.')
  } finally {
    clearSearch()
  }
}

const selectThread = async (thread) => {
  console.log('Selecting thread:', thread)
  console.log('Other user:', getOtherUser(thread))

  selectedThread.value = thread
  await loadMessages(thread.id)

  // Connect WebSocket only if not already connected to this thread
  if (!websocket || websocket.threadId !== thread.id) {
    connectWebSocket(thread.id)
  }

  // Mark as read if needed
  if (thread.unread_count > 0) {
    await markAsRead(thread.id)
    thread.unread_count = 0
  }

  // Focus message input
  nextTick(() => {
    if (messageInput.value) {
      messageInput.value.focus()
    }
  })
}

const loadMessages = async (threadId, offset = 0) => {
  try {
    isLoadingMessages.value = offset > 0
    const response = await api.get(`/api/chat/threads/${threadId}/messages/`, {
      params: { offset, limit: 50 }
    })

    const newMessages = response.data.results || response.data || []
    console.log('Loaded messages:', newMessages)

    if (offset === 0) {
      messages.value = newMessages
      await nextTick(() => scrollToBottom())
    } else {
      messages.value = [...newMessages, ...messages.value]
    }

    hasMoreMessages.value = newMessages.length === 50
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    isLoadingMessages.value = false
  }
}

const loadMoreMessages = () => {
  if (selectedThread.value && !isLoadingMessages.value) {
    loadMessages(selectedThread.value.id, messages.value.length)
  }
}

const sendMessage = async () => {
  if (!newMessageText.value.trim() || !selectedThread.value || isSendingMessage.value) return

  const text = newMessageText.value.trim()
  newMessageText.value = ''
  isSendingMessage.value = true

  // Optimistic update
  const tempMessage = {
    id: Date.now(),
    text,
    sender: currentUser,
    created_at: new Date().toISOString(),
    read: false
  }

  messages.value.push(tempMessage)
  await nextTick(() => scrollToBottom())

  try {
    const response = await api.post(`/api/chat/threads/${selectedThread.value.id}/messages/`, {
      text
    })

    console.log('Message sent:', response.data)

    // Replace temp message with real one
    const messageIndex = messages.value.findIndex(m => m.id === tempMessage.id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = response.data
    }

    // Send via WebSocket if connected
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'message',
        message: text
      }))
    }

  } catch (error) {
    console.error('Error sending message:', error)
    // Remove temp message on error
    messages.value = messages.value.filter(m => m.id !== tempMessage.id)
  } finally {
    isSendingMessage.value = false
  }
}

const connectWebSocket = (threadId) => {
  if (websocket) {
    websocket.close()
  }

  const wsUrl = process.env.VUE_APP_WS_URL || 'ws://127.0.0.1:8000'
  const token = localStorage.getItem('access')

  websocket = new WebSocket(`${wsUrl}/ws/chat/thread/${threadId}/?token=${token}`)
  websocket.threadId = threadId // Store thread ID for reference

  websocket.onopen = () => {
    console.log(`WebSocket connected to thread ${threadId}`)
  }

  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'message') {
        handleIncomingMessage(data.message)
      } else if (data.type === 'typing') {
        handleTypingIndicator(data)
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error)
    }
  }

  // ... error and close handlers
}

// const isTyping = ref(false)
const otherUserTyping = ref(false)
let typingTimeout = null

const handleTypingIndicator = (data) => {
  // Only process typing indicators for the current thread
  if (selectedThread.value?.id !== data.thread_id) return

  const otherUser = getOtherUser(selectedThread.value)

  // Check if the typing event is from the other user
  if (data.user_id === otherUser.id) {
    otherUserTyping.value = data.typing

    // Auto-clear typing indicator after 3 seconds
    clearTimeout(typingTimeout)
    if (data.typing) {
      typingTimeout = setTimeout(() => {
        otherUserTyping.value = false
      }, 3000)
    }
  }
}

const handleIncomingMessage = (message) => {
  // Only add if it belongs to the current thread
  if (selectedThread.value?.id === message.thread) {
    messages.value.push(message)

    // Mark as read if we're the recipient
    if (message.sender.id !== currentUser.id) {
      markAsRead(message.thread)
    }

    nextTick(() => scrollToBottom())
  }

  // Update unread count in threads list
  const thread = threads.value.find(t => t.id === message.thread)
  if (thread && message.sender.id !== currentUser.id) {
    thread.unread_count = (thread.unread_count || 0) + 1
    thread.last_msg_at = message.created_at
  }
}

const markAsRead = async (threadId) => {
  try {
    await api.post(`/api/chat/threads/${threadId}/mark-read/`)

    // Update local state
    const thread = threads.value.find(t => t.id === threadId)
    if (thread) {
      thread.unread_count = 0
    }
  } catch (error) {
    console.error('Error marking as read:', error)
  }
}

const clearCurrentChat = () => {
  if (confirm('Tem certeza que deseja limpar esta conversa?')) {
    messages.value = []
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleScroll = () => {
  if (messagesContainer.value.scrollTop === 0 && hasMoreMessages.value) {
    loadMoreMessages()
  }
}

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// ═══════════════════════════════════════════════════════════════
// WATCHERS & LIFECYCLE
// ═══════════════════════════════════════════════════════════════

watch(isOpen, (newValue) => {
  if (newValue && threads.value.length === 0) {
    loadThreads()
  }
})

onMounted(() => {
  if (currentUser) {
    loadThreads()
  } else {
    console.error('No current user found in localStorage')
  }
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
})
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(100%);
}

@media (min-width: 768px) {
  .slide-enter-from,
  .slide-leave-to {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.dark ::-webkit-scrollbar-thumb {
  background: #4a5568;
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: #2d3748;
}

/* Auto-resize textarea */
textarea {
  min-height: 40px;
  max-height: 120px;
  resize: none;
}
</style>
