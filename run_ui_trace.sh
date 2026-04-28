#!/bin/bash

echo "🔍 UI → API TRACE MODE"
echo "====================="
echo ""

# Check if frontend is running
echo "Checking if frontend is running on localhost:3000..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend not running"
    echo ""
    echo "Start it with:"
    echo "  npm run dev"
    echo ""
    exit 1
fi

echo ""
echo "✅ All trace logs are in place"
echo ""
echo "📋 Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Open browser console (F12 or Cmd+Option+I)"
echo "3. Click the floating robot button"
echo "4. Type: 'I like coding'"
echo "5. Click Send"
echo "6. Watch the console for trace logs"
echo ""
echo "Expected logs:"
echo "  🤖 [STEP 1] Robot clicked"
echo "  💬 [STEP 2] Chat open state: true"
echo "  ⌨️  [STEP 3] User typed: I like coding"
echo "  📤 [STEP 4] sendMessage triggered"
echo "  🌐 [STEP 5] API CALL →"
echo "  📥 [STEP 6] API RESPONSE ←"
echo "  ✅ [STEP 7] Bot response received"
echo "  🎨 [STEP 8] Rendering message"
echo ""
echo "Report back with which step FAILS (last one that appears)"
