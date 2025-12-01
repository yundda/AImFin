<script setup>
import { ref, onMounted } from 'vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import MarketTicker from '@/components/home/MarketTicker.vue';
import PortfolioEmpty from '@/components/home/PortfolioEmpty.vue';
// ✅ 대시보드 컴포넌트 import
import PortfolioDashboard from '@/components/home/PortfolioDashboard.vue'; 

const hasPortfolio = ref(false);

onMounted(() => {
  // 로컬 스토리지 확인하여 포트폴리오 존재 여부 판단
  const saved = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  hasPortfolio.value = saved.length > 0;
});
</script>

<template>
  <DefaultLayout>
    <!-- 1. 상단: 흐르는 지수 티커 (공통) -->
    <MarketTicker />

    <!-- 2. 메인 컨텐츠 -->
    <div class="min-h-[calc(100vh-120px)] bg-gradient-to-b from-[#F5F7FA] to-white relative overflow-hidden px-6 py-10">
      
      <!-- 배경 장식 (패턴) -->
      <div class="absolute top-20 left-0 w-full h-[500px] bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] pointer-events-none"></div>

      <div class="relative z-10">
        
        <!-- ✅ 조건부 렌더링 -->
        <!-- Case A: 포트폴리오가 있을 때 (대시보드) -->
        <div v-if="hasPortfolio" class="fade-in">
          <PortfolioDashboard />
        </div>

        <!-- Case B: 포트폴리오가 없을 때 (설문 유도) -->
        <div v-else class="fade-in">
          <PortfolioEmpty />
        </div>

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