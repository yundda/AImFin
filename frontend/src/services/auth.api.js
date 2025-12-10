import axios from "axios";

// Axios 인스턴스 생성
const instance = axios.create({
  // .env 파일에 VITE_API_URL이 있으면 그걸 쓰고, 없으면 로컬호스트를 씁니다.
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청 인터셉터: API 요청을 보낼 때마다 토큰이 있으면 헤더에 자동으로 실어 보냅니다.
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default instance;
