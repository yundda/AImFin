<script setup lang="ts">
import { ref } from 'vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue';

import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';

const router = useRouter();

const form = ref({
  email: '',
  password: '',
  agreeTerms: false
});

const handleSignup = async () => {
  if (!form.value.agreeTerms) {
    alert('이용약관에 동의해주세요.');
    return;
  }
  
  try {
    await authApi.signup({
      email: form.value.email,
      password: form.value.password
    });
    alert('회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.');
    router.push('/login');
  } catch (error) {
    console.error('Signup failed:', error);
    // DRF returns object with field errors, e.g. { email: [...], non_field_errors: [...] }
    const errorData = error.response?.data || {};
    let msg = '회원가입 실패';
    
    if (Object.keys(errorData).length > 0) {
      // Create a readable error message from the object
      const details = Object.entries(errorData)
        .map(([key, msgs]) => `${key}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
        .join('\n');
      msg += `:\n${details}`;
    } else {
      msg += `: ${error.message}`;
    }
    
    alert(msg);
  }
};
</script>

<template>
  <AuthLayout>
    <div class="text-center mb-10">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">계정 생성</h2>
      <p class="text-xs text-gray-400">스마트한 AI 포트폴리오 비교 분석 서비스 AImFIN</p>
    </div>

    <form @submit.prevent="handleSignup">
      <BaseInput
        id="signup-email"
        label="EMAIL ADDRESS"
        v-model="form.email"
        placeholder="johndoe@example.com"
      />

      <BaseInput
        id="signup-password"
        label="PASSWORD"
        type="password"
        v-model="form.password"
        placeholder="**********"
      />

      <div class="mb-8 text-xs">
        <label class="flex items-center text-gray-500 cursor-pointer">
          <input type="checkbox" v-model="form.agreeTerms" class="mr-2 rounded text-[#536dfe] focus:ring-[#536dfe]" />
          <span class="border-b border-gray-400">AImFIN의 이용약관 및 개인정보 수집에 동의합니다.</span>
        </label>
      </div>

      <button
        type="submit"
        class="w-full bg-[#1a1a1a] text-white font-bold py-4 rounded hover:bg-gray-800 transition-colors shadow-lg"
      >
        계정 생성하기
      </button>
    </form>

    <SocialLoginButtons mode="signup" />
  </AuthLayout>
</template>