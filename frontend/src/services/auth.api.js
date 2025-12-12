import axios from "axios";

// Axios 인스턴스 생성
const instance = axios.create({
  // .env 파일에 VITE_API_URL이 있으면 그걸 쓰고, 없으면 로컬호스트를 씁니다.
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // ✅ 쿠키 전송 허용
});

// 요청 인터셉터 (더 이상 Bearer 토큰을 헤더에 넣을 필요 없음 - 쿠키 사용)
// instance.interceptors.request.use(...) 


export default instance;
