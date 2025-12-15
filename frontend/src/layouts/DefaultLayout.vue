<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const handleLogout = async() => {
  // 로그아웃 로직
  await authStore.logout();
  router.push('/auth/login');
};
</script>

<template>
  <div class="min-h-screen bg-[#F5F7FA] flex flex-col font-sans">
    <!-- 헤더 (네비게이션) -->
    <nav class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 sticky top-0 z-50">
      <!-- 1. 로고: 클릭 시 메인('/')으로 이동 -->
      <router-link to="/" class="text-xl font-bold text-[#536dfe]">AImFIN.</router-link>
      
      <!-- 우측 메뉴 -->
      <div class="flex items-center gap-6">
        <!-- 2. 뉴스: 클릭 시 '/news'로 이동 -->
        <router-link to="/news" class="text-sm font-medium text-gray-600 hover:text-black transition-colors">
          뉴스
        </router-link>
        
        <!-- 3. 마이페이지: 클릭 시 '/user/mypage'로 이동 -->
        <router-link to="/user/mypage" class="text-sm font-medium text-gray-600 hover:text-black transition-colors">
          마이페이지
        </router-link>
        
        <button @click="handleLogout" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
          로그아웃
        </button>
      </div>
    </nav>

    <!-- 페이지 컨텐츠 -->
    <main class="flex-1 w-full relative">
      <slot></slot>
    </main>

    <!-- 푸터 -->
    <footer class="py-6 text-center text-[10px] text-gray-400 mt-auto">
      &copy; 2021. - 2026 All Rights Reserved. AImFIN
    </footer>
  </div>
</template>