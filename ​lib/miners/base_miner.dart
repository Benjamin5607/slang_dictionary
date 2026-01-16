// lib/miners/base_miner.dart

abstract class BaseMiner {
  /// 검색어(query)를 받아서 원본 데이터(Raw Data) 리스트를 반환합니다.
  Future<List<String>> mine(String query);

  /// 어떤 광부인지 이름표 (디버깅용)
  String get minerName;
}
