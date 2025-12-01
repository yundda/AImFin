<script setup>
import { ref, onMounted } from 'vue';

const emit = defineEmits(['back']); // 뒤로가기 이벤트

const portfolios = ref([]);
const editingId = ref(null); // 수정 중인 포트폴리오 ID
const editName = ref('');

onMounted(() => {
  portfolios.value = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
});

// 대표 포트폴리오 설정
const setMain = (id) => {
  portfolios.value = portfolios.value.map(p => ({ ...p, isMain: p.id === id }));
  saveToStorage();
};

// 삭제
const deletePortfolio = (id) => {
  if(!confirm('정말 삭제하시겠습니까?')) return;
  portfolios.value = portfolios.value.filter(p => p.id !== id);
  // 만약 대표 포트폴리오를 삭제했다면 첫 번째 것을 대표로 지정
  if (portfolios.value.length > 0 && !portfolios.value.some(p => p.isMain)) {
    portfolios.value[0].isMain = true;
  }
  saveToStorage();
};

// 수정 모드 진입
const startEdit = (p) => {
  editingId.value = p.id;
  editName.value = p.name;
};

// 수정 저장
const saveEdit = (id) => {
  const target = portfolios.value.find(p => p.id === id);
  if (target) target.name = editName.value;
  editingId.value = null;
  saveToStorage();
};

const saveToStorage = () => {
  localStorage.setItem('my_portfolios', JSON.stringify(portfolios.value));
};
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center gap-4 mb-6">
      <button @click="emit('back')" class="text-2xl text-gray-400 hover:text-black transition-colors">←</button>
      <h2 class="text-xl font-bold text-gray-900">마이포트폴리오 리스트</h2>
    </div>

    <div class="flex-1 overflow-y-auto pr-2 custom-scroll space-y-4">
      <div 
        v-for="p in portfolios" 
        :key="p.id" 
        class="border rounded-xl p-5 hover:border-[#536dfe] transition-all group relative bg-white"
        :class="p.isMain ? 'border-[#536dfe] ring-1 ring-[#536dfe] bg-blue-50/20' : 'border-gray-200'"
      >
        <!-- 대표 설정 체크박스 -->
        <button 
          @click="setMain(p.id)" 
          class="absolute top-4 left-4 transition-colors"
          :class="p.isMain ? 'text-[#536dfe]' : 'text-gray-300 hover:text-gray-400'"
          title="대표 포트폴리오로 설정"
        >
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
        </button>

        <!-- 우측 컨트롤 버튼 (수정/삭제) -->
        <div class="absolute top-4 right-4 flex gap-2">
          <button @click="startEdit(p)" class="text-gray-400 hover:text-[#536dfe]" title="이름 수정">✎</button>
          <button @click="deletePortfolio(p.id)" class="text-gray-400 hover:text-red-500" title="삭제">🗑️</button>
        </div>

        <div class="pl-10 pr-16">
          <!-- 이름 수정 모드 -->
          <div v-if="editingId === p.id" class="flex gap-2 mb-2">
            <input v-model="editName" class="border-b border-[#536dfe] outline-none text-sm font-bold w-full bg-transparent" @keyup.enter="saveEdit(p.id)" />
            <button @click="saveEdit(p.id)" class="text-xs bg-[#536dfe] text-white px-2 rounded">저장</button>
          </div>
          <!-- 일반 모드 -->
          <h3 v-else class="font-bold text-gray-900 mb-1 truncate">{{ p.name }}</h3>
          
          <div class="flex items-center gap-2 mb-4">
            <span class="inline-block px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">{{ p.typeLabel }}</span>
            <span class="text-xs text-gray-400">{{ p.date }}</span>
          </div>
          
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