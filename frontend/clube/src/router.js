import { createRouter, createWebHistory } from 'vue-router';
import App from './views/home.vue'; // Import your views as needed
import AppLogin from './views/login.vue'; // Import your views as needed
import AppRegister from './views/register.vue'; // Import your views as needed
import LojaPublica from './views/loja/lojaPublica.vue'
import Checkout       from './views/Checkout.vue'
import EncomendaSucesso from './views/EncomendaSucesso.vue'
import Backoffice from './views/backoffice/Index.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import criarLoja from './views/criarLoja.vue';
import GoogleCallback from './views/google/GoogleCallback.vue';
import FlutterwaveCallback from './views/flutterwave/FlutterwaveCallback.vue';



// POS Components
import POSRegister from '@/views/pos/POSRegister.vue'
import POSLogin from '@/views/pos/POSLogin.vue'
import POSDashboard from '@/views/pos/POSDashboard.vue'


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
    {
        path: '/auth/google/callback',
        name: 'GoogleCallback',
        component: GoogleCallback,
    },
    {
        path: '/pagamento/callback',
        name: 'FlutterwaveCallback',
        component: FlutterwaveCallback,
    },
    {
        path: '/pos/register',
        name: 'POSRegister',
        component: POSRegister,
        meta: { title: 'Criar Conta POS' }
    },
    {
        path: '/pos/login',
        name: 'POSLogin',
        component: POSLogin,
        meta: { title: 'Login POS' }
    },
    {
        path: '/pos/dashboard',
        name: 'POSDashboard',
        component: POSDashboard,
        meta: { 
            title: 'Dashboard POS',
            requiresPOSAuth: true  // Nova flag para autenticação POS
        }
    }
    
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
