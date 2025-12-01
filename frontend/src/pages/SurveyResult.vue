<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';

const route = useRoute();
const router = useRouter();
const type = route.query.type || 'Balanced';

const typeInfo = {
  Anjung: { label: '안정형', color: 'bg-green-500', desc: '원금 보존을 최우선으로 합니다.', chart: [20, 50, 20, 10] },
  AnjungChugu: { label: '안정추구형', color: 'bg-teal-500', desc: '안정적인 수익을 추구합니다.', chart: [30, 40, 20, 10] },
  Balanced: { label: '중립형', color: 'bg-blue-500', desc: '위험과 수익의 균형을 맞춥니다.', chart: [40, 30, 20, 10] },
  Jeogeug: { label: '적극투자형', color: 'bg-indigo-500', desc: '높은 수익을 위해 위험을 감수합니다.', chart: [60, 20, 10, 10] },
  Aggressive: { label: '공격투자형', color: 'bg-purple-500', desc: '최대 수익을 목표로 공격적으로 투자합니다.', chart: [80, 10, 5, 5] }
};

const result = computed(() => typeInfo[type]);
const showModal = ref(false);
const saveForm = ref({ name: `${result.value.label} 포트폴리오`, memo: '' });

// 도넛 차트 스타일 계산
const pieStyle = computed(() => {
  const [s, b, r, c] = result.value.chart;
  return `background: conic-gradient(#536dfe 0% ${s}%, #a5b4fc ${s}% ${s+b}%, #cbd5e1 ${s+b}% ${s+b+r}%, #e2e8f0 ${s+b+r}% 100%)`;
});

const savePortfolio = () => {
  if (!saveForm.value.name) return alert('포트폴리오 이름을 입력해주세요.');

  const newPortfolio = {
    id: Date.now(),
    typeLabel: result.value.label,
    typeCode: type,
    name: saveForm.value.name,
    memo: saveForm.value.memo,
    date: new Date().toLocaleDateString(),
    assets: result.value.chart,
    isMain: false // 기본값
  };
  
  // 로컬 스토리지 저장 (데모용)
  const saved = JSON.parse(localStorage.getItem('my_portfolios') || '[]');
  
  // 첫 저장이면 자동으로 대표 포트폴리오로 설정
  if (saved.length === 0) newPortfolio.isMain = true;
  
  saved.push(newPortfolio);
  localStorage.setItem('my_portfolios', JSON.stringify(saved));

  alert('포트폴리오가 저장되었습니다!');
  router.push('/user/mypage');
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-4xl mx-auto px-6 py-12">
      <div class="bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden text-center p-10">
        <div class="text-sm font-bold text-gray-400 mb-2">AI 추천 포트폴리오</div>
        <h2 class="text-2xl font-bold text-gray-900 mb-4">당신의 투자 성향에 맞는 최적의 전략</h2>
        <p class="text-gray-500 mb-8">{{ result.desc }}</p>
        
        <span class="inline-block px-4 py-1.5 rounded-full text-white text-sm font-bold mb-10" :class="result.color">
          {{ result.label }}
        </span>

        <!-- 차트 영역 -->
        <div class="relative w-56 h-56 mx-auto rounded-full mb-12 shadow-sm" :style="pieStyle">
          <div class="absolute inset-4 bg-white rounded-full flex items-center justify-center shadow-inner">
            <span class="text-2xl font-bold text-gray-800">{{ result.label }}</span>
          </div>
        </div>

        <!-- 자산 배분 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-12 bg-gray-50 p-6 rounded-xl">
          <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#536dfe] rounded-full"></span>주식 {{ result.chart[0] }}%</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#a5b4fc] rounded-full"></span>채권 {{ result.chart[1] }}%</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#cbd5e1] rounded-full"></span>부동산 {{ result.chart[2] }}%</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 bg-[#e2e8f0] rounded-full"></span>현금 {{ result.chart[3] }}%</div>
        </div>

        <div class="flex gap-4 justify-center">
          <button @click="router.push('/survey')" class="px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-600 hover:bg-gray-50">투자 성향 재진단하기</button>
          <button @click="showModal = true" class="px-8 py-3 bg-[#536dfe] text-white rounded-xl font-bold hover:bg-[#4059e0] shadow-md">저장하기</button>
        </div>
      </div>
    </div>

    <!-- 저장 모달 -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative animate-fade-in-up">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-bold">포트폴리오 저장</h3>
          <button @click="showModal = false" class="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        
        <BaseInput label="포트폴리오 이름" v-model="saveForm.name" placeholder="예: 안정형 포트폴리오 2024" />
        
        <div class="mb-8">
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">메모 (선택)</label>
          <textarea v-model="saveForm.memo" rows="3" class="w-full border-b-2 border-gray-200 py-2 text-gray-900 focus:outline-none focus:border-[#536dfe] resize-none bg-transparent" placeholder="포트폴리오에 대한 메모를 입력하세요"></textarea>
        </div>
        
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