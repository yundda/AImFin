<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import SimpleDonut from '@/components/common/SimpleDonut.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import { authApi } from '@/services/auth.api';

const router = useRouter();

// --- 상태 관리 ---
const step = ref('select'); 
const portfolios = ref([]);
const selectedIds = ref([null, null]); 
const showSelectModal = ref(false);
const selectingIndex = ref(0);

// 분석 상태
const showComparisonReport = ref(false); // 비교 분석 리포트 표시 여부
const comparisonResult = ref(null); // API 결과 저장
const analysisLoading = ref(false);

// 리밸런싱 관련
const isRebalancing = ref(false);
const tempPortfolio = ref(null);
const rebalancedAssets = ref([]);
const showSaveModal = ref(false);
const saveForm = ref({ name: '', memo: '', isRepresentative: false });

// 자산 정보 (7개 버킷으로 확장)
// 순서: 국내주식, 미국주식, 국내채권, 해외채권, 대체투자, 펀드, 현금성자산
const assetLabels = ['국내주식', '미국주식', '국내채권', '해외채권', '대체투자', '펀드', '현금성자산'];
// Colors matching SimpleDonut default or customized here
const assetColors = ['#283593', '#3b82f6', '#10b981', '#34d399', '#f59e0b', '#8b5cf6', '#cbd5e1'];
const bucketKeys = ['STOCKS_KR', 'STOCKS_GLB', 'BONDS_KR', 'BONDS_GLB', 'ALTERNATIVES', 'FUNDS', 'CASH'];

// 포트폴리오 로드
const loadPortfolios = async () => {
  try {
    const res = await authApi.getPortfolioList();
    const list = res.data.map(p => {
      // Parse allocations if available from API
      const assetMap = {
        'STOCKS_KR': 0, 'STOCKS_GLB': 0,
        'BONDS_KR': 0, 'BONDS_GLB': 0,
        'ALTERNATIVES': 0, 'FUNDS': 0, 'CASH': 0
      };

      if (p.allocations && Array.isArray(p.allocations)) {
        p.allocations.forEach(a => {
           if (assetMap.hasOwnProperty(a.bucket)) {
             assetMap[a.bucket] += (a.weight_pct || 0);
           }
        });
      }
      
      const assetsArray = bucketKeys.map(key => Number(assetMap[key].toFixed(1)));

      return {
        ...p,
        assets: assetsArray
      };
    });
    
    // 대표 포트폴리오 상단 정렬
    list.sort((a, b) => {
      if (a.is_representative && !b.is_representative) return -1;
      if (!a.is_representative && b.is_representative) return 1;
      return 0;
    });

    portfolios.value = list;
  } catch (err) {
    console.error("Failed to load portfolios:", err);
  }
};

onMounted(loadPortfolios);

// 선택된 포트폴리오 객체 저장 (API 상세 조회 결과)
const selectedPortfolios = ref([null, null]);

const leftP = computed(() => selectedPortfolios.value[0]);
const rightP = computed(() => tempPortfolio.value || selectedPortfolios.value[1]);

// 수치 계산 로직 (API metrics 사용)
const getStats = (p) => {
  if (!p || !p.metrics) return { returnRate: 0, riskScore: 0 };
  return { 
    returnRate: p.metrics.expected_return_pct, 
    riskScore: p.metrics.risk_score 
  };
};

const leftStats = computed(() => getStats(leftP.value));
const rightStats = computed(() => getStats(rightP.value));

// 기능 함수들
const openSelectModal = (idx) => { selectingIndex.value = idx; showSelectModal.value = true; };

const selectPortfolio = async (id) => {
  try {
    // 상세 조회하여 assets 정보 등을 채움
    const res = await authApi.getPortfolioDetail(id);
    const p = res.data;
    
    // assets 배열로 변환 (7 buckets)
    const assetMap = {
      'STOCKS_KR': 0, 'STOCKS_GLB': 0,
      'BONDS_KR': 0, 'BONDS_GLB': 0,
      'ALTERNATIVES': 0, 'FUNDS': 0, 'CASH': 0
    };

    if (p.allocations) {
      p.allocations.forEach(a => {
        if (assetMap.hasOwnProperty(a.bucket)) {
          assetMap[a.bucket] += (a.weight_pct || 0);
        }
      });
    }
    
    // Map object to array in specific order
    const assetsArray = bucketKeys.map(key => Number(assetMap[key].toFixed(1))); // 1 decimal place

    // UI용 객체 생성
    const portObj = {
      ...p,
      typeLabel: p.profile_label,
      assets: assetsArray,
      aiComment: p.rationale || p.summary || ''
    };

    selectedPortfolios.value[selectingIndex.value] = portObj;
    selectedIds.value[selectingIndex.value] = id;
    
    showSelectModal.value = false;
    
    if (selectingIndex.value === 1) {
      tempPortfolio.value = null; // 리밸런싱 해제
      showComparisonReport.value = false;
      comparisonResult.value = null;
    }
  } catch (err) {
    console.error("Failed to fetch detail:", err);
    alert("포트폴리오 정보를 가져오는데 실패했습니다.");
  }
};

const startAnalysis = async () => {
  if (!leftP.value || !rightP.value) return alert('비교할 포트폴리오를 모두 선택해주세요.');
  step.value = 'analyze';
  await runComparison();
};

// 비교 분석 실행
const runComparison = async () => {
  if (!leftP.value || !rightP.value) return;
  
  try {
    analysisLoading.value = true;
    showComparisonReport.value = false;
    
    const payload = {};
    
    // Left: 항상 ID 기반 
    payload.left = { type: 'id', id: leftP.value.id };
    
    // Right: Temp(리밸런싱)이면 Allocations, 아니면 ID
    if (rightP.value.isTemp) {
      const currentAssets = rightP.value.assets;
      const allocations = bucketKeys.map((key, idx) => ({
        bucket: key,
        weight_pct: currentAssets[idx]
      }));

      payload.right = {
        type: 'allocations',
        allocations: allocations
      };
    } else {
      payload.right = { type: 'id', id: rightP.value.id };
    }

    const res = await authApi.comparePortfolios(payload);
    comparisonResult.value = res.data;
    showComparisonReport.value = true;
    
    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }, 100);
    
  } catch (err) {
    console.error("Comparison failed:", err);
    alert("비교 분석 중 오류가 발생했습니다: " + (err.response?.data?.detail || err.message));
  } finally {
    analysisLoading.value = false;
  }
};

const toggleRebalance = () => {
  if (!isRebalancing.value) {
    rebalancedAssets.value = [...rightP.value.assets];
  }
  isRebalancing.value = !isRebalancing.value;
};

// 리밸런싱 개별 수정 (버튼용)
const updateWeight = (index, delta) => {
  let val = rebalancedAssets.value[index] + delta;
  if (val < 0) val = 0;
  if (val > 100) val = 100;
  rebalancedAssets.value[index] = Number(val.toFixed(0)); // 정수 단위 유지
};

const totalRebalanceWeight = computed(() => {
  return rebalancedAssets.value.reduce((a, b) => a + b, 0);
});

// 리밸런싱 적용 및 AI 분석 요청
const analyzeRebalance = async () => {
  const total = rebalancedAssets.value.reduce((a, b) => a + b, 0);
  // Allow slight float error but ensure strictly 100 for backend
  if (Math.abs(total - 100) > 0.1) return alert(`자산 비중의 합이 ${total.toFixed(1)}%입니다. 100%를 맞춰주세요.`);
  
  try {
    analysisLoading.value = true;

    // 1. 7개 버킷 Allocations 생성 (1:1 매핑)
    const newAllocations = bucketKeys.map((key, idx) => ({
        bucket: key,
        weight_pct: rebalancedAssets.value[idx]
    }));
    
    // 원본 가져오기 (ID 참조용)
    const original = selectedPortfolios.value[1]; 
    if (!original) throw new Error("원본 포트폴리오 데이터를 찾을 수 없습니다.");

    // 2. 백엔드 분석 요청
    const payload = { allocations: newAllocations };
    const res = await authApi.rebalancePortfolio(original.id, payload);
    const result = res.data;

    // 3. 임시 포트폴리오 업데이트
    tempPortfolio.value = {
      ...original,
      id: 'temp-' + Date.now(),
      name: original.name + ' (조정됨)',
      assets: [...rebalancedAssets.value],
      isTemp: true,
      allocations: result.final_allocations || newAllocations,
      metrics: {
        expected_return_pct: result.metrics?.expected_return_pct || 0,
        risk_score: result.metrics?.risk_score || 0
      },
      aiComment: Array.isArray(result.summary) ? result.summary.join('\n') : (result.summary || '분석 결과가 없습니다.')
    };

    isRebalancing.value = false;
    
    // 리밸런싱 후 즉시 비교 분석 재실행
    await runComparison();

  } catch (err) {
    console.error("Rebalance analysis failed:", err);
    alert("분석 중 오류가 발생했습니다: " + (err.response?.data?.detail || err.message));
  } finally {
    analysisLoading.value = false;
  }
};

const calculateStats = (assets) => {
  // 로컬 계산 로직은 이제 사용하지 않거나, 초기 대략적 갱신용으로 남겨둠.
  // API 호출이 있으므로 실제로는 필요없을 수 있음.
  return { returnRate: 0, riskScore: 0 }; 
};

const resetRebalance = () => { 
  tempPortfolio.value = null; 
  showComparisonReport.value = false;
  comparisonResult.value = null;
};

const openSaveModal = () => {
  saveForm.value = { name: rightP.value.name, memo: '', isRepresentative: false };
  showSaveModal.value = true;
};

const saveNewPortfolio = async () => {
  if (!saveForm.value.name) return alert("이름을 입력해주세요.");
  
  try {
    const currentAssets = rightP.value.assets;
    const allocations = bucketKeys.map((key, idx) => ({
        bucket: key,
        weight_pct: currentAssets[idx]
    }));

    const payload = {
      name: saveForm.value.name,
      amount_krw: rightP.value.amount_krw || 0,
      profile: rightP.value.profile || 'CONSERVATIVE', 
      profile_label: rightP.value.typeLabel || 'User Custom',
      horizon_desc: 'Custom',
      allocations: allocations,
      rationale: comparisonResult.value?.rationale || '',
      summary: comparisonResult.value?.summary || '',
      risks: comparisonResult.value?.risks || '',
      set_representative: saveForm.value.isRepresentative
    };
    
    await authApi.savePortfolio(payload);
    alert('저장되었습니다!');
    
    await loadPortfolios();
    showSaveModal.value = false;
  } catch (err) {
    console.error("Save failed:", err);
    alert("저장 실패");
  }
};

const getSortedAssets = (assets, limit = null) => {
  if (!assets) return [];
  const sorted = assets
    .map((v, i) => ({ value: v, label: assetLabels[i], color: assetColors[i] }))
    .filter(item => item.value > 0)
    .sort((a, b) => b.value - a.value);
    
  return limit ? sorted.slice(0, limit) : sorted;
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
        <div @click="openSelectModal(0)" class="w-full max-w-md min-h-[500px] rounded-3xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-[#283593] hover:bg-blue-50/30 transition-all group relative bg-white overflow-hidden shadow-sm hover:shadow-md p-6">
          <div v-if="leftP" class="text-center w-full h-full flex flex-col items-center justify-between gap-6">
            <div class="w-full relative pt-2">
              <h3 class="font-bold text-2xl text-gray-900 truncate px-2">{{ leftP.name }}</h3>
              <p class="text-sm text-gray-400 mt-1">{{ leftP.created_at ? new Date(leftP.created_at).toLocaleDateString() : '날짜 없음' }}</p>
              <button @click.stop="openSelectModal(0)" class="absolute top-0 right-0 px-3 py-1.5 text-xs font-bold text-gray-400 hover:text-[#283593] hover:bg-blue-50/50 rounded-lg transition-colors flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>
                다시 선택
              </button>
            </div>

            <!-- 차트 & 타입 -->
            <div class="relative shrink-0">
              <SimpleDonut :assets="leftP.assets" :labels="assetLabels" :colors="assetColors" size="w-40 h-40" :show-tooltip="false" />
              <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span class="text-xl font-extrabold text-[#283593]">{{ leftP.typeLabel }}</span>
              </div>
            </div>

             <!-- 자산 배분 상세 (카드에 추가) -->
             <div class="w-full bg-gray-50 rounded-xl p-4 text-left relative group/list cursor-help">
               <div class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1">
                 자산 구성 (Top 3)
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
               </div>
                <div class="space-y-2">
                  <div v-for="(info, idx) in getSortedAssets(leftP.assets, 3)" :key="idx" class="flex items-center justify-between text-sm">
                    <span class="flex items-center gap-2 text-gray-600"><span class="w-2 h-2 rounded-full" :style="{background: info.color}"></span>{{ info.label }}</span>
                    <span class="font-bold text-gray-800">{{ info.value }}%</span>
                  </div>
               </div>

               <!-- Full Asset Tooltip -->
               <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-gray-900/95 text-white text-xs rounded-xl py-3 px-4 shadow-xl opacity-0 group-hover/list:opacity-100 transition-opacity duration-200 z-50 pointer-events-none backdrop-blur-sm border border-gray-700">
                  <div class="flex flex-col gap-1.5">
                    <div class="text-xs font-bold text-gray-400 mb-1 text-center">자산 구성</div>
                    <div v-for="(item, i) in getSortedAssets(leftP.assets)" :key="i" class="flex justify-between items-center">
                      <div class="flex items-center gap-1.5 overflow-hidden">
                        <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: item.color }"></span>
                        <span class="text-gray-200 truncate">{{ item.label || '기타' }}</span>
                      </div>
                      <span class="font-bold shrink-0 text-white">{{ item.value }}%</span>
                    </div>
                  </div>
                  <!-- Arrow -->
                  <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900/95"></div>
               </div>
             </div>

            <!-- 스탯 -->
            <div class="grid grid-cols-2 gap-3 w-full bg-gray-50 rounded-xl p-3 text-sm">
              <div class="flex flex-col items-start pl-2">
                <span class="text-[10px] text-gray-400 font-bold mb-0.5">운용 자산</span>
                <span class="font-bold text-gray-900">{{ (leftP.amount_krw || 0).toLocaleString() }}원</span>
              </div>
              <div class="flex flex-col items-start pl-2">
                <span class="text-[10px] text-gray-400 font-bold mb-0.5">위험도</span>
                <span class="font-bold" :class="leftStats.riskScore > 60 ? 'text-red-500' : (leftStats.riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">{{ leftStats.riskScore }}점</span>
              </div>
              <div class="col-span-2 flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-blue-100 shadow-sm mt-1">
                <span class="text-xs font-bold text-gray-500">예상 수익률</span>
                <span class="text-lg font-bold text-[#283593]">+{{ leftStats.returnRate }}%</span>
              </div>
            </div>
          </div>
          <div v-else class="text-center flex flex-col items-center justify-center h-full w-full py-20">
            <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center text-3xl mb-4 text-gray-400 group-hover:bg-[#283593] group-hover:text-white transition-colors shadow-inner">＋</div>
            <p class="text-lg text-gray-500 font-bold">포트폴리오 선택</p>
            <p class="text-sm text-gray-400 mt-1">비교할 첫 번째 전략을 가져옵니다</p>
          </div>
        </div>

        <div class="w-12 h-12 rounded-full bg-[#283593] text-white flex items-center justify-center font-bold text-lg shadow-lg z-10">VS</div>

        <div @click="openSelectModal(1)" class="w-full max-w-md min-h-[500px] rounded-3xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-[#283593] hover:bg-blue-50/30 transition-all group relative bg-white overflow-hidden shadow-sm hover:shadow-md p-6">
          <div v-if="rightP" class="text-center w-full h-full flex flex-col items-center justify-between gap-6">
            <div class="w-full relative pt-2">
              <h3 class="font-bold text-2xl text-gray-900 truncate px-2">{{ rightP.name }}</h3>
              <p class="text-sm text-gray-400 mt-1">{{ rightP.created_at ? new Date(rightP.created_at).toLocaleDateString() : '날짜 없음' }}</p>
              <button @click.stop="openSelectModal(1)" class="absolute top-0 right-0 px-3 py-1.5 text-xs font-bold text-gray-400 hover:text-[#283593] hover:bg-blue-50/50 rounded-lg transition-colors flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>
                다시 선택
              </button>
            </div>

            <!-- 차트 & 타입 -->
            <div class="relative shrink-0">
              <SimpleDonut :assets="rightP.assets" :labels="assetLabels" :colors="assetColors" size="w-40 h-40" :show-tooltip="false" />
              <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span class="text-xl font-extrabold text-[#283593]">{{ rightP.typeLabel }}</span>
              </div>
            </div>

             <!-- 자산 배분 상세 (카드에 추가) -->
             <div class="w-full bg-gray-50 rounded-xl p-4 text-left relative group/list cursor-help">
               <div class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1">
                 자산 구성 (Top 3)
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
               </div>
                <div class="space-y-2">
                  <div v-for="(info, idx) in getSortedAssets(rightP.assets, 3)" :key="idx" class="flex items-center justify-between text-sm">
                    <span class="flex items-center gap-2 text-gray-600"><span class="w-2 h-2 rounded-full" :style="{background: info.color}"></span>{{ info.label }}</span>
                    <span class="font-bold text-gray-800">{{ info.value }}%</span>
                  </div>
               </div>

               <!-- Full Asset Tooltip -->
               <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-gray-900/95 text-white text-xs rounded-xl py-3 px-4 shadow-xl opacity-0 group-hover/list:opacity-100 transition-opacity duration-200 z-50 pointer-events-none backdrop-blur-sm border border-gray-700">
                  <div class="flex flex-col gap-1.5">
                    <div class="text-xs font-bold text-gray-400 mb-1 text-center">자산 구성</div>
                    <div v-for="(item, i) in getSortedAssets(rightP.assets)" :key="i" class="flex justify-between items-center">
                      <div class="flex items-center gap-1.5 overflow-hidden">
                        <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: item.color }"></span>
                        <span class="text-gray-200 truncate">{{ item.label || '기타' }}</span>
                      </div>
                      <span class="font-bold shrink-0 text-white">{{ item.value }}%</span>
                    </div>
                  </div>
                  <!-- Arrow -->
                  <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900/95"></div>
               </div>
             </div>

            <!-- 스탯 -->
            <div class="grid grid-cols-2 gap-3 w-full bg-gray-50 rounded-xl p-3 text-sm">
              <div class="flex flex-col items-start pl-2">
                <span class="text-[10px] text-gray-400 font-bold mb-0.5">운용 자산</span>
                <span class="font-bold text-gray-900">{{ (rightP.amount_krw || 0).toLocaleString() }}원</span>
              </div>
              <div class="flex flex-col items-start pl-2">
                <span class="text-[10px] text-gray-400 font-bold mb-0.5">위험도</span>
                <span class="font-bold" :class="rightStats.riskScore > 60 ? 'text-red-500' : (rightStats.riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">{{ rightStats.riskScore }}점</span>
              </div>
              <div class="col-span-2 flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-blue-100 shadow-sm mt-1">
                <span class="text-xs font-bold text-gray-500">예상 수익률</span>
                <span class="text-lg font-bold text-[#283593]">+{{ rightStats.returnRate }}%</span>
              </div>
            </div>
          </div>
          <div v-else class="text-center flex flex-col items-center justify-center h-full w-full py-20">
            <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center text-3xl mb-4 text-gray-400 group-hover:bg-[#283593] group-hover:text-white transition-colors shadow-inner">＋</div>
            <p class="text-lg text-gray-500 font-bold">포트폴리오 선택</p>
            <p class="text-sm text-gray-400 mt-1">비교할 두 번째 전략을 가져옵니다</p>
          </div>
        </div>
      </div>

      <div v-if="step === 'select'" class="text-center mt-12">
        <button @click="startAnalysis" class="px-12 py-4 bg-[#283593] text-white text-lg font-bold rounded-2xl shadow-lg hover:bg-[#1a237e] disabled:bg-gray-300 disabled:cursor-not-allowed transition-all" :disabled="!leftP || !rightP">
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
              <SimpleDonut :assets="leftP.assets" :labels="assetLabels" :colors="assetColors" size="w-24 h-24" />
              <div class="space-y-1 flex-1">
                <div class="space-y-2 flex-1">
                  <div class="flex justify-between text-sm"><span class="text-gray-500">수익률</span><span class="font-bold text-[#283593]">+{{ leftStats.returnRate }}%</span></div>
                  
                  <!-- Unified Risk UI -->
                  <div>
                    <div class="flex justify-between items-end mb-1 px-1">
                      <span class="text-xs font-bold text-gray-400">위험도 진단</span>
                      <span class="text-sm font-bold" :class="leftStats.riskScore > 60 ? 'text-red-500' : (leftStats.riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">
                        {{ leftStats.riskScore }}점 ({{ leftStats.riskScore > 60 ? '높음' : (leftStats.riskScore > 40 ? '중간' : '낮음') }})
                      </span>
                    </div>
                    <div class="h-2 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative shadow-inner">
                      <div class="absolute top-1/2 -translate-y-1/2 w-1.5 h-4 bg-gray-800 border-2 border-white rounded-sm shadow-md transition-all duration-1000 ease-out" :style="{ left: leftStats.riskScore + '%' }"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-gray-400 mt-1.5 font-medium px-1">
                      <span>안전</span>
                      <span>위험</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="bg-blue-50 p-4 rounded-xl text-sm text-[#2C4768]">
              <strong>🤖 AI 분석:</strong> {{ leftP.aiComment || leftP.memo || '분석 정보 없음' }}
            </div>
          </div>

          <!-- 중앙 VS (버튼 제거) -->
          <div class="flex flex-col items-center justify-center gap-4">
            <div class="w-10 h-10 rounded-full bg-[#2C4768] text-white flex items-center justify-center font-bold shadow-md">VS</div>
          </div>

          <!-- 오른쪽 포트폴리오 (리밸런싱) -->
          <div class="flex-1 bg-white p-8 rounded-3xl shadow-sm border-2 transition-all relative" :class="isRebalancing ? 'border-[#283593] ring-2 ring-blue-50' : 'border-gray-200'">
            <div class="flex justify-between items-start mb-6">
              <h3 class="font-bold text-xl flex items-center gap-2">
                {{ isRebalancing ? '조정 중...' : rightP.name }}
                <span v-if="rightP.isTemp" class="text-[10px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded">미저장</span>
              </h3>
              <!-- 리밸런싱 토글 -->
              <div class="flex items-center gap-2 cursor-pointer" @click="toggleRebalance">
                <span class="text-xs font-bold" :class="isRebalancing ? 'text-[#283593]' : 'text-gray-400'">리밸런싱</span>
                <div class="w-10 h-5 bg-gray-200 rounded-full relative transition-colors" :class="{'bg-[#283593]': isRebalancing}"><div class="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform shadow-sm" :class="{'translate-x-5': isRebalancing}"></div></div>
              </div>
            </div>

            <div v-if="!isRebalancing">
              <div class="flex items-center gap-6 mb-6">
                <SimpleDonut :assets="rightP.assets" :labels="assetLabels" :colors="assetColors" size="w-24 h-24" />
                <div class="space-y-1 flex-1">
                <div class="space-y-2 flex-1">
                  <div class="flex justify-between text-sm"><span class="text-gray-500">수익률</span><span class="font-bold text-[#283593]">+{{ rightStats.returnRate }}%</span></div>
                  
                  <!-- Unified Risk UI -->
                  <div>
                    <div class="flex justify-between items-end mb-1 px-1">
                      <span class="text-xs font-bold text-gray-400">위험도 레벨</span>
                      <span class="text-sm font-bold" :class="rightStats.riskScore > 60 ? 'text-red-500' : (rightStats.riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">
                        {{ rightStats.riskScore }}점 ({{ rightStats.riskScore > 60 ? '높음' : (rightStats.riskScore > 40 ? '중간' : '낮음') }})
                      </span>
                    </div>
                    <div class="h-2 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative shadow-inner">
                      <div class="absolute top-1/2 -translate-y-1/2 w-1.5 h-4 bg-gray-800 border-2 border-white rounded-sm shadow-md transition-all duration-1000 ease-out" :style="{ left: rightStats.riskScore + '%' }"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-gray-400 mt-1.5 font-medium px-1">
                      <span>안전</span>
                      <span>위험</span>
                    </div>
                  </div>
                </div>
                </div>
              </div>
            <div class="bg-blue-50 p-4 rounded-xl text-sm text-[#2C4768]">
              <strong>🤖 AI 분석:</strong>
              <div class="mt-1 whitespace-pre-line">{{ rightP.aiComment || '분석 정보 없음' }}</div>
            </div>
              
              <!-- 저장 버튼 (리밸런싱 분석 완료된 상태일 때만 표시) -->
              <div v-if="rightP.isTemp" class="mt-4 flex gap-2">
                <button @click="resetRebalance" class="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-500">초기화</button>
                <button @click="openSaveModal" class="flex-[2] py-2 bg-[#283593] text-white rounded-lg text-sm font-bold shadow hover:bg-[#1a237e]">이 분석 결과로 저장</button>
              </div>
            </div>

            <!-- 리밸런싱 모드 -->
            <div v-else>
              <div class="space-y-4 mb-6">
                <div v-for="(label, i) in assetLabels" :key="i">
                  <!-- Header -->
                  <div class="flex justify-between text-xs mb-1.5 font-bold text-gray-600">
                     <span class="flex items-center gap-1.5">
                       <span class="w-2.5 h-2.5 rounded-full shadow-sm" :style="{background: assetColors[i]}"></span>
                       {{ label }}
                     </span>
                  </div>
                  
                  <!-- Controls -->
                  <div class="flex items-center gap-3">
                     <!-- Slider -->
                     <input type="range" v-model.number="rebalancedAssets[i]" min="0" max="100" step="1" class="flex-1 h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer" :style="{'accent-color': assetColors[i]}" />
                     
                     <!-- Input Group -->
                     <div class="flex items-center bg-gray-50 rounded-lg border border-gray-200 p-0.5 shrink-0">
                       <button @click="updateWeight(i, -1)" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-black hover:bg-white rounded shadow-sm transition-all font-bold text-lg">-</button>
                       <div class="relative w-12 text-center">
                         <input type="number" v-model.number="rebalancedAssets[i]" class="w-full bg-transparent text-center font-bold text-sm text-gray-900 focus:outline-none p-0 appearance-none-number" min="0" max="100" />
                       </div>
                       <span class="text-xs text-gray-400 mr-1">%</span>
                       <button @click="updateWeight(i, 1)" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-black hover:bg-white rounded shadow-sm transition-all font-bold text-lg">+</button>
                     </div>
                  </div>
                </div>
              </div>

               <!-- Total & Warning -->
              <div class="mb-4 p-3 rounded-xl bg-gray-50 border border-gray-100 flex justify-between items-center transition-colors" :class="totalRebalanceWeight !== 100 ? 'bg-red-50 border-red-100' : ''">
                 <span class="text-xs font-bold text-gray-500">총 비중 합계</span>
                 <span class="font-bold text-sm" :class="totalRebalanceWeight === 100 ? 'text-[#283593]' : 'text-red-500'">
                   {{ totalRebalanceWeight }}% / 100%
                 </span>
              </div>
              <div v-if="totalRebalanceWeight !== 100" class="mb-4 text-xs text-red-500 font-bold bg-white p-2 rounded-lg text-center border border-red-100 animate-pulse shadow-sm">
                 ⚠️ 총 합계가 100%가 되어야 합니다. (현재: {{ totalRebalanceWeight }}%)
              </div>

              <div class="flex gap-2">
                 <button @click="toggleRebalance" class="flex-1 py-3 border border-gray-200 text-gray-500 font-bold rounded-xl hover:bg-gray-50 transition-colors text-sm">
                   취소
                 </button>
                 <button @click="analyzeRebalance" :disabled="totalRebalanceWeight !== 100" class="flex-[2] py-3 bg-[#283593] text-white font-bold rounded-xl shadow-md hover:bg-[#1a237e] text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                   분석 및 적용하기
                 </button>
              </div>
            </div>
          </div>
        </div>

        <!-- [하단] 비교 분석 리포트 -->
        <!-- [하단] 비교 분석 리포트 -->
        <div v-if="showComparisonReport && comparisonResult" class="bg-gray-50 border border-gray-200 rounded-3xl p-8 animate-fade-in-up">
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span>📑</span> 포트폴리오 비교 분석 결과
          </h3>
          <div class="space-y-6 text-sm text-gray-700 leading-relaxed">
            
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
               <h4 class="font-bold text-[#283593] mb-2">분석 근거 (Rationale)</h4>
               <p class="whitespace-pre-line">{{ comparisonResult.rationale }}</p>
            </div>

             <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
               <h4 class="font-bold text-green-600 mb-2">요약 및 제안 (Summary)</h4>
               <p class="whitespace-pre-line">{{ comparisonResult.summary }}</p>
            </div>

             <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
               <h4 class="font-bold text-orange-500 mb-2">위험 요인 (Risks)</h4>
               <p class="whitespace-pre-line">{{ comparisonResult.risks }}</p>
            </div>

          </div>
        </div>

      </div>
    </div>

    <!-- 모달들 (기존 동일) -->
    <div v-if="showSelectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white w-full max-w-2xl rounded-2xl p-6 shadow-2xl max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4"><h3 class="text-lg font-bold">포트폴리오 선택</h3><button @click="showSelectModal = false">✕</button></div>
        <div class="space-y-3">
          <button v-for="p in portfolios.filter(i => !i.isTemp && i.id !== selectedIds[1 - selectingIndex])" :key="p.id" @click="selectPortfolio(p.id)" class="w-full text-left p-4 rounded-xl border hover:border-[#283593] bg-gray-50 hover:bg-blue-50 transition-all flex justify-between items-center">
            <div>
              <div class="font-bold">{{ p.name }}</div>
              <div v-if="p.typeLabel" class="text-xs text-gray-500">{{ p.typeLabel }}</div>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span v-if="p.is_representative" class="inline-flex items-center gap-1 px-2 py-0.5 bg-[#283593] text-white text-[10px] font-bold rounded-full">
                <span class="w-1.5 h-1.5 bg-white rounded-full"></span>
                대표
              </span>
              <span v-if="p.isAi" class="text-[10px] bg-purple-100 text-purple-600 px-2 py-1 rounded-full font-bold">AI 추천</span>
            </div>
          </button>
        </div>
      </div>
    </div>
    <div v-if="showSaveModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white w-full max-w-md rounded-2xl p-8 shadow-2xl">
        <h3 class="text-xl font-bold mb-6">새 포트폴리오 저장</h3>
        <BaseInput label="이름" v-model="saveForm.name" />
        <div class="mb-6"><label class="block text-xs font-bold text-gray-500 mb-2">메모 (선택)</label><textarea v-model="saveForm.memo" rows="3" class="w-full border-b-2 p-2 outline-none resize-none"></textarea></div>
        <div class="flex gap-3 justify-end"><button @click="showSaveModal = false" class="px-4 py-2 border rounded font-bold text-gray-500">취소</button><button @click="saveNewPortfolio" class="px-6 py-2 bg-[#283593] text-white rounded font-bold">저장</button></div>
      </div>
    </div>
    <!-- 로딩 오버레이 -->
    <div v-if="analysisLoading" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100] backdrop-blur-sm fade-in">
      <div class="bg-white p-8 rounded-3xl shadow-2xl flex flex-col items-center text-center max-w-sm animate-fade-in-up">
        <div class="w-16 h-16 border-4 border-gray-200 border-t-[#283593] rounded-full animate-spin mb-6"></div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">
          {{ isRebalancing ? '전략 재설계 및 분석 중...' : '포트폴리오 비교 분석 중...' }}
        </h3>
        <p class="text-gray-500 text-sm leading-relaxed">
          AI가 상세 리포트를 생성하고 있습니다.<br/>
          최대 30초 정도 소요될 수 있으니 잠시만 기다려주세요 ☕️
        </p>
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