// lib/miners/urban_miner.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'base_miner.dart';

class UrbanMiner implements BaseMiner {
  @override
  String get minerName => 'Urban Dictionary API';

  @override
  Future<List<String>> mine(String query) async {
    // 얼반 딕셔너리 공식 API 엔드포인트
    final url = Uri.parse('https://api.urbandictionary.com/v0/define?term=$query');

    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final list = data['list'] as List;

        // 결과가 없으면 빈 리스트 반환
        if (list.isEmpty) return [];

        // 너무 많이 가져오면 토큰 낭비니까, 좋아요 순 상위 5개 정도만 추려서 가져옵니다.
        // Groq가 읽기 좋게 "Definition"과 "Example"을 묶어서 문자열로 만듭니다.
        return list.take(5).map((item) {
          return """
          [Source: UrbanDictionary]
          Definition: ${item['definition']}
          Example: ${item['example']}
          Thumbs Up: ${item['thumbs_up']}
          """;
        }).toList().cast<String>();
        
      } else {
        print('Error: Urban API Status ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('Urban Miner Error: $e');
      return [];
    }
  }
}
