import 'package:flutter/material.dart';
import 'miners/urban_miner.dart'; // 방금 만든 파일 임포트

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(useMaterial3: true),
      home: Scaffold(
        appBar: AppBar(title: const Text('Slang Miner Test Lab 🧪')),
        body: const TestScreen(),
      ),
    );
  }
}

class TestScreen extends StatefulWidget {
  const TestScreen({super.key});

  @override
  State<TestScreen> createState() => _TestScreenState();
}

class _TestScreenState extends State<TestScreen> {
  String _status = "준비 완료";
  final _miner = UrbanMiner(); // 우리의 첫 번째 광부

  void _runTest() async {
    setState(() {
      _status = "⛏️ Urban Dictionary 채굴 중...";
    });

    // 테스트할 단어: 'GOAT' (Greatest of All Time)
    const testWord = 'GOAT'; 
    
    try {
      print('--- [요청 시작] 단어: $testWord ---');
      
      final results = await _miner.mine(testWord);
      
      print('✅ 채굴 완료! 가져온 데이터 개수: ${results.length}');
      print('--- [상세 결과 (Console 확인)] ---');
      for (var item in results) {
        print(item); // 콘솔창(Debug Console)을 보세요!
        print('-----------------------------');
      }

      setState(() {
        if (results.isNotEmpty) {
          _status = "성공! ${results.length}개의 정의를 찾았습니다.\n(디버그 콘솔을 확인하세요)";
        } else {
          _status = "결과 없음 (리스트가 비어있음)";
        }
      });
    } catch (e) {
      print('❌ 에러 발생: $e');
      setState(() {
        _status = "에러 발생: $e";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              _status, 
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 30),
            ElevatedButton.icon(
              onPressed: _runTest,
              icon: const Icon(Icons.search),
              label: const Text("Urban Miner 테스트 (Keyword: GOAT)"),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
