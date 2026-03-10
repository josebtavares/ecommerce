<template>
  <div class="flex flex-col items-center  bg-[#1c1c1e]">
    <h1 class="text-2xl text-white font-bold mr-auto ml-[1.3rem] mt-[2rem]">Calendário de Jogos</h1>

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
              <option value="amigavel" class=" font-bold">Amigáveis</option>
            </select>
          </div>

          <button @click="openCreateCompetitionModal" class="btn btn-primary-2 bg-red-500">
            <i class="fa-solid fa-circle-plus" style="color: #ffffff;"></i>
            <span class="btn-text">Nova Competição</span>
          </button>
          
          <button @click="openCreateModal" class="btn btn-primary">
            <i class="fa-solid fa-circle-plus" style="color: #ffffff;"></i>
            <span class="btn-text">Novo Jogo</span>
          </button>
        </div>
        
        <div class="view-controls">

          <input
            v-model="searchQuery"
            @keyup.enter="loadGames"
            @input="onSearchInput"
            type="text"
            class="form-input"
            style="width: 200px"
            placeholder="Pesquisar.."
          />
          
          <!-- ...inside <template>... -->
          <div class="goto-month-controls flex gap-2 items-center">
            <!-- Year input and select arrow -->
            <div style="display: flex; flex-direction: column; align-items: flex-start; position: relative;">
              <div style="display: flex; align-items: center;">
                <input
                  type="text"
                  v-model.number="gotoYear"
                  :min="minYear"
                  :max="maxYear"
                  class="form-input"
                  style="width:90px;display:inline-block;"
                  placeholder="Ano"
                  list="year-list"
                />
                <button
                  type="button"
                  class="btn btn-outline"
                  style="padding: 0 8px; margin-left: 2px; height: 36px; display: flex; align-items: center;"
                  @click="showYearDropdown = !showYearDropdown"
                  tabindex="-1"
                >
                  ▼
                </button>
              </div>
              <div
                v-if="showYearDropdown"
                class="dropdown-list"
                style="position: absolute; left: 0; top: 100%; z-index: 10; background: #262629; border: 1px solid #3d3d40; border-radius: 6px; max-height: 200px; overflow-y: auto; min-width: 100%; margin-top: 0.5rem"
              >
                <div class="dropdown-item"
                  v-for="year in yearOptions"
                  :key="year"
                  @click="selectYear(year)"
                  style="padding: 6px 16px; cursor: pointer; color: #fff; background-color: #3d3d40; border-bottom: 1px solid #4d4d50;"
                  @mousedown.prevent
                >
                  {{ year }}
                </div>
              </div>
            </div>

            <!-- Month input and select arrow -->
            <div style="display: flex; flex-direction: column; align-items: flex-start; position: relative;">
              <div style="display: flex; align-items: center;">
                <input
                  type="text"
                  v-model.number="gotoMonthInput"
                  min="1"
                  max="12"
                  class="form-input"
                  style="width:70px;display:inline-block;"
                  placeholder="Mês"
                  list="month-list"
                  @change="syncGotoMonth"
                />
                <button
                  type="button"
                  class="btn btn-outline"
                  style="padding: 0 8px; margin-left: 2px; height: 36px; display: flex; align-items: center;"
                  @click="showMonthDropdown = !showMonthDropdown"
                  tabindex="-1"
                >
                  ▼
                </button>
              </div>
              <div
                v-if="showMonthDropdown"
                class="dropdown-list"
                style="position: absolute; left: 0; top: 100%; z-index: 10; background: #262629; border: 1px solid #3d3d40; border-radius: 6px; max-height: 200px; overflow-y: auto; min-width: 100%; margin-top: 0.5rem;"
              >
                <div class="dropdown-item"
                  v-for="(m, idx) in monthOptions"
                  :key="idx"
                  @click="selectMonth(idx)"
                  style="padding: 6px 16px; cursor: pointer; color: #fff; background-color: #3d3d40; border-bottom: 1px solid #4d4d50;"
                  @mousedown.prevent
                >
                  {{ m }}
                </div>
              </div>
            </div>

            <button class="btn btn-outline" @click="goToMonth">Ver</button>
          </div>


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

      <!-- Create Competicao Modal -->
      <div v-if="showCompeticaoModal" class="modal-overlay" @click="closeCompeticaoModal">
        <div class="modal-content modal-large" @click.stop>
          <div class="modal-header">
            <h3>{{ isEditingCompetition ? 'Editar Competição' : 'Nova Competição' }}</h3>
            <button @click="closeCompeticaoModal" class="btn-close">&times;</button>
          </div>
          
          <form @submit.prevent="saveCompetition" class="modal-body">
            <div class="form-grid">
              <div class="form-group full-width">
                <label>Nome da Competição *</label>
                <input 
                  v-model="competitionForm.nome" 
                  type="text" 
                  class="form-input" 
                  placeholder="Nome da competição..." 
                  required
                >
              </div>
              
              <div class="form-group full-width">
                <label>Tipo de Competição *</label>
                <select v-model="competitionForm.tipo" class="form-select" required>
                  <option value="">Selecionar tipo</option>
                  <option value="liga">Liga</option>
                  <option value="torneio">Torneio</option>
                </select> 
              </div>

              <div class="form-group full-width">
                <label>Descrição</label>
                <textarea 
                  v-model="competitionForm.descricao" 
                  class="form-textarea" 
                  rows="3"
                  placeholder="Informações adicionais sobre a competição..."
                ></textarea>
              </div>

              <div class="form-group

                full-width">
                
                <div class="form-group full-width">
                  <label>Equipas Participantes</label>
                  <Multiselect
                    v-model="competitionForm.equipas"
                    :options="teams"
                    :multiple="true"
                    :close-on-select="false"
                    :clear-on-select="false"
                    :preserve-search="true"
                    placeholder="Escolha as equipas..."
                    label="nome"
                    track-by="id"
                    :preselect-first="false"
                  />
                </div>
              </div>
            </div>
          </form>

          <div class="modal-footer">
            <button type="button" @click="closeCompeticaoModal" class="btn btn-secondary">Cancelar</button>
            <button type="submit" @click="saveCompetition" class="btn btn-primary">
              {{ isEditingCompetition ? 'Atualizar' : 'Criar' }}
            </button>
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
import Multiselect from '@/components/multiSelect/multiSelect.vue'
import 'vue-multiselect/dist/vue-multiselect.min.css'
import {toast} from 'vue3-toastify' 


/* helper that shows toasts / catches errors the same way as the rest
 * of your SPA ---------------------------------------------------- */
const { wrap } = useAsyncAction()


/* --------------------------------------------------------------- */
/* small helpers                                                   */
/* --------------------------------------------------------------- */
function paged (path, limit = 100, offset = 0) {
  const sep = path.includes('?') ? '&' : '?'     // <-- 1 linha nova
  return `${path}${sep}limit=${limit}&offset=${offset}`
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
  components: { FullCalendar, Multiselect },
  emits: ['gameUpdated', 'gameCreated', 'gameDeleted'],
  

  setup () {
    /* ------------------------------------------------------------- */
    /* reactive state                                                */
    /* ------------------------------------------------------------- */

    
    
    const loading             = ref(false)
    const currentView         = ref('dayGridMonth')
    const selectedCompetition = ref('')

    const backendUrl = process.env.VUE_APP_URL_BASE || 'http://localhost:8000'

    const searchQuery = ref('')
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

    const calendar = ref(null)

    const now = new Date()
    const minYear = now.getFullYear() - 10
    const maxYear = now.getFullYear() + 10
    const gotoYear = ref(now.getFullYear())
    const gotoMonth = ref(now.getMonth()) // 0-based for calendar
    const gotoMonthInput = ref(now.getMonth() + 1) // 1-based for input

    watch(gotoMonth, (val) => {
      // keep input in sync if changed by select
      gotoMonthInput.value = val + 1
    })

    function syncGotoMonth() {
      // when user types month, update gotoMonth (0-based)
      if (gotoMonthInput.value >= 1 && gotoMonthInput.value <= 12) {
        gotoMonth.value = gotoMonthInput.value - 1
      }
    }

    const yearOptions = computed(() => {
      const current = now.getFullYear()
      return Array.from({length: 21}, (_, i) => current - 10 + i)
    })
    const monthOptions = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]


    const showYearDropdown = ref(false)
    const showMonthDropdown = ref(false)

    function selectYear(year) {
      gotoYear.value = year
      showYearDropdown.value = false
    }
    function selectMonth(idx) {
      gotoMonthInput.value = idx + 1
      syncGotoMonth()
      showMonthDropdown.value = false
    }
  

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

    const showCompeticaoModal = ref(false)
    const isEditingCompetition = ref(false)
    const competitionForm = reactive({
      id: null,
      nome: '',
      tipo: '',
      descricao: '',
      equipas: []
    })

    function openCreateCompetitionModal() {
      competitionForm.id = null
      competitionForm.nome = ''
      competitionForm.tipo = ''
      competitionForm.descricao = ''
      competitionForm.equipas = []
      isEditingCompetition.value = false
      showCompeticaoModal.value = true
    }
    function closeCompeticaoModal() {
      showCompeticaoModal.value = false
    }

    const saveCompetition = () => wrap(async () => {
      if (!competitionForm.nome || !competitionForm.tipo){
        toast.warning('Por favor, preencha o nome e o tipo da competição.', {
              position: toast.POSITION.TOP_RIGHT,
              autoClose: 2000,
             
        })
        return 
      }
      if (competitionForm.tipo !== 'liga' && competitionForm.tipo !== 'torneio') {
        toast.warning('Por favor, selecione um tipo de competição válido.', {
              position: toast.POSITION.TOP_RIGHT,
              autoClose: 2000,
             
        })
        return
      }
      if (competitionForm.equipas.length === 0) {
        toast.warning('Por favor, adicione pelo menos uma equipa à competição.', {
              position: toast.POSITION.TOP_RIGHT,
              autoClose: 2000,
             
        })
        return
      }
      if (competitionForm.equipas.length < 2) {
        toast.warning('A competição deve ter pelo menos duas equipas.', {
              position: toast.POSITION.TOP_RIGHT,
              autoClose: 2000,
             
        })
        return
      }

      loading.value = true
      const payload = {
        nome: competitionForm.nome,
        descricao: competitionForm.descricao,
        equipes: competitionForm.equipas.map(e => e.id) // send only IDs
      }
      let url = ''
      if (competitionForm.tipo === 'liga') {
        url = '/app/liga/registar/'
      } else if (competitionForm.tipo === 'torneio') {
        url = '/app/torneio/registar/'
      } else {
        loading.value = false
        return
      }
      await api.post(url, payload)
      await loadInitialData()
      toast.success(`Competição ${isEditingCompetition.value ? 'atualizada' : 'criada'} com sucesso!`, {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 2000,
      })
      showCompeticaoModal.value = false
      loading.value = false
    })

    /* ------------------------------------------------------------- */
    /* calendar options                                              */
    /* ------------------------------------------------------------- */
    const viewOptions = [
      // { value: 'dayGridMonth', label: 'Mês' },
      // { value: 'timeGridWeek', label: 'Semana' },
      // { value: 'timeGridDay',  label: 'Dia' },
      // { value: 'multiYear',    label: 'Ano' }

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
          g.liga_id ? 'liga-event' : (g.torneio_id ? 'torneio-event' : 'amigavel-event')
          
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
      },

      views: {
        multiYear: {
          type: 'dayGridYear', 
          duration: { years: 1 },
          buttonText: 'Ano'
        }
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
      loading.value = true
      let path = '/app/jogo/'
      const params = []

      if (selectedCompetition.value) {
        if (selectedCompetition.value === 'amigavel') {
          params.push('amigavel=1')
        } else {
          const [type, id] = selectedCompetition.value.split('-')
          params.push(`${type}_id=${id}`)
        }
      }
      if (searchQuery.value && searchQuery.value.trim() !== '') {
        params.push('q=' + encodeURIComponent(searchQuery.value.trim()))
      }
      if (params.length) {
        path += '?' + params.join('&')
      }
      await fetchPaginated(path, games.value)
      loading.value = false
    }

    // Optional: debounce search for better UX
    let searchTimeout = null
    function onSearchInput() {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        loadGames()
      }, 400)
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

    function goToMonth() {
      const year = gotoYear.value
      const month = gotoMonth.value
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-01`
      if (calendar.value && calendar.value.getApi) {
        calendar.value.getApi().gotoDate(dateStr)
        calendar.value.getApi().changeView('dayGridMonth')
      }
    }

    /* ------------------------------------------------------------- */
    /* SAVE / UPDATE / DELETE                                        */
    /* ------------------------------------------------------------- */
    const saveGame = () => wrap(async () => {
      if (!isFormValid.value) return
      loading.value = true
      const localDt = new Date(`${gameForm.date}T${gameForm.time}`)

      const payload = {
        equipa_casa_id : gameForm.equipa_casa,
        equipa_fora_id : gameForm.equipa_fora,
        data: localDt.toISOString(),
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
      if( isEditing.value) {
        toast.success('Jogo atualizado com sucesso!', {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 2000,
        })
        // Emit event for parent component if needed
        this.$emit('gameUpdated', payload)
      } else {
        toast.success('Jogo criado com sucesso!', {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 2000,
        })
      }
    })

    const confirmDelete = () => wrap(async () => {
      //if (!confirm('Tem certeza que deseja eliminar este jogo?')) return
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

      const local = new Date(g.data) // g.data vem em UTC + Z
      gameForm.date = local.toISOString().slice(0,10)   // YYYY-MM-DD
      gameForm.time = local.toTimeString().slice(0,5) 

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
    const changeView = v => {
      currentView.value = v
      if (calendar.value && calendar.value.getApi) {
        calendar.value.getApi().changeView(v)
      }
    }
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
      availableTeams, availableCompetitions, gameForm,backendUrl,calendar,
      
      /* computed */
      calendarOptions, calendarEvents, isFormValid, viewOptions,
      gotoYear, gotoMonth, gotoMonthInput, minYear, maxYear, yearOptions, monthOptions, goToMonth, syncGotoMonth,
      showYearDropdown, showMonthDropdown, selectYear, selectMonth,
      searchQuery,

      showCompeticaoModal,
      isEditingCompetition,
      competitionForm,
      openCreateCompetitionModal,
      closeCompeticaoModal,
      saveCompetition,
      
      onSearchInput,

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
/* ========================================================= */
/*  ALWAYS-ON DARK THEME for GameCalendar.vue                */
/*  (no toggle, no variables – just dark colours)            */
/* ========================================================= */

.game-calendar-container {
  max-width: 100vw;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1c1c1e;         /* dark BG */
  color: #000000;              /* light text */
}

/* ------------ header / buttons --------------------------- */
.calendar-header { 
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; flex-wrap: wrap; gap: 15px;
}

.header-controls,
.view-controls       { display: flex; align-items: center; gap: 15px; flex-wrap: wrap;  }

.competition-selector { min-width: 200px; }

/* generic button */
.btn {
  padding: 8px 16px; border: 1px solid transparent;
  border-radius: 6px; font-size: 14px; font-weight: 500;
  display: inline-flex; align-items: center; gap: 6px;
  cursor: pointer; transition: background .2s;
}

/* primary – blue */
.btn-primary  { background:#0d6efd; color:#fff; }
.btn-primary:hover { background:#2a7eff; }

.btn-primary-2  { background:#ff1515; color:#fff; }
.btn-primary-2:hover { background:#ff3f3f; }

/* secondary – grey */
.btn-secondary { background:#3d3d40; color:#fff; }
.btn-secondary:hover { background:#56565a; }

/* danger – red */
.btn-danger { background:#c92a2a; color:#fff; }
.btn-danger:hover { background:#e03131; }

/* outline (for view switch / cancel) */
.btn-outline{
  background:transparent; color:#e5e5e7; border-color:#3d3d40;
}
.btn-outline:hover,
.btn-outline.active{
  background:#2b2b2e; border-color:#0d6efd; color:#0d6efd;
}

.btn:disabled{ opacity:.55; cursor:not-allowed; }

/* X icon button */
.btn-close{
  background:transparent; border:0; font-size:24px;
  width:30px;height:30px; display:flex;align-items:center;justify-content:center;
  color:#9e9ea0; cursor:pointer;
}
.btn-close:hover{ color:#fff; }

/* ------------ form elements ------------------------------ */
.form-select,
.form-input,
.form-textarea{
  width:100%; padding:8px 12px; border:1px solid #3d3d40;
  border-radius:6px; font-size:14px; background:#2b2b2e; color:#e5e5e7;
}
.form-select:focus,
.form-input:focus,
.form-textarea:focus{
  outline:none; border-color:#0d6efd; box-shadow:0 0 0 2px rgba(13,110,253,.35);
}

/* ------------ calendar wrapper --------------------------- */
.calendar-wrapper{
  background:#2b2b2e; border-radius:8px;
  box-shadow:0 2px 10px rgba(0,0,0,.55); overflow:hidden;
}
.custom-calendar{ min-height:600px; }

/* FullCalendar dark overrides */
:deep(.fc){
  --fc-page-bg:#1c1c1e;
  --fc-neutral-text-color:#b5b5b7;
  --fc-border-color:#3d3d40;
}

/* weekday headers “Seg Ter Qua …” */
:deep(.fc-col-header-cell) {
  background: #2f2f33 !important;   /* a lighter grey strip */
  color: #ffffff !important;        /* white text           */
  border-color: #3d3d40 !important; /* keep grid border     */
}

/* small number in top-right of each cell */
:deep(.fc-daygrid-day-number) {
  color: #ffffff !important;        /* white date numerals  */
}

/* make sure the grid itself keeps the dark border */
:deep(.fc-theme-standard .fc-scrollgrid),
:deep(.fc-theme-standard td),
:deep(.fc-theme-standard th) {
  border-color: #3d3d40 !important;
}

:deep(.fc-toolbar-title){ color:#e5e5e7 !important; }
:deep(.fc-button){
  background:#3d3d40; border:1px solid #3d3d40; color:#e5e5e7;
}
:deep(.fc-button:hover){ background:#56565a; }
:deep(.fc-daygrid-day-frame){ background:#1c1c1e; }

:deep(.liga-event){ background:#0d6efd !important; color:#fff !important; }
:deep(.torneio-event){ background:#22c55e !important; color:#fff !important; }
:deep(.amigavel-event){ background:#e03131 !important; color:#fff !important; }
:deep(.fc-event:hover){ filter:brightness(1.15); }

/* ------------ modal -------------------------------------- */
.modal-overlay{
  position:fixed; inset:0; background:rgba(0,0,0,.6);
  display:flex; align-items:center; justify-content:center; padding:20px; z-index:1000;
}
.modal-content{
  background:#262629; color:#e5e5e7;
  border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,.7);
  max-width:500px; width:100%; max-height:90vh; overflow-y:auto;
}
.modal-large{ max-width:800px; }
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  
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
  
}

.form-grid{ display:grid; grid-template-columns:1fr 1fr; gap:15px; }
.form-group.full-width{ grid-column:1/-1; }

/* ------------ game details ------------------------------- */
.teams-section{
  display:flex; justify-content:space-between; align-items:center;
  margin-bottom:30px; padding:20px; background:#1f1f21; border-radius:8px;
}
.team{ flex:1; display:flex; flex-direction:column; align-items:center; gap:10px; }
.team img{ width:60px;height:60px; object-fit:contain; border-radius:50%; }
.score{ font-size:24px; font-weight:bold; color:#0d6efd; }
.vs-separator span{display:flex; flex-direction: column; align-items: center; font-weight:bold; color:#b5b5b7; }
.match-time{ font-size:12px; color:#b5b5b7; }

.info-row{ display:flex; margin-bottom:10px; }
.info-row .label{ min-width:100px; font-weight:600; color:#b5b5b7; }

/* ------------ loading spinner ---------------------------- */
.loading-overlay{
  position:fixed; inset:0; background:rgba(0,0,0,.8);
  display:flex; align-items:center; justify-content:center; z-index:2000;
}
.spinner{
  width:40px;height:40px; border:4px solid #3d3d40; border-top-color:#0d6efd;
  border-radius:50%; animation:spin 1s linear infinite;
}
@keyframes spin{ to{ transform:rotate(360deg); } }

/* ------------ responsive tweaks (kept) ------------------- */
@media(max-width:768px){
  .game-calendar-container{ padding:10px; }
  .calendar-header{ flex-direction:column; align-items:stretch; }
  .btn-text{ display:none; }
  .teams-section{ flex-direction:column; gap:20px; }
  .vs-separator{ order:-1; margin:0; }
  .form-grid{ grid-template-columns:1fr; }
  .modal-content{ margin:10px; max-height:calc(100vh - 20px); }
  .team img{ width:50px;height:50px; }
  .score{ font-size:20px; }
}

@media(max-width:480px){
  .competition-selector{ min-width:auto; flex:1; }
  .info-row{ flex-direction:column; }
  .info-row .label{ margin-bottom:2px; min-width:auto; }
}


/* Add hover effect for year/month dropdown items */
.dropdown-item {
  background-color: #4d4d50;
}

.form-input {
  /* already styled, but you can add margin if needed */
  margin-right: 10px;
}

:deep(.multiselect) {
  background: #2b2b2e;
  color: #e5e5e7;
  border: 1px solid #3d3d40;
  border-radius: 6px;
}
:deep(.multiselect__input) {
  background: #2b2b2e;
  color: #e5e5e7;
}
:deep(.multiselect__content) {
  background: #262629;
  color: #e5e5e7;
}
:deep(.multiselect__option) {
  background: #262629;
  color: #e5e5e7;
}
:deep(.multiselect__option--highlight) {
  background: #0d6efd;
  color: #fff;
}
:deep(.multiselect__tag) {
  background: #0d6efd;
  color: #000000;
  border-radius: 4px;
}
:deep(.multiselect__placeholder) {
  color: #b5b5b7;
}

</style>


