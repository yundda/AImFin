import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/pages/auth/Login.vue'
import Signup from '@/pages/auth/Signup.vue'
import Home from '@/pages/Home.vue'
import News from '@/pages/News.vue'
import MyPage from '@/pages/user/MyPage.vue'
import Survey from '@/pages/Survey.vue'
import SurveyResult from '@/pages/SurveyResult.vue'
import PortfolioCreate from '@/pages/PortfolioCreate.vue'
import PortfolioResult from '@/pages/PortfolioResult.vue'
import PortfolioCompare from '@/pages/PortfolioCompare.vue'
import NicknameSetup from '@/pages/onboarding/NicknameSetup.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home, meta: { requiresAuth: true } }, // ✅ 인증 필요 표시
    { path: '/auth/login', name: 'login', component: Login },
    { path: '/auth/signup', name: 'signup', component: Signup },
    
    // ✅ 인증이 필요한 페이지들에 meta 추가
    { path: '/news', name: 'news', component: News, meta: { requiresAuth: true } },
    { path: '/user/mypage', name: 'mypage', component: MyPage, meta: { requiresAuth: true } },
    { path: '/survey', name: 'survey', component: Survey, meta: { requiresAuth: true } },
    { path: '/survey/result', name: 'survey-result', component: SurveyResult, meta: { requiresAuth: true } },
    { path: '/portfolio/create', name: 'portfolio-create', component: PortfolioCreate, meta: { requiresAuth: true } },
    { path: '/portfolio/result', name: 'portfolio-result', component: PortfolioResult, meta: { requiresAuth: true } },
    { path: '/portfolio/compare', name: 'portfolio-compare', component: PortfolioCompare, meta: { requiresAuth: true } },
    { path: '/onboarding/nickname', name: 'nickname-setup', component: NicknameSetup, },
  ]
})

router.beforeEach((to, from, next) => {
  // 로컬 스토리지에서 토큰 확인
  const token = localStorage.getItem('accessToken');
  
  // 1. 이동하려는 페이지가 '인증이 필요한(requiresAuth)' 페이지인지 확인
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 2. 토큰이 없으면 로그인 페이지로 튕겨냄
    if (!token) {
      // alert('로그인이 필요한 서비스입니다.'); // (선택사항) 알림 띄우기
      next({ name: 'login' });
    } else {
      // 3. 토큰이 있으면 통과
      next();
    }
  } else {
    // 4. 인증이 필요 없는 페이지(로그인/회원가입)는 그냥 통과
    
    // (선택사항) 이미 로그인한 사람이 로그인 페이지 가려고 하면 메인으로 보냄
    if (token && (to.name === 'login' || to.name === 'signup')) {
      next({ name: 'home' });
    } else {
      next();
    }
  }
});

export default router