<script setup>
import { computed } from 'vue';

const props = defineProps({
  assets: {
    type: Array,
    required: true,
    default: () => [0, 0, 0, 0] // 주식, 채권, 부동산, 현금
  },
  size: {
    type: String,
    default: 'w-20 h-20'
  }
});

const labels = ['주식', '채권', '부동산', '현금'];
const colors = ['#536dfe', '#a5b4fc', '#cbd5e1', '#e2e8f0'];

const chartStyle = computed(() => {
  const [stock, bond, real, cash] = props.assets;
  const p1 = stock;
  const p2 = stock + bond;
  const p3 = stock + bond + real;
  
  return `background: conic-gradient(
    ${colors[0]} 0% ${p1}%, 
    ${colors[1]} ${p1}% ${p2}%, 
    ${colors[2]} ${p2}% ${p3}%, 
    ${colors[3]} ${p3}% 100%
  )`;
});
</script>

<template>
  <div class="relative group cursor-help inline-block">
    
    <!-- 차트 본체 -->
    <div :class="[size, 'rounded-full relative shadow-sm flex-shrink-0']" :style="chartStyle">
      <div class="absolute inset-[20%] bg-white rounded-full flex items-center justify-center"></div>
    </div>

    <!-- ✅ 툴팁 수정: 위쪽(bottom-full) -> 왼쪽(right-full)으로 변경 -->
    <!-- z-index를 높여서 다른 요소 위로 뜨게 함 -->
    <div class="absolute top-1/2 right-full -translate-y-1/2 mr-3 w-32 bg-gray-800 text-white text-xs rounded-lg py-2 px-3 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
      
      <div class="flex flex-col gap-1">
        <div v-for="(val, i) in assets" :key="i" class="flex justify-between items-center">
          <div class="flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: colors[i] }"></span>
            <span class="text-gray-300">{{ labels[i] }}</span>
          </div>
          <span class="font-bold">{{ val }}%</span>
        </div>
      </div>

      <!-- 말풍선 꼬리 (오른쪽을 향함) -->
      <div class="absolute top-1/2 -right-1 -translate-y-1/2 border-4 border-transparent border-l-gray-800"></div>
    </div>

  </div>
</template>