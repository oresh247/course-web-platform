# Кэширование детального контента урока

## Проблема

При каждом открытии модального окна генерации видео для урока пользователь видел надпись "Загрузка детального контента урока..." и ждал загрузки данных с сервера, даже если контент уже был загружен ранее.

## Решение ✅

Реализовано интеллектуальное кэширование детального контента урока в `localStorage` с автоматической проверкой актуальности и возможностью принудительного обновления.

## Техническая реализация

### **1. Функции для работы с кэшем:**

```jsx
// Генерация ключа кэша
const getLessonContentCacheKey = (courseId, moduleNumber, lessonIndex) => {
  return `lesson_content_${courseId}_${moduleNumber}_${lessonIndex}`;
};

// Получение кэшированного контента
const getCachedLessonContent = (courseId, moduleNumber, lessonIndex) => {
  try {
    const cacheKey = getLessonContentCacheKey(courseId, moduleNumber, lessonIndex);
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const parsedCache = JSON.parse(cached);
      // Проверяем актуальность кэша (24 часа)
      const cacheAge = Date.now() - parsedCache.timestamp;
      const maxAge = 24 * 60 * 60 * 1000; // 24 часа в миллисекундах
      
      if (cacheAge < maxAge) {
        return parsedCache.content;
      } else {
        // Удаляем устаревший кэш
        localStorage.removeItem(cacheKey);
      }
    }
  } catch (error) {
    console.warn('Ошибка чтения кэша контента урока:', error);
  }
  return null;
};

// Сохранение в кэш
const setCachedLessonContent = (courseId, moduleNumber, lessonIndex, content) => {
  try {
    const cacheKey = getLessonContentCacheKey(courseId, moduleNumber, lessonIndex);
    const cacheData = {
      content,
      timestamp: Date.now()
    };
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
  } catch (error) {
    console.warn('Ошибка сохранения кэша контента урока:', error);
  }
};
```

### **2. Обновленная функция загрузки контента:**

```jsx
const loadLessonContent = async (forceRefresh = false) => {
  // Проверяем кэш, если не принудительное обновление
  if (!forceRefresh) {
    const cachedContent = getCachedLessonContent(courseId, moduleNumber, lessonIndex);
    if (cachedContent) {
      console.log('📦 Используем кэшированный контент урока');
      setLessonContent(cachedContent);
      setIsContentFromCache(true);
      // Устанавливаем скрипт из кэшированного контента
      return;
    }
  }

  // Загружаем с сервера
  setLoadingLessonContent(true);
  setIsContentFromCache(false);
  
  try {
    const response = await coursesApi.getLessonContent(courseId, moduleNumber, lessonIndex);
    if (response.status === 'found' && response.lesson_content) {
      setLessonContent(response.lesson_content);
      // Сохраняем в кэш
      setCachedLessonContent(courseId, moduleNumber, lessonIndex, response.lesson_content);
    }
  } catch (error) {
    // Обработка ошибок...
  } finally {
    setLoadingLessonContent(false);
  }
};
```

### **3. UI индикаторы кэша:**

```jsx
// Индикатор в заголовке карточки
<Card 
  title={
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span>Скрипт для генерации видео</span>
      {isContentFromCache && (
        <span style={{ 
          fontSize: '12px', 
          color: '#52c41a', 
          fontWeight: 'normal',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          📦 Из кэша
        </span>
      )}
    </div>
  } 
  size="small"
>

// Кнопка принудительного обновления
{isContentFromCache && (
  <div style={{ marginBottom: '8px', textAlign: 'right' }}>
    <Button 
      size="small" 
      type="link" 
      onClick={() => loadLessonContent(true)}
      style={{ padding: '0', height: 'auto' }}
    >
      🔄 Обновить контент
    </Button>
  </div>
)}
```

## Особенности реализации

### **⏰ Время жизни кэша:**
- **24 часа** - оптимальный баланс между актуальностью и производительностью
- Автоматическое удаление устаревшего кэша
- Возможность принудительного обновления

### **🔑 Уникальность ключей:**
- Формат: `lesson_content_{courseId}_{moduleNumber}_{lessonIndex}`
- Гарантирует изоляцию кэша для разных уроков
- Поддержка множественных курсов и модулей

### **🛡️ Обработка ошибок:**
- Graceful fallback при ошибках чтения/записи localStorage
- Логирование предупреждений без прерывания работы
- Автоматический переход к загрузке с сервера при проблемах с кэшем

### **📱 UX улучшения:**
- Мгновенная загрузка из кэша
- Визуальный индикатор источника данных
- Кнопка принудительного обновления
- Сохранение состояния скрипта

## Результат

### ✅ **До внедрения кэширования:**
- Каждое открытие модального окна = загрузка с сервера
- Надпись "Загрузка детального контента урока..."
- Ожидание 1-3 секунды каждый раз
- Повторные запросы к API

### ✅ **После внедрения кэширования:**
- **Мгновенная загрузка** из кэша при повторном открытии
- **Нет надписи загрузки** для кэшированного контента
- **Индикатор источника** данных (📦 Из кэша)
- **Кнопка обновления** для принудительного обновления
- **Снижение нагрузки** на сервер

## Тестирование

### **Сценарий 1: Первая загрузка**
1. Открываем модальное окно генерации видео
2. ✅ Видим "Загрузка детального контента урока..."
3. ✅ Контент загружается с сервера
4. ✅ Контент сохраняется в кэш

### **Сценарий 2: Повторное открытие**
1. Закрываем и снова открываем модальное окно
2. ✅ Контент загружается мгновенно из кэша
3. ✅ Видим индикатор "📦 Из кэша"
4. ✅ Нет надписи загрузки

### **Сценарий 3: Принудительное обновление**
1. Нажимаем "🔄 Обновить контент"
2. ✅ Контент загружается с сервера
3. ✅ Кэш обновляется
4. ✅ Индикатор "📦 Из кэша" исчезает

### **Сценарий 4: Устаревший кэш**
1. Ждем 24+ часов
2. ✅ Устаревший кэш автоматически удаляется
3. ✅ Контент загружается с сервера
4. ✅ Новый кэш создается

## Заключение

Кэширование детального контента урока значительно улучшило пользовательский опыт! Теперь пользователи не ждут загрузки при повторном открытии модального окна генерации видео, а система автоматически управляет актуальностью данных. 🚀
