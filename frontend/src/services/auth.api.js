// src/services/auth.api.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

const instance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // 쿠키 사용하는 경우 대비(로컬은 영향 적음)
});

// ---- 요청 인터셉터: auth 엔드포인트는 Authorization 제외 ----
instance.interceptors.request.use((config) => {
  const url = config.url || "";
  const isAuthEndpoint =
    url.includes("/users/auth/login") ||
    url.includes("/users/auth/signup") ||
    url.includes("/users/auth/refresh") ||
    url.includes("/users/auth/logout");

  if (!isAuthEndpoint) {
    const access = localStorage.getItem(ACCESS_KEY);
    if (access) {
      config.headers = config.headers || {};
      if (!config.headers["Authorization"]) {
        config.headers["Authorization"] = `Bearer ${access}`;
      }
    }
  }
  return config;
});

// ---- 인증 API 래퍼 ----
export const authApi = {
  signup: (userData) => instance.post("/users/auth/signup", userData),

  // 일반 로그인: 응답 토큰을 localStorage에 저장
  login: async (credentials) => {
    const resp = await instance.post("/users/auth/login", credentials);
    const { access, refresh } = resp.data || {};
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    return resp;
  },

  logout: async () => {
    try {
      await instance.post("/users/auth/logout");
    } finally {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    }
  },

  refreshToken: () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    return instance.post("/users/auth/refresh", { refresh });
  },

  // 프로필/설문/선호
  getProfile: () => instance.get("/users/profile"),
  updateNickname: (nickname) =>
    instance.patch("/users/profile/nickname", { nickname }),
  saveSurvey: (payload) => instance.post("/users/survey/save", payload),
  getSurvey: () => instance.get("/users/survey/current"),
  savePreference: (payload) => instance.post("/users/preference/save", payload),

  // AI 분석
  recommendPortfolio: (payload) =>
    instance.post("/analysis/recommend/portfolio", payload),
  rebalancePortfolio: (portfolioId, payload) =>
    instance.post(`/analysis/rebalance/portfolio/${portfolioId}`, payload),
  comparePortfolio: (payload) =>
    instance.post("/analysis/compare/portfolio", payload),

  // 포트폴리오 관리
  getPortfolioList: () => instance.get("/portfolios/list"),
  getPortfolioDetail: (id) => instance.get(`/portfolios/${id}`),
  getRepresentativePortfolio: () => instance.get("/portfolios/representative"),
  savePortfolio: (payload) => instance.post("/portfolios/save", payload),
};

// ---- 응답 인터셉터: login/refresh 시 토큰 동기화 ----
instance.interceptors.response.use(
  (res) => {
    try {
      const url = res.config?.url || "";
      const data = res.data || {};
      if (
        url.includes("/users/auth/login") ||
        url.includes("/users/auth/refresh")
      ) {
        if (data.access) localStorage.setItem(ACCESS_KEY, data.access);
        if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
      }
    } catch (_) {}
    return res;
  },
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status || 0;
    const url = original?.url || "";
    const isAuthCall =
      url?.includes("/users/auth/login") ||
      url?.includes("/users/auth/refresh");

    if (status === 401 && !original._retry && !isAuthCall) {
      original._retry = true;

      // 동시 401 방지를 위한 간단 큐
      if (window.__isRefreshing) {
        return new Promise((resolve, reject) => {
          (window.__refreshQueue = window.__refreshQueue || []).push(
            (newAccess) => {
              original.headers = original.headers || {};
              original.headers["Authorization"] = `Bearer ${newAccess}`;
              instance.request(original).then(resolve).catch(reject);
            }
          );
        });
      }

      window.__isRefreshing = true;
      try {
        const resp = await authApi.refreshToken();
        const { access, refresh } = resp.data || {};
        if (access) localStorage.setItem(ACCESS_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_KEY, refresh);

        const q = window.__refreshQueue || [];
        q.forEach((cb) => cb(access));
        window.__refreshQueue = [];
        window.__isRefreshing = false;

        original.headers = original.headers || {};
        original.headers["Authorization"] = `Bearer ${access}`;
        return instance.request(original);
      } catch (e) {
        window.__isRefreshing = false;
        window.__refreshQueue = [];
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
