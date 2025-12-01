<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import UserProfileCard from '@/components/user/UserProfileCard.vue';
import MyPortfolioStatus from '@/components/user/MyPortfolioStatus.vue';
import MyPropensity from '@/components/user/MyPropensity.vue';
import MyAccountSettings from '@/components/user/MyAccountSettings.vue'; // ✅ 추가

const router = useRouter();

// activeTab 기본값을 'dashboard'로 설정하여 처음엔 포트폴리오 현황이 보이게 함
const activeTab = ref('dashboard'); 

const handleLogout = () => {
  router.push('/auth/login');
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        
        <!-- 왼쪽: 프로필 사이드바 -->
        <div class="lg:col-span-4 h-full">
          <UserProfileCard 
            v-model:activeTab="activeTab" 
            @logout="handleLogout"
          />
        </div>

        <!-- 오른쪽: 컨텐츠 영역 -->
        <div class="lg:col-span-8 h-full">
          
          <!-- 1. 투자 성향 설정 -->
          <div v-if="activeTab === 'propensity'" class="fade-in h-full">
            <MyPropensity />
          </div>

          <!-- 2. 계정 설정 (✅ 추가됨) -->
          <div v-else-if="activeTab === 'account'" class="fade-in h-full">
            <MyAccountSettings />
          </div>

          <!-- 3. 기본 화면 (포트폴리오 현황) -->
          <div v-else class="fade-in h-full">
            <MyPortfolioStatus />
          </div>

        </div>

      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
/* 부드러운 전환 효과 */
.fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>