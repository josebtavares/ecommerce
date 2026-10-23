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
import CompletarPerfil from './views/google/CompletarPerfil.vue';
import MensagensPagina from './views/Mensagens.vue';
import { POS_ACCESS } from './services/api';
import { estaAutenticado } from './services/sessao';
import FlutterwaveCallback from './views/flutterwave/FlutterwaveCallback.vue';
import PedirReembolso from './views/reembolsos/PedirReembolso.vue';
import ReembolsoDetalhe from './views/reembolsos/ReembolsoDetalhe.vue';
import MeusReembolsos from './views/reembolsos/MeusReembolsos.vue';
const MinhasMarcacoes = () => import('./views/servicos/MinhasMarcacoes.vue');
const MarcacaoCliente = () => import('./views/servicos/MarcacaoCliente.vue');



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
        // pública: ver lojas e produtos não exige conta (encomendar sim — checkout tem requiresAuth)
    },
    {
        path: '/loja/:id',
        name: 'Loja',
        component: LojaPublica,
    },
    {
        // os serviços estão na página da loja (secção Serviços em todos os templates)
        path: '/loja/:id/servicos',
        redirect: to => ({ path: `/loja/${to.params.id}`, query: to.query }),
    },
    {
        path: '/minhas-marcacoes',
        name: 'MinhasMarcacoes',
        component: MinhasMarcacoes,
        meta: { requiresAuth: true }
    },
    {
        path: '/minhas-marcacoes/:id',
        name: 'MarcacaoCliente',
        component: MarcacaoCliente,
        meta: { requiresAuth: true }
    },
        {   
        path: '/',
        redirect: '/Home'
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
        path: '/completar-perfil',
        name: 'CompletarPerfil',
        component: CompletarPerfil,
        meta: { requiresAuth: true }
    },
    {
        // o perfil é uma gaveta da home: as notificações antigas apontam para /perfil
        path: '/perfil',
        redirect: { path: '/Home', query: { perfil: 'encomendas' } },
    },
    {
        path: '/perfil/reembolsos',
        name: 'Reembolsos',
        component: MeusReembolsos,
        meta: { requiresAuth: true }
    },
    {
        path: '/perfil/reembolsos/:id',
        name: 'Reembolso',
        component: ReembolsoDetalhe,
        meta: { requiresAuth: true }
    },
    {
        path: '/encomenda/:id/reembolso',
        name: 'PedirReembolso',
        component: PedirReembolso,
        meta: { requiresAuth: true }
    },
    {
        // chat em ecrã inteiro (o balão flutuante abre o mesmo painel)
        path: '/mensagens',
        name: 'Mensagens',
        component: MensagensPagina,
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
        path: '/pos/completar-perfil',
        name: 'POSCompletarPerfil',
        component: CompletarPerfil,
        meta: { title: 'Completar perfil', requiresPOSAuth: true }
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
    // Páginas do POS: precisam da sessão do POS (dono ou membro) — independente da Bendi
    if (to.matched.some(record => record.meta.requiresPOSAuth)) {
        const sessao = localStorage.getItem(POS_ACCESS)
        return sessao ? next() : next({ name: 'POSLogin' })
    }
    if (to.matched.some(record => record.meta.requiresAuth)) {
        // páginas privadas (checkout, backoffice, admin…): sem sessão vai ao login e volta cá depois
        if (estaAutenticado()) {
            next();
        } else {
            next({ name: 'Login', query: { seguinte: to.fullPath } });
        }
    } else {
        next();
    }
});

export default router;
