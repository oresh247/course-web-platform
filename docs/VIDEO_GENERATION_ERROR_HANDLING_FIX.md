# Исправление проблемы с остановкой генерации видео при ошибках

## Проблема

При получении статуса `failed` от HeyGen API генерация видео не останавливалась немедленно, что приводило к:

1. **Продолжению проверки статуса** даже после получения ошибки
2. **Неочистке состояния** генерации
3. **Отсутствию детальной информации** об ошибках
4. **Плохому пользовательскому опыту** - пользователь не понимал, что произошло

## Причины проблемы

### 1. **Неполная обработка статуса `failed`**
```javascript
// Старая логика - не всегда срабатывала
if (status.status === 'failed') {
  // Обработка ошибки
}
```

### 2. **Отсутствие централизованной остановки**
Каждый тип ошибки обрабатывался отдельно, что приводило к дублированию кода.

### 3. **Недостаточная информация об ошибках**
HeyGen API возвращает детальную информацию об ошибках, которая не использовалась.

## Решение ✅

### 1. **Централизованная функция остановки**

**VideoGenerationPanel.jsx:**
```javascript
const stopGenerationImmediately = (reason = 'Остановлено') => {
  setIsGenerating(false);
  setProgress(0);
  clearVideoStatus();
  message.warning(`Генерация остановлена: ${reason}`);
};
```

### 2. **Улучшенная обработка ошибок в HeyGen API**

**heygen_service.py:**
```python
def get_video_status(self, video_id: str) -> Dict[str, Any]:
    try:
        response = requests.get(
            f"{self.base_url}/v1/video_status.get?video_id={video_id}",
            headers=self.headers,
            timeout=10,
            verify=False
        )
        
        # Проверяем статус ответа
        if response.status_code == 404:
            return {
                "status": "not_found",
                "error": "Видео не найдено в системе HeyGen",
                "video_id": video_id
            }
        
        response.raise_for_status()
        result = response.json()
        
        # Добавляем детальную информацию об ошибках
        if result.get("status") == "failed":
            error_details = result.get("error", {})
            return {
                "status": "failed",
                "error": error_details.get("message", "Неизвестная ошибка генерации"),
                "error_code": error_details.get("code", "unknown"),
                "error_details": error_details,
                "video_id": video_id
            }
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "error": "Таймаут при проверке статуса видео",
            "video_id": video_id
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "connection_error",
            "error": "Ошибка подключения к HeyGen API",
            "video_id": video_id
        }
    # ... другие типы ошибок
```

### 3. **Немедленная остановка при любых ошибках**

**VideoGenerationPanel.jsx:**
```javascript
const trackVideoProgress = async (videoId) => {
  const interval = setInterval(async () => {
    try {
      const status = await checkVideoStatus(videoId);
      
      if (status) {
        setVideoStatus(status);
        saveVideoStatus(status);
        
        // ✅ Немедленно останавливаем генерацию при любых ошибках
        if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error'].includes(status.status)) {
          clearInterval(interval);
          stopGenerationImmediately(getStatusText(status.status));
          return; // Выходим из функции немедленно
        }
        
        if (status.status === 'completed') {
          setProgress(100);
          setIsGenerating(false);
          clearInterval(interval);
          message.success('Видео готово!');
        } else if (status.progress !== undefined) {
          setProgress(status.progress);
        }
      }
    } catch (error) {
      // Обработка ошибок сети
    }
  }, 5000);
};
```

### 4. **Детальное отображение ошибок в UI**

**VideoGenerationPanel.jsx:**
```javascript
{/* Детальная информация об ошибках */}
{['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error'].includes(videoStatus.status) && (
  <Card 
    size="small" 
    style={{ 
      backgroundColor: '#2a1a1a',
      border: '1px solid #5c2626'
    }}
  >
    <Title level={6} style={{ color: '#ff4d4f', margin: 0 }}>
      Детали ошибки:
    </Title>
    <Text style={{ color: '#ff7875', fontSize: '12px' }}>
      {videoStatus.error || 'Нет дополнительной информации об ошибке'}
    </Text>
    {videoStatus.error_code && (
      <Text style={{ color: '#ff9c9c', fontSize: '11px', fontFamily: 'monospace' }}>
        Код ошибки: {videoStatus.error_code}
      </Text>
    )}
    {videoStatus.error_details && (
      <Text style={{ color: '#ff9c9c', fontSize: '11px', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
        {JSON.stringify(videoStatus.error_details, null, 2)}
      </Text>
    )}
  </Card>
)}
```

