<template>
    <nav class="flex items-center  text-white font-koulen px-4 h-20">
      <div class="w-16 h-16">
        <img src="@/assets/img/login/clube_logo.png"
             alt="logo"
             class="w-full h-full object-cover" />
      </div>
  
      <ul class="flex-1 flex justify-center gap-16 text-xs">
        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('women_icon')">HOME</h2></li>
        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('noticias')">NOTÍCIAS</h2></li>
        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('equipa')">EQUIPA</h2></li>

        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('feed')">FEED</h2></li>

        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('loja')">LOJA</h2></li>
        <li><h2 class="cursor-pointer hover:underline"
          @click="scroll_to('calendario')">CALENDÁRIO</h2></li>
        <li><h2 class="cursor-pointer hover:underline"
                @click="scroll_to('resultados')">RESULTADOS</h2></li>
      </ul>
  
      <div class="flex items-center gap-6">
        <!-- exemplos: -->
        <!-- <font-awesome-icon :icon="['fas','cart-shopping']" @click="show_cart" /> -->
        <!-- <font-awesome-icon :icon="['fas','user']" @click="show_profile" /> -->
      </div>
    </nav>
  </template>
  
  <script>
  export default {
    name: 'AppNavbar',
    methods: {
      scroll_to (id) {
        const el = document.getElementById(id)
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }
    }
  }
  </script>
  
  <style scoped>
  html { scroll-behavior: smooth; }
  </style>
  