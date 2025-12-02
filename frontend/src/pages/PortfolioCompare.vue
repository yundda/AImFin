<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import SimpleDonut from '@/components/common/SimpleDonut.vue';
import BaseInput from '@/components/common/BaseInput.vue';

const router = useRouter();

// --- 상태 관리 ---
const step = ref('select'); 
const portfolios = ref([]);
const selectedIds = ref([null, null]); 
const showSelectModal = ref(false);
const selectingIndex = ref(0);

// 분석 상태
const showComparisonReport = ref(false); // 비교 분석 리포트 표시 여부

// 리밸런싱 관련
const isRebalancing = ref(false);
const tempPortfolio = ref(null);
const rebalancedAssets = ref([]);
const showSaveModal = ref(false);
const saveForm = ref({ name: '', memo: '' });

// 자산 정보
const assetLabels = ['주식', '채권', '부동산', '현금'];
const assetColors = ['#536dfe', '#a5b4fc', '#cbd5e1', '#e2e8f0'];

onMounted(() => {
  const saved = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  
  saved.unshift({
    id: 'ai-balanced', name: 'AI 추천 포트폴리오', typeLabel: '균형형', 
    assets: [40, 30, 20, 10], typeCode: 'Balanced', isAi: true,
    aiComment: 'AI가 제안하는 가장 이상적인 균형 포트폴리오입니다. 시장 변동성에 강한 면모를 보입니다.'
  });
  
  portfolios.value = saved;
});

const leftP = computed(() => portfolios.value.find(p => p.id === selectedIds.value[0]));

const rightP = computed(() => {
  if (tempPortfolio.value) return tempPortfolio.value;
  return portfolios.value.find(p => p.id === selectedIds.value[1]);
});

// 수치 계산 로직
const calculateStats = (assets) => {
  if (!assets) return { returnRate: 0, riskScore: 0 };
  const weights = { return: [12, 5, 7, 2], risk: [90, 20, 50, 0] };
  let wReturn = 0, wRisk = 0;
  assets.forEach((percent, i) => {
    wReturn += percent * weights.return[i];
    wRisk += percent * weights.risk[i];
  });
  return { returnRate: (wReturn / 100).toFixed(1), riskScore: Math.round(wRisk / 100) };
};

const leftStats = computed(() => calculateStats(leftP.value?.assets));
const rightStats = computed(() => calculateStats(rightP.value?.assets));

// 기능 함수들
const openSelectModal = (idx) => { selectingIndex.value = idx; showSelectModal.value = true; };
const selectPortfolio = (id) => { 
  selectedIds.value[selectingIndex.value] = id; 
  showSelectModal.value = false;
  if (selectingIndex.value === 1) {
    tempPortfolio.value = null;
    showComparisonReport.value = false; // 포트폴리오 바뀌면 분석 결과 초기화
  }
};

const startAnalysis = () => {
  if (!leftP.value || !rightP.value) return alert('비교할 포트폴리오를 모두 선택해주세요.');
  step.value = 'analyze';
};

// 비교 분석 실행
const runComparison = () => {
  // 로딩 효과 등을 넣을 수 있음
  showComparisonReport.value = true;
  // 스크롤을 아래로 부드럽게 이동
  setTimeout(() => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }, 100);
};

const toggleRebalance = () => {
  if (!isRebalancing.value) {
    rebalancedAssets.value = [...rightP.value.assets];
  }
  isRebalancing.value = !isRebalancing.value;
};

// 리밸런싱 적용 및 분석
const analyzeRebalance = () => {
  const total = rebalancedAssets.value.reduce((a, b) => a + b, 0);
  if (total !== 100) return alert(`자산 비중의 합이 ${total}%입니다. 100%를 맞춰주세요.`);
  
  // 임시 포트폴리오 생성 (AI 코멘트 포함)
  tempPortfolio.value = {
    ...rightP.value, id: 'temp-' + Date.now(),
    name: rightP.value.name.includes('(조정됨)') ? rightP.value.name : `${rightP.value.name} (조정됨)`,
    assets: [...rebalancedAssets.value], isTemp: true,
    // 리밸런싱에 대한 AI 분석 생성 (가상)
    aiComment: `주식 비중을 ${rebalancedAssets.value[0]}%로 조정하여 기대 수익률이 변화했습니다. 이전보다 ${rebalancedAssets.value[0] > 40 ? '공격적' : '보수적'}인 전략으로 수정되었습니다.`
  };
  isRebalancing.value = false;
  showComparisonReport.value = false; // 리밸런싱 했으니 전체 비교 분석은 다시 해야 함
};

const resetRebalance = () => { 
  tempPortfolio.value = null; 
  showComparisonReport.value = false;
};

const openSaveModal = () => {
  saveForm.value = { name: rightP.value.name, memo: '' };
  showSaveModal.value = true;
};

const saveNewPortfolio = () => {
  const newP = {
    ...rightP.value, id: Date.now(),
    name: saveForm.value.name, memo: saveForm.value.memo,
    isAi: false, isTemp: false, date: new Date().toLocaleDateString()
  };
  const saved = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  saved.push(newP);
  localStorage.setItem('my_portfolios', JSON.stringify(saved));
  portfolios.value.push(newP);
  selectedIds.value[1] = newP.id;
  tempPortfolio.value = null;
  showSaveModal.value = false;
  alert('포트폴리오가 저장되었습니다!');
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="text-center mb-10">
        <h2 class="text-3xl font-bold text-gray-900">포트폴리오 비교하기</h2>
        <p class="text-gray-500 mt-2">두 개의 전략을 나란히 놓고 분석해보세요</p>
      </div>

      <!-- [STEP 1] 선택 화면 -->
      <div v-if="step === 'select'" class="flex flex-col md:flex-row items-center justify-center gap-8 fade-in">
        <div @click="openSelectModal(0)" class="w-full max-w-sm h-80 rounded-3xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-[#536dfe] hover:bg-blue-50/30 transition-all group relative bg-white">
          <div v-if="leftP" class="text-center w-full h-full p-8 flex flex-col items-center justify-center">
            <h3 class="font-bold text-xl mb-2">{{ leftP.name }}</h3>
            <span class="px-2 py-1 bg-gray-100 text-xs rounded text-gray-500">{{ leftP.typeLabel }}</span>
            <div class="mt-6"><SimpleDonut :assets="leftP.assets" size="w-32 h-32" /></div>
            <button class="absolute top-4 right-4 text-gray-400 hover:text-[#536dfe]">🔄</button>
          </div>
          <div v-else class="text-center">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-3xl mb-4 text-gray-400 group-hover:bg-[#536dfe] group-hover:text-white transition-colors">＋</div>
            <p class="text-gray-500 font-bold">포트폴리오 선택</p>
          </div>
        </div>

        <div class="w-12 h-12 rounded-full bg-[#536dfe] text-white flex items-center justify-center font-bold text-lg shadow-lg z-10">VS</div>

        <div @click="openSelectModal(1)" class="w-full max-w-sm h-80 rounded-3xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-[#536dfe] hover:bg-blue-50/30 transition-all group relative bg-white">
          <div v-if="rightP" class="text-center w-full h-full p-8 flex flex-col items-center justify-center">
            <h3 class="font-bold text-xl mb-2">{{ rightP.name }}</h3>
            <span class="px-2 py-1 bg-gray-100 text-xs rounded text-gray-500">{{ rightP.typeLabel }}</span>
            <div class="mt-6"><SimpleDonut :assets="rightP.assets" size="w-32 h-32" /></div>
            <button class="absolute top-4 right-4 text-gray-400 hover:text-[#536dfe]">🔄</button>
          </div>
          <div v-else class="text-center">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-3xl mb-4 text-gray-400 group-hover:bg-[#536dfe] group-hover:text-white transition-colors">＋</div>
            <p class="text-gray-500 font-bold">포트폴리오 선택</p>
          </div>
        </div>
      </div>

      <div v-if="step === 'select'" class="text-center mt-12">
        <button @click="startAnalysis" class="px-12 py-4 bg-[#536dfe] text-white text-lg font-bold rounded-2xl shadow-lg hover:bg-[#4059e0] disabled:bg-gray-300 disabled:cursor-not-allowed transition-all" :disabled="!leftP || !rightP">
          분석하러 가기 🚀
        </button>
      </div>

      <!-- [STEP 2] 비교 분석 화면 -->
      <div v-if="step === 'analyze'" class="fade-in">
        
        <div class="flex flex-col lg:flex-row gap-8 items-stretch mb-12">
          
          <!-- 왼쪽 포트폴리오 -->
          <div class="flex-1 bg-white p-8 rounded-3xl shadow-sm border border-gray-200">
            <div class="flex justify-between items-start mb-6">
              <h3 class="font-bold text-xl">{{ leftP.name }}</h3>
              <span class="px-3 py-1 bg-gray-100 rounded-full text-xs font-bold">{{ leftP.typeLabel }}</span>
            </div>
            <div class="flex items-center gap-6 mb-6">
              <SimpleDonut :assets="leftP.assets" size="w-24 h-24" />
              <div class="space-y-1 flex-1">
                <div class="flex justify-between text-sm"><span class="text-gray-500">수익률</span><span class="font-bold text-[#536dfe]">+{{ leftStats.returnRate }}%</span></div>
                <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden"><div class="h-full bg-gradient-to-r from-green-400 to-red-500" :style="{width: leftStats.riskScore + '%'}"></div></div>
                <div class="flex justify-between text-[10px] text-gray-400"><span>안전</span><span>위험</span></div>
              </div>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl text-sm text-gray-600">
              {{ leftP.aiComment || leftP.memo || '분석 정보 없음' }}
            </div>
          </div>

          <!-- 중앙 VS 및 비교 버튼 -->
          <div class="flex flex-col items-center justify-center gap-4">
            <div class="w-10 h-10 rounded-full bg-[#2C4768] text-white flex items-center justify-center font-bold shadow-md">VS</div>
            <button @click="runComparison" class="px-6 py-2 bg-green-500 text-white font-bold rounded-lg shadow hover:bg-green-600 transition-colors whitespace-nowrap">
              📑 비교 분석 하기
            </button>
          </div>

          <!-- 오른쪽 포트폴리오 (리밸런싱) -->
          <div class="flex-1 bg-white p-8 rounded-3xl shadow-sm border-2 transition-all relative" :class="isRebalancing ? 'border-[#536dfe] ring-2 ring-blue-50' : 'border-gray-200'">
            <div class="flex justify-between items-start mb-6">
              <h3 class="font-bold text-xl flex items-center gap-2">
                {{ isRebalancing ? '조정 중...' : rightP.name }}
                <span v-if="rightP.isTemp" class="text-[10px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded">미저장</span>
              </h3>
              <!-- 리밸런싱 토글 -->
              <div class="flex items-center gap-2 cursor-pointer" @click="toggleRebalance">
                <span class="text-xs font-bold" :class="isRebalancing ? 'text-[#536dfe]' : 'text-gray-400'">리밸런싱</span>
                <div class="w-10 h-5 bg-gray-200 rounded-full relative transition-colors" :class="{'bg-[#536dfe]': isRebalancing}"><div class="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform shadow-sm" :class="{'translate-x-5': isRebalancing}"></div></div>
              </div>
            </div>

            <div v-if="!isRebalancing">
              <div class="flex items-center gap-6 mb-6">
                <SimpleDonut :assets="rightP.assets" size="w-24 h-24" />
                <div class="space-y-1 flex-1">
                  <div class="flex justify-between text-sm"><span class="text-gray-500">수익률</span><span class="font-bold text-[#536dfe]">+{{ rightStats.returnRate }}%</span></div>
                  <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden"><div class="h-full bg-gradient-to-r from-green-400 to-red-500" :style="{width: rightStats.riskScore + '%'}"></div></div>
                  <div class="flex justify-between text-[10px] text-gray-400"><span>안전</span><span>위험</span></div>
                </div>
              </div>
              <div class="bg-blue-50 p-4 rounded-xl text-sm text-[#2C4768]">
                <strong>🤖 AI 분석:</strong> {{ rightP.aiComment || '분석 정보 없음' }}
              </div>
              
              <!-- 저장 버튼 (리밸런싱 분석 완료된 상태일 때만 표시) -->
              <div v-if="rightP.isTemp" class="mt-4 flex gap-2">
                <button @click="resetRebalance" class="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-500">초기화</button>
                <button @click="openSaveModal" class="flex-[2] py-2 bg-[#536dfe] text-white rounded-lg text-sm font-bold shadow hover:bg-[#4059e0]">이 분석 결과로 저장</button>
              </div>
            </div>

            <!-- 리밸런싱 모드 -->
            <div v-else>
              <div class="space-y-3 mb-6">
                <div v-for="(label, i) in assetLabels" :key="i">
                  <div class="flex justify-between text-xs mb-1 font-bold"><span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" :style="{background: assetColors[i]}"></span>{{ label }}</span><span class="text-[#536dfe]">{{ rebalancedAssets[i] }}%</span></div>
                  <input type="range" v-model.number="rebalancedAssets[i]" min="0" max="100" step="5" class="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#536dfe]" />
                </div>
              </div>
              <div class="text-right text-xs font-bold mb-4" :class="rebalancedAssets.reduce((a,b)=>a+b,0) === 100 ? 'text-green-500' : 'text-red-500'">합계: {{ rebalancedAssets.reduce((a,b)=>a+b,0) }}% / 100%</div>
              <button @click="analyzeRebalance" class="w-full py-3 bg-gray-900 text-white font-bold rounded-xl shadow-md hover:bg-black text-sm">
                분석 및 적용하기
              </button>
            </div>
          </div>
        </div>

        <!-- [하단] 비교 분석 리포트 -->
        <div v-if="showComparisonReport" class="bg-gray-50 border border-gray-200 rounded-3xl p-8 animate-fade-in-up">
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span>📑</span> 포트폴리오 비교 분석 결과
          </h3>
          <div class="space-y-4 text-sm text-gray-700 leading-relaxed">
            <p>
              <span class="font-bold text-[#536dfe]">수익률 차이:</span> 
              왼쪽 포트폴리오 대비 오른쪽이 <span class="font-bold">{{ (rightStats.returnRate - leftStats.returnRate).toFixed(1) }}%p</span> {{ rightStats.returnRate > leftStats.returnRate ? '높은' : '낮은' }} 예상 수익률을 보입니다.
            </p>
            <p>
              <span class="font-bold text-orange-500">위험도 분석:</span> 
              {{ rightStats.riskScore > leftStats.riskScore ? '오른쪽 포트폴리오는 주식 비중이 높아 변동성 위험이 증가했습니다.' : '오른쪽 포트폴리오는 안정 자산 비중을 높여 리스크를 효과적으로 낮췄습니다.' }}
            </p>
            <p>
              <span class="font-bold text-gray-900">최종 조언:</span> 
              단기적인 시장 변동성을 견딜 수 있다면 오른쪽 전략이 유효하나, 안정성을 중시한다면 왼쪽 전략 유지를 권장합니다.
            </p>
          </div>
        </div>

      </div>
    </div>

    <!-- 모달들 (기존 동일) -->
    <div v-if="showSelectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white w-full max-w-md rounded-2xl p-6 shadow-2xl max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4"><h3 class="text-lg font-bold">포트폴리오 선택</h3><button @click="showSelectModal = false">✕</button></div>
        <div class="space-y-3">
          <button v-for="p in portfolios.filter(i => !i.isTemp)" :key="p.id" @click="selectPortfolio(p.id)" class="w-full text-left p-4 rounded-xl border hover:border-[#536dfe] bg-gray-50 hover:bg-blue-50 transition-all flex justify-between items-center">
            <div><div class="font-bold">{{ p.name }}</div><div class="text-xs text-gray-500">{{ p.typeLabel }}</div></div><span v-if="p.isAi" class="text-[10px] bg-purple-100 text-purple-600 px-2 py-1 rounded-full font-bold">AI 추천</span>
          </button>
        </div>
      </div>
    </div>
    <div v-if="showSaveModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white w-full max-w-md rounded-2xl p-8 shadow-2xl">
        <h3 class="text-xl font-bold mb-6">새 포트폴리오 저장</h3>
        <BaseInput label="이름" v-model="saveForm.name" />
        <div class="mb-6"><label class="block text-xs font-bold text-gray-500 mb-2">메모 (선택)</label><textarea v-model="saveForm.memo" rows="3" class="w-full border-b-2 p-2 outline-none resize-none"></textarea></div>
        <div class="flex gap-3 justify-end"><button @click="showSaveModal = false" class="px-4 py-2 border rounded font-bold text-gray-500">취소</button><button @click="saveNewPortfolio" class="px-6 py-2 bg-[#536dfe] text-white rounded font-bold">저장</button></div>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.fade-in { animation: fadeIn 0.5s ease-out; }
.animate-fade-in-up { animation: fadeInUp 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>