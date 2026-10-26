import { createApp } from 'vue';
import videoVisivel from './directives/videoVisivel';
import imgDirectiva from './directives/img';
import { miniatura } from './utils/media';
import App from './App.vue';
import { formatarDinheiro } from './utils/dinheiro';
import router from './router'; // Import the router
import '@/assets/toastify.css';
import 'vue3-toastify/dist/index.css';
import '@/assets/tailwind.css';
import '@/assets/loja-acoes.css';
import '@fortawesome/fontawesome-free/css/all.min.css'   // <-- aqui
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';


import { faCommentDots } from '@fortawesome/free-solid-svg-icons'



library.add(faBars, fas, faCommentDots); // Add the icons to the library

const app = createApp(App);

app.component('font-awesome-icon', FontAwesomeIcon);
app.directive('video-visivel', videoVisivel); // vídeos só tocam quando visíveis (directives/videoVisivel.js)
app.directive('img', imgDirectiva); // imagens lazy + volta ao original se faltar a miniatura (directives/img.js)
app.config.globalProperties.$miniatura = miniatura; // foto de 600 px para cartões e listas (utils/media.js)

app.config.globalProperties.$dinheiro = formatarDinheiro; // 1250 → "1.250$00" em qualquer template

app.use(router); // Use the router

app.mount('#app');
