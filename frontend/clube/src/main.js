import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Import the router
import '@/assets/toastify.css';
import 'vue3-toastify/dist/index.css';
import '@/assets/tailwind.css';
import '@fortawesome/fontawesome-free/css/all.min.css'   // <-- aqui
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';


import { faCommentDots } from '@fortawesome/free-solid-svg-icons'



library.add(faBars, fas, faCommentDots); // Add the icons to the library

const app = createApp(App);

app.component('font-awesome-icon', FontAwesomeIcon);

app.use(router); // Use the router

app.mount('#app');