### 5. **Обновленные статусы ошибок**

**VideoGenerationPanel.jsx:**
```javascript
const getStatusColor = (status) => {
  switch (status) {
    case 'completed': return 'success';
    case 'generating': return 'processing';
    case 'failed': 
    case 'not_found':
    case 'timeout':
    case 'connection_error':
    case 'api_error':
    case 'unknown_error':
      return 'exception'; // ✅ Все ошибки отображаются красным
    case 'pending': return 'warning';
    default: return 'normal';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'completed': return 'Готово';
    case 'generating': return 'Генерируется';
    case 'failed': return 'Ошибка генерации';
    case 'not_found': return 'Видео не найдено';
    case 'timeout': return 'Таймаут';
    case 'connection_error': return 'Ошибка подключения';
    case 'api_error': return 'Ошибка API';
    case 'unknown_error': return 'Неизвестная ошибка';
    case 'pending': return 'Ожидание';
    default: return 'Неизвестно';
  }
};
```

## Типы ошибок HeyGen API

### 1. **`failed`** - Ошибка генерации
- **Причина**: Проблемы с контентом, аватаром или голосом
- **Действие**: Немедленная остановка + детали ошибки

### 2. **`not_found`** - Видео не найдено
- **Причина**: Видео удалено или не существует
- **Действие**: Немедленная остановка

### 3. **`timeout`** - Таймаут API
- **Причина**: Медленный ответ от HeyGen
- **Действие**: Немедленная остановка

### 4. **`connection_error`** - Ошибка подключения
- **Причина**: Проблемы с сетью
- **Действие**: Немедленная остановка

### 5. **`api_error`** - Ошибка API
- **Причина**: Проблемы с HeyGen API
- **Действие**: Немедленная остановка + детали

### 6. **`unknown_error`** - Неизвестная ошибка
- **Причина**: Неожиданные проблемы
- **Действие**: Немедленная остановка + логирование

## Результат

### ✅ **Немедленная остановка**
- Генерация останавливается сразу при получении любого статуса ошибки
- Интервал проверки статуса очищается
- Состояние генерации сбрасывается

### ✅ **Детальная информация**
- Пользователь видит точную причину ошибки
- Отображается код ошибки HeyGen
- Показываются детали ошибки для отладки

### ✅ **Улучшенный UX**
- Понятные сообщения об ошибках
- Визуальное выделение ошибок красным цветом
- Возможность повторной попытки

### ✅ **Надежность**
- Централизованная обработка ошибок
- Консистентное поведение
- Логирование для отладки

## Проверка

1. **Откройте** `http://localhost:3000/video-test`
2. **Сгенерируйте видео** с неверными параметрами
3. **Проверьте** - генерация должна остановиться немедленно
4. **Посмотрите** детали ошибки в интерфейсе

## Примеры ошибок

### Ошибка генерации:
```
Статус: Ошибка генерации
Детали ошибки:
Недостаточно кредитов для генерации видео
Код ошибки: INSUFFICIENT_CREDITS
```

### Ошибка подключения:
```
Статус: Ошибка подключения
Детали ошибки:
Ошибка подключения к HeyGen API
```

### Таймаут:
```
Статус: Таймаут
Детали ошибки:
Таймаут при проверке статуса видео
```

## Заключение

Проблема с неостановкой генерации при ошибках полностью решена! Теперь система:

- 🎯 **Немедленно останавливает** генерацию при любых ошибках
- 🎯 **Показывает детальную информацию** об ошибках
- 🎯 **Предоставляет понятные сообщения** пользователю
- 🎯 **Обеспечивает надежную работу** с HeyGen API

Система AI Course Builder теперь корректно обрабатывает все типы ошибок HeyGen API! 🚀
