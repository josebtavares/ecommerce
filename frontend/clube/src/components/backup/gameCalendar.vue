<template>
  <div class="game-calendar-container">
    <!-- Header with filters and actions -->
    <div class="calendar-header">
      <div class="header-controls">
        <div class="competition-selector">
          <select v-model="selectedCompetition" @change="loadGames" class="form-select">
            <option value="">Todas as Competições</option>
            <optgroup label="Ligas">
              <option v-for="liga in ligas" :key="`liga-${liga.id}`" :value="`liga-${liga.id}`">
                {{ liga.nome }}
              </option>
            </optgroup>
            <optgroup label="Torneios">
              <option v-for="torneio in torneios" :key="`torneio-${torneio.id}`" :value="`torneio-${torneio.id}`">
                {{ torneio.nome }}
              </option>
            </optgroup>
          </select>
        </div>
        
        <button @click="openCreateModal" class="btn btn-primary">
          <i class="icon-plus"></i>
          <span class="btn-text">Novo Jogo</span>
        </button>
      </div>
      
      <div class="view-controls">
        <button 
          v-for="view in viewOptions" 
          :key="view.value"
          @click="changeView(view.value)"
          :class="['btn', 'btn-outline', { 'active': currentView === view.value }]"
        >
          {{ view.label }}
        </button>
      </div>
    </div>

    <!-- Calendar Component -->
    <div class="calendar-wrapper">
      <FullCalendar
        ref="calendar"
        :options="calendarOptions"
        class="custom-calendar"
      />
    </div>

    <!-- Game Details Modal -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="closeDetailsModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Detalhes do Jogo</h3>
          <button @click="closeDetailsModal" class="btn-close">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="game-details">
            <div class="teams-section">
              <div class="team home-team">
                <img :src="backendUrl + selectedGame.equipa_casa.foto || '/placeholder-team.png'" :alt="selectedGame.equipa_casa.nome">
                <h4>{{ selectedGame.equipa_casa.nome }}</h4>
                <div class="score">{{ selectedGame.golo_casa || 0 }}</div>
              </div>
              
              <div class="vs-separator">
                <span>VS</span>
                <div class="match-time">{{ formatDateTime(selectedGame.data) }}</div>
              </div>
              
              <div class="team away-team">
                <img :src="backendUrl + selectedGame.equipa_fora.foto || '/placeholder-team.png'" :alt="selectedGame.equipa_fora.nome">
                <h4>{{ selectedGame.equipa_fora.nome }}</h4>
                <div class="score">{{ selectedGame.golo_fora || 0 }}</div>
              </div>
            </div>
            
            <div class="game-info">
              <div class="info-row">
                <span class="label">Local:</span>
                <span>{{ selectedGame.local || 'A definir' }}</span>
              </div>
              <div class="info-row">
                <span class="label">Estádio:</span>
                <span>{{ selectedGame.estadio || 'A definir' }}</span>
              </div>
              <div class="info-row">
                <span class="label">Árbitro:</span>
                <span>{{ selectedGame.arbitro?.nome || 'A definir' }}</span>
              </div>
              <div class="info-row">
                <span class="label">Competição:</span>
                <span>{{ getCompetitionName(selectedGame) }}</span>
              </div>
              <div v-if="selectedGame.descricao" class="info-row">
                <span class="label">Descrição:</span>
                <p>{{ selectedGame.descricao }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="openEditModal" class="btn btn-secondary">Editar</button>
          <button @click="confirmDelete" class="btn btn-danger">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Game Modal -->
    <div v-if="showFormModal" class="modal-overlay" @click="closeFormModal">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? 'Editar Jogo' : 'Novo Jogo' }}</h3>
          <button @click="closeFormModal" class="btn-close">&times;</button>
        </div>
        
        <form @submit.prevent="saveGame" class="modal-body">
          <div class="form-grid">
            <!-- Competition Selection -->
            <div class="form-group full-width">
              <label>Competição *</label>
              <select v-model="gameForm.competitionType" @change="onCompetitionTypeChange" class="form-select" required>
                <option value="">Selecionar competição</option>
                <option value="liga">Liga</option>
                <option value="torneio">Torneio</option>
                <option value="amigavel">Amigável</option>
              </select>
            </div>
            
            <div v-if="gameForm.competitionType && gameForm.competitionType !== 'amigavel'" class="form-group full-width">
              <label>{{ gameForm.competitionType === 'liga' ? 'Liga' : 'Torneio' }} *</label>
              <select v-model="gameForm.competitionId" @change="loadCompetitionTeams" class="form-select" required>
                <option value="">Selecionar {{ gameForm.competitionType }}</option>
                <option 
                  v-for="comp in availableCompetitions" 
                  :key="comp.id" 
                  :value="comp.id"
                >
                  {{ comp.nome }}
                </option>
              </select>
            </div>

            <!-- Teams Selection -->
            <div class="form-group">
              <label>Equipa Casa *</label>
              <select v-model="gameForm.equipa_casa" class="form-select" required>
                <option value="">Selecionar equipa</option>
                <option v-for="team in availableTeams" :key="team.id" :value="team.id">
                  {{ team.nome }}
                </option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Equipa Fora *</label>
              <select v-model="gameForm.equipa_fora" class="form-select" required>
                <option value="">Selecionar equipa</option>
                <option 
                  v-for="team in availableTeams" 
                  :key="team.id" 
                  :value="team.id"
                  :disabled="team.id === gameForm.equipa_casa"
                >
                  {{ team.nome }}
                </option>
              </select>
            </div>

            <!-- Date and Time -->
            <div class="form-group">
              <label>Data *</label>
              <input 
                v-model="gameForm.date" 
                type="date" 
                class="form-input" 
                required
              >
            </div>
            
            <div class="form-group">
              <label>Hora *</label>
              <input 
                v-model="gameForm.time" 
                type="time" 
                class="form-input" 
                required
              >
            </div>

            <!-- Location Details -->
            <div class="form-group">
              <label>Local</label>
              <input 
                v-model="gameForm.local" 
                type="text" 
                class="form-input" 
                placeholder="Cidade, região..."
              >
            </div>
            
            <div class="form-group">
              <label>Estádio</label>
              <input 
                v-model="gameForm.estadio" 
                type="text" 
                class="form-input" 
                placeholder="Nome do estádio..."
              >
            </div>

            <!-- Referee -->
            <div class="form-group">
              <label>Árbitro</label>
              <select v-model="gameForm.arbitro" class="form-select">
                <option value="">Selecionar árbitro</option>
                <option v-for="referee in referees" :key="referee.id" :value="referee.id">
                  {{ referee.nome }}
                </option>
              </select>
            </div>

            <!-- Scores (only for editing) -->
            <div v-if="isEditing" class="form-group">
              <label>Golos Casa</label>
              <input 
                v-model.number="gameForm.golo_casa" 
                type="number" 
                min="0" 
                class="form-input"
              >
            </div>
            
            <div v-if="isEditing" class="form-group">
              <label>Golos Fora</label>
              <input 
                v-model.number="gameForm.golo_fora" 
                type="number" 
                min="0" 
                class="form-input"
              >
            </div>

            <!-- Description -->
            <div class="form-group full-width">
              <label>Descrição</label>
              <textarea 
                v-model="gameForm.descricao" 
                class="form-textarea" 
                rows="3"
                placeholder="Informações adicionais sobre o jogo..."
              ></textarea>
            </div>
          </div>
        </form>
        
        <div class="modal-footer">
          <button type="button" @click="closeFormModal" class="btn btn-outline">Cancelar</button>
          <button @click="saveGame" class="btn btn-primary" :disabled="!isFormValid">
            {{ isEditing ? 'Atualizar' : 'Criar' }} Jogo
          </button>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import FullCalendar       from '@fullcalendar/vue3'
