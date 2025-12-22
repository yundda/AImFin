<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

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

  try {
    await authStore.login(form.value.username, form.value.password);
    
    // 닉네임 유무 확인 후 리다이렉트
    if (!authStore.user?.nickname) {
      router.push('/onboarding/nickname');
    } else {
      router.push('/');
    } 
  } catch (error) {
    console.error('Login failed:', error);
    alert('로그인 실패: ' + (error.response?.data?.detail || '아이디 또는 비밀번호를 확인해주세요.'));
  }
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
        label="이메일"
        v-model="form.username"
        placeholder="janedoe@gmail.com"
      />

      <BaseInput
        id="login-password"
        label="비밀번호"
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
        로그인
      </button>
    </form>

    <SocialLoginButtons mode="login" />
  </AuthLayout>
</template>