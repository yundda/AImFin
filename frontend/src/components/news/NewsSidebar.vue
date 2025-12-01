<script setup>
import { ref, onMounted } from 'vue';
import { newsApi } from '@/services/news.api';

const keywords = ref([]);

onMounted(async () => {
  keywords.value = await newsApi.getTrendingKeywords();
});
</script>

<template>
  <div class="space-y-6">
    <!-- 위젯 1: 실시간 인기 키워드 -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h3 class="font-bold text-gray-900 mb-4 flex items-center">
        🔥 실시간 인기 키워드
      </h3>
      <div class="flex flex-wrap gap-2">
        <span 
          v-for="(word, i) in keywords" 
          :key="i"
          class="px-3 py-1.5 bg-gray-50 hover:bg-[#536dfe] hover:text-white text-gray-600 text-sm rounded-full transition-colors cursor-pointer border border-gray-100"
        >
          #{{ word }}
        </span>
      </div>
    </div>

    <!-- 위젯 2: 광고 배너 스타일 (포트폴리오 유도) -->
    <div class="bg-[#2C4768] rounded-xl p-6 text-white text-center shadow-lg relative overflow-hidden group cursor-pointer">
      <div class="absolute top-0 right-0 -mr-4 -mt-4 w-24 h-24 bg-white opacity-10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
      
      <h3 class="font-bold text-lg mb-2 relative z-10">내 투자 성향은?</h3>
      <p class="text-sm text-gray-300 mb-4 relative z-10">AI가 분석해드려요.</p>
      <button class="text-xs font-bold bg-white text-[#2C4768] px-4 py-2 rounded shadow-sm hover:bg-gray-100 transition-colors relative z-10">
        지금 확인하기 >
      </button>
    </div>
  </div>
</template>