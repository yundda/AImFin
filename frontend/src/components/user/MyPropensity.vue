<script setup>
const retakeSurvey = () => {
  if(confirm('기존 성향 정보가 초기화됩니다. 다시 진행하시겠습니까?')) {
    alert('설문 페이지로 이동합니다.');
    // router.push('/survey');
  }
};
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold text-gray-900">투자 성향 설정</h2>

    <!-- 현재 성향 카드 -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
      <h3 class="text-sm font-bold text-gray-500 mb-6">현재 투자 성향</h3>
      
      <div class="flex items-center gap-6">
        <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-3xl">
          🛡️
        </div>
        <div>
          <span class="inline-block px-3 py-1 bg-[#536dfe] text-white text-xs font-bold rounded-full mb-2">안정형</span>
          <p class="text-gray-600 text-sm">
            원금 보존을 최우선으로 하며, 안정적인 수익을 추구하는 투자자입니다.
          </p>
        </div>
      </div>
    </div>

    <!-- 성향 특징 리스트 -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
      <h3 class="text-sm font-bold text-gray-500 mb-6">투자 성향 특징</h3>
      <ul class="space-y-3">
        <li class="flex items-center text-sm text-gray-700">
          <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs mr-3">✔</span>
          낮은 위험 선호
        </li>
        <li class="flex items-center text-sm text-gray-700">
          <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs mr-3">✔</span>
          채권 및 예금 중심 포트폴리오
        </li>
        <li class="flex items-center text-sm text-gray-700">
          <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs mr-3">✔</span>
          장기 안정적 수익 추구
        </li>
        <li class="flex items-center text-sm text-gray-700">
          <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs mr-3">✔</span>
          변동성이 낮은 자산 선호
        </li>
      </ul>

      <!-- 재진단 버튼 -->
      <button 
        @click="retakeSurvey"
        class="w-full mt-8 py-4 bg-[#536dfe] text-white font-bold rounded-xl hover:bg-[#4059e0] transition-colors shadow-md"
      >
        투자 성향 재진단하기
      </button>
    </div>
  </div>
</template>