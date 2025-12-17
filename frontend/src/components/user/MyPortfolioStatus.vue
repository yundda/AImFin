<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';
import MyPortfolioList from './MyPortfolioList.vue';
import SimpleDonut from '@/components/common/SimpleDonut.vue';

const router = useRouter();
const portfolios = ref([]);
const mainPortfolioDetail = ref(null);
const isListView = ref(false);
const loading = ref(true);

const loadData = async () => {
  loading.value = true;
  try {
    // 1. 리스트 조회 (개수 등)
    const listRes = await authApi.getPortfolioList();
    portfolios.value = listRes.data;

    // 2. 대표 포트폴리오 상세 조회 (차트용 자산배분 정보 필요)
    try {
      const repRes = await authApi.getRepresentativePortfolio();
      mainPortfolioDetail.value = repRes.data;
    } catch (e) {
      // 대표 포인트가 없거나 에러 시 무시 (리스트에서 첫번째라도 가져올 수 있으면 좋겠지만, 대표 api가 있기에 그것 사용)
      mainPortfolioDetail.value = null;
    }

  } catch (err) {
    console.error("Failed to load portfolio status:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);

const handleListBack = () => {
  isListView.value = false;
  loadData(); 
};

// 날짜 포맷
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString();
};

// 자산 배분 매핑 (API Allocations -> [주식, 채권, 부동산, 현금])
const mainAssets = computed(() => {
  if (!mainPortfolioDetail.value) return [0, 0, 0, 0];
  
  const p = mainPortfolioDetail.value;
  let stocks = 0, bonds = 0, alts = 0, cash = 0;
  
  if (p.allocations) {
    p.allocations.forEach(a => {
      const w = a.weight_pct || 0;
      if (['STOCKS_KR', 'STOCKS_GLB'].includes(a.bucket)) stocks += w;
      else if (['BONDS_KR', 'BONDS_GLB'].includes(a.bucket)) bonds += w;
      else if (['ALTERNATIVES', 'FUNDS'].includes(a.bucket)) alts += w;
      else if (['CASH'].includes(a.bucket)) cash += w;
    });
  }
  
  return [
    Number(stocks.toFixed(1)), 
    Number(bonds.toFixed(1)), 
    Number(alts.toFixed(1)), 
    Number(cash.toFixed(1))
  ];
});
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

      <!-- 로딩 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#536dfe]"></div>
      </div>

      <!-- 포트폴리오 없을 때 -->
      <div v-else-if="portfolios.length === 0" class="flex-1 flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-3xl mb-4 text-[#536dfe]">📈</div>
        <p class="text-gray-400 text-sm mb-6">아직 생성된 포트폴리오가 없습니다.</p>
        <button @click="router.push('/survey')" class="px-8 py-3 bg-[#536dfe] text-white font-bold rounded-xl hover:bg-[#4059e0] shadow-lg">
          포트폴리오 만들기
        </button>
      </div>

      <!-- 있을 때: 대표 포트폴리오 요약 -->
      <div v-else-if="mainPortfolioDetail" class="flex-1 flex flex-col">
        <!-- 상단 카드 -->
        <div class="grid grid-cols-3 gap-4 mb-4">
          <div class="bg-gray-50 rounded-xl p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">포트폴리오명</div>
            <div class="text-sm font-bold text-gray-900 truncate">{{ mainPortfolioDetail.name }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">투자 성향</div>
            <div class="text-sm font-bold text-[#536dfe]">{{ mainPortfolioDetail.profile_label }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1 font-bold">생성일</div>
            <div class="text-sm font-bold text-gray-900">{{ formatDate(mainPortfolioDetail.created_at) }}</div>
          </div>
        </div>

        <!-- 차트 영역 -->
        <div class="border border-gray-100 rounded-2xl p-4 sm:p-6 flex items-center justify-between mt-auto">
          <div>
            <h3 class="font-bold text-gray-900 mb-4">AI 추천 자산 배분</h3>
            <div class="space-y-2 text-sm text-gray-600">
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#536dfe] rounded-full"></span>주식 {{ mainAssets[0] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#a5b4fc] rounded-full"></span>채권 {{ mainAssets[1] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#cbd5e1] rounded-full"></span>부동산 {{ mainAssets[2] }}%</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#e2e8f0] rounded-full"></span>현금 {{ mainAssets[3] }}%</div>
            </div>
          </div>
          
          <!-- 도넛 차트 -->
          <div class="relative w-28 h-28 sm:w-32 sm:h-32">
            <SimpleDonut :assets="mainAssets" size="w-28 h-28 sm:w-32 sm:h-32" />
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span class="text-sm font-bold text-[#536dfe]">{{ mainPortfolioDetail.profile_label }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 리스트는 있지만 상세 로드 실패 시 (Fallback) -->
      <div v-else class="flex-1 flex items-center justify-center text-gray-400">
        대표 포트폴리오 상세 정보를 불러올 수 없습니다.
      </div>

    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>