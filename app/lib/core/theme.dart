import 'package:flutter/material.dart';

const Color heartRed = Color(0xFFFF0028);

ThemeData buildTheme() {
  return ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: heartRed, brightness: Brightness.dark),
    useMaterial3: true,
  );
}
