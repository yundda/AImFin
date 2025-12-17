<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import { authApi } from '@/services/auth.api'; // API import

const route = useRoute();
const router = useRouter();

// 상태 관리
const loading = ref(true);
const error = ref(null);
const resultData = ref(null);
const showModal = ref(false);
const saveForm = ref({ name: '', memo: '' });

// URL 파라미터 파싱
const amount = Number(route.query.amount) || 0;
const horizon = route.query.horizon || 'Y_1_3';
let mustBuckets = [];
try {
  mustBuckets = JSON.parse(route.query.assets || '[]');
} catch (e) {
  console.error("JSON parse error:", e);
}

// API 호출
const fetchRecommendation = async () => {
  try {
    loading.value = true;
    const response = await authApi.recommendPortfolio({
      amount_krw: amount,
      horizon: horizon,
      must_buckets: mustBuckets
    });
    console.log("Portfolio Response:", response.data); // 디버깅용 로그
    resultData.value = response.data;
    // 저장 폼 기본 이름 설정
    saveForm.value.name = `${response.data.profile_label} 포트폴리오`;
  } catch (err) {
    console.error("Error fetching portfolio:", err);
    error.value = "분석 결과를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchRecommendation();
});

// 화면 표시용 Computed Properties
// 화면 표시용 Computed Properties
const profileLabel = computed(() => resultData.value?.profile_label || '분석 중');
const profileColor = computed(() => {
  const p = resultData.value?.profile;
  if (p === 'CONSERVATIVE') return 'bg-green-500';
  if (p === 'MODERATE_CONSERVATIVE') return 'bg-teal-500';
  if (p === 'BALANCED') return 'bg-blue-500';
  if (p === 'GROWTH') return 'bg-indigo-500';
  if (p === 'AGGRESSIVE') return 'bg-purple-500';
  return 'bg-gray-500';
});

const pieStyle = computed(() => {
  if (!resultData.value) return '';
  // 7개 버킷에 대응하는 색상 매핑
  const colorMap = {
    'STOCKS_KR': '#536dfe', 
    'STOCKS_GLB': '#3b82f6',
    'BONDS_KR': '#10b981', 
    'BONDS_GLB': '#34d399',
    'ALTERNATIVES': '#f59e0b', 
    'FUNDS': '#8b5cf6', 
    'CASH': '#cbd5e1'
  };
  
  let gradient = 'conic-gradient(';
  let currentPos = 0;
  
  resultData.value.final_allocations.forEach((item) => {
    const start = currentPos;
    const end = currentPos + item.weight_pct;
    const color = colorMap[item.bucket] || '#cccccc'; // Fallback color
    gradient += `${color} ${start}% ${end}%, `;
    currentPos = end;
  });
  
  gradient = gradient.slice(0, -2) + ')'; // 마지막 쉼표 제거
  return `background: ${gradient}`;
});

const formattedAmount = computed(() => amount.toLocaleString() + '원');

const savePortfolio = async () => {
  if (!saveForm.value.name) return alert('이름을 입력해주세요.');
  
  try {
    const payload = {
      name: saveForm.value.name,
      amount_krw: amount,
      profile: resultData.value.profile,
      profile_label: resultData.value.profile_label,
      horizon_desc: resultData.value.horizon_desc,
      must_buckets: mustBuckets, 
      allocations: resultData.value.final_allocations,
      metrics: resultData.value.metrics,
      rationale: resultData.value.rationale,
      summary: resultData.value.summary,
      risks: resultData.value.risks,
    };

    await authApi.savePortfolio(payload);
    alert('저장되었습니다!');
    router.push('/user/mypage');
  } catch (err) {
    console.error("Save failed:", err);
    alert('저장 중 오류가 발생했습니다.');
  }
};

