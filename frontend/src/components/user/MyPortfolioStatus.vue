<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import MyPortfolioList from './MyPortfolioList.vue';
import SimpleDonut from '@/components/common/SimpleDonut.vue'; // ✅ 차트 컴포넌트 추가

const router = useRouter();
const portfolios = ref([]);
const isListView = ref(false);

const loadPortfolios = () => {
  portfolios.value = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
};

onMounted(loadPortfolios);

// 대표 포트폴리오 찾기
const mainPortfolio = computed(() => {
  return portfolios.value.find(p => p.isMain) || portfolios.value[0];
});

const handleListBack = () => {
  isListView.value = false;
  loadPortfolios(); 
};
</script>

<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 h-full flex flex-col relative">
    
    <!-- 1. 리스트 보기 모드 -->
    <MyPortfolioList v-if="isListView" @back="handleListBack" class="animate-fade-in" />

    <!-- 2. 요약 화면 (대시보드) -->
    <div v-else class="h-full flex flex-col">
      <div class="flex justify-between items-start mb-8">
        <div>
          <h2 class="text-2xl font-bold text-[#536dfe] mb-1">내 포트폴리오</h2>
          <p v-if="portfolios.length > 0" class="text-sm text-gray-400">
            총 {{ portfolios.length }}개의 포트폴리오를 관리 중입니다.
          </p>
        </div>
        <button 
          v-if="portfolios.length > 0" 
          @click="isListView = true"
          class="px-4 py-2 bg-[#536dfe] text-white text-xs font-bold rounded-full hover:bg-[#4059e0] transition-colors shadow-sm"
        >
          마이 포트폴리오 리스트 >
        </button>
      </div>

      <!-- 포트폴리오 없을 때 -->
      <div v-if="portfolios.length === 0" class="flex-1 flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-3xl mb-4 text-[#536dfe]">📈</div>
        <p class="text-gray-400 text-sm mb-6">아직 생성된 포트폴리오가 없습니다.</p>
        <button @click="router.push('/survey')" class="px-8 py-3 bg-[#536dfe] text-white font-bold rounded-xl hover:bg-[#4059e0] shadow-lg">
          포트폴리오 만들기
        </button>
      </div>

      <!-- 있을 때: 대표 포트폴리오 요약 -->
      <div v-else class="flex-1 flex flex-col">
        <!-- 상단 카드 -->
        <div class="grid grid-cols-3 gap-4 mb-8">
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">포트폴리오명</div>
            <div class="text-sm font-bold text-gray-900 truncate">{{ mainPortfolio.name }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">투자 성향</div>
            <div class="text-sm font-bold text-[#536dfe]">{{ mainPortfolio.typeLabel }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">생성일</div>
            <div class="text-sm font-bold text-gray-900">{{ mainPortfolio.date }}</div>
          </div>
        </div>

        <!-- 차트 영역 -->
        <div class="border border-gray-100 rounded-2xl p-6 flex items-center justify-between">
          <div>
            <h3 class="font-bold text-gray-900 mb-4">AI 추천 자산 배분</h3>
            <div class="space-y-2 text-sm text-gray-600">
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#536dfe] rounded-full"></span>주식 {{ mainPortfolio.assets[0] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#a5b4fc] rounded-full"></span>채권 {{ mainPortfolio.assets[1] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#cbd5e1] rounded-full"></span>부동산 {{ mainPortfolio.assets[2] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#e2e8f0] rounded-full"></span>현금 {{ mainPortfolio.assets[3] }}%</div>
            </div>
          </div>
          
          <!-- ✅ 도넛 차트 및 텍스트 수정 -->
          <div class="relative w-32 h-32">
            <SimpleDonut :assets="mainPortfolio.assets" size="w-32 h-32" />
            
            <!-- 중앙 텍스트 오버레이 -->
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span class="text-sm font-bold text-[#536dfe]">{{ mainPortfolio.typeLabel }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>