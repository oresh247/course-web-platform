# Скрипт для перезапуска backend сервера
# Использование: .\restart_backend.ps1

Write-Host "🔄 Перезапуск backend сервера..." -ForegroundColor Cyan

# 1. Ищем процессы Python, которые могут быть uvicorn
Write-Host "`n1️⃣ Поиск процессов Python..." -ForegroundColor Yellow
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw"}

if ($pythonProcesses) {
    Write-Host "   Найдено процессов Python: $($pythonProcesses.Count)" -ForegroundColor Gray
    foreach ($proc in $pythonProcesses) {
        Write-Host "   - PID: $($proc.Id), Имя: $($proc.ProcessName), Путь: $($proc.Path)" -ForegroundColor Gray
    }
} else {
    Write-Host "   Процессы Python не найдены" -ForegroundColor Gray
}

# 2. Проверяем, занят ли порт 8000
Write-Host "`n2️⃣ Проверка порта 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | findstr :8000

if ($port8000) {
    Write-Host "   Порт 8000 занят:" -ForegroundColor Yellow
    Write-Host "   $port8000" -ForegroundColor Gray
    
    # Извлекаем PID из вывода netstat
    $pidMatch = $port8000 | Select-String -Pattern "LISTENING\s+(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    if ($pidMatch) {
        Write-Host "   Найден PID процесса: $pidMatch" -ForegroundColor Yellow
        Write-Host "   Останавливаем процесс..." -ForegroundColor Yellow
        
        try {
            Stop-Process -Id $pidMatch -Force -ErrorAction Stop
            Write-Host "   ✅ Процесс остановлен (PID: $pidMatch)" -ForegroundColor Green
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "   ⚠️ Не удалось остановить процесс: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   Порт 8000 свободен" -ForegroundColor Green
}

# 3. Останавливаем все процессы uvicorn (если есть)
Write-Host "`n3️⃣ Поиск процессов uvicorn..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or 
    $_.ProcessName -like "*uvicorn*"
} -ErrorAction SilentlyContinue

if ($uvicornProcesses) {
    foreach ($proc in $uvicornProcesses) {
        Write-Host "   Останавливаем процесс uvicorn (PID: $($proc.Id))..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "   ✅ Процесс остановлен" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Ошибка: $_" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "   Процессы uvicorn не найдены" -ForegroundColor Gray
}

# 4. Запускаем backend заново
Write-Host "`n4️⃣ Запуск backend сервера..." -ForegroundColor Yellow

$backendDir = Split-Path -Parent $PSScriptRoot
$mainPy = Join-Path $backendDir "main.py"

if (Test-Path $mainPy) {
    Write-Host "   Найден main.py: $mainPy" -ForegroundColor Green
    Write-Host "   Запускаем: uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
    
    # Переходим в директорию backend
    Push-Location $backendDir
    
    # Запускаем uvicorn в фоновом режиме
    Start-Process python -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WindowStyle Hidden
    
    Pop-Location
    
    Write-Host "   ✅ Backend запущен в фоновом режиме" -ForegroundColor Green
    Write-Host "`n💡 Проверьте логи или откройте http://localhost:8000/docs" -ForegroundColor Cyan
} else {
    Write-Host "   ❌ Файл main.py не найден в $backendDir" -ForegroundColor Red
}

Write-Host "`n✅ Готово!" -ForegroundColor Green