// 메트릭 표시용
const expectedReturn = computed(() => resultData.value?.metrics?.expected_return_pct || 0);
const riskScore = computed(() => resultData.value?.metrics?.risk_score || 0);
const rationale = computed(() => resultData.value?.summary || ''); 
const assetLabels = {
  STOCKS_KR: '국내주식',
  STOCKS_GLB: '미국주식',
  BONDS_KR: '국내채권',
  BONDS_GLB: '해외채권',
  ALTERNATIVES: '대체투자',
  FUNDS: '펀드',
  CASH: '현금성자산'
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-4xl mx-auto px-6 py-12">
      <!-- 로딩 상태 -->
      <div v-if="loading" class="text-center py-20">
        <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#536dfe] mx-auto mb-4"></div>
        <p class="text-gray-500 font-medium">AI가 최고의 포트폴리오를 구성하고 있습니다...</p>
        <p class="text-xs text-gray-400 mt-2">약 5~10초 정도 소요될 수 있습니다.</p>
      </div>

      <!-- 에러 상태 -->
      <div v-else-if="error" class="text-center py-20 bg-white rounded-3xl shadow-lg border border-gray-100 p-10">
        <div class="text-red-500 text-6xl mb-4">⚠️</div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">오류가 발생했습니다</h3>
        <p class="text-gray-600 mb-8">{{ error }}</p>
        <button @click="router.push('/survey')" class="px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-600 hover:bg-gray-50">다시 시도하기</button>
      </div>

      <!-- 결과 표시 -->
      <div v-else class="bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden text-center p-10">
        
        <div class="text-sm font-bold text-gray-400 mb-2">AI 맞춤 분석 결과</div>
        <h2 class="text-3xl font-bold text-gray-900 mb-2">나만의 AI 포트폴리오</h2>
        <p class="text-gray-500 mb-8">
          투자금 <span class="font-bold text-[#536dfe]">{{ formattedAmount }}</span>, 
          기간 <span class="font-bold text-gray-700">{{ resultData.horizon_desc }}</span>
        </p>
        
        <span class="inline-block px-4 py-1.5 rounded-full text-white text-sm font-bold mb-10" :class="profileColor">
          {{ profileLabel }}
        </span>

        <!-- 차트 영역 -->
        <div class="relative w-64 h-64 mx-auto rounded-full mb-8 shadow-lg scale-100 hover:scale-105 transition-transform duration-500" :style="pieStyle">
          <div class="absolute inset-4 bg-white rounded-full flex flex-col items-center justify-center shadow-inner">
            <span class="text-sm text-gray-400 font-medium">기대 수익률</span>
            <span class="text-3xl font-bold text-[#536dfe]">+{{ expectedReturn }}%</span>
          </div>
        </div>

        <!-- 위험도 게이지 (추가) -->
        <div class="max-w-xs mx-auto mb-12">
          <div class="flex justify-between items-end mb-2 px-1">
            <span class="text-xs font-bold text-gray-400">위험도 진단</span>
            <span class="text-sm font-bold" :class="riskScore > 60 ? 'text-red-500' : (riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">
              {{ riskScore }}점 ({{ riskScore > 60 ? '높음' : (riskScore > 40 ? '중간' : '낮음') }})
            </span>
          </div>
          <div class="h-3 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative">
            <div 
              class="absolute top-1/2 -translate-y-1/2 w-1 h-5 bg-gray-800 rounded-sm shadow-sm transition-all duration-1000 ease-out"
              :style="{ left: riskScore + '%' }"
            ></div>
          </div>
          <div class="flex justify-between text-[10px] text-gray-400 mt-1.5 font-medium px-1">
            <span>안전 (0)</span>
            <span>중간 (50)</span>
            <span>위험 (100)</span>
          </div>
        </div>

        <!-- AI 코멘트  -->
        <div class="bg-blue-50 p-6 rounded-xl text-left mb-10">
          <h4 class="font-bold text-[#536dfe] mb-2 flex items-center">
            <span class="text-xl mr-2">💡</span> AI 투자 전략
          </h4>
          <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{{ summary }}</p>
        </div>

        <!-- 자산 배분 리스트 -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm mb-12 bg-gray-50 p-6 rounded-xl">
          <div v-for="item in resultData.final_allocations" :key="item.bucket" class="flex justify-between items-center bg-white px-3 py-2 rounded border border-gray-100">
            <span class="font-medium text-gray-600">{{ assetLabels[item.bucket] || item.bucket }}</span>
            <span class="font-bold text-[#536dfe]">{{ item.weight_pct }}%</span>
          </div>
        </div>

        <div class="flex gap-4 justify-center">
          <button @click="router.push('/survey')" class="px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-600 hover:bg-gray-50">다시 진단하기</button>
          <button @click="showModal = true" class="px-8 py-3 bg-[#536dfe] text-white rounded-xl font-bold hover:bg-[#4059e0] shadow-md">내 포트폴리오에 저장</button>
        </div>
      </div>
    </div>

    <!-- 저장 모달 -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative animate-fade-in-up">
        <h3 class="text-xl font-bold mb-6">포트폴리오 저장</h3>
        <BaseInput label="포트폴리오 이름" v-model="saveForm.name" placeholder="예: 2024년 1억 만들기 플랜" />
        <div class="h-4"></div>
        <div class="flex gap-3 justify-end">
          <button @click="showModal = false" class="px-6 py-2.5 border border-gray-300 rounded-lg font-bold text-gray-500 hover:bg-gray-50">취소</button>
          <button @click="savePortfolio" class="px-6 py-2.5 bg-[#536dfe] text-white rounded-lg font-bold hover:bg-[#4059e0]">저장하기</button>
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.animate-fade-in-up { animation: fadeInUp 0.3s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>