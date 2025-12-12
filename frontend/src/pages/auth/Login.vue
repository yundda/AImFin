<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue';
// import { authApi } from '@/services/auth.api'; // 백엔드 연결 전이라 주석 처리

const router = useRouter();

const form = ref({
  username: '', 
  password: '',
  rememberMe: false
});

const handleLogin = async () => {
  // 1. 입력 확인
  if (!form.value.username || !form.value.password) {
    return alert('아이디와 비밀번호를 입력해주세요.');
  }

  // ✅ [테스트 모드] 백엔드 없이 강제 로그인
  // 실제 API 통신 코드는 주석 처리해둡니다.
  /*
  try {
    const { data } = await authApi.login({ ... });
    localStorage.setItem('accessToken', data.token);
    // ... 프로필 조회 로직 ...
  } catch (error) { ... }
  */

  // 가짜 토큰 저장 (라우터 가드를 통과하기 위함)
  localStorage.setItem('accessToken', 'test-token-12345');
  
  alert('⚡ 개발용 임시 로그인 성공! 메인으로 이동합니다.');
  router.push('/'); 
};
</script>

<template>
  <AuthLayout>
    <div class="text-center mb-10">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">로그인</h2>
      <p class="text-xs text-gray-400">스마트한 AI 포트폴리오 비교 분석 서비스 AImFIN</p>
    </div>

    <form @submit.prevent="handleLogin">
      <BaseInput
        id="login-id"
        label="ID"
        v-model="form.username"
        placeholder="janedoe@gmail.com"
      />

      <BaseInput
        id="login-password"
        label="PASSWORD"
        type="password"
        v-model="form.password"
        
      />

      <div class="flex justify-between items-center mb-8 text-xs">
        <label class="flex items-center text-gray-500 cursor-pointer">
          <input type="checkbox" v-model="form.rememberMe" class="mr-2 rounded text-[#536dfe] focus:ring-[#536dfe]" />
          로그인 정보 저장하기
        </label>
        <a href="#" class="text-gray-400 underline hover:text-gray-600">비밀번호를 잊어버리셨나요?</a>
      </div>

      <button
        type="submit"
        class="w-full bg-[#1a1a1a] text-white font-bold py-4 rounded hover:bg-gray-800 transition-colors shadow-lg"
      >
        로그인 (테스트용)
      </button>
    </form>

    <SocialLoginButtons mode="login" />
  </AuthLayout>
</template>