import { createRouter, createWebHistory } from 'vue-router';
import App from './views/home.vue'; // Import your views as needed
import AppLogin from './views/login.vue'; // Import your views as needed
import AppRegister from './views/register.vue'; // Import your views as needed
import LojaPublica from './views/loja/lojaPublica.vue'
import Checkout       from './views/Checkout.vue'
import EncomendaSucesso from './views/EncomendaSucesso.vue'
const Backoffice = () => import('./views/backoffice/Index.vue')
const AdminLayout = () => import('@/views/admin/AdminLayout.vue')
import criarLoja from './views/criarLoja.vue';
import GoogleCallback from './views/google/GoogleCallback.vue';
import CompletarPerfil from './views/google/CompletarPerfil.vue';
import MensagensPagina from './views/Mensagens.vue';
import { POS_ACCESS, verAdminPOS } from './services/api';
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
import { esperarConta } from '@/services/confirmarEmail'
const POSDashboard = () => import('@/views/pos/POSDashboard.vue')


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
        // "Esqueceste?" do login e destino do link do email (?uid=…&token=…, ver password_reset_request)
        path: '/recuperar_senha',
        name: 'RecuperarSenha',
        component: () => import('@/views/RecuperarSenha.vue'),
    },
    {
        // link do email de confirmação (?token=…, utils/confirmar_email.py) — não precisa de sessão
        path: '/confirmar_email',
        name: 'ConfirmarEmail',
        component: () => import('@/views/ConfirmarEmail.vue'),
    },
    {
        // páginas institucionais com endereço próprio (links do rodapé e do checkout; a SISP pede-os)
        path: '/:slug(ajuda|contacto|faq|termos|privacidade|devolucoes|entregas)',
        name: 'Pagina',
        component: () => import('@/views/PaginaPublica.vue'),
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
    { path: '/loja/:id/backoffice/:seccao?/:ficha?', 
        name: 'Backoffice', 
        component: Backoffice, 
        meta: { requiresAuth: true } 
    },
    {
        path: '/admin/:seccao?/:ficha?',
        name: 'Admin',
        component: AdminLayout,
        meta: { requiresAuth: true, contaAtual: true }
    },
    { 
        path: '/loja/criar', 
        name: 'CriarLoja', 
        component: criarLoja, 
        meta: { requiresAuth: true, contaAtual: true } 
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
        // "Esqueceste?" da conta principal do POS e destino do link do email (destino 'pos')
        path: '/pos/recuperar_senha',
        name: 'POSRecuperarSenha',
        component: () => import('@/views/pos/POSRecuperarSenha.vue'),
        meta: { title: 'Recuperar password POS' }
    },
    {
        path: '/pos/completar-perfil',
        name: 'POSCompletarPerfil',
        component: CompletarPerfil,
        meta: { title: 'Completar perfil', requiresPOSAuth: true }
    },
    {
        path: '/pos/dashboard/:aba?',
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
        // (ou o admin a ver este POS em modo de leitura — services/api.js verAdminPOS)
        const sessao = localStorage.getItem(POS_ACCESS) || verAdminPOS()
        return sessao ? next() : next({ name: 'POSLogin' })
    }
    if (to.matched.some(record => record.meta.requiresAuth)) {
        // páginas privadas (checkout, backoffice, admin…): sem sessão vai ao login e volta cá depois
        if (estaAutenticado()) {
            // decidem pelo que está guardado (papel de admin, verificado): só abrem com a conta já lida
            if (to.meta.contaAtual) esperarConta().finally(() => next());
            else next();
        } else {
            next({ name: 'Login', query: { seguinte: to.fullPath } });
        }
    } else {
        next();
    }
});

// título do separador: a página da loja escreve o seu (lojaPublica.vue); ao entrar no site fica o que veio do servidor
router.afterEach((to, from) => {
    if (from.name && to.name !== 'Loja') document.title = 'Bende';
});

export default router;
