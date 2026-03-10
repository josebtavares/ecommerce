<template>
  <div class="competition-standings">
    <!-- Header with tabs -->
    <div class="standings-header">
        <h1 class="text-2xl text-white font-bold mr-auto mt-[2rem]">Resultados</h1>
        <!-- refresh button -->
        <button 
          @click="reload" 
          class="refresh-button cursor-pointer"
          :disabled="loading"
        >
          <i class="fa-solid fa-arrows-rotate fa-xl" style="color: #ffffff;"></i>
          <span v-if="loading">
            <span class="loading-spinner"></span>
            

          </span>
          <span v-else></span>
        </button>

      <!-- Competition Type Tabs -->
      <div class="tab-container">
        <button 
          @click="activeTab = 'liga'"
          :class="['tab-button', { active: activeTab === 'liga' }]"
        >
          <i class="icon-trophy"></i>
          Ligas
        </button>
        <button 
          @click="activeTab = 'torneio'"
          :class="['tab-button', { active: activeTab === 'torneio' }]"
        >
          <i class="icon-award"></i>
          Torneios
        </button>
      </div>
    </div>

    <!-- Competition Selector -->
    <div class="competition-selector">
      <div class="selector-group">
        <label :for="`${activeTab}-select`" class="selector-label">
          Selecionar {{ activeTab === 'liga' ? 'Liga' : 'Torneio' }}:
        </label>
        <select 
          :id="`${activeTab}-select`"
          v-model="selectedCompetition" 
          @change="loadStandings"
          class="competition-select"
          :disabled="loading"
        >
          <option value="">
            -- Escolher {{ activeTab === 'liga' ? 'Liga' : 'Torneio' }} --
          </option>
          <option 
            v-for="competition in currentCompetitions" 
            :key="competition.id" 
            :value="competition.id"
          >
            {{ competition.nome }}
            <span v-if="competition.data_inicio && competition.data_fim" class="competition-dates">
              ({{ formatDate(competition.data_inicio) }} - {{ formatDate(competition.data_fim) }})
            </span>
          </option>
        </select>
      </div>

      <!-- Competition Info -->
      <div v-if="selectedCompetitionData" class="competition-info">
        <div class="info-card">
          <h3>{{ selectedCompetitionData.nome }}</h3>
          <p v-if="selectedCompetitionData.descricao" class="description">
            {{ selectedCompetitionData.descricao }}
          </p>
          <div class="competition-meta">
            <span v-if="selectedCompetitionData.data_inicio" class="meta-item">
              <i class="icon-calendar"></i>
              Início: {{ formatDate(selectedCompetitionData.data_inicio) }}
            </span>
            <span v-if="selectedCompetitionData.data_fim" class="meta-item">
              <i class="icon-calendar"></i>
              Fim: {{ formatDate(selectedCompetitionData.data_fim) }}
            </span>
            <span class="meta-item">
              <i class="icon-users"></i>
              {{ standings.length }} equipas
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Carregando classificações...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-container">
      <div class="error-message">
        <i class="icon-alert-circle"></i>
        <p>{{ error }}</p>
        <button @click="loadStandings" class="retry-button">Tentar Novamente</button>
      </div>
    </div>

    <!-- Standings Table -->
    <div v-if="!loading && !error && standings.length > 0" class="standings-container">
      <div class="table-wrapper">
        <table class="standings-table">
          <thead>
            <tr>
              <th class="position-col">Pos</th>
              <th class="team-col">Equipa</th>
              <th class="points-col">Pts</th>
              <th class="games-col">J</th>
              <th class="wins-col">V</th>
              <th class="draws-col">E</th>
              <th class="losses-col">D</th>
              <th class="goals-col">GM</th>
              <th class="goals-col">GS</th>
              <th class="goals-col">±</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="(team) in standings" 
              :key="team.id"
              :class="getRowClass(team.posicao)"
            >
              <td class="position-cell">
                <span class="position-number">{{ team.posicao }}</span>
                <div class="position-indicator" :class="getPositionClass(team.posicao)"></div>
              </td>
              <td class="team-cell">
                <div class="team-info">
                  <img 
                    :src="backendUrl+team.equipa.foto || backend + '/media/utilizadores/default.png'"
                    :alt="team.equipa.nome"
                    class="team-logo"
                    @error="handleImageError"
                  >
                  <div class="team-details">
                    <span class="team-name">{{ team.equipa.nome }}</span>
                    <span v-if="team.equipa.cidade" class="team-city">{{ team.equipa.cidade }}</span>
                  </div>
                </div>
              </td>
              <td class="points-cell">
                <strong>{{ team.pontos }}</strong>
              </td>
              <td class="games-cell">{{ team.vitorias + team.empates + team.derrotas }}</td>
              <td class="wins-cell">{{ team.vitorias }}</td>
              <td class="draws-cell">{{ team.empates }}</td>
              <td class="losses-cell">{{ team.derrotas }}</td>
              <td class="goals-cell">{{ team.golos_marcados }}</td>
              <td class="goals-cell">{{ team.golos_sofridos }}</td>
              <td class="goals-diff-cell">
                <span :class="getGoalDiffClass(team.golos_marcados - team.golos_sofridos)">
                  {{ formatGoalDiff(team.golos_marcados - team.golos_sofridos) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Legend -->
      <div class="table-legend">
        <div class="legend-item">
          <div class="legend-color champion"></div>
          <span>Campeão</span>
        </div>
        <div class="legend-item">
          <div class="legend-color qualification"></div>
          <span>Qualificação Europeia</span>
        </div>
        <div class="legend-item">
          <div class="legend-color relegation"></div>
          <span>Despromoção</span>
        </div>
      </div>

      <!-- Statistics Summary -->
      <div class="stats-summary">
        <div class="stat-card">
          <div class="stat-value">{{ getTotalGoals() }}</div>
          <div class="stat-label">Total de Golos</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ getAverageGoalsPerGame().toFixed(1) }}</div>
          <div class="stat-label">Golos por Jogo</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ getTopScorer().golos_marcados }}</div>
          <div class="stat-label">Melhor Ataque</div>
          <div class="stat-sublabel">{{ getTopScorer().equipa.nome }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ getBestDefense().golos_sofridos }}</div>
          <div class="stat-label">Melhor Defesa</div>
          <div class="stat-sublabel">{{ getBestDefense().equipa.nome }}</div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && selectedCompetition && standings.length === 0" class="empty-state">
      <div class="empty-message">
        <i class="icon-table"></i>
        <h3>Nenhuma classificação encontrada</h3>
        <p>Esta {{ activeTab === 'liga' ? 'liga' : 'torneio' }} ainda não possui classificações.</p>
      </div>
    </div>

    <!-- No Selection State -->
    <div v-if="!loading && !error && !selectedCompetition" class="no-selection-state">
      <div class="no-selection-message">
        <i class="icon-list"></i>
        <h3>Selecione uma {{ activeTab === 'liga' ? 'Liga' : 'Torneio' }}</h3>
        <p>Escolha uma {{ activeTab === 'liga' ? 'liga' : 'torneio' }} para ver as classificações.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'

export default {
  name: 'CompetitionStandings',

  props: {
    refresh: { type: Boolean, default: false }
  },
  setup(props) {
    // Reactive data
    const activeTab = ref('liga')
    const selectedCompetition = ref('')
    const loading = ref(false)

    

    // refresh the standings
    watch(() => props.refresh, (newVal) => {
      if (newVal) {
        loadStandings()
      }
    })

    

    
   
    const error = ref('')
    const backendUrl =process.env.VUE_APP_URL_BASE || 'http://localhost:8000/'
    // Data arrays
    const ligas = ref([])
    const torneios = ref([])
    const standings = ref([])
    const selectedCompetitionData = ref(null)

    // Computed properties
    const currentCompetitions = computed(() => {
      return activeTab.value === 'liga' ? ligas.value : torneios.value
    })

    
    // Load competitions (ligas and torneios)
    const loadCompetitions = async () => {
      if (loading.value) return
      loading.value = true
      error.value = ''
      try {
        const [ligasRes, torneiosRes] = await Promise.all([
          api.get('app/liga/'),
          api.get('app/torneio/')
        ])
        ligas.value = ligasRes.data.results || ligasRes.data
        torneios.value = torneiosRes.data.results || torneiosRes.data
      } catch (err) {
        error.value = 'Erro ao carregar competições'
      } finally {
        loading.value = false
      }
    }

    watch(() => props.refresh, (newVal) => {
      if (newVal) {
        loadCompetitions()
      }
    })

    // Load standings for selected competition
    const loadStandings = async () => {
      if (loading.value) return
      if (!selectedCompetition.value) {
        standings.value = []
        selectedCompetitionData.value = null
        return
      }
      loading.value = true
      error.value = ''
      try {
        // Competition details
        const compRes = await api.get(`app/${activeTab.value}/${selectedCompetition.value}/`)
        selectedCompetitionData.value = compRes.data

        // Standings
        const endpoint = activeTab.value === 'liga' ? 'ligaTabela' : 'torneioTabela'
        const standingsRes = await api.get(`app/${endpoint}/?${activeTab.value}=${selectedCompetition.value}`)
        const data = standingsRes.data.results || standingsRes.data
        standings.value = data.sort((a, b) => a.posicao - b.posicao)
      } catch (err) {
        error.value = 'Erro ao carregar classificações'
        standings.value = []
        selectedCompetitionData.value = null
      } finally {
        loading.value = false
      }
    }

    // Utility functions
    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString('pt-PT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    }

    const formatGoalDiff = (diff) => {
      return diff > 0 ? `+${diff}` : diff.toString()
    }

    const getRowClass = (position) => {
      if (position === 1) return 'champion-row'
      if (position <= 4) return 'qualification-row'
      if (position >= standings.value.length - 2) return 'relegation-row'
      return ''
    }

    const getPositionClass = (position) => {
      if (position === 1) return 'champion'
      if (position <= 4) return 'qualification'
      if (position >= standings.value.length - 2) return 'relegation'
      return ''
    }

    const getGoalDiffClass = (diff) => {
      if (diff > 0) return 'positive'
      if (diff < 0) return 'negative'
      return 'neutral'
    }

    const handleImageError = (event) => {
      event.target.src = backendUrl + 'media/utilizadores/default.png'
    }

    // Statistics functions
    const getTotalGoals = () => {
      return standings.value.reduce((total, team) => total + team.golos_marcados, 0)
    }

    const getAverageGoalsPerGame = () => {
      const totalGames = standings.value.reduce((total, team) => 
        total + team.vitorias + team.empates + team.derrotas, 0
      )
      return totalGames > 0 ? getTotalGoals() / totalGames : 0
    }

    const getTopScorer = () => {
      return standings.value.reduce((top, team) => 
        team.golos_marcados > top.golos_marcados ? team : top, 
        standings.value[0] || { golos_marcados: 0, equipa: { nome: '-' } }
      )
    }

    const getBestDefense = () => {
      return standings.value.reduce((best, team) => 
        team.golos_sofridos < best.golos_sofridos ? team : best,
        standings.value[0] || { golos_sofridos: 999, equipa: { nome: '-' } }
      )
    }

    const reload = async () => {
      selectedCompetition.value = ''
      standings.value = []
      selectedCompetitionData.value = null
      error.value = ''
      await loadCompetitions()
      await loadStandings()

    }

    // Watchers
    watch(activeTab, () => {
      selectedCompetition.value = ''
      standings.value = []
      selectedCompetitionData.value = null
      error.value = ''
    })

    // Lifecycle
    onMounted(() => {
      loadCompetitions()
    })

    return {
      // Reactive data
      activeTab,
      selectedCompetition,
      loading,
      error,
      ligas,
      torneios,
      standings,
      selectedCompetitionData,
      
      // Computed
      currentCompetitions,
      backendUrl,
      
      // Methods
      loadStandings,
      formatDate,
      formatGoalDiff,
      getRowClass,
      getPositionClass,
      getGoalDiffClass,
      handleImageError,
      getTotalGoals,
      getAverageGoalsPerGame,
      getTopScorer,
      getBestDefense,
      reload
    }
  }
}
</script>

<!-- <style scoped>
.competition-standings {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header Styles */
.standings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
}

.tab-container {
  display: flex;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.tab-button {
  padding: 12px 20px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.tab-button:hover {
  background: #e9ecef;
  color: #333;
}

.tab-button.active {
  background: #007bff;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

/* Competition Selector */
.competition-selector {
  margin-bottom: 30px;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.selector-label {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.competition-select {
  min-width: 300px;
  padding: 10px 15px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 16px;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.competition-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.competition-select:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.competition-dates {
  color: #666;
  font-size: 0.9em;
}

/* Competition Info */
.info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.info-card h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 700;
}

.description {
  margin: 0 0 15px 0;
  opacity: 0.9;
  line-height: 1.5;
}

.competition-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  opacity: 0.9;
}

/* Loading and Error States */
.loading-container,
.error-container,
.empty-state,
.no-selection-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.retry-button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.retry-button:hover {
  background: #0056b3;
}

.empty-message,
.no-selection-message {
  color: #666;
}

.empty-message i,
.no-selection-message i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

/* Standings Table */
.standings-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-wrapper {
  overflow-x: auto;
}

.standings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.standings-table th {
  background: #f8f9fa;
  padding: 15px 10px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e9ecef;
  white-space: nowrap;
}

.standings-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f3f4;
  vertical-align: middle;
}

.standings-table tbody tr:hover {
  background: #f8f9fa;
}

/* Table Column Styles */
.position-col { width: 60px; }
.team-col { min-width: 200px; }
.points-col { width: 50px; text-align: center; }
.games-col, .wins-col, .draws-col, .losses-col { width: 40px; text-align: center; }
.goals-col { width: 50px; text-align: center; }

.position-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.position-number {
  font-weight: 600;
  min-width: 20px;
}

.position-indicator {
  width: 4px;
  height: 20px;
  border-radius: 2px;
}

.position-indicator.champion { background: #ffd700; }
.position-indicator.qualification { background: #28a745; }
.position-indicator.relegation { background: #dc3545; }

.team-cell {
  padding: 8px 10px !important;
}

.team-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.team-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 4px;
  flex-shrink: 0;
}

.team-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.team-name {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.team-city {
  font-size: 12px;
  color: #666;
}

.points-cell {
  text-align: center;
  font-size: 16px;
  color: #007bff;
}

.games-cell, .wins-cell, .draws-cell, .losses-cell, .goals-cell {
  text-align: center;
  font-weight: 500;
}

.goals-diff-cell {
  text-align: center;
  font-weight: 600;
}

.goals-diff-cell .positive { color: #28a745; }
.goals-diff-cell .negative { color: #dc3545; }
.goals-diff-cell .neutral { color: #666; }

/* Row Styles */
.champion-row { background: rgba(255, 215, 0, 0.1); }
.qualification-row { background: rgba(40, 167, 69, 0.1); }
.relegation-row { background: rgba(220, 53, 69, 0.1); }

/* Table Legend */
.table-legend {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 16px;
  height: 4px;
  border-radius: 2px;
}

.legend-color.champion { background: #ffd700; }
.legend-color.qualification { background: #28a745; }
.legend-color.relegation { background: #dc3545; }

/* Statistics Summary */
.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  padding: 25px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.stat-card {
  text-align: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #007bff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-sublabel {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .competition-standings {
    padding: 15px;
  }
  
  .standings-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
  
  .title {
    font-size: 24px;
  }
  
  .tab-container {
    justify-content: center;
  }
  
  .selector-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .competition-select {
    min-width: auto;
  }
  
  .competition-meta {
    justify-content: center;
  }
  
  .standings-table {
    font-size: 12px;
  }
  
  .standings-table th,
  .standings-table td {
    padding: 8px 6px;
  }
  
  .team-name {
    font-size: 13px;
  }
  
  .team-city {
    display: none;
  }
  
  .table-legend {
    gap: 15px;
  }
  
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .tab-button {
    padding: 10px 15px;
    font-size: 14px;
  }
  
  .team-logo {
    width: 24px;
    height: 24px;
  }
  
  .stats-summary {
    grid-template-columns: 1fr;
  }
  
  .legend-item {
    font-size: 11px;
  }
}
</style> -->

<style scoped>
.competition-standings {
  max-width: 100vw;
  margin: 0 auto;
  padding: 50px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #181a20;
  color: #e0e0e0;
}

/* Header Styles */
.standings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.tab-container {
  display: flex;
  background: #232634;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.tab-button {
  padding: 12px 20px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #b0b8c1;
}

.tab-button:hover {
  background: #232634;
  color: #fff;
}

.tab-button.active {
  background: #007bff;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

/* Competition Selector */
.competition-selector {
  margin-bottom: 30px;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.selector-label {
  font-weight: 600;
  color: #e0e0e0;
  white-space: nowrap;
}

.competition-select {
  min-width: 300px;
  padding: 10px 15px;
  border: 2px solid #232634;
  border-radius: 8px;
  font-size: 16px;
  background: #232634;
  color: #e0e0e0;
  cursor: pointer;
  transition: border-color 0.2s;
}

.competition-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
}

.competition-select:disabled {
  background: #232634;
  color: #888;
  cursor: not-allowed;
}

.competition-dates {
  color: #b0b8c1;
  font-size: 0.9em;
}

/* Competition Info */
.info-card {
  background: linear-gradient(135deg, #232634 0%, #2d3250 100%);
  color: #fff;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.info-card h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 700;
}

.description {
  margin: 0 0 15px 0;
  opacity: 0.9;
  line-height: 1.5;
}

.competition-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  opacity: 0.9;
  color: #b0b8c1;
}

/* Loading and Error States */
.loading-container,
.error-container,
.empty-state,
.no-selection-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #232634;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #ff6b6b;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.retry-button {
  padding: 10px 20px;
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.retry-button:hover {
  background: #0056b3;
}

.empty-message,
.no-selection-message {
  color: #b0b8c1;
}

.empty-message i,
.no-selection-message i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

/* Standings Table */
.standings-container {
  background: #232634;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.table-wrapper {
  overflow-x: auto;
}

.standings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #232634;
  color: #e0e0e0;
}

.standings-table th {
  background: #232634;
  padding: 15px 10px;
  text-align: left;
  font-weight: 600;
  color: #b0b8c1;
  border-bottom: 2px solid #35394a;
  white-space: nowrap;
}

.standings-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #35394a;
  vertical-align: middle;
}

.standings-table tbody tr:hover {
  background: #1a1d29;
}

/* Table Column Styles */
.position-col { width: 60px; }
.team-col { min-width: 200px; }
.points-col { width: 50px; text-align: center; }
.games-col, .wins-col, .draws-col, .losses-col { width: 40px; text-align: center; }
.goals-col { width: 50px; text-align: center; }

.position-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.position-number {
  font-weight: 600;
  min-width: 20px;
}

.position-indicator {
  width: 4px;
  height: 20px;
  border-radius: 2px;
}

.position-indicator.champion { background: #ffd700; }
.position-indicator.qualification { background: #28a745; }
.position-indicator.relegation { background: #ff6b6b; }

.team-cell {
  padding: 8px 10px !important;
}

.team-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.team-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 4px;
  flex-shrink: 0;
  background: #181a20;
  border: 1px solid #35394a;
}

.team-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.team-name {
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.team-city {
  font-size: 12px;
  color: #b0b8c1;
}

.points-cell {
  text-align: center;
  font-size: 16px;
  color: #007bff;
}

.games-cell, .wins-cell, .draws-cell, .losses-cell, .goals-cell {
  text-align: center;
  font-weight: 500;
}

.goals-diff-cell {
  text-align: center;
  font-weight: 600;
}

.goals-diff-cell .positive { color: #28a745; }
.goals-diff-cell .negative { color: #ff6b6b; }
.goals-diff-cell .neutral { color: #b0b8c1; }

/* Row Styles */
.champion-row { background: rgba(255, 215, 0, 0.08); }
.qualification-row { background: rgba(40, 167, 69, 0.08); }
.relegation-row { background: rgba(255, 107, 107, 0.08); }

/* Table Legend */
.table-legend {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 20px;
  background: #232634;
  border-top: 1px solid #35394a;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #b0b8c1;
}

.legend-color {
  width: 16px;
  height: 4px;
  border-radius: 2px;
}

.legend-color.champion { background: #ffd700; }
.legend-color.qualification { background: #28a745; }
.legend-color.relegation { background: #ff6b6b; }

/* Statistics Summary */
.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  padding: 25px;
  background: #232634;
  border-top: 1px solid #35394a;
}

.stat-card {
  text-align: center;
  padding: 15px;
  background: #181a20;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #007bff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  font-weight: 600;
  color: #b0b8c1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-sublabel {
  font-size: 11px;
  color: #888;
  margin-top: 2px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .competition-standings {
    padding: 15px;
  }
  
  .standings-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
  
  .title {
    font-size: 24px;
  }
  
  .tab-container {
    justify-content: center;
  }
  
  .selector-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .competition-select {
    min-width: auto;
  }
  
  .competition-meta {
    justify-content: center;
  }
  
  .standings-table {
    font-size: 12px;
  }
  
  .standings-table th,
  .standings-table td {
    padding: 8px 6px;
  }
  
  .team-name {
    font-size: 13px;
  }
  
  .team-city {
    display: none;
  }
  
  .table-legend {
    gap: 15px;
  }
  
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .tab-button {
    padding: 10px 15px;
    font-size: 14px;
  }
  
  .team-logo {
    width: 24px;
    height: 24px;
  }
  
  .stats-summary {
    grid-template-columns: 1fr;
  }
  
  .legend-item {
    font-size: 11px;
  }
}
</style>