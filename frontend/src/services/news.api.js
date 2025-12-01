export const newsApi = {
  async getNewsList(category = 'popular') {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 1,
            title: "엔비디아, 3분기 실적 발표 앞두고 '긴장감' 고조... AI 거품론 잠재울까",
            summary: "월가의 이목이 엔비디아 실적에 쏠리고 있다. 이번 실적이 AI 반도체 시장의 향방을 가를 분수령이 될 것이라는 전망이다.",
            source: "서울경제",
            time: "15분 전",
            thumbnail: "https://images.unsplash.com/photo-1624996379697-f01d168b1a52?w=200&h=200&fit=crop"
          },
          {
            id: 2,
            title: "비트코인 1억 돌파 눈앞... '가상자산 과세 유예' 논의 급물살",
            summary: "비트코인 가격이 연일 고공행진하며 1억 원 돌파를 목전에 두고 있다. 정치권에서는 가상자산 과세 유예 논의가 활발하다.",
            source: "한국경제",
            time: "1시간 전",
            thumbnail: "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=200&h=200&fit=crop"
          },
          {
            id: 3,
            title: "테슬라, 자율주행 FSD 베타 버전 북미 전역 확대... 주가 5% 급등",
            summary: "테슬라가 완전자율주행(FSD) 소프트웨어의 베타 버전을 북미 전역으로 확대 배포한다고 밝혔다.",
            source: "블룸버그",
            time: "2시간 전",
            thumbnail: "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=200&h=200&fit=crop"
          },
          {
            id: 4,
            title: "국내 증시 '밸류업 프로그램' 기대감 여전... 저PBR주 옥석 가리기",
            summary: "정부의 기업 밸류업 프로그램에 대한 기대감이 지속되면서 저평가된 주식(저PBR) 찾기가 계속되고 있다.",
            source: "매일경제",
            time: "3시간 전",
            thumbnail: null // 이미지가 없는 경우 테스트
          },
          {
            id: 5,
            title: "연준, 금리 인하 신중론 유지... '물가 잡히는 것 더 확인해야'",
            summary: "제롬 파월 연준 의장은 금리 인하에 대해 여전히 신중한 입장을 보였다. 인플레이션 목표치 달성 확신이 필요하다는 설명이다.",
            source: "연합뉴스",
            time: "4시간 전",
            thumbnail: "https://images.unsplash.com/photo-1611974765270-ca1258822981?w=200&h=200&fit=crop"
          }
        ]);
      }, 600);
    });
  },

  async getTrendingKeywords() {
    return new Promise(resolve => {
      setTimeout(() => resolve(['삼성전자', '에코프로', '비트코인', '금리', '환율', '엔비디아', '카카오', 'IPO']), 300);
    });
  }
};