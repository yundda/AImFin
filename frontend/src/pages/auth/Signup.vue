<script setup lang="ts">
import { ref } from 'vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue';

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
  // TODO: 실제 회원가입 API 호출
  console.log('회원가입 정보:', form.value);
  alert('계정 생성 요청이 전송되었습니다.');
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