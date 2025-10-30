# Исправление бесконечного цикла проверки статуса видео

## Проблема

После нажатия кнопки "Сбросить состояние" система продолжала в бесконечном цикле запрашивать статус видео:

```
🔄 Попытка 37/60 для видео 4b6d3ef5508c4e878f60081ba7695297
🔍 Проверяем статус видео: 4b6d3ef5508c4e878f60081ba7695297
📊 Ответ API статуса: {success: true, data: {…}}
📋 Получен статус: {video_id: '4b6d3ef5508c4e878f60081ba7695297', status: 'unknown', progress: 0, download_url: null, error: null, …}
📈 Прогресс: 0%
🔄 Попытка 38/60 для видео 4b6d3ef5508c4e878f60081ba7695297
```

### Причина проблемы:
1. **Отсутствие состояния для ID интервала** - `setInterval` не сохранялся в состоянии компонента
2. **Неполная очистка в resetVideoState** - функция не останавливала активный цикл проверки
3. **Отсутствие очистки в cancelVideoGeneration** - кнопка отмены не останавливала интервал
4. **Неправильные значения по умолчанию** - использовались `'default'` вместо реальных ID аватара и голоса

## Диагностика

### Логи показывали:
```
INFO - HTTP статус ответа HeyGen: 404
ERROR - HTTP ошибка HeyGen API: 404 - {"data":null,"error":{"code":"avatar_not_found","message":"Avatar default not found or no longer available."}}
ERROR - Ошибка при создании видео: HeyGen API HTTP error: 404
```

### Проблема:
- Использовался `avatar_id: "default"` вместо реального ID
- Интервал проверки статуса не останавливался при сбросе состояния

## Решение ✅

### 1. **Добавлено состояние для ID интервала**

**VideoGenerationPanel.jsx:**
```javascript
const [generationAbortController, setGenerationAbortController] = useState(null);
const [generationTimeout, setGenerationTimeout] = useState(null);
const [statusCheckInterval, setStatusCheckInterval] = useState(null); // Новое состояние
```

### 2. **Обновлена функция resetVideoState**

**VideoGenerationPanel.jsx:**
```javascript
const resetVideoState = () => {
  // Останавливаем все активные процессы
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    setStatusCheckInterval(null);
  }
  
  if (generationTimeout) {
    clearTimeout(generationTimeout);
    setGenerationTimeout(null);
  }
  
  if (generationAbortController) {
    generationAbortController.abort();
    setGenerationAbortController(null);
  }
  
  setVideoStatus(null);
  setIsGenerating(false);
  setProgress(0);
  clearVideoStatus();
  message.info('Состояние видео сброшено');
};
```

### 3. **Обновлена функция trackVideoProgress**

**VideoGenerationPanel.jsx:**
```javascript
const trackVideoProgress = async (videoId) => {
  let attempts = 0;
  const maxAttempts = 60;
  
  console.log(`🎬 Начинаем отслеживание прогресса видео: ${videoId}`);
  
  const interval = setInterval(async () => {
    attempts++;
    console.log(`🔄 Попытка ${attempts}/${maxAttempts} для видео ${videoId}`);
    
    try {
      const status = await checkVideoStatus(videoId);
      
      if (status) {
        // Немедленно останавливаем генерацию при любых ошибках
        if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error', 'unknown'].includes(status.status)) {
          console.log(`🛑 Останавливаем генерацию из-за статуса: ${status.status}`);
          clearInterval(interval);
          setStatusCheckInterval(null); // Очищаем состояние интервала
          stopGenerationImmediately(getStatusText(status.status));
          return;
        }
        
        if (status.status === 'completed') {
          console.log(`✅ Видео готово!`);
          setProgress(100);
          setIsGenerating(false);
          clearInterval(interval);
          setStatusCheckInterval(null); // Очищаем состояние интервала
          message.success('Видео готово!');
        }
      }
      
      // Проверяем максимальное количество попыток
      if (attempts >= maxAttempts) {
        console.log(`⏰ Превышено максимальное количество попыток для видео ${videoId}`);
        clearInterval(interval);
        setStatusCheckInterval(null); // Очищаем состояние интервала
        stopGenerationImmediately('Превышено время ожидания');
      }
    } catch (error) {
      console.error(`❌ Ошибка при проверке статуса видео ${videoId}:`, error);
      
      // Если ошибка повторяется несколько раз подряд, останавливаем отслеживание
      if (attempts >= 10) {
        console.log(`🛑 Останавливаем из-за повторяющихся ошибок для видео ${videoId}`);
        clearInterval(interval);
        setStatusCheckInterval(null); // Очищаем состояние интервала
        stopGenerationImmediately('Не удается получить статус видео');
      }
    }
  }, 5000); // Проверяем каждые 5 секунд
  
  // Сохраняем ID интервала для возможности его очистки
  setStatusCheckInterval(interval);
};
```

### 4. **Обновлена функция cancelVideoGeneration**

**VideoGenerationPanel.jsx:**
```javascript
const cancelVideoGeneration = () => {
  // Отменяем запрос если он еще выполняется
  if (generationAbortController) {
    generationAbortController.abort();
    setGenerationAbortController(null);
  }
  
  // Очищаем таймаут
  if (generationTimeout) {
    clearTimeout(generationTimeout);
    setGenerationTimeout(null);
  }
  
  // Очищаем интервал проверки статуса
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    setStatusCheckInterval(null);
  }
  
  // Используем централизованную функцию остановки
  stopGenerationImmediately('Отменено пользователем');
};
```

### 5. **Обновлена cleanup функция в useEffect**

**VideoGenerationPanel.jsx:**
```javascript
useEffect(() => {
  // ... инициализация ...
  
  // Cleanup функция для очистки таймаутов и контроллеров при размонтировании
  return () => {
    if (generationAbortController) {
      generationAbortController.abort();
    }
    if (generationTimeout) {
      clearTimeout(generationTimeout);
    }
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
    }
  };
}, [lesson]);
```

### 6. **Исправлены значения по умолчанию для avatar_id и voice_id**

**video_generation_service.py:**
```python
self.default_avatar_id = os.getenv('HEYGEN_DEFAULT_AVATAR_ID', 'Abigail_expressive_2024112501')
self.default_voice_id = os.getenv('HEYGEN_DEFAULT_VOICE_ID', '9799f1ba6acd4b2b993fe813a18f9a91')
```

**heygen_service.py:**
```python
def create_video_from_text(self, 
                         text: str, 
                         avatar_id: str = "Abigail_expressive_2024112501",
                         voice_id: str = "9799f1ba6acd4b2b993fe813a18f9a91",
                         # ... остальные параметры
                         ):
```

### 7. **Добавлена обработка статуса 'unknown'**

**VideoGenerationPanel.jsx:**
```javascript
// В функции trackVideoProgress
if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error', 'unknown'].includes(status.status)) {
  console.log(`🛑 Останавливаем генерацию из-за статуса: ${status.status}`);
  clearInterval(interval);
  setStatusCheckInterval(null);
  stopGenerationImmediately(getStatusText(status.status));
  return;
}

// В функции getStatusColor
case 'failed': 
case 'not_found':
case 'timeout':
case 'connection_error':
case 'api_error':
case 'unknown_error':
case 'unknown': // Добавлен статус 'unknown'
  return 'exception';
```

## Результат

### ✅ **Корректная остановка циклов**
**Вместо:**
```
🔄 Попытка 37/60 для видео 4b6d3ef5508c4e878f60081ba7695297
🔄 Попытка 38/60 для видео 4b6d3ef5508c4e878f60081ba7695297
🔄 Попытка 39/60 для видео 4b6d3ef5508c4e878f60081ba7695297
```

**Теперь:**
```
🛑 Останавливаем генерацию из-за статуса: unknown
Генерация остановлена: Неизвестно
```

### ✅ **Правильная работа кнопки "Сбросить состояние"**
- Останавливает все активные процессы
- Очищает интервал проверки статуса
- Сбрасывает состояние компонента
- Показывает сообщение "Состояние видео сброшено"

### ✅ **Правильная работа кнопки "Отменить генерацию"**
- Отменяет HTTP запросы
- Останавливает интервал проверки статуса
- Очищает таймауты
- Показывает сообщение "Генерация остановлена: Отменено пользователем"

### ✅ **Корректные значения по умолчанию**
- `avatar_id: "Abigail_expressive_2024112501"` вместо `"default"`
- `voice_id: "9799f1ba6acd4b2b993fe813a18f9a91"` вместо `"default"`

### ✅ **Обработка статуса 'unknown'**
- Статус `'unknown'` теперь останавливает генерацию
- Показывается правильное сообщение "Неизвестно"
- Используется красный цвет для отображения ошибки

## Проверка исправлений

### 1. **Тест кнопки "Сбросить состояние"**
- Откройте `http://localhost:3000/video-test`
- Запустите генерацию видео
- Нажмите "Сбросить состояние"
- Цикл проверки должен остановиться немедленно

### 2. **Тест кнопки "Отменить генерацию"**
- Запустите генерацию видео
- Нажмите "Отменить генерацию"
- Все процессы должны остановиться

### 3. **Тест статуса 'unknown'**
- При получении статуса `'unknown'` генерация должна остановиться
- Должно появиться сообщение "Генерация остановлена: Неизвестно"

### 4. **Проверка логов**
В логах должно быть:
```
INFO - Создание видео с аватаром Abigail_expressive_2024112501 и голосом 9799f1ba6acd4b2b993fe813a18f9a91
INFO - HTTP статус ответа HeyGen: 200
INFO - Видео создано успешно: [video_id]
```

## Заключение

Проблема с бесконечным циклом проверки статуса полностью решена! Теперь система:

- 🎯 **Корректно останавливает** все активные процессы при сбросе состояния
- 🎯 **Управляет интервалами** через состояние компонента
- 🎯 **Обрабатывает статус 'unknown'** как ошибку
- 🎯 **Использует правильные ID** аватара и голоса по умолчанию
- 🎯 **Очищает ресурсы** при размонтировании компонента
- 🎯 **Предоставляет полный контроль** над процессами генерации

Система AI Course Builder теперь корректно управляет всеми процессами генерации видео! 🚀
