<script setup>
// ✅ 1. 라우터 기능 불러오기
import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';

// ✅ 2. 라우터 사용 준비
const router = useRouter();

// 감각적인 문구들
const steps = [
  { 
    step: 'STEP 01', 
    icon: '✨', 
    title: '나만의 투자 DNA 발견', 
    desc: '복잡한 고민 없이,\n몇 가지 질문으로 성향을 파악해요.' 
  },
  { 
    step: 'STEP 02', 
    icon: '🧠', 
    title: 'AI 알고리즘 설계', 
    desc: '금융 데이터 3억 건을 학습한 AI가\n최적의 포트폴리오를 그려냅니다.' 
  },
  { 
    step: 'STEP 03', 
    icon: '💎', 
    title: '자산 가치 레벨업', 
    desc: '시장 상황에 흔들리지 않는\n단단한 자산 배분을 경험하세요.' 
  }
];

// ✅ 3. 버튼 클릭 시 설문 여부 확인 후 이동
const startSurvey = async () => {
  try {
    const res = await authApi.getSurveyStatus();
    if (res.data && res.data.exists) {
      // 이미 설문 진행함 -> 바로 포트폴리오 생성
      router.push({ name: 'portfolio-create' });
    } else {
      // 설문 없음 -> 설문부터
      router.push('/survey');
    }
  } catch (e) {
    console.error("Survey check failed:", e);
    // 에러/비로그인 등 -> 일단 설문으로 이동 (가드나 리다이렉트 처리)
    router.push('/survey');
  }
};
</script>

<template>
  <div class="w-full max-w-6xl mx-auto mt-12 mb-20">
    
    <!-- 1. 히어로 섹션 (메인 타이틀) -->
    <div class="text-center mb-16 relative">
      <!-- 배경 장식 -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-gradient-to-r from-blue-100 to-purple-100 rounded-full blur-3xl opacity-50 -z-10"></div>

      <span class="inline-block py-1 px-3 rounded-full bg-blue-50 text-[#536dfe] text-xs font-bold tracking-wider mb-4 border border-blue-100">
        AI PORTFOLIO SERVICE
      </span>
      
      <h1 class="text-4xl md:text-5xl font-extrabold text-gray-900 leading-tight mb-6">
        전문가 수준의 자산 관리를<br/>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-[#536dfe] to-purple-600">
          가장 쉽고 완벽하게 시작하는 법
        </span>
      </h1>
      
      <p class="text-gray-500 text-lg mb-10 max-w-2xl mx-auto">
        투자가 처음이라도 괜찮아요. AImFIN이 당신의 성향을 분석하고,<br/>
        상위 1%의 자산 배분 전략을 자동으로 제안해 드립니다.
      </p>

      <!-- 메인 CTA 버튼 -->
      <!-- ✅ @click="startSurvey"가 위에서 만든 함수를 실행합니다 -->
      <button 
        @click="startSurvey"
        class="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-[#2C4768] font-sans rounded-full hover:bg-[#1a2f4d] hover:shadow-lg hover:-translate-y-1 focus:outline-none ring-offset-2 focus:ring-2 ring-blue-400"
      >
        <span class="mr-2 text-lg"></span> 내 맞춤 포트폴리오 확인하기
        <svg class="w-5 h-5 ml-2 -mr-1 transition-transform group-hover:translate-x-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
      </button>
    </div>

    <!-- 2. 프로세스 카드 (기능 소개) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 px-4">
      <div 
        v-for="(item, index) in steps" 
        :key="index"
        class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 hover:shadow-xl hover:border-blue-100 transition-all duration-300 group cursor-default relative overflow-hidden"
      >
        <!-- 카드 상단 장식바 -->
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 group-hover:from-[#536dfe] group-hover:to-purple-500 transition-all duration-500"></div>

        <div class="flex flex-col items-center text-center">
          <div class="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-50 text-3xl group-hover:scale-110 group-hover:bg-blue-50 transition-all duration-300">
            {{ item.icon }}
          </div>
          
          <div class="text-xs font-bold text-gray-400 mb-2 tracking-widest group-hover:text-[#536dfe] transition-colors">
            {{ item.step }}
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-[#2C4768] transition-colors">
            {{ item.title }}
          </h3>
          
          <p class="text-sm text-gray-500 leading-relaxed whitespace-pre-line">
            {{ item.desc }}
          </p>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
@keyframes pulse-slow {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
}
.blur-3xl {
  animation: pulse-slow 6s infinite;
}
</style>