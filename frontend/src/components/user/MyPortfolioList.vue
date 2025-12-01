<script setup>
import { ref, onMounted } from 'vue';
import SimpleDonut from '@/components/common/SimpleDonut.vue';

const emit = defineEmits(['back']); 

const portfolios = ref([]);
const showEditModal = ref(false);
const editForm = ref({ id: null, name: '', memo: '' });

onMounted(() => {
  portfolios.value = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
});

const setMain = (id) => {
  portfolios.value = portfolios.value.map(p => ({ ...p, isMain: p.id === id }));
  saveToStorage();
};

const deletePortfolio = (id) => {
  if(!confirm('정말 삭제하시겠습니까? 복구할 수 없습니다.')) return;
  portfolios.value = portfolios.value.filter(p => p.id !== id);
  if (portfolios.value.length > 0 && !portfolios.value.some(p => p.isMain)) {
    portfolios.value[0].isMain = true;
  }
  saveToStorage();
};

const openEditModal = (p) => {
  editForm.value = { id: p.id, name: p.name, memo: p.memo };
  showEditModal.value = true;
};

const saveEdit = () => {
  const targetIndex = portfolios.value.findIndex(p => p.id === editForm.value.id);
  if (targetIndex !== -1) {
    portfolios.value[targetIndex].name = editForm.value.name;
    portfolios.value[targetIndex].memo = editForm.value.memo;
    saveToStorage();
    showEditModal.value = false;
  }
};

const saveToStorage = () => {
  localStorage.setItem('my_portfolios', JSON.stringify(portfolios.value));
};
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

    <!-- 리스트 영역 -->
    <div class="flex-1 overflow-y-auto pr-2 custom-scroll space-y-4 pb-4 p-1">
      <div 
        v-for="p in portfolios" 
        :key="p.id" 
        class="rounded-2xl p-5 transition-all group relative bg-white shadow-sm hover:shadow-md cursor-pointer flex items-stretch justify-between"
        :class="[
          p.isMain ? 'border-2 border-[#536dfe] bg-blue-50/10' : 'border-2 border-gray-100 hover:border-[#536dfe]/50'
        ]"
        @click="setMain(p.id)"
      >
        <!-- 좌측: 정보 영역 -->
        <div class="flex-1 pl-8 pr-4 flex flex-col justify-center">
          
          <!-- 대표 설정 체크박스 -->
          <button 
            @click.stop="setMain(p.id)" 
            class="absolute top-5 left-4 transition-colors"
            :class="p.isMain ? 'text-[#536dfe]' : 'text-gray-300 hover:text-gray-400'"
            title="대표 포트폴리오로 설정"
          >
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
          </button>

          <!-- 제목 및 날짜 -->
          <div class="mb-3">
            <h3 class="font-bold text-gray-900 text-lg leading-tight">{{ p.name }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <span class="inline-block px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-bold rounded">{{ p.typeLabel }}</span>
              <span class="text-xs text-gray-400">{{ p.date }}</span>
            </div>
          </div>

          <!-- ✅ 메모 박스 (복구됨) -->
          <div v-if="p.memo" class="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 mb-4 border border-gray-100 relative">
            <div class="absolute -top-1.5 left-3 w-3 h-3 bg-gray-50 border-t border-l border-gray-100 transform rotate-45"></div>
            <p class="line-clamp-2">{{ p.memo }}</p>
          </div>

          <!-- 자산 배분 텍스트 -->
          <div class="grid grid-cols-2 gap-y-1 text-xs text-gray-500">
            <div class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 bg-[#536dfe] rounded-full"></span>주식 {{ p.assets[0] }}%</div>
            <div class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 bg-[#a5b4fc] rounded-full"></span>채권 {{ p.assets[1] }}%</div>
            <div class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 bg-[#cbd5e1] rounded-full"></span>부동산 {{ p.assets[2] }}%</div>
            <div class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 bg-[#e2e8f0] rounded-full"></span>현금 {{ p.assets[3] }}%</div>
          </div>
        </div>

        <!-- 우측: 도넛 차트 & 컨트롤 -->
        <div class="flex flex-col items-end gap-2 pl-4 border-l border-gray-100 justify-start relative w-24">
          <!-- 수정/삭제 버튼 -->
          <div class="flex gap-1 mb-2">
            <button @click.stop="openEditModal(p)" class="p-1.5 text-gray-300 hover:text-[#536dfe] hover:bg-blue-50 rounded transition-colors" title="수정">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
            </button>
            <button @click.stop="deletePortfolio(p.id)" class="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded transition-colors" title="삭제">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
            </button>
          </div>
          
          <!-- 도넛 차트 (가운데 정렬) -->
          <div class="mt-2 mr-1">
            <SimpleDonut :assets="p.assets" size="w-14 h-14" />
          </div>
        </div>

      </div>
    </div>

    <!-- 수정 모달 (기존과 동일) -->
    <div v-if="showEditModal" class="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 rounded-2xl">
      <div class="bg-white w-full max-w-sm border border-gray-200 shadow-xl rounded-2xl p-6 animate-fade-in-up">
        <h3 class="text-lg font-bold text-gray-900 mb-6">포트폴리오 수정</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">이름</label>
            <input v-model="editForm.name" class="w-full border-b-2 border-gray-200 py-2 text-gray-900 focus:outline-none focus:border-[#536dfe] bg-transparent" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">메모</label>
            <textarea v-model="editForm.memo" rows="3" class="w-full border-2 border-gray-100 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-[#536dfe] resize-none bg-gray-50"></textarea>
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