import dayGridPlugin      from '@fullcalendar/daygrid'
import timeGridPlugin     from '@fullcalendar/timegrid'
import interactionPlugin  from '@fullcalendar/interaction'
import ptLocale           from '@fullcalendar/core/locales/pt'

import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'


/* helper that shows toasts / catches errors the same way as the rest
 * of your SPA ---------------------------------------------------- */
const { wrap } = useAsyncAction()


/* --------------------------------------------------------------- */
/* small helpers                                                   */
/* --------------------------------------------------------------- */
function paged (path, limit = 100, offset = 0) {
  return `${path}?limit=${limit}&offset=${offset}`
}

/* generic “keep loading until next_offset == null” -------------- */
async function fetchPaginated (path, targetArray) {
  let off = 0
  targetArray.length = 0
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const { data } = await api.get(paged(path, 100, off))
      targetArray.push(...(data.results || []))
      if (data.next_offset == null) break
      off = data.next_offset
    } catch (err) {
      console.warn('Fetch failed for', path, err.response?.status)
     /* break the loop but pretend fetch succeeded with 0 rows       */
      return                                   // <-- exits gracefully
    }
  }
}

export default {
  name: 'GameCalendar',
  components: { FullCalendar },

  setup () {
    /* ------------------------------------------------------------- */
    /* reactive state                                                */
    /* ------------------------------------------------------------- */
    const loading             = ref(false)
    const currentView         = ref('dayGridMonth')
    const selectedCompetition = ref('')

    const backendUrl = process.env.VUE_APP_URL_BASE || 'http://localhost:8000'


    const showDetailsModal = ref(false)
    const showFormModal    = ref(false)
    const isEditing        = ref(false)
    const selectedGame     = ref(null)

    const games     = ref([])
    const ligas     = ref([])
    const torneios  = ref([])
    const teams     = ref([])
    const referees  = ref([])

    const availableTeams        = ref([])
    const availableCompetitions = ref([])
    const initializingForm = ref(false)

    const gameForm = reactive({
      competitionType: '',
      competitionId : '',
      equipa_casa   : '',
      equipa_fora   : '',
      date          : '',
      time          : '',
      local         : '',
      estadio       : '',
      arbitro       : '',
      golo_casa     : 0,
      golo_fora     : 0,
      descricao     : ''
    })

    /* ------------------------------------------------------------- */
    /* calendar options                                              */
    /* ------------------------------------------------------------- */
    const viewOptions = [
      { value: 'dayGridMonth', label: 'Mês' },
      { value: 'timeGridWeek', label: 'Semana' },
      { value: 'timeGridDay',  label: 'Dia' }
    ]

    const calendarEvents = computed(() =>
      games.value.map(g => ({
        id  : g.id,
        title: g.liga_id || g.torneio_id
          ? `${g.equipa_casa.nome} vs ${g.equipa_fora.nome}`
          : `[Amigável] ${g.equipa_casa.nome} vs ${g.equipa_fora.nome}`,
        start: g.data,
        extendedProps: { game: g },
        classNames: [
          'game-event',
          g.liga_id ? 'liga-event' : 'torneio-event'
        ]
      }))
    )

    const calendarOptions = computed(() => ({
      plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
      initialView: currentView.value,
      locale: ptLocale,
      headerToolbar: { left: 'prev,next today', center: 'title', right: '' },
      height: 'auto',
      events: calendarEvents.value,
      eventClick: ({ event }) => { selectedGame.value = event.extendedProps.game; showDetailsModal.value = true },
      dateClick : ({ dateStr }) => {
        resetForm()
        gameForm.date = dateStr
        gameForm.time = '00:00' // or any default time you want
        showFormModal.value = true
      },
      eventDidMount: ({ el, event }) => {
        el.classList.add(`event-${event.extendedProps.game.liga_id ? 'liga' : 'torneio'}`)
      }
    }))

    const isFormValid = computed(() =>
      gameForm.competitionType &&
      (
        (gameForm.competitionType === 'amigavel') ||
        (gameForm.competitionId)
      ) &&
      gameForm.equipa_casa &&
      gameForm.equipa_fora &&
      gameForm.date && gameForm.time &&
      gameForm.equipa_casa !== gameForm.equipa_fora
    )

    /* ------------------------------------------------------------- */
    /* LOADERS                                                       */
    /* ------------------------------------------------------------- */
   const loadInitialData = async () => {
      loading.value = true
      
      Promise.allSettled([
        fetchPaginated('/app/liga/',    ligas.value),
        fetchPaginated('/app/torneio/', torneios.value),
        fetchPaginated('/app/equipa/pagination/', teams.value),
        fetchPaginated('/app/arbitro/', referees.value)
      ]).then(() => console.log('master-data finished'))
      await loadGames()
      loading.value = false
    }

    const loadGames = async () => {
      console.log('Loading games...')
      loading.value = true
      let path = '/app/jogo/'
      if (selectedCompetition.value) {
        const [type, id] = selectedCompetition.value.split('-')
        path += `?${type}_id=${id}`
      }
      await fetchPaginated(path, games.value)
      loading.value = false
      console.log('Games loaded:', games.value)
    }

    const loadCompetitionTeams = () => wrap(async () => {
      if (gameForm.competitionType === 'amigavel') {
        availableTeams.value = teams.value
        return
      }
      if (!gameForm.competitionId) return
      const endpoint = gameForm.competitionType === 'liga'
        ? `/app/liga/${gameForm.competitionId}/equipas/`
        : `/app/torneio/${gameForm.competitionId}/equipas/`
      await fetchPaginated(endpoint, availableTeams.value)
    })

    /* ------------------------------------------------------------- */
    /* SAVE / UPDATE / DELETE                                        */
    /* ------------------------------------------------------------- */
    const saveGame = () => wrap(async () => {
      if (!isFormValid.value) return
      loading.value = true

      const payload = {
        equipa_casa_id : gameForm.equipa_casa,
        equipa_fora_id : gameForm.equipa_fora,
        data        : `${gameForm.date}T${gameForm.time}`,
        local       : gameForm.local,
        estadio     : gameForm.estadio,
        arbitro_id  : gameForm.arbitro || null,
        descricao   : gameForm.descricao,
        competicao: gameForm.competitionType,
      }
      console.log('Saving game with payload:', payload)
      if (gameForm.competitionType !== 'amigavel') {
        payload[`${gameForm.competitionType}_id`] = gameForm.competitionId
      }
      if (isEditing.value) {
        payload.golo_casa = gameForm.golo_casa
        payload.golo_fora = gameForm.golo_fora
      }

      const url = isEditing.value
        ? `/app/jogo/editar/${selectedGame.value.id}/`
        : '/app/jogo/registar/'

      await (isEditing.value ? api.put(url, payload) : api.post(url, payload))
      await loadGames()
      closeFormModal()
      loading.value = false
    })

    const confirmDelete = () => wrap(async () => {
      if (!confirm('Tem certeza que deseja eliminar este jogo?')) return
      loading.value = true
      await api.delete(`/app/jogo/eliminar/${selectedGame.value.id}/`)
      await loadGames()
      closeDetailsModal()
      loading.value = false
    })

    /* ------------------------------------------------------------- */
    /* UTILS                                                         */
    /* ------------------------------------------------------------- */
    function resetForm () {
      Object.assign(gameForm, {
        competitionType: '', competitionId: '',
        equipa_casa: '', equipa_fora: '',
        date: '', time: '',
        local: '', estadio: '', arbitro: '',
        golo_casa: 0, golo_fora: 0,
        descricao: ''
      })
      availableTeams.value = []
      availableCompetitions.value = []
    }

    async function populateForm (g) {
      initializingForm.value = true        // ➊ silencia o watcher

      const type = g.liga_id ? 'liga' : g.torneio_id ? 'torneio' : 'amigavel'
      const comp = g.liga_id || g.torneio_id || 0

      gameForm.competitionType = type
      gameForm.competitionId   = comp

      // prepara listas para o <select> – não dispara o watcher!
      availableCompetitions.value =
            type === 'liga'    ? ligas.value
          : type === 'torneio' ? torneios.value
          : []

      await loadCompetitionTeams()         // carrega equipas certas
      await nextTick()                     // DOM já tem <option>s

      /* agora que há opções, podemos preencher */
      gameForm.equipa_casa = g.equipa_casa.id
      gameForm.equipa_fora = g.equipa_fora.id

      const [date, time] = g.data.split('T')
      gameForm.date = date
      gameForm.time = time?.slice(0,5) ?? ''

      gameForm.local      = g.local      ?? ''
      gameForm.estadio    = g.estadio    ?? ''
      gameForm.arbitro    = g.arbitro?.id?? ''
      gameForm.golo_casa  = g.golo_casa  ?? 0
      gameForm.golo_fora  = g.golo_fora  ?? 0
      gameForm.descricao  = g.descricao  ?? ''

      initializingForm.value = false       // ➋ volta ao normal
    }

    /* ------------------------------------------------------------- */
    /* handlers for modal / view buttons                             */
    /* ------------------------------------------------------------- */
    const changeView      = v => (currentView.value = v)
    const openCreateModal = () => {
      resetForm()
      isEditing.value = false
      showFormModal.value = true
    }
    const openEditModal = async () => {
      await populateForm(selectedGame.value)
      isEditing.value = true
      showDetailsModal.value = false
      showFormModal.value = true
    }
    const closeDetailsModal = () => { showDetailsModal.value = false; selectedGame.value = null }
    const closeFormModal = () => {
      showFormModal.value = false
      isEditing.value = false   // <-- add this line
      resetForm()
    }
    const onCompetitionTypeChange = () => {
      gameForm.competitionId = ''
      availableCompetitions.value = gameForm.competitionType === 'liga' ? ligas.value : torneios.value
      availableTeams.value = []
      loadCompetitionTeams() // <-- add this line
    }

    /* ------------------------------------------------------------- */
    /* watchers / lifecycle                                          */
    /* ------------------------------------------------------------- */
    watch(
      () => gameForm.competitionType,

      () => { if (!initializingForm.value) onCompetitionTypeChange() }
    )
    onMounted(loadInitialData)

    /* ------------------------------------------------------------- */
    /* expose to template                                            */
    /* ------------------------------------------------------------- */
    return {
      /* state */
      loading, currentView, selectedCompetition,
      showDetailsModal, showFormModal, isEditing, selectedGame, 
      games, ligas, torneios, teams, referees,
      availableTeams, availableCompetitions, gameForm,backendUrl,

      /* computed */
      calendarOptions, calendarEvents, isFormValid, viewOptions,

      /* methods (template) */
      loadGames, loadCompetitionTeams,
      changeView, openCreateModal, openEditModal,
      closeDetailsModal, closeFormModal,
      onCompetitionTypeChange, saveGame, confirmDelete,
      formatDateTime: dt => new Date(dt).toLocaleString('pt-PT', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }),
      getCompetitionName: g => {
        if (g.liga_id) {
          const l = ligas.value.find(x => x.id === g.liga_id)
          return l ? `Liga: ${l.nome}` : 'Liga'
        }
        if (g.torneio_id) {
          const t = torneios.value.find(x => x.id === g.torneio_id)
          return t ? `Torneio: ${t.nome}` : 'Torneio'
        }
        return 'Amigável'
      }
    }
  }
}
</script>


<style scoped>
.game-calendar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  
}

/* Header Styles */
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.competition-selector {
  min-width: 200px;
}

.view-controls {
  display: flex;
  gap: 5px;
}

/* Form Elements */
.form-select,
.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

/* Button Styles */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-outline {
  background: transparent;
  border: 1px solid #ddd;
  color: #333;
}

.btn-outline:hover,
.btn-outline.active {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-text {
  display: inline;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #333;
}

/* Calendar Styles */
.calendar-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.custom-calendar {
  min-height: 600px;
}

/* Custom event styling */
:deep(.fc-event) {
  border: none !important;
  border-radius: 4px !important;
  padding: 2px 6px !important;
  font-size: 12px !important;
  cursor: pointer !important;
}

:deep(.liga-event) {
  background: #007bff !important;
  color: white !important;
}

:deep(.torneio-event) {
  background: #28a745 !important;
  color: white !important;
}

:deep(.fc-event:hover) {
  opacity: 0.8 !important;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

/* Game Details Styles */
.game-details {
  text-align: center;
}

.teams-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.team {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.team img {
  width: 60px;
  height: 60px;
  object-fit: contain;
  border-radius: 50%;
}

.team h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.score {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}

.vs-separator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  margin: 0 20px;
}

.vs-separator span {
  font-weight: bold;
  color: #666;
}

.match-time {
  font-size: 12px;
  color: #666;
}

.game-info {
  text-align: left;
}

.info-row {
  display: flex;
  margin-bottom: 10px;
  align-items: flex-start;
}

.info-row .label {
  font-weight: 600;
  min-width: 100px;
  color: #666;
}

.info-row p {
  margin: 0;
}

/* Form Styles */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

/* Loading Styles */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 768px) {
  .game-calendar-container {
    padding: 10px;
  }
  
  .calendar-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: space-between;
  }
  
  .view-controls {
    justify-content: center;
  }
  
  .btn-text {
    display: none;
  }
  
  .teams-section {
    flex-direction: column;
    gap: 20px;
  }
  
  .vs-separator {
    margin: 0;
    order: -1;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    margin: 10px;
    max-height: calc(100vh - 20px);
  }
  
  .team img {
    width: 50px;
    height: 50px;
  }
  
  .score {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .competition-selector {
    min-width: auto;
    flex: 1;
  }
  
  .info-row {
    flex-direction: column;
  }
  
  .info-row .label {
    min-width: auto;
    margin-bottom: 2px;
  }
}
</style>