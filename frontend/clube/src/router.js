import { createRouter, createWebHistory } from 'vue-router';
import App from './views/home.vue'; // Import your views as needed
import AppLogin from './views/login.vue'; // Import your views as needed
import AppRegister from './views/register.vue'; // Import your views as needed
import LojaPublica from './views/lojaPublica.vue'
import Checkout       from './views/Checkout.vue'
import EncomendaSucesso from './views/EncomendaSucesso.vue'
import Backoffice from './views/backoffice/Index.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import criarLoja from './views/criarLoja.vue';


const routes = [
    {
        path: '/Login',
        name: 'Login',
        component: AppLogin,
    },
    {
        path: '/Register',
        name: 'Register',
        component: AppRegister,
    },
    {
        path: '/Home',
        name: 'Home',
        component: App,
        meta: { requiresAuth: true },
    },
    {
        path: '/loja/:id',
        name: 'Loja',
        component: LojaPublica,
    },
        {   
        path: '/',
        redirect: '/Login'
    },
    {   path: '/checkout/:lojaId',  
        name: 'Checkout',        
        component: Checkout,        
        meta: { requiresAuth: true } 
    },
    {   path: '/encomenda/:id/ok',  
        name: 'EncomendaSucesso', 
        component: EncomendaSucesso, 
        meta: { requiresAuth: true } 
    },
    { path: '/loja/:id/backoffice', 
        name: 'Backoffice', 
        component: Backoffice, 
        meta: { requiresAuth: true } 
    },
    {
        path: '/admin',
        name: 'Admin',
        component: AdminLayout,
        meta: { requiresAuth: true }
    },
    { 
        path: '/loja/criar', 
        name: 'CriarLoja', 
        component: criarLoja, 
        meta: { requiresAuth: true } 
    },

    // Add other routes here
];

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition;
        } else {
            return { top: 0, behavior: 'smooth' };
        }
    },
});

router.beforeEach((to, from, next) => {
    if (to.matched.some(record => record.meta.requiresAuth)) {
        // This line checks if the user is authenticated
        // Replace `false` with your authentication check
        if (localStorage.getItem('user')) {
            next();
        } else {
            next({ name: 'Login' });
        }
    } else {
        next();
    }
});

export default router;
