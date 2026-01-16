import 'package:flutter/material.dart';
import 'miners/urban_miner.dart'; // 우리가 만든 광부 파일 임포트

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // 오른쪽 위 'Debug' 띠 제거
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.blueAccent, // 파란색 테마
        brightness: Brightness.light,
      ),
      home: const SlangSearchScreen(),
    );
  }
}

class SlangSearchScreen extends StatefulWidget {
  const SlangSearchScreen({super.key});

  @override
  State<SlangSearchScreen> createState() => _SlangSearchScreenState();
}

class _SlangSearchScreenState extends State<SlangSearchScreen> {
  // 입력창 컨트롤러
  final TextEditingController _controller = TextEditingController();
  // 광부 인스턴스 생성
  final UrbanMiner _miner = UrbanMiner();
  
  // 상태 변수들
  List<String> _results = [];
  bool _isLoading = false;
  String? _errorMessage;

  // 검색 실행 함수
  Future<void> _searchSlang() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    // 키보드 내리기
    FocusScope.of(context).unfocus();

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _results = []; // 기존 결과 초기화
    });

    try {
      // ⛏️ 채굴 시작 (비동기)
      final data = await _miner.mine(query);
      
      setState(() {
        _results = data;
        if (data.isEmpty) {
          _errorMessage = "검색 결과가 없습니다.\n(철자를 확인하거나, 없는 단어일 수 있습니다.)";
        }
      });
    } catch (e) {
      setState(() {
        _errorMessage = "에러가 발생했습니다: $e";
      });
    } finally {
      // 성공하든 실패하든 로딩 종료
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Slang Dictionary ⛏️'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // 1. 검색어 입력창
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: '슬랭을 입력하세요 (예: GOAT, Rizz)',
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: _controller.clear, // X 버튼 누르면 지우기
                ),
              ),
              textInputAction: TextInputAction.search, // 키보드 '검색' 버튼 활성화
              onSubmitted: (_) => _searchSlang(),
            ),
            const SizedBox(height: 12),
            
            // 2. 검색 버튼
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _searchSlang,
                icon: _isLoading 
                    ? const SizedBox(
                        width: 20, 
                        height: 20, 
                        child: CircularProgressIndicator(strokeWidth: 2)
                      )
                    : const Icon(Icons.search),
                label: Text(
                  _isLoading ? '채굴 중...' : '검색하기 (Urban Dictionary)',
                  style: const TextStyle(fontSize: 16),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // 3. 결과 표시 영역 (리스트뷰)
            Expanded(
              child: _buildResultArea(),
            ),
          ],
        ),
      ),
    );
  }

  // 결과 영역 UI 빌더
  Widget _buildResultArea() {
    if (_isLoading) {
      return const Center(child: Text("데이터를 가져오는 중입니다... 📡"));
    }

    if (_errorMessage != null) {
      return Center(
        child: Text(
          _errorMessage!,
          style: const TextStyle(color: Colors.redAccent),
          textAlign: TextAlign.center,
        ),
      );
    }

    if (_results.isEmpty) {
      return const Center(
        child: Text(
          "검색어를 입력하고 버튼을 눌러주세요.\n현재는 '영미권(Urban Dictionary)'만 지원합니다.",
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    // 결과 리스트
    return ListView.separated(
      itemCount: _results.length,
      separatorBuilder: (ctx, i) => const SizedBox(height: 10),
      itemBuilder: (ctx, index) {
        return Card(
          elevation: 3, // 그림자 효과
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              _results[index], // UrbanMiner가 만든 텍스트
              style: const TextStyle(fontSize: 14, height: 1.5),
            ),
          ),
        );
      },
    );
  }
}
