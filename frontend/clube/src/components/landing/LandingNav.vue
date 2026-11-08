<!-- LandingNav.vue — barra fixa da landing page: logo, secções (desliza até elas, marca a que está à vista),
     tema, e a conta (Entrar / Criar conta, ou "Olá, Nome" com Ir à loja, Backoffice, Admin, Sair). ☰ no telemóvel. -->
<template>
  <header class="fixed top-0 inset-x-0 z-50 transition-all duration-300" data-teste="landing-nav"
          :class="claro ? 'bg-transparent' : (isDark ? 'bg-zinc-950/90 border-b border-zinc-800 backdrop-blur-md shadow-lg'
                                                    : 'bg-white/90 border-b border-stone-200 backdrop-blur-md shadow-sm')">
    <nav class="max-w-7xl mx-auto h-16 px-4 sm:px-6 flex items-center gap-3" aria-label="Secções">
      <a href="#hero" @click.prevent="ir('hero')" class="flex items-center flex-shrink-0" aria-label="Início">
        <img :src="claro || isDark ? logoLight : logoDefault" alt="Bende" class="h-11 w-11 object-contain" />
      </a>

      <ul class="hidden lg:flex items-center gap-1 ml-4">
        <li v-for="s in links" :key="s.tipo">
          <a :href="'#' + s.tipo" @click.prevent="ir(s.tipo)" :data-teste="'nav-' + s.tipo"
             :aria-current="ativa === s.tipo ? 'true' : null"
             class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
             :class="ativa === s.tipo ? corAtiva : corLink">{{ s.nav }}</a>
        </li>
      </ul>

      <div class="ml-auto flex items-center gap-2">
        <button type="button" @click="$emit('tema')" :aria-label="isDark ? 'Tema claro' : 'Tema escuro'"
          class="w-9 h-9 rounded-full flex items-center justify-center transition-colors" :class="corIcone">
          <font-awesome-icon :icon="['fas', isDark ? 'sun' : 'moon']" class="w-4 h-4" />
        </button>

        <template v-if="!user">
          <button type="button" @click="$emit('entrar')" data-teste="nav-entrar"
            class="hidden sm:inline-flex px-3 py-2 rounded-lg text-sm font-semibold transition-colors" :class="corLink">Entrar</button>
          <button type="button" @click="$emit('registo')" data-teste="nav-registo"
            class="hidden sm:inline-flex px-4 py-2 rounded-xl text-sm font-bold text-white shadow transition hover:opacity-90"
            :class="isDark ? 'bg-red-600' : 'bg-orange-500'">Criar conta</button>
        </template>
        <div v-else class="relative" ref="menuConta">
          <button type="button" @click="menu = !menu" data-teste="nav-conta" :aria-expanded="menu ? 'true' : 'false'"
            class="flex items-center gap-2 pl-1 pr-3 py-1 rounded-full border transition-colors"
            :class="claro ? 'border-white/30 text-white hover:bg-white/10'
                          : (isDark ? 'border-zinc-700 text-zinc-200 hover:bg-zinc-800' : 'border-stone-300 text-zinc-700 hover:bg-stone-100')">
            <img v-if="user.foto && !semFoto" :src="user.foto" alt="" class="w-7 h-7 rounded-full object-cover" @error="semFoto = true" />
            <span v-else class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  :class="isDark ? 'bg-red-600' : 'bg-orange-500'">{{ inicial }}</span>
            <span class="hidden sm:inline text-sm font-semibold max-w-[9rem] truncate">Olá, {{ nome }}</span>
            <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-3 h-3 opacity-70" />
          </button>
          <div v-if="menu" class="absolute right-0 mt-2 w-60 rounded-xl border shadow-xl py-1.5 text-sm" data-teste="nav-conta-menu"
               :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-200' : 'bg-white border-stone-200 text-zinc-700'">
            <p class="sm:hidden px-4 py-2 text-xs font-semibold truncate" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Olá, {{ nome }}</p>
            <router-link to="/Home" class="item-menu" :class="hover"><font-awesome-icon :icon="['fas', 'store']" fixed-width class="mr-2 opacity-70" />Ir à loja Bende</router-link>
            <router-link to="/encomendas" class="item-menu" :class="hover">
              <font-awesome-icon :icon="['fas', 'bag-shopping']" fixed-width class="mr-2 opacity-70" />As minhas encomendas</router-link>
            <router-link v-for="l in lojas" :key="l.id" :to="`/loja/${l.id}/backoffice`" class="item-menu" :class="hover" data-teste="nav-backoffice">
              <font-awesome-icon :icon="['fas', 'shop']" fixed-width class="mr-2 opacity-70" /><span class="truncate">Backoffice · {{ l.nome }}</span></router-link>
            <router-link v-if="user.is_staff" to="/admin" class="item-menu" :class="hover" data-teste="nav-admin">
              <font-awesome-icon :icon="['fas', 'shield-halved']" fixed-width class="mr-2 opacity-70" />Painel admin</router-link>
            <div class="my-1 border-t" :class="isDark ? 'border-zinc-800' : 'border-stone-200'"></div>
            <button type="button" @click="menu = false; $emit('sair')" class="item-menu w-full text-left" :class="hover" data-teste="nav-sair">
              <font-awesome-icon :icon="['fas', 'right-from-bracket']" fixed-width class="mr-2 opacity-70" />Sair</button>
          </div>
        </div>

        <router-link to="/Home" data-teste="nav-loja"
          class="hidden md:inline-flex px-4 py-2 rounded-xl text-sm font-bold border transition-colors"
          :class="user ? (isDark ? 'bg-red-600 border-red-600 text-white hover:opacity-90' : 'bg-orange-500 border-orange-500 text-white hover:opacity-90')
                       : (claro ? 'border-white/40 text-white hover:bg-white/10' : (isDark ? 'border-zinc-700 text-zinc-200 hover:bg-zinc-800' : 'border-stone-300 text-zinc-700 hover:bg-stone-100'))">
          Ir à loja</router-link>

        <button type="button" class="lg:hidden w-10 h-10 rounded-lg flex items-center justify-center" :class="corIcone"
                @click="aberto = !aberto" :aria-expanded="aberto ? 'true' : 'false'" aria-label="Menu" data-teste="nav-menu">
          <font-awesome-icon :icon="['fas', aberto ? 'xmark' : 'bars']" class="w-5 h-5" />
        </button>
      </div>
    </nav>

    <!-- telemóvel / tablet -->
    <div v-if="aberto" class="lg:hidden border-t px-4 pb-4 pt-2 shadow-xl" data-teste="nav-painel"
         :class="isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-white border-stone-200'">
      <a v-for="s in links" :key="s.tipo" :href="'#' + s.tipo" @click.prevent="ir(s.tipo)"
         class="block px-3 py-3 rounded-lg text-base font-medium"
         :class="ativa === s.tipo ? (isDark ? 'text-red-400 bg-zinc-900' : 'text-orange-600 bg-orange-50') : (isDark ? 'text-zinc-300' : 'text-zinc-700')">{{ s.nav }}</a>
      <div class="grid grid-cols-2 gap-2 mt-3">
        <template v-if="!user">
          <button type="button" @click="aberto = false; $emit('entrar')" class="py-2.5 rounded-xl border text-sm font-semibold"
                  :class="isDark ? 'border-zinc-700 text-zinc-200' : 'border-stone-300 text-zinc-700'">Entrar</button>
          <button type="button" @click="aberto = false; $emit('registo')" class="py-2.5 rounded-xl text-sm font-bold text-white"
                  :class="isDark ? 'bg-red-600' : 'bg-orange-500'">Criar conta</button>
        </template>
        <router-link to="/Home" class="col-span-2 py-2.5 rounded-xl text-sm font-bold text-center border"
                     :class="isDark ? 'border-zinc-700 text-zinc-100' : 'border-stone-300 text-zinc-800'">Ir à loja Bende</router-link>
      </div>
    </div>
  </header>
