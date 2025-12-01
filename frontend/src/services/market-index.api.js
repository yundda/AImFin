// 실제로는 axios.get('/api/market/indices') 같은 요청을 보내야 합니다.
// 지금은 UI 구현을 위해 가짜 데이터를 반환합니다.

export const marketApi = {
  async getIndices() {
    // 0.5초 뒤에 데이터가 오는 것처럼 흉내냅니다.
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 'exchange',
            name: '달러 환율',
            value: 1470.85,
            change: 6.05,
            rate: 0.41,
            isUp: true, // 상승 여부
            // 그래프용 더미 데이터 (최근 추이)
            chartData: [1460, 1462, 1458, 1465, 1468, 1470, 1472, 1470.85]
          },
          {
            id: 'kospi',
            name: '코스피',
            value: 2650.12,
            change: -15.4,
            rate: -0.58,
            isUp: false,
            chartData: [2670, 2665, 2660, 2655, 2640, 2645, 2648, 2650]
          },
          {
            id: 'kosdaq',
            name: '코스닥',
            value: 890.55,
            change: 12.3,
            rate: 1.40,
            isUp: true,
            chartData: [870, 875, 872, 880, 885, 882, 888, 890]
          }
        ]);
      }, 500);
    });
  }
};