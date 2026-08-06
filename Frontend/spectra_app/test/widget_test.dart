import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:spectra_app/main.dart';

void main() {
  testWidgets('SpectraApp builds successfully', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: SpectraApp()));
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}