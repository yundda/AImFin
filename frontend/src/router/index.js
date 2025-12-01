import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/pages/auth/Login.vue'
import Signup from '@/pages/auth/Signup.vue'
import Home from '@/pages/Home.vue'
import News from '@/pages/News.vue'
import MyPage from '@/pages/user/MyPage.vue'
import Survey from '@/pages/Survey.vue' // ✅ 추가됨
import SurveyResult from '@/pages/SurveyResult.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/auth/login', name: 'login', component: Login },
    { path: '/auth/signup', name: 'signup', component: Signup },
    { path: '/news', name: 'news', component: News },
    { path: '/user/mypage', name: 'mypage', component: MyPage },
    { path: '/survey', name: 'survey', component: Survey }, // ✅ 라우트 추가
    { path: '/survey/result', name: 'survey-result', component: SurveyResult}
  ]

})

export default router