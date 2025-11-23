#!/bin/bash
# Скрипт для перезапуска backend сервера (Linux/Mac)
# Использование: ./restart_backend.sh

echo "🔄 Перезапуск backend сервера..."

# 1. Ищем процессы uvicorn
echo ""
echo "1️⃣ Поиск процессов uvicorn..."
UVICORN_PIDS=$(pgrep -f "uvicorn.*main:app")

if [ -n "$UVICORN_PIDS" ]; then
    echo "   Найдены процессы uvicorn: $UVICORN_PIDS"
    echo "   Останавливаем процессы..."
    kill -9 $UVICORN_PIDS 2>/dev/null
    sleep 2
    echo "   ✅ Процессы остановлены"
else
    echo "   Процессы uvicorn не найдены"
fi

# 2. Проверяем порт 8000
echo ""
echo "2️⃣ Проверка порта 8000..."
PORT_8000=$(lsof -ti:8000 2>/dev/null)

if [ -n "$PORT_8000" ]; then
    echo "   Порт 8000 занят процессом: $PORT_8000"
    echo "   Останавливаем процесс..."
    kill -9 $PORT_8000 2>/dev/null
    sleep 2
    echo "   ✅ Процесс остановлен"
else
    echo "   Порт 8000 свободен"
fi

# 3. Запускаем backend заново
echo ""
echo "3️⃣ Запуск backend сервера..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

if [ -f "main.py" ]; then
    echo "   Найден main.py"
    echo "   Запускаем: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    
    # Запускаем в фоновом режиме
    nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
    
    echo "   ✅ Backend запущен в фоновом режиме (PID: $!)"
    echo "   Логи: tail -f $BACKEND_DIR/uvicorn.log"
    echo ""
    echo "💡 Проверьте: http://localhost:8000/docs"
else
    echo "   ❌ Файл main.py не найден в $BACKEND_DIR"
fi

echo ""
echo "✅ Готово!"

