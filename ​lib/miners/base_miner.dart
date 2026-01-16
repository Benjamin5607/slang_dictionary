// 모든 마이너들의 아버지
abstract class BaseMiner {
  // 1. 검색 기능: 검색어를 주면 날것의 텍스트(Raw Data) 리스트를 뱉어라.
  Future<List<String>> mine(String query);
  
  // 2. 마이너 이름 (디버깅용: "지금 네이버가 일하는 중..." 확인)
  String get minerName;
}
