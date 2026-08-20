#!/usr/bin/env bash
set -e

echo "🚀 Starting Appium CI Test Runner..."

# Inject GITHUB_PATH into PATH if present
if [ -n "$GITHUB_PATH" ] && [ -f "$GITHUB_PATH" ]; [
  export PATH="$(cat $GITHUB_PATH | tr '\n' ':')$PATH"
]

echo "📱 Installing built debug APK onto emulator..."
if [ -n "$APK_PATH" ] && [ -f "$APK_PATH" ]; then
  adb install -r "${APK_PATH}" || true
fi

echo "🌐 Starting Appium Server..."
appium --log-level warn > /tmp/appium.log 2>&1 &

echo "⏳ Waiting for Appium port 4723..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:4723/status > /dev/null; then
    echo "✅ Appium server responsive."
    break
  fi
  sleep 1
done

echo "⚡ Running Appium Spec Suite..."
node BrainBattleAppium/tests/12_e2e/mega_android_1100.test.js

echo "✅ Appium CI Test Runner completed successfully."
