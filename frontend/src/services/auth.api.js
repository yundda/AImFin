// src/services/auth.api.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

const instance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // 쿠키 사용 시
});

// 요청 인터셉터: Authorization 자동 첨부
// 요청 인터셉터에서 ↓ 추가
instance.interceptors.request.use((config) => {
  const isRefresh = config.url?.includes("/users/auth/refresh");
  const access = localStorage.getItem("access_token");
  if (!isRefresh && access) {
    // <-- 리프레시 요청은 스킵
    config.headers = config.headers || {};
    if (!config.headers["Authorization"]) {
      config.headers["Authorization"] = `Bearer ${access}`;
    }
  }
  return config;
});

// 인증 관련 API 래퍼
export const authApi = {
  // 회원가입
  signup: (userData) => instance.post("/users/auth/signup", userData),

  // 로그인: 받은 토큰 저장
  login: async (credentials) => {
    const resp = await instance.post("/users/auth/login", credentials);
    const { access, refresh } = resp.data || {};
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    return resp;
  },

  // 로그아웃: 서버 호출 후 로컬 토큰 삭제
  logout: async () => {
    try {
      await instance.post("/users/auth/logout");
    } finally {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    }
  },

  // 토큰 리프레시
  refreshToken: () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    return instance.post("/users/auth/refresh", { refresh });
  },

  // 프로필/설문/선호/추천
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
};

// 401 자동-리프레시(동시에 여러 요청 들어와도 1회만 시도)
let isRefreshing = false;
let queue = [];
const enqueue = (cb) => queue.push(cb);
const flush = (newToken) => {
  queue.forEach((cb) => cb(newToken));
  queue = [];
};

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

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          enqueue((newAccess) => {
            original.headers = original.headers || {};
            original.headers["Authorization"] = `Bearer ${newAccess}`;
            instance.request(original).then(resolve).catch(reject);
          });
        });
      }

      isRefreshing = true;
      try {
        const resp = await authApi.refreshToken();
        const { access, refresh } = resp.data || {};
        if (access) localStorage.setItem(ACCESS_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
        isRefreshing = false;
        flush(access);

        original.headers = original.headers || {};
        original.headers["Authorization"] = `Bearer ${access}`;
        return instance.request(original);
      } catch (e) {
        isRefreshing = false;
        queue = [];
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
