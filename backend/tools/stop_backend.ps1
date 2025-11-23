# Скрипт для остановки backend сервера
# Использование: .\stop_backend.ps1

Write-Host "🛑 Остановка backend сервера..." -ForegroundColor Yellow

# 1. Проверяем порт 8000
Write-Host "`n1️⃣ Проверка порта 8000..." -ForegroundColor Cyan
$port8000 = netstat -ano | findstr :8000

if ($port8000) {
    Write-Host "   Порт 8000 занят:" -ForegroundColor Yellow
    Write-Host "   $port8000" -ForegroundColor Gray
    
    # Извлекаем PID
    $pidMatch = $port8000 | Select-String -Pattern "LISTENING\s+(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    if ($pidMatch) {
        Write-Host "   Найден PID: $pidMatch" -ForegroundColor Yellow
        Write-Host "   Останавливаем процесс..." -ForegroundColor Yellow
        
        try {
            Stop-Process -Id $pidMatch -Force -ErrorAction Stop
            Write-Host "   ✅ Процесс остановлен (PID: $pidMatch)" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Не удалось остановить процесс: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   Порт 8000 свободен" -ForegroundColor Green
}

# 2. Ищем процессы Python, которые могут быть uvicorn
Write-Host "`n2️⃣ Поиск процессов Python..." -ForegroundColor Cyan
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw"}

if ($pythonProcesses) {
    Write-Host "   Найдено процессов Python: $($pythonProcesses.Count)" -ForegroundColor Gray
    
    # Пытаемся найти процессы, которые используют uvicorn
    foreach ($proc in $pythonProcesses) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*main:app*") {
                Write-Host "   Найден процесс uvicorn (PID: $($proc.Id))" -ForegroundColor Yellow
                Write-Host "   Останавливаем..." -ForegroundColor Yellow
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                Write-Host "   ✅ Процесс остановлен" -ForegroundColor Green
            }
        } catch {
            # Игнорируем ошибки доступа
        }
    }
} else {
    Write-Host "   Процессы Python не найдены" -ForegroundColor Gray
}

Write-Host "`n✅ Готово!" -ForegroundColor Green

