import { createRouter, createWebHistory } from "vue-router";
import Login from "@/pages/auth/Login.vue";
import Signup from "@/pages/auth/Signup.vue";
import Home from "@/pages/Home.vue";
import MyPage from "@/pages/user/MyPage.vue";
import Survey from "@/pages/Survey.vue";
import SurveyResult from "@/pages/SurveyResult.vue";
import PortfolioCreate from "@/pages/PortfolioCreate.vue";
import PortfolioResult from "@/pages/PortfolioResult.vue";
import PortfolioCompare from "@/pages/PortfolioCompare.vue";
import NicknameSetup from "@/pages/onboarding/NicknameSetup.vue";
import OauthCallback from "@/pages/OauthCallback.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: Home, meta: { requiresAuth: true } }, // ✅ 인증 필요 표시
    { path: "/auth/login", name: "login", component: Login },
    { path: "/auth/signup", name: "signup", component: Signup },

    // ✅ 인증이 필요한 페이지들에 meta 추가
    // ✅ 인증이 필요한 페이지들에 meta 추가
    {
      path: "/user/mypage",
      name: "mypage",
      component: MyPage,
      meta: { requiresAuth: true },
    },
    {
      path: "/survey",
      name: "survey",
      component: Survey,
      meta: { requiresAuth: true },
    },
    {
      path: "/survey/result",
      name: "survey-result",
      component: SurveyResult,
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/create",
      name: "portfolio-create",
      component: PortfolioCreate,
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/result",
      name: "portfolio-result",
      component: PortfolioResult,
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/compare",
      name: "portfolio-compare",
      component: PortfolioCompare,
      meta: { requiresAuth: true },
    },
    {
      path: "/onboarding/nickname",
      name: "nickname-setup",
      component: NicknameSetup,
    },
    {
      path: "/oauth/callback",
      name: "oauth-callback",
      component: OauthCallback,
    },
  ],
});

import { useAuthStore } from "@/stores/auth";

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // 앱 시작 시 또는 새로고침 시 인증 상태 확인
  if (!authStore.isAuthenticated && !authStore.user) {
    await authStore.checkAuth();
  }

  // 1. 이동하려는 페이지가 '인증이 필요한(requiresAuth)' 페이지인지 확인
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // 2. 로그인 상태가 아니면 로그인 페이지로
    if (!authStore.isAuthenticated) {
      next({ name: "login" });
    } else {
      // 3. 로그인 상태면 통과
      next();
    }
  } else {
    // 4. 인증이 필요 없는 페이지 (로그인/회원가입 등)
    // 이미 로그인한 상태에서 로그인/회원가입 접근 시 홈으로 리다이렉트
    if (
      authStore.isAuthenticated &&
      (to.name === "login" || to.name === "signup")
    ) {
      next({ name: "home" });
    } else {
      next();
    }
  }
});

export default router;
