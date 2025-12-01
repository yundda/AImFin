<script setup>
import { ref, onMounted, watch } from 'vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import NewsCard from '@/components/news/NewsCard.vue';
import NewsSidebar from '@/components/news/NewsSidebar.vue';
import { newsApi } from '@/services/news.api';

const activeTab = ref('popular');
const newsList = ref([]);
const loading = ref(true);

const tabs = [
  { id: 'popular', name: '인기뉴스' },
  { id: 'major', name: '주요뉴스' },
  { id: 'latest', name: '최신뉴스' },
  { id: 'rising', name: '급상승' },
];

const fetchNews = async () => {
  loading.value = true;
  newsList.value = await newsApi.getNewsList(activeTab.value);
  loading.value = false;
};

// 탭이 바뀌면 뉴스 다시 불러오기
watch(activeTab, fetchNews);

onMounted(fetchNews);
</script>

<template>
  <DefaultLayout>
    <div class="max-w-6xl mx-auto px-6 py-10">
      
      <!-- 상단 타이틀 & 탭 -->
      <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <h2 class="text-2xl font-bold text-gray-900">금융 뉴스</h2>
        
        <!-- 탭 메뉴 -->
        <div class="flex bg-gray-100 p-1 rounded-lg self-start md:self-auto">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            @click="activeTab = tab.id"
            class="px-4 py-2 text-sm font-bold rounded-md transition-all"
            :class="activeTab === tab.id ? 'bg-white text-[#536dfe] shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ tab.name }}
          </button>
        </div>
      </div>

      <!-- 메인 컨텐츠 영역 (2단 그리드) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        <!-- 왼쪽: 뉴스 리스트 (8칸 차지) -->
        <div class="lg:col-span-8">
          <!-- 로딩 스켈레톤 -->
          <div v-if="loading" class="space-y-6">
            <div v-for="i in 5" :key="i" class="flex gap-5 animate-pulse">
              <div class="w-32 h-24 bg-gray-100 rounded-lg"></div>
              <div class="flex-1 space-y-3 py-2">
                <div class="h-4 bg-gray-100 rounded w-3/4"></div>
                <div class="h-3 bg-gray-100 rounded w-full"></div>
                <div class="h-3 bg-gray-100 rounded w-1/2"></div>
              </div>
            </div>
          </div>

          <!-- 실제 뉴스 리스트 -->
          <div v-else class="flex flex-col">
            <NewsCard 
              v-for="news in newsList" 
              :key="news.id" 
              :news="news" 
            />
            
            <!-- 더보기 버튼 -->
            <button class="w-full py-4 mt-4 text-sm font-medium text-gray-500 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
              뉴스 더보기 +
            </button>
          </div>
        </div>

        <!-- 오른쪽: 사이드바 위젯 (4칸 차지) -->
        <div class="hidden lg:block lg:col-span-4 pl-4 border-l border-gray-100">
          <NewsSidebar />
        </div>

      </div>
    </div>
  </DefaultLayout>
</template>