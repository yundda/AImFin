<script setup>
import { ref, onMounted, computed } from 'vue';
import { authApi } from '@/services/auth.api';
import SimpleDonut from '@/components/common/SimpleDonut.vue';

const emit = defineEmits(['back']); 

const portfolios = ref([]);
const loading = ref(true);

// 수정 관련
const showEditModal = ref(false);
const editForm = ref({ id: null, name: '' });

// 상세 모달 관련
const showDetailModal = ref(false);
const detailLoading = ref(false);
const detailData = ref(null);

const loadPortfolios = async () => {
  try {
    const res = await authApi.getPortfolioList();
    portfolios.value = res.data;
  } catch (err) {
    console.error("Failed to load list:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(loadPortfolios);

// 클릭 시 상세 모달 열기
const openDetailModal = async (id) => {
  showDetailModal.value = true;
  detailLoading.value = true;
  detailData.value = null; // 초기화
  
  try {
    const res = await authApi.getPortfolioDetail(id);
    detailData.value = res.data;
  } catch (err) {
    console.error("Failed to load detail:", err);
    alert("상세 정보를 불러오지 못했습니다.");
    showDetailModal.value = false;
  } finally {
    detailLoading.value = false;
  }
};

// 모달에서 대표 설정
const setMainFromModal = async () => {
  if (!detailData.value) return;
  const id = detailData.value.id;
  
  try {
    await authApi.setRepresentative(id);
    
    // 리스트 UI 업데이트
    portfolios.value = portfolios.value.map(p => ({
      ...p,
      is_representative: p.id === id
    }));
    
    // 상세 데이터도 업데이트 (필요하다면)
    detailData.value.is_representative = true;

    alert("대표 포트폴리오로 설정되었습니다.");
    showDetailModal.value = false; // 설정 후 닫기 (선택적)
  } catch (err) {
    console.error("Failed to set main:", err);
    alert("설정 실패");
  }
};

const deletePortfolio = async (id) => {
  if(!confirm('정말 삭제하시겠습니까? 복구할 수 없습니다.')) return;
  try {
    await authApi.deletePortfolio(id);
    portfolios.value = portfolios.value.filter(p => p.id !== id);
    if (showDetailModal.value && detailData.value?.id === id) {
      showDetailModal.value = false;
    }
  } catch (err) {
    console.error("Failed to delete:", err);
    alert("삭제 실패");
  }
};

const openEditModal = (p) => {
  editForm.value = { id: p.id, name: p.name }; 
  showEditModal.value = true;
};

const saveEdit = async () => {
  if (!editForm.value.name) return alert("이름을 입력해주세요.");
  
  try {
    const res = await authApi.updatePortfolio(editForm.value.id, {
      name: editForm.value.name
    });
    const updated = res.data;
    const idx = portfolios.value.findIndex(p => p.id === updated.id);
    if (idx !== -1) {
      portfolios.value[idx].name = updated.name;
    }
    showEditModal.value = false;
  } catch (err) {
    console.error("Failed to update:", err);
    alert("수정 실패");
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString();
};

// 상세 자산 배분 매핑 (상세 모달용)
const detailAssets = computed(() => {
  if (!detailData.value) return [0, 0, 0, 0];
  
  const p = detailData.value;
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

const sortedPortfolios = computed(() => {
  return [...portfolios.value].sort((a, b) => {
    // 1. 대표 포트폴리오 우선
    if (a.is_representative && !b.is_representative) return -1;
    if (!a.is_representative && b.is_representative) return 1;
    // 2. 최신순 정렬
    return new Date(b.created_at) - new Date(a.created_at);
  });
});

const assetsInfo = [
  { label: '주식', color: '#536dfe' },
  { label: '채권', color: '#a5b4fc' },
  { label: '부동산/펀드', color: '#cbd5e1' },
  { label: '현금', color: '#e2e8f0' },
];
</script>

<template>
  <div class="h-full flex flex-col relative">
    <!-- 헤더 -->
    <div class="flex items-center gap-4 mb-4 flex-shrink-0">
      <button @click="emit('back')" class="text-2xl text-gray-400 hover:text-black transition-colors p-1 rounded-full hover:bg-gray-100">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
      </button>
      <h2 class="text-xl font-bold text-gray-900">마이포트폴리오 리스트</h2>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#536dfe]"></div>
    </div>

    <!-- 리스트 영역 -->
    <div v-else class="flex-1 overflow-y-auto pr-2 custom-scroll space-y-4 pb-4 p-1">
      <div 
        v-for="p in sortedPortfolios" 
        :key="p.id" 
        class="rounded-2xl p-5 transition-all group relative bg-white shadow-sm hover:shadow-md cursor-pointer flex items-stretch justify-between"
        :class="[
          p.is_representative ? 'border-2 border-[#536dfe] bg-blue-50/10' : 'border-2 border-gray-100 hover:border-[#536dfe]/50'
        ]"
        @click="openDetailModal(p.id)"
      >
        <!-- 좌측: 정보 영역 -->
        <div class="flex-1 pl-4 pr-4 flex flex-col justify-center">
          
          <!-- 대표 뱃지 (체크박스 대신 뱃지로 변경) -->
          <div v-if="p.is_representative" class="mb-2">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-[#536dfe] text-white text-[10px] font-bold rounded-full">
              <span class="w-1.5 h-1.5 bg-white rounded-full"></span>
              대표
            </span>
          </div>

          <!-- 제목 및 날짜 -->
          <div class="mb-3">
            <h3 class="font-bold text-gray-900 text-lg leading-tight">{{ p.name }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <span class="inline-block px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-bold rounded">{{ p.profile_label || p.profile }}</span>
              <span class="text-xs text-gray-400">{{ formatDate(p.created_at) }}</span>
            </div>
          </div>

          <!-- 메트릭 -->
          <div class="flex gap-4 text-sm mt-1">
            <div class="flex items-center gap-1.5">
              <span class="text-gray-500">수익률</span>
              <span class="font-bold text-[#536dfe]">+{{ p.metrics?.expected_return_pct }}%</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-gray-500">위험도</span>
              <span class="font-bold text-gray-700">{{ p.metrics?.risk_score }}점</span>
            </div>
          </div>
        </div>

        <!-- 우측: 컨트롤 (수정/삭제) -->
        <div class="flex flex-col items-end gap-2 pl-4 border-l border-gray-100 justify-center relative w-16">
          <button @click.stop="openEditModal(p)" class="p-2 text-gray-300 hover:text-[#536dfe] hover:bg-blue-50 rounded transition-colors" title="수정">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
          </button>
          <button @click.stop="deletePortfolio(p.id)" class="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded transition-colors" title="삭제">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
          </button>
        </div>

      </div>
    </div>

    <!-- ✅ 상세 모달 (Fixed Full Screen) -->
    <div v-if="showDetailModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" @click="showDetailModal = false"></div>

      <!-- Modal Content -->
      <div class="relative bg-white w-full max-w-2xl max-h-[90vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-fade-in-up">
        
        <!-- Header -->
        <div class="px-8 py-5 border-b border-gray-100 flex justify-between items-center bg-white shrink-0">
          <h3 class="text-xl font-bold text-gray-900">포트폴리오 상세 분석</h3>
          <button @click="showDetailModal = false" class="p-2 -mr-2 text-gray-400 hover:text-black rounded-full transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
        
        <!-- Body -->
        <div class="flex-1 overflow-y-auto custom-scroll p-8 bg-gray-50/50">
          <div v-if="detailLoading" class="flex h-64 items-center justify-center">
             <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#536dfe]"></div>
          </div>
          <div v-else-if="detailData" class="space-y-8">
            
            <!-- 1. 기본 정보 & 점수 -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
              <div>
                <div class="flex items-center gap-3 mb-2">
                  <h2 class="text-2xl font-bold text-gray-900">{{ detailData.name }}</h2>
                  <span class="px-2.5 py-1 bg-blue-50 text-[#536dfe] text-xs font-bold rounded-lg">{{ detailData.profile_label }}</span>
                </div>
                <p class="text-gray-400 text-sm">{{ formatDate(detailData.created_at) }} 생성</p>
                <div class="mt-4 flex items-baseline gap-2">
                  <span class="text-sm font-bold text-gray-500">예상 수익률</span>
                  <span class="text-2xl font-bold text-[#536dfe]">+{{ detailData.metrics?.expected_return_pct }}%</span>
                </div>
              </div>

              <!-- 위험도 게이지 -->
              <div class="bg-gray-50 rounded-xl p-4">
                <div class="flex justify-between items-end mb-2 px-1">
                  <span class="text-xs font-bold text-gray-500">위험도 레벨</span>
                  <span class="text-sm font-bold" :class="(detailData.metrics?.risk_score || 0) > 60 ? 'text-red-500' : ((detailData.metrics?.risk_score || 0) > 40 ? 'text-yellow-500' : 'text-green-500')">
                    {{ detailData.metrics?.risk_score }}점 ({{ (detailData.metrics?.risk_score || 0) > 60 ? '높음' : ((detailData.metrics?.risk_score || 0) > 40 ? '중간' : '낮음') }})
                  </span>
                </div>
                <div class="h-3 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative shadow-inner">
                  <div 
                    class="absolute top-1/2 -translate-y-1/2 w-1.5 h-6 bg-gray-800 border-2 border-white rounded-sm shadow-md transition-all duration-1000 ease-out"
                    :style="{ left: (detailData.metrics?.risk_score || 0) + '%' }"
                  ></div>
                </div>
                <div class="flex justify-between text-[10px] text-gray-400 mt-2 font-medium px-1">
                  <span>안전</span>
                  <span>위험</span>
                </div>
              </div>
            </div>

            <!-- 2. 차트 & 자산배분 -->
            <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col sm:flex-row items-center justify-around gap-8">
              <div class="relative w-48 h-48 shrink-0">
                <SimpleDonut :assets="detailAssets" size="w-48 h-48" :show-tooltip="false" />
                <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span class="text-lg font-bold text-[#536dfe]">{{ detailData.profile_label }}</span>
                </div>
              </div>
              
              <div class="w-full max-w-sm space-y-3">
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">자산 배분</div>
                <div v-for="(info, idx) in assetsInfo" :key="idx" class="flex justify-between items-center p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div class="flex items-center gap-3">
                    <span class="w-3 h-3 rounded-full shadow-sm" :style="{ backgroundColor: info.color }"></span>
                    <span class="text-gray-700 font-bold text-sm">{{ info.label }}</span>
                  </div>
                  <span class="font-bold text-gray-900">{{ detailAssets[idx] }}%</span>
                </div>
              </div>
            </div>

            <!-- 3. AI 코멘트 -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h4 class="text-sm font-bold text-[#536dfe] mb-3 uppercase tracking-wider flex items-center gap-2">
                <span class="text-lg">💡</span> AI 
              </h4>
              <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-line p-4 bg-blue-50/30 rounded-xl border border-blue-50">
                 {{ detailData.rationale || detailData.summary || "분석 코멘트가 없습니다." }}
              </div>
            </div>

          </div>
        </div>

        <!-- Footer -->
        <div v-if="!detailLoading && detailData" class="p-6 bg-white border-t border-gray-100 flex gap-4 shrink-0">
          <button 
            @click="showDetailModal = false"
            class="flex-1 py-3.5 rounded-xl border border-gray-200 font-bold text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all text-sm"
          >
            닫기
          </button>
          <button 
            @click="setMainFromModal"
            :disabled="detailData.is_representative"
            class="flex-[2] py-3.5 rounded-xl bg-[#536dfe] text-white font-bold hover:bg-[#4059e0] hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none text-sm flex items-center justify-center gap-2"
          >
            <span v-if="detailData.is_representative">✅ 현재 대표 포트폴리오입니다</span>
            <span v-else>이 포트폴리오를 대표로 설정하기</span>
          </button>
        </div>

      </div>
    </div>

    <!-- 수정 모달 (기존 유지) -->
    <div v-if="showEditModal" class="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 rounded-2xl">
      <div class="bg-white w-full max-w-sm border border-gray-200 shadow-xl rounded-2xl p-6 animate-fade-in-up">
        <h3 class="text-lg font-bold text-gray-900 mb-6">포트폴리오 이름 수정</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">이름</label>
            <input v-model="editForm.name" class="w-full border-b-2 border-gray-200 py-2 text-gray-900 focus:outline-none focus:border-[#536dfe] bg-transparent" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-8">
          <button @click="showEditModal = false" class="px-4 py-2 border border-gray-300 rounded-lg font-bold text-gray-500 text-sm hover:bg-gray-50">취소</button>
          <button @click="saveEdit" class="px-6 py-2 bg-[#536dfe] text-white rounded-lg font-bold text-sm hover:bg-[#4059e0]">수정 완료</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #e2e8f0; border-radius: 3px; }
.animate-fade-in-up { animation: fadeInUp 0.3s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>