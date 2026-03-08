import 'package:flutter_test/flutter_test.dart';
import 'package:air_marshall/main.dart';

void main() {
  testWidgets('App renders without throwing', (WidgetTester tester) async {
    await tester.pumpWidget(const App());
    expect(find.text('air-marshall'), findsOneWidget);
  });
}