</template>

<script>
import logoDefault from '@/assets/img/login/logo_final_640.webp'
import logoLight from '@/assets/img/login/logo_final_640_light.webp'

export default {
  name: 'LandingNav',
  props: {
    links: { type: Array, default: () => [] },      // [{tipo, nav}]
    ativa: { type: String, default: '' },
    isDark: { type: Boolean, default: false },
    user: { type: Object, default: null },
    lojas: { type: Array, default: () => [] },
    sobreHero: { type: Boolean, default: false },   // no topo, por cima de um hero com imagem: letras brancas, sem fundo
  },
  emits: ['ir', 'entrar', 'registo', 'tema', 'sair'],
  data () { return { aberto: false, menu: false, semFoto: false, logoDefault, logoLight } },
  computed: {
    claro () { return this.sobreHero && !this.aberto },
    nome () { return this.user?.first_name || this.user?.username || '' },
    inicial () { return (this.nome[0] || '?').toUpperCase() },
    corLink () {
      if (this.claro) return 'text-white/85 hover:text-white hover:bg-white/10'
      return this.isDark ? 'text-zinc-300 hover:text-white hover:bg-zinc-800' : 'text-zinc-600 hover:text-zinc-900 hover:bg-stone-100'
    },
    corAtiva () {
      if (this.claro) return 'text-white bg-white/15'
      return this.isDark ? 'text-red-400 bg-zinc-900' : 'text-orange-600 bg-orange-50'
    },
    corIcone () {
      if (this.claro) return 'text-white hover:bg-white/10'
      return this.isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-stone-100 hover:bg-stone-200 text-zinc-600'
    },
    hover () { return this.isDark ? 'hover:bg-zinc-800' : 'hover:bg-stone-100' },
  },
  mounted () {
    this.fora = e => { if (this.menu && !this.$refs.menuConta?.contains(e.target)) this.menu = false }
    document.addEventListener('click', this.fora)
  },
  beforeUnmount () { document.removeEventListener('click', this.fora) },
  methods: {
    ir (tipo) { this.aberto = false; this.$emit('ir', tipo) },
  },
}
</script>

<style scoped>
.item-menu { display: flex; align-items: center; padding: 0.55rem 1rem; }
</style>
