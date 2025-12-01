<script setup>
import { ref, onMounted } from 'vue';
import { marketApi } from '@/services/market-index.api';

const indices = ref([]);
const loading = ref(true);

// 간단한 스파크라인 SVG 경로 생성 함수
const getSvgPath = (data, width = 60, height = 30) => {
  if (!data || data.length === 0) return '';
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  
  return data.map((val, i) => {
    const x = i * stepX;
    const y = height - ((val - min) / range) * height; 
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');
};

onMounted(async () => {
  try {
    const data = await marketApi.getIndices();
    // 무한 스크롤을 위해 데이터를 4번 정도 복제해서 길게 만듭니다.
    indices.value = [...data, ...data, ...data, ...data]; 
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="w-full bg-white border-b border-gray-200 overflow-hidden h-14 flex items-center relative">
    <!-- 좌우 그라데이션 (부드러운 사라짐 효과) -->
    <div class="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none"></div>
    <div class="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"></div>

    <!-- 흐르는 컨텐츠 트랙 -->
    <div class="flex items-center animate-marquee whitespace-nowrap hover:pause">
      <div 
        v-for="(item, index) in indices" 
        :key="index"
        class="flex items-center gap-3 px-8 border-r border-gray-100 last:border-0"
      >
        <!-- 미니 차트 -->
        <svg width="40" height="20" viewBox="0 0 60 30" class="overflow-visible opacity-80">
          <path
            :d="getSvgPath(item.chartData)"
            fill="none"
            :stroke="item.isUp ? '#e22a40' : '#2e68ff'"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <!-- 지수 정보 -->
        <div class="flex flex-col">
          <span class="text-[11px] text-gray-500 font-bold leading-tight">{{ item.name }}</span>
          <div class="flex items-center gap-1 text-[11px]">
            <span class="font-bold text-gray-800">{{ item.value.toLocaleString() }}</span>
            <span :class="item.isUp ? 'text-[#e22a40]' : 'text-[#2e68ff]'">
              {{ item.isUp ? '+' : '' }}{{ item.change }} ({{ item.rate }}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); } /* 데이터 양에 따라 조절 */
}

.animate-marquee {
  animation: marquee 40s linear infinite; /* 속도 조절: 숫자가 클수록 느림 */
}

/* 마우스 올리면 멈춤 */
.hover\:pause:hover {
  animation-play-state: paused;
}
</style>