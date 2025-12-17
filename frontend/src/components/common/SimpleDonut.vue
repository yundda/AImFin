<script setup>
import { computed } from 'vue';

const props = defineProps({
  assets: {
    type: Array, // Expected: Array of numbers [val1, val2, ...] OR Objects if refactored, but sticking to numbers for now based on usage
    required: true,
    default: () => []
  },
  labels: {
    type: Array,
    default: () => ['국내주식', '미국주식', '국내채권', '해외채권', '대체투자', '펀드', '현금성자산']
  },
  colors: {
    type: Array,
    default: () => ['#536dfe', '#3b82f6', '#10b981', '#34d399', '#f59e0b', '#8b5cf6', '#cbd5e1'] // 7 colors
    // STOCKS_KR(blue), STOCKS_GLB(lighter blue), BONDS_KR(green), BONDS_GLB(light green), ALTS(orange), FUNDS(purple), CASH(gray)
  },
  size: {
    type: String,
    default: 'w-20 h-20'
  },
  showTooltip: {
    type: Boolean,
    default: true
  }
});

const chartStyle = computed(() => {
  if (!props.assets || props.assets.length === 0) return 'background: #f3f4f6';
  
  let gradient = 'conic-gradient(';
  let currentPos = 0;
  
  props.assets.forEach((val, index) => {
    // If val is effectively 0, skip visual segment logic or just handle it naturally
    // conic-gradient handles 0-width segments fine
    const color = props.colors[index % props.colors.length];
    const segmentStart = currentPos;
    const segmentEnd = currentPos + val;
    
    gradient += `${color} ${segmentStart}% ${segmentEnd}%, `;
    currentPos = segmentEnd;
  });
  
  // Remove last comma and close
  gradient = gradient.slice(0, -2) + ')';
  
  return `background: ${gradient}`;
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
    <div v-if="showTooltip" class="absolute top-1/2 right-full -translate-y-1/2 mr-3 w-40 bg-gray-800 text-white text-xs rounded-lg py-2 px-3 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
      
      <div class="flex flex-col gap-1">
        <div v-for="(val, i) in assets" :key="i" class="flex justify-between items-center">
          <div class="flex items-center gap-1.5 overflow-hidden">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: colors[i % colors.length] }"></span>
            <span class="text-gray-300 truncate">{{ labels[i] || '기타' }}</span>
          </div>
          <span class="font-bold shrink-0">{{ val }}%</span>
        </div>
      </div>

      <!-- 말풍선 꼬리 (오른쪽을 향함) -->
      <div class="absolute top-1/2 -right-1 -translate-y-1/2 border-4 border-transparent border-l-gray-800"></div>
    </div>

  </div>
</template>