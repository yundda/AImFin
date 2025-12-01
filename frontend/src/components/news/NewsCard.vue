<script setup>
defineProps({
  news: {
    type: Object,
    required: true
  }
});
</script>

<template>
  <div class="flex gap-5 py-6 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer group px-2">
    <!-- 썸네일 (이미지가 있을 때만 표시) -->
    <div v-if="news.thumbnail" class="w-24 h-24 md:w-32 md:h-24 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 border border-gray-100">
      <img :src="news.thumbnail" alt="thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
    </div>
    
    <!-- 썸네일 없을 때 대체 아이콘 (공간 채우기용) -->
    <div v-else class="w-24 h-24 md:w-32 md:h-24 flex-shrink-0 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-300">
      <!-- 아이콘 대신 간단한 텍스트나 SVG 사용 -->
      <span class="text-2xl">📰</span>
    </div>

    <!-- 텍스트 영역 -->
    <div class="flex-1 flex flex-col justify-between py-0.5">
      <div>
        <h3 class="text-[17px] font-bold text-gray-900 mb-2 leading-tight group-hover:text-[#536dfe] transition-colors line-clamp-2">
          {{ news.title }}
        </h3>
        <p class="text-sm text-gray-500 line-clamp-2 leading-relaxed">
          {{ news.summary }}
        </p>
      </div>
      <div class="flex items-center text-xs text-gray-400 mt-3 font-medium">
        <span class="text-gray-500 mr-2">{{ news.source }}</span>
        <span class="w-0.5 h-0.5 bg-gray-300 rounded-full mx-1"></span>
        <span class="ml-1">{{ news.time }}</span>
      </div>
    </div>
  </div>
</template>