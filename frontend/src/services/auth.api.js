import axios from "axios";

// Axios 인스턴스 생성
const instance = axios.create({
  // .env 파일에 VITE_API_URL이 있으면 그걸 쓰고, 없으면 로컬호스트를 씁니다.
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // ✅ 쿠키 전송 허용
});

// Auth API 객체
export const authApi = {
  // 회원가입
  signup: (userData) => instance.post("/users/auth/signup", userData),

  // 로그인
  login: (credentials) => instance.post("/users/auth/login", credentials),

  // 로그아웃
  logout: () => instance.post("/users/auth/logout"),

  // 토큰 리프레시
  refreshToken: () => {
    const refresh = localStorage.getItem('refresh_token');
    return instance.post("/users/auth/refresh", { refresh });
  },

  // 프로필 조회
  getProfile: () => instance.get("/users/profile"),

  // 닉네임 수정
  updateNickname: (nickname) => instance.patch("/users/profile/nickname", { nickname }),

  // 설문 결과 저장
  saveSurvey: (payload) => instance.post("/users/survey/save", payload),

  // 최신 설문 결과 조회
  getSurvey: () => instance.get("/users/survey/current"),

  // 투자 선호도 저장
  savePreference: (payload) => instance.post("/users/preference/save", payload),

  // 포트폴리오 추천 요청
  recommendPortfolio: (payload) => instance.post("/analysis/recommend/portfolio", payload),

  // 포트폴리오 저장
  savePortfolio: (payload) => instance.post("/portfolios/save", payload),

  // 포트폴리오 목록 조회
  getPortfolioList: () => instance.get("/portfolios/list"),

  // 대표 포트폴리오 조회
  getRepresentativePortfolio: () => instance.get("/portfolios/representative"),

  // 대표 포트폴리오 설정
  setRepresentative: (id) => instance.post("/portfolios/representative", { id }),

  // 포트폴리오 상세 조회
  getPortfolioDetail: (id) => instance.get(`/portfolios/${id}`),

  // 포트폴리오 수정 (이름, 메모)
  updatePortfolio: (id, data) => instance.patch(`/portfolios/${id}/update`, data),

  // 포트폴리오 삭제
  deletePortfolio: (id) => instance.delete(`/portfolios/${id}/delete`),
};

// Interceptor로 401 발생 시 자동 갱신 처리
instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // 401 에러이고, 아직 재시도하지 않은 요청이며, 리프레시 요청 자체가 아닐 때
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      originalRequest._retry = true;
      try {
        console.log("Token expired. Attempting refresh...");
        const refreshResponse = await authApi.refreshToken();
        const { access, refresh } = refreshResponse.data;

        // 새로 받은 토큰 저장
        if (access) localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);

        console.log("Refresh successful. New Access Token:", access);
        console.log("Refresh successful. New Refresh Token:", refresh);

        console.log("Retrying original request...");
        return instance(originalRequest);
      } catch (refreshError) {
        console.error("RefreshToken failed:", refreshError);
        // 리프레시 실패 시 로그아웃 처리나 로그인 페이지 이동 등을 수행할 수 있음
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
