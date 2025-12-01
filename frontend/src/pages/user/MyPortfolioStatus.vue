<script setup>
import { ref, onMounted } from 'vue';

const portfolios = ref([]);
const mainId = ref(null); // 대표 포트폴리오 ID

onMounted(() => {
  // 로컬 스토리지에서 불러오기 (나중엔 API 호출)
  portfolios.value = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  if (portfolios.value.length > 0) mainId.value = portfolios.value[0].id;
});

const createPortfolio = () => {
  // router.push('/survey'); // 설문 페이지로 이동
};

const deletePortfolio = (id) => {
  if(!confirm('정말 삭제하시겠습니까?')) return;
  portfolios.value = portfolios.value.filter(p => p.id !== id);
  localStorage.setItem('my_portfolios', JSON.stringify(portfolios.value));
};

const setMain = (id) => {
  mainId.value = id;
};
</script>

<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 h-full flex flex-col">
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-2xl font-bold text-[#536dfe]">내 포트폴리오</h2>
      <button v-if="portfolios.length > 0" class="px-4 py-2 bg-[#536dfe] text-white text-xs font-bold rounded-full hover:bg-[#4059e0]">
        마이 포트폴리오
      </button>
    </div>

    <!-- 1. 포트폴리오 없을 때 -->
    <div v-if="portfolios.length === 0" class="flex-1 flex flex-col items-center justify-center text-center">
      <div class="text-4xl mb-4 text-gray-200">📈</div>
      <p class="text-gray-400 text-sm mb-6">아직 생성된 포트폴리오가 없습니다.</p>
      <button @click="$router.push('/survey')" class="px-6 py-3 bg-[#536dfe] text-white font-bold rounded-lg shadow-md hover:bg-[#4059e0]">
        포트폴리오 만들기
      </button>
    </div>

    <!-- 2. 리스트 있을 때 -->
    <div v-else class="space-y-4 overflow-y-auto max-h-[600px] pr-2 custom-scroll">
      <div 
        v-for="p in portfolios" 
        :key="p.id" 
        class="border rounded-xl p-5 hover:border-[#536dfe] transition-all group relative cursor-pointer"
        :class="mainId === p.id ? 'border-[#536dfe] bg-blue-50/30' : 'border-gray-200'"
        @click="setMain(p.id)"
      >
        <!-- 대표 설정 체크박스 (왼쪽 상단) -->
        <div class="absolute top-4 left-4 text-[#536dfe]" v-if="mainId === p.id">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
        </div>

        <!-- 삭제 버튼 (우측 상단) -->
        <button @click.stop="deletePortfolio(p.id)" class="absolute top-4 right-4 text-gray-300 hover:text-red-500 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
        </button>

        <div class="pl-10">
          <div class="flex items-center gap-2 mb-1">
            <h3 class="font-bold text-gray-900">{{ p.name }}</h3>
            <span class="text-xs text-gray-400">✎</span>
          </div>
          <span class="inline-block px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded mb-4">{{ p.type }}</span>
          
          <!-- 미니 차트 정보 -->
          <div class="grid grid-cols-2 gap-y-1 text-xs text-gray-500">
            <div class="flex items-center gap-1"><span class="w-2 h-2 bg-[#536dfe] rounded-full"></span>주식 {{ p.assets[0] }}%</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 bg-[#a5b4fc] rounded-full"></span>채권 {{ p.assets[1] }}%</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 bg-[#cbd5e1] rounded-full"></span>부동산 {{ p.assets[2] }}%</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 bg-[#e2e8f0] rounded-full"></span>현금 {{ p.assets[3] }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #e2e8f0; border-radius: 3px; }
</style>
```

### 4. 라우터 추가 (`src/router/index.js`)

`survey-result` 라우트를 추가합니다.

```javascript
// ...
import SurveyResult from '@/pages/SurveyResult.vue'; // ✅ 추가

const router = createRouter({
  // ...
  routes: [
    // ...
    { path: '/survey/result', name: 'survey-result', component: SurveyResult }, // ✅ 추가
  ]
})