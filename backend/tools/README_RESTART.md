# Инструкция по перезапуску backend сервера

## Быстрый способ (вручную)

### 1. Остановить процесс

**Windows (PowerShell):**
```powershell
# Найти PID процесса на порту 8000
netstat -ano | findstr :8000

# Остановить процесс (замените PID на ваш)
Stop-Process -Id <PID> -Force

# Или остановить все процессы Python
Get-Process python | Stop-Process -Force
```

**Linux/Mac:**
```bash
# Найти процесс uvicorn
pgrep -f "uvicorn.*main:app"

# Остановить процесс
pkill -f "uvicorn.*main:app"

# Или найти процесс на порту 8000
lsof -ti:8000 | xargs kill -9
```

### 2. Запустить заново

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Автоматический способ (скрипты)

### Windows (PowerShell)

**Остановить backend:**
```powershell
.\backend\tools\stop_backend.ps1
```

**Перезапустить backend:**
```powershell
.\backend\tools\restart_backend.ps1
```

### Linux/Mac

**Остановить backend:**
```bash
chmod +x backend/tools/stop_backend.sh
./backend/tools/stop_backend.sh
```

**Перезапустить backend:**
```bash
chmod +x backend/tools/restart_backend.sh
./backend/tools/restart_backend.sh
```

## Проверка статуса

**Проверить, запущен ли backend:**
```powershell
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i:8000
```

**Проверить доступность API:**
```bash
curl http://localhost:8000/docs
# или откройте в браузере: http://localhost:8000/docs
```

## Решение проблем

### Backend не останавливается

1. **Принудительная остановка:**
   ```powershell
   # Windows
   taskkill /F /PID <PID>
   
   # Linux/Mac
   kill -9 <PID>
   ```

2. **Остановить все процессы Python:**
   ```powershell
   # Windows
   Get-Process python | Stop-Process -Force
   
   # Linux/Mac
   pkill -9 python
   ```

### Порт 8000 занят другим процессом

1. **Найти процесс:**
   ```powershell
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i:8000
   ```

2. **Остановить процесс или использовать другой порт:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

### Backend завис и не отвечает

1. Остановите процесс (см. выше)
2. Проверьте логи на наличие ошибок
3. Перезапустите backend
4. Если проблема повторяется, проверьте:
   - Настройки базы данных
   - Переменные окружения (.env файл)
   - Зависимости (requirements.txt)

## Полезные команды

**Просмотр логов в реальном времени:**
```bash
# Если запущен с --reload, логи выводятся в консоль
# Для фонового режима:
tail -f uvicorn.log
```

**Проверка версии Python и зависимостей:**
```bash
python --version
pip list | grep uvicorn
pip list | grep fastapi
```

