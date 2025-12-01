<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import SimpleDonut from '@/components/common/SimpleDonut.vue';

const router = useRouter();
const portfolio = ref(null);

onMounted(() => {
  const saved = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  if (saved.length > 0) {
    portfolio.value = saved.find(p => p.isMain) || saved[0];
  }
});

const returnRates = {
  Anjung: 3.2,
  AnjungChugu: 5.5,
  Balanced: 8.5,
  Jeogeug: 12.4,
  Aggressive: 15.8
};

const estimatedReturn = computed(() => {
  if (!portfolio.value) return 0;
  return returnRates[portfolio.value.typeCode] || 8.5;
});

const formattedAmount = computed(() => {
  return portfolio.value ? Number(portfolio.value.amount).toLocaleString() : '0';
});

const assetsInfo = [
  { label: '국내/해외 주식', color: 'bg-[#536dfe]' },
  { label: '채권', color: 'bg-[#a5b4fc]' },
  { label: '부동산/원자재', color: 'bg-[#cbd5e1]' },
  { label: '현금성 자산', color: 'bg-[#e2e8f0]' },
];

const goToList = () => {
  router.push('/user/mypage');
};

const goToCompare = () => {
  alert('📈 포트폴리오 비교 기능은 준비 중입니다.\n곧 업데이트될 예정입니다!');
};

const modifyPortfolio = () => {
  router.push({ 
    name: 'portfolio-create', 
    query: { type: portfolio.value.typeCode } 
  });
};
</script>

<template>
  <div v-if="portfolio" class="w-full max-w-6xl mx-auto mt-8 px-4 md:px-0">
    
    <!-- 대시보드 카드 -->
    <div class="bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden p-8 md:p-12 relative">
      
      <!-- 배경 장식 -->
      <div class="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 opacity-50 pointer-events-none"></div>

      <!-- 상단 헤더 -->
      <div class="flex justify-between items-center mb-6 relative z-10">
        <div class="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-[#536dfe] text-xs font-bold rounded-full">
          <span class="w-2 h-2 rounded-full bg-[#536dfe]"></span>
          대표 포트폴리오
        </div>

        <button 
          @click="goToList"
          class="flex items-center gap-1 text-sm font-bold text-gray-400 hover:text-[#536dfe] transition-colors"
        >
          <span>마이포트폴리오 리스트</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>

      <div class="flex flex-col lg:flex-row gap-12 items-center relative z-10 mb-12">
        
        <!-- 좌측: 텍스트 정보 -->
        <div class="flex-1 w-full">
          <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900 mb-2 leading-tight">
            {{ portfolio.name }}
          </h2>
          <p class="text-gray-500 mb-6">{{ portfolio.typeLabel }} 성향 기반의 AI 맞춤 전략입니다.</p>

          <!-- 메모 표시 영역 -->
          <div v-if="portfolio.memo" class="mb-8 relative pl-4 border-l-4 border-gray-200">
            <p class="text-gray-600 font-medium italic">"{{ portfolio.memo }}"</p>
          </div>

          <!-- 핵심 지표 카드 -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <div class="text-sm font-bold text-gray-400 mb-1">총 운용 자산</div>
              <div class="text-2xl font-bold text-gray-900">{{ formattedAmount }}원</div>
            </div>
            <div class="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <div class="text-sm font-bold text-gray-400 mb-1">예상 연수익률</div>
              <div class="text-2xl font-bold text-[#536dfe]">+{{ estimatedReturn }}%</div>
            </div>
          </div>
        </div>

        <!-- 우측: 대형 차트 & 범례 -->
        <div class="flex-1 flex flex-col items-center justify-center w-full">
          <div class="relative mb-8">
            <SimpleDonut :assets="portfolio.assets" size="w-72 h-72 md:w-80 md:h-80" />
            
            <!-- ✅ 수정됨: 중앙 텍스트를 포트폴리오 성향으로 변경 -->
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span class="text-2xl font-extrabold text-[#536dfe]">{{ portfolio.typeLabel }}</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-x-8 gap-y-3 w-full max-w-sm">
            <div v-for="(info, idx) in assetsInfo" :key="idx" class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors">
              <div class="flex items-center gap-3">
                <span :class="['w-3 h-3 rounded-full shadow-sm', info.color]"></span>
                <span class="text-sm text-gray-600 font-medium">{{ info.label }}</span>
              </div>
              <span class="text-base font-bold text-gray-900">{{ portfolio.assets[idx] }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 하단 기능 버튼 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-8 border-t border-gray-100">
        <button 
          @click="goToCompare"
          class="flex items-center justify-center gap-3 py-4 rounded-xl border-2 border-gray-100 hover:border-[#536dfe] hover:text-[#536dfe] hover:bg-blue-50 transition-all group"
        >
          <span class="text-2xl group-hover:scale-110 transition-transform">🆚</span>
          <div class="text-left">
            <div class="font-bold text-gray-900 group-hover:text-[#536dfe]">포트폴리오 비교하기</div>
            <div class="text-xs text-gray-400">다른 전략과 수익률을 비교해보세요</div>
          </div>
        </button>

        <button 
          @click="modifyPortfolio"
          class="flex items-center justify-center gap-3 py-4 rounded-xl bg-gray-900 hover:bg-black text-white transition-all shadow-md hover:shadow-lg group"
        >
          <span class="text-2xl group-hover:rotate-180 transition-transform duration-500">⚙️</span>
          <div class="text-left">
            <div class="font-bold">포트폴리오 수정하기</div>
            <div class="text-xs text-gray-400">투자 금액 및 선호 상품 재설정</div>
          </div>
        </button>
      </div>

    </div>
  </div>
</template>