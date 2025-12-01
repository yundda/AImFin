import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/pages/auth/Login.vue'
import Signup from '@/pages/auth/Signup.vue'
import Home from '@/pages/Home.vue'
import News from '@/pages/News.vue'
import MyPage from '@/pages/user/MyPage.vue'
import Survey from '@/pages/Survey.vue'
import SurveyResult from '@/pages/SurveyResult.vue'
// ✅ 새로 추가되는 페이지들
import PortfolioCreate from '@/pages/PortfolioCreate.vue'
import PortfolioResult from '@/pages/PortfolioResult.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/auth/login', name: 'login', component: Login },
    { path: '/auth/signup', name: 'signup', component: Signup },
    { path: '/news', name: 'news', component: News },
    { path: '/user/mypage', name: 'mypage', component: MyPage },
    { path: '/survey', name: 'survey', component: Survey },
    { path: '/survey/result', name: 'survey-result', component: SurveyResult },
    
    // ✅ 신규 라우트 추가
    { path: '/portfolio/create', name: 'portfolio-create', component: PortfolioCreate },
    { path: '/portfolio/result', name: 'portfolio-result', component: PortfolioResult },
  ]
})

export default router