#!/bin/bash

# Radio PrideSync - Backup Script
# Backup opgenomen audio bestanden

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RECORDINGS_DIR="$PROJECT_DIR/recordings"
BACKUP_DIR="$PROJECT_DIR/backups"

# Configuratie
MAX_BACKUP_DAYS=30
COMPRESS_BACKUPS=true

echo "💾 Radio PrideSync Backup wordt gestart..."
echo "Recordings directory: $RECORDINGS_DIR"
echo "Backup directory: $BACKUP_DIR"

# Controleer of recordings directory bestaat
if [ ! -d "$RECORDINGS_DIR" ]; then
    echo "⚠️  Recordings directory niet gevonden: $RECORDINGS_DIR"
    exit 1
fi

# Maak backup directory
mkdir -p "$BACKUP_DIR"

# Genereer backup naam met timestamp
BACKUP_NAME="recordings_backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Tel bestanden
TOTAL_FILES=$(find "$RECORDINGS_DIR" -name "*.mp3" -type f | wc -l)
if [ "$TOTAL_FILES" -eq 0 ]; then
    echo "ℹ️  Geen MP3 bestanden gevonden om te backuppen"
    exit 0
fi

echo "📁 $TOTAL_FILES bestanden gevonden voor backup"

# Maak backup
if [ "$COMPRESS_BACKUPS" = true ]; then
    echo "🗜️  Gecomprimeerde backup wordt gemaakt..."
    BACKUP_FILE="$BACKUP_PATH.tar.gz"
    
    if tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" recordings/; then
        echo "✅ Backup gemaakt: $BACKUP_FILE"
        
        # Toon backup grootte
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "📊 Backup grootte: $BACKUP_SIZE"
    else
        echo "❌ Backup gefaald!"
        exit 1
    fi
else
    echo "📂 Directory backup wordt gemaakt..."
    
    if cp -r "$RECORDINGS_DIR" "$BACKUP_PATH"; then
        echo "✅ Backup gemaakt: $BACKUP_PATH"
        
        # Toon backup grootte
        BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
        echo "📊 Backup grootte: $BACKUP_SIZE"
    else
        echo "❌ Backup gefaald!"
        exit 1
    fi
fi

# Ruim oude backups op
echo "🧹 Oude backups worden opgeruimd (ouder dan $MAX_BACKUP_DAYS dagen)..."
REMOVED_COUNT=0

find "$BACKUP_DIR" -name "recordings_backup_*" -type f -mtime +$MAX_BACKUP_DAYS -print0 | while IFS= read -r -d '' file; do
    echo "🗑️  Verwijderen: $(basename "$file")"
    rm "$file"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
done

find "$BACKUP_DIR" -name "recordings_backup_*" -type d -mtime +$MAX_BACKUP_DAYS -print0 | while IFS= read -r -d '' dir; do
    echo "🗑️  Verwijderen: $(basename "$dir")"
    rm -rf "$dir"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
done

if [ "$REMOVED_COUNT" -gt 0 ]; then
    echo "✅ $REMOVED_COUNT oude backups verwijderd"
else
    echo "ℹ️  Geen oude backups om te verwijderen"
fi

# Toon backup overzicht
echo ""
echo "📋 Backup Overzicht:"
echo "==================="
ls -lh "$BACKUP_DIR" | grep "recordings_backup_" | tail -5

# Toon schijfruimte
echo ""
echo "💽 Schijfruimte:"
echo "==============="
df -h "$BACKUP_DIR" | tail -1

echo ""
echo "✅ Backup voltooid!"
