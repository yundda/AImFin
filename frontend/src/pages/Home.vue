<script setup>
import { ref } from 'vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import MarketTicker from '@/components/home/MarketTicker.vue'; // 흐르는 티커
import PortfolioEmpty from '@/components/home/PortfolioEmpty.vue'; // 설문 유도

// 나중에 백엔드에서 '포트폴리오 생성 여부'를 받아와서 true/false로 바꿉니다.
const hasPortfolio = ref(false); 
</script>

<template>
  <DefaultLayout>
    <!-- 1. 상단: 흐르는 지수 티커 -->
    <MarketTicker />

    <!-- 2. 메인 컨텐츠 -->
    <div class="px-6 py-10 relative">
      
      <!-- 포트폴리오가 없을 때 (초기 상태) -->
      <div v-if="!hasPortfolio" class="fade-in">
        <PortfolioEmpty />
      </div>

      <!-- 포트폴리오가 있을 때 (나중에 구현) -->
      <div v-else>
        <h2 class="text-2xl font-bold mb-4">나의 자산 현황</h2>
        <!-- 포트폴리오 대시보드 컴포넌트 -->
      </div>

    </div>
  </DefaultLayout>
</template>

<style scoped>
.fade-in {
  animation: fadeIn 0.8s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>