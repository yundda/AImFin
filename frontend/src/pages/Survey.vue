<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const currentStep = ref(0);
const answers = ref({});

// ✅ 질문 데이터 (점수 매핑 포함)
const questions = [
  // 1~2. Experience (가중치 0.2)
  {
    id: 1, category: '투자 경험', type: 'multi',
    question: '투자 경험이 있는 상품을 모두 선택해주세요.',
    options: [
      { label: '예·적금', score: 0 }, { label: '채권', score: 1 },
      { label: '주식·ETF', score: 2 }, { label: '펀드', score: 2 },
      { label: '파생상품(ELS 등)', score: 3 }, { label: '해외상품', score: 3 }
    ]
  },
  {
    id: 2, category: '투자 기간',
    question: '지금까지의 투자 기간과 빈도는?',
    options: [
      { label: '1년 미만 / 거의 없음', score: 0 },
      { label: '1~3년 / 연 1~3회', score: 1 },
      { label: '3년 이상 / 월 1회 이상', score: 2 }
    ]
  },
  // 3~6. Afford (가중치 0.2)
  { id: 3, category: '연 소득', question: '연 소득 수준은?', options: [{ label: '3천만 미만', score: 0 }, { label: '3천~7천', score: 1 }, { label: '7천~1억', score: 2 }, { label: '1억 이상', score: 3 }] },
  { id: 4, category: '자산 규모', question: '총 금융자산 규모는?', options: [{ label: '5천만 미만', score: 0 }, { label: '5천~1억', score: 1 }, { label: '1억~5억', score: 2 }, { label: '5억 이상', score: 3 }] },
  { id: 5, category: '부채 비중', question: '자산 대비 부채 비중은?', options: [{ label: '상당히 있음', score: 0 }, { label: '소폭 있음', score: 2 }, { label: '없음', score: 3 }] },
  { id: 6, category: '투자 비중', question: '전체 자산 중 투자금 비중은?', options: [{ label: '50% 이상', score: 0 }, { label: '30~50%', score: 1 }, { label: '10~30%', score: 2 }, { label: '10% 미만', score: 3 }] },
  // 7~8. Purpose (가중치 0.2)
  { id: 7, category: '투자 목적', question: '이번 투자의 주된 목적은?', options: [{ label: '자산 보존', score: 0 }, { label: '예금+α 수익', score: 1 }, { label: '자산 증식', score: 2 }, { label: '적극적 수익', score: 3 }, { label: '단기 고수익', score: 4 }] },
  { id: 8, category: '목표 수익률', question: '기대하는 연 수익률은?', options: [{ label: '3% 이하', score: 0 }, { label: '3~5%', score: 1 }, { label: '5~10%', score: 2 }, { label: '10% 이상', score: 3 }] },
  // 9~11. Risk (가중치 0.3)
  { id: 9, category: '손실 대응', question: '-10% 손실 시 대응은?', options: [{ label: '전량 매도', score: 0 }, { label: '일부 매도', score: 1 }, { label: '보유', score: 2 }, { label: '추가 매수', score: 3 }] },
  { id: 10, category: '변동성', question: '변동성이 큰 상품에 대한 생각은?', options: [{ label: '매우 불안', score: 0 }, { label: '다소 불안', score: 1 }, { label: '괜찮음', score: 2 }, { label: '기회라고 생각', score: 3 }] },
  { id: 11, category: '위험 선호', question: '원금 손실 감수하고 고수익 기대?', options: [{ label: '전혀 아님', score: 0 }, { label: '아님', score: 1 }, { label: '그렇다', score: 2 }, { label: '매우 그렇다', score: 3 }] },
  // 12. Period (가중치 0.1)
  { id: 12, category: '투자 기간', question: '투자 가능한 기간은?', options: [{ label: '1년 미만', score: 0 }, { label: '1~3년', score: 1 }, { label: '3~5년', score: 2 }, { label: '5년 이상', score: 3 }] }
];

const progress = computed(() => ((currentStep.value + 1) / questions.length) * 100);
const currentQ = computed(() => questions[currentStep.value]);

const handleSelect = (option) => {
  if (currentQ.value.type === 'multi') {
    const currentAnswers = answers.value[currentQ.value.id] || [];
    const idx = currentAnswers.findIndex(item => item.label === option.label);
    if (idx > -1) currentAnswers.splice(idx, 1);
    else currentAnswers.push(option);
    answers.value[currentQ.value.id] = currentAnswers;
  } else {
    answers.value[currentQ.value.id] = option;
    nextStep();
  }
};

const nextStep = () => {
  if (currentStep.value < questions.length - 1) currentStep.value++;
  else finishSurvey();
};

const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--;
  else router.back();
};

// ✅ 성향 진단 알고리즘 구현
const calculateResult = () => {
  const getScore = (id) => {
    const ans = answers.value[id];
    // 복수 선택은 합산하되 최대 6점으로 제한
    if (Array.isArray(ans)) return Math.min(ans.reduce((acc, cur) => acc + cur.score, 0), 6);
    return ans ? ans.score : 0;
  };

  // 영역별 점수 계산 (만점 기준 환산)
  const experience = (getScore(1) + getScore(2)) / 8 * 20; 
  const afford = (getScore(3) + getScore(4) + getScore(5) + getScore(6)) / 12 * 20;
  const purpose = (getScore(7) + getScore(8)) / 7 * 20;
  const risk = (getScore(9) + getScore(10) + getScore(11)) / 9 * 30;
  const period = (getScore(12)) / 3 * 10;

  const totalScore = experience + afford + purpose + risk + period;
  
  let type = '';
  if (totalScore <= 25) type = 'Anjung';
  else if (totalScore <= 45) type = 'AnjungChugu';
  else if (totalScore <= 65) type = 'Balanced';
  else if (totalScore <= 80) type = 'Jeogeug';
  else type = 'Aggressive';

  return { score: Math.round(totalScore), type };
};

const finishSurvey = () => {
  const result = calculateResult();
  router.push({ name: 'survey-result', query: { type: result.type, score: result.score } });
};
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col font-sans">
    <!-- 상단 진행바 -->
    <div class="px-6 py-6 sticky top-0 bg-white z-10">
      <div class="flex items-center mb-6">
        <button @click="prevStep" class="text-2xl text-gray-400 hover:text-black">←</button>
        <span class="ml-auto text-xs font-bold text-[#536dfe]">{{ currentStep + 1 }} / {{ questions.length }}</span>
      </div>
      <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div class="h-full bg-[#536dfe] transition-all duration-500 ease-out" :style="{ width: progress + '%' }"></div>
      </div>
    </div>

    <!-- 질문 컨텐츠 -->
    <div class="flex-1 px-6 pb-10 flex flex-col justify-center max-w-lg mx-auto w-full">
      <div class="mb-10">
        <span class="inline-block py-1 px-3 bg-blue-50 text-[#536dfe] text-xs font-bold rounded-full mb-4">Q{{ currentQ.id }}. {{ currentQ.category }}</span>
        <h2 class="text-2xl font-bold text-gray-900 leading-snug whitespace-pre-line">{{ currentQ.question }}</h2>
      </div>

      <div class="space-y-3">
        <button 
          v-for="(opt, idx) in currentQ.options" 
          :key="idx" 
          @click="handleSelect(opt)"
          class="w-full text-left p-5 rounded-2xl border transition-all active:scale-[0.98]"
          :class="[
            currentQ.type === 'multi' && answers[currentQ.id]?.some(a => a.label === opt.label) 
              ? 'border-[#536dfe] bg-blue-50 text-[#536dfe] font-bold' 
              : 'border-gray-200 hover:border-[#536dfe] text-gray-700'
          ]"
        >
          {{ opt.label }}
        </button>
      </div>
      
      <button v-if="currentQ.type === 'multi'" @click="nextStep" class="mt-8 w-full py-4 bg-[#536dfe] text-white font-bold rounded-xl shadow-md hover:bg-[#4059e0]">
        다음
      </button>
    </div>
  </div>
</template>