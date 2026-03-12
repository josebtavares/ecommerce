import { createRouter, createWebHistory } from 'vue-router';
import App from './views/home.vue'; // Import your views as needed
import AppLogin from './views/login.vue'; // Import your views as needed
import AppRegister from './views/register.vue'; // Import your views as needed

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
        path: '/',
        redirect: '/Login'
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
