#!/bin/bash

# Radio PrideSync - Stop Script
# Stop de radio applicatie gracefully

echo "🛑 Radio PrideSync wordt gestopt..."

# Zoek naar draaiende Python processen
PIDS=$(pgrep -f "python.*main.py" || true)

if [ -z "$PIDS" ]; then
    echo "ℹ️  Geen draaiende Radio PrideSync processen gevonden"
    exit 0
fi

echo "Gevonden processen: $PIDS"

# Stuur SIGTERM voor graceful shutdown
echo "📤 SIGTERM wordt verzonden..."
for PID in $PIDS; do
    if kill -TERM "$PID" 2>/dev/null; then
        echo "✅ SIGTERM verzonden naar PID $PID"
    else
        echo "⚠️  Kan SIGTERM niet verzenden naar PID $PID"
    fi
done

# Wacht op graceful shutdown
echo "⏳ Wachten op graceful shutdown (max 10 seconden)..."
for i in {1..10}; do
    REMAINING_PIDS=$(pgrep -f "python.*main.py" || true)
    if [ -z "$REMAINING_PIDS" ]; then
        echo "✅ Radio PrideSync succesvol gestopt"
        exit 0
    fi
    sleep 1
    echo -n "."
done

echo ""

# Force kill als nodig
REMAINING_PIDS=$(pgrep -f "python.*main.py" || true)
if [ -n "$REMAINING_PIDS" ]; then
    echo "⚠️  Graceful shutdown gefaald, force kill wordt gebruikt..."
    for PID in $REMAINING_PIDS; do
        if kill -KILL "$PID" 2>/dev/null; then
            echo "💀 Force kill PID $PID"
        fi
    done
    
    # Finale check
    sleep 1
    FINAL_CHECK=$(pgrep -f "python.*main.py" || true)
    if [ -z "$FINAL_CHECK" ]; then
        echo "✅ Radio PrideSync geforceerd gestopt"
    else
        echo "❌ Kan Radio PrideSync niet stoppen!"
        exit 1
    fi
else
    echo "✅ Radio PrideSync succesvol gestopt"
fi
