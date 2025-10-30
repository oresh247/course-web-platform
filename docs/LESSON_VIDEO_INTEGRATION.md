# Интеграция генерации видео в страницу просмотра модуля

## Обзор

Добавлена функциональность генерации видео для каждого урока прямо на странице просмотра модуля. Теперь пользователи могут:

- 🎬 **Генерировать видео** для любого урока одним кликом
- 🎭 **Выбирать аватар и голос** для озвучивания
- 📝 **Просматривать скрипт** перед генерацией
- 📊 **Отслеживать прогресс** генерации в реальном времени
- ▶️ **Просматривать готовое видео** прямо в браузере
- 💾 **Скачивать видео** на локальное устройство

## Компоненты

### 1. **LessonVideoGenerator**

Новый компонент для управления генерацией видео урока.

**Файл:** `frontend/src/components/LessonVideoGenerator.jsx`

**Основные функции:**
- Загрузка списка аватаров и голосов
- Отображение модального окна с настройками
- Генерация видео через HeyGen API
- Отслеживание прогресса генерации
- Управление состоянием видео

**Состояния:**
```javascript
const [isGenerating, setIsGenerating] = useState(false);
const [progress, setProgress] = useState(0);
const [videoStatus, setVideoStatus] = useState(null);
const [isModalVisible, setIsModalVisible] = useState(false);
const [avatars, setAvatars] = useState([]);
const [voices, setVoices] = useState([]);
const [selectedAvatar, setSelectedAvatar] = useState('');
const [selectedVoice, setSelectedVoice] = useState('');
```

### 2. **Обновленный LessonItem**

Интегрирован генератор видео в существующий компонент урока.

**Файл:** `frontend/src/components/LessonItem.jsx`

**Изменения:**
- Добавлен импорт `LessonVideoGenerator`
- Вставлен компонент в список кнопок действий
- Сохранена совместимость с существующим функционалом

## Функциональность

### 🎬 **Иконки генерации видео**

Компонент автоматически отображает соответствующую иконку в зависимости от состояния:

#### **До генерации:**
```jsx
<Button 
  type="primary" 
  size="small" 
  icon={<VideoCameraOutlined />}
  onClick={() => setIsModalVisible(true)}
>
  Генерировать видео
</Button>
```

#### **Во время генерации:**
```jsx
<Button 
  type="primary" 
  size="small" 
  icon={<VideoCameraOutlined />}
  loading={true}
  onClick={() => setIsModalVisible(true)}
>
  Генерация...
</Button>
```

#### **После успешной генерации:**
```jsx
<Space size="small">
  <Button 
    type="primary" 
    size="small" 
    icon={<PlayCircleOutlined />}
    onClick={() => window.open(videoStatus.download_url, '_blank')}
  >
    Смотреть
  </Button>
  <Button 
    size="small" 
    icon={<DownloadOutlined />}
    onClick={downloadVideo}
  >
    Скачать
  </Button>
</Space>
```

#### **При ошибке:**
```jsx
<Button 
  type="primary" 
  size="small" 
  icon={<ReloadOutlined />}
  onClick={() => setIsModalVisible(true)}
>
  Повторить
</Button>
```

### 🎭 **Модальное окно настроек**

При нажатии на иконку генерации открывается модальное окно с:

#### **1. Скрипт для генерации**
```jsx
<Card title="Скрипт для генерации видео" size="small">
  <Paragraph 
    style={{ 
      backgroundColor: '#f5f5f5', 
      padding: '12px', 
      borderRadius: '6px',
      margin: 0,
      color: '#333',
      whiteSpace: 'pre-wrap'
    }}
  >
    {lesson.content || lesson.lesson_content || 'Содержание урока'}
  </Paragraph>
</Card>
```

#### **2. Выбор аватара**
```jsx
<Select
  style={{ width: '100%', marginTop: 8 }}
  placeholder="Выберите аватар"
  value={selectedAvatar}
  onChange={setSelectedAvatar}
  loading={loadingAvatars}
>
  {avatars.map(avatar => (
    <Option key={avatar.avatar_id} value={avatar.avatar_id}>
      {avatar.avatar_name}
    </Option>
  ))}
</Select>
```

#### **3. Выбор голоса**
```jsx
<Select
  style={{ width: '100%', marginTop: 8 }}
  placeholder="Выберите голос"
  value={selectedVoice}
  onChange={setSelectedVoice}
  loading={loadingVoices}
>
  {voices.map(voice => (
    <Option key={voice.voice_id} value={voice.voice_id}>
      {voice.language} - {voice.gender}
    </Option>
  ))}
</Select>
```

### 📊 **Шкала прогресса**

Во время генерации отображается прогресс-бар:

```jsx
{isGenerating && (
  <Card title="Прогресс генерации" size="small">
    <Space direction="vertical" style={{ width: '100%' }}>
      <Progress 
        percent={progress} 
        status={progress === 100 ? 'success' : 'active'}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
      />
      <Text type="secondary">
        {progress === 100 ? 'Видео готово!' : 'Генерируется видео...'}
      </Text>
    </Space>
  </Card>
)}
```

### 🔄 **Управление процессом**

#### **Отслеживание прогресса:**
```javascript
const trackVideoProgress = async (videoId) => {
  let attempts = 0;
  const maxAttempts = 60; // 5 минут
  
  const interval = setInterval(async () => {
    attempts++;
    
    try {
      const status = await checkVideoStatus(videoId);
      
      if (status) {
        setVideoStatus(status);
        
        // Останавливаем при ошибках
        if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error', 'unknown'].includes(status.status)) {
          clearInterval(interval);
          setStatusCheckInterval(null);
          setIsGenerating(false);
          setProgress(0);
          message.error(`Ошибка генерации: ${status.error || 'Неизвестная ошибка'}`);
          return;
        }
        
        if (status.status === 'completed') {
          setProgress(100);
          setIsGenerating(false);
          clearInterval(interval);
          setStatusCheckInterval(null);
          message.success('Видео готово!');
          onVideoGenerated?.(status);
        } else if (status.progress !== undefined) {
          setProgress(status.progress);
        }
      }
      
      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setStatusCheckInterval(null);
        setIsGenerating(false);
        setProgress(0);
        message.error('Превышено время ожидания');
      }
    } catch (error) {
      console.error('Ошибка проверки статуса:', error);
      if (attempts >= 10) {
        clearInterval(interval);
        setStatusCheckInterval(null);
        setIsGenerating(false);
        setProgress(0);
        message.error('Не удается получить статус видео');
      }
    }
  }, 5000);
  
  setStatusCheckInterval(interval);
};
```

#### **Отмена генерации:**
```javascript
const cancelGeneration = () => {
  if (generationAbortController) {
    generationAbortController.abort();
    setGenerationAbortController(null);
  }
  if (generationTimeout) {
    clearTimeout(generationTimeout);
    setGenerationTimeout(null);
  }
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    setStatusCheckInterval(null);
  }
  setIsGenerating(false);
  setProgress(0);
  message.warning('Генерация отменена');
};
```

## Интеграция с API

### **Загрузка аватаров:**
```javascript
const loadAvatars = async () => {
  setLoadingAvatars(true);
  try {
    const response = await fetch(getVideoApiUrl('AVATARS'));
    const data = await response.json();
    
    if (data.success && data.data.avatars) {
      setAvatars(data.data.avatars);
      if (data.data.avatars.length > 0 && !selectedAvatar) {
        setSelectedAvatar(data.data.avatars[0].avatar_id);
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки аватаров:', error);
    message.error('Ошибка загрузки аватаров');
  } finally {
    setLoadingAvatars(false);
  }
};
```

### **Загрузка голосов:**
```javascript
const loadVoices = async () => {
  setLoadingVoices(true);
  try {
    const response = await fetch(getVideoApiUrl('VOICES'));
    const data = await response.json();
    
    if (data.success && data.data.list) {
      setVoices(data.data.list);
      if (data.data.list.length > 0 && !selectedVoice) {
        setSelectedVoice(data.data.list[0].voice_id);
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки голосов:', error);
    message.error('Ошибка загрузки голосов');
  } finally {
    setLoadingVoices(false);
  }
};
```

### **Генерация видео:**
```javascript
const generateVideo = async () => {
  if (!selectedAvatar || !selectedVoice) {
    message.error('Выберите аватар и голос');
    return;
  }

  setIsGenerating(true);
  setProgress(0);
  setVideoStatus(null);

  const abortController = new AbortController();
  setGenerationAbortController(abortController);

  try {
    const response = await fetch(getVideoApiUrl('GENERATE_LESSON'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: lesson.lesson_title,
        content: lesson.content || lesson.lesson_content || 'Содержание урока',
        avatar_id: selectedAvatar,
        voice_id: selectedVoice,
        language: 'ru'
      }),
      signal: abortController.signal
    });

    const data = await response.json();
    
    if (!response.ok) {
      const errorMessage = data.detail || data.message || `HTTP ${response.status}`;
      message.error(errorMessage);
      setIsGenerating(false);
      setProgress(0);
      return;
    }
    
    if (data.success) {
      if (data.data.video && data.data.video.status === 'failed') {
        const errorMsg = data.data.video.error || 'Ошибка генерации видео';
        message.error(`Ошибка генерации: ${errorMsg}`);
        setIsGenerating(false);
        setProgress(0);
      } else {
        message.success('Видео поставлено в очередь генерации');
        setVideoStatus(data.data.video);
        
        if (data.data.video.video_id) {
          trackVideoProgress(data.data.video.video_id);
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      message.warning('Генерация видео отменена');
    } else {
      console.error('Ошибка генерации видео:', error);
      message.error('Ошибка при генерации видео');
      setIsGenerating(false);
      setProgress(0);
    }
  }
};
```

## Использование

### **1. Открытие страницы курса**
- Перейдите на страницу курса: `http://localhost:3000/courses`
- Выберите курс для просмотра
- Откроется страница с модулями и уроками

### **2. Генерация видео урока**
- Найдите урок, для которого хотите сгенерировать видео
- Нажмите на иконку 🎬 "Генерировать видео"
- Откроется модальное окно с настройками

### **3. Настройка генерации**
- **Просмотрите скрипт** - содержимое урока, которое будет озвучено
- **Выберите аватар** - персонаж для видео
- **Выберите голос** - голос для озвучивания
- Нажмите "Генерировать видео"

### **4. Отслеживание прогресса**
- Во время генерации отображается прогресс-бар
- Можно отменить генерацию кнопкой "Отменить"
- При ошибке появится сообщение с описанием проблемы

### **5. Просмотр и скачивание**
- После завершения генерации появится кнопка "Смотреть"
- Нажмите для открытия видео в новой вкладке
- Используйте кнопку "Скачать" для сохранения на устройство

## Обработка ошибок

### **Типы ошибок:**
- `failed` - Ошибка генерации на стороне HeyGen
- `not_found` - Видео не найдено
- `timeout` - Превышено время ожидания
- `connection_error` - Ошибка подключения к API
- `api_error` - Ошибка API
- `unknown_error` - Неизвестная ошибка
- `unknown` - Неопределенный статус

### **Действия при ошибках:**
- Автоматическая остановка генерации
- Отображение сообщения об ошибке
- Возможность повторить генерацию
- Сохранение состояния для диагностики

## Совместимость

### **С существующим функционалом:**
- ✅ Сохранена совместимость с генерацией слайдов
- ✅ Работает с экспортом контента
- ✅ Интегрируется с редактированием уроков
- ✅ Поддерживает все существующие функции

### **С HeyGen API:**
- ✅ Использует существующие endpoints
- ✅ Поддерживает все типы аватаров и голосов
- ✅ Обрабатывает все статусы генерации
- ✅ Совместимо с лимитами API

## Заключение

Интеграция генерации видео в страницу просмотра модуля значительно улучшает пользовательский опыт:

- 🎯 **Удобный доступ** - генерация видео прямо из списка уроков
- 🎯 **Полный контроль** - выбор аватара, голоса и просмотр скрипта
- 🎯 **Визуальная обратная связь** - прогресс-бар и статусы
- 🎯 **Быстрый доступ** - просмотр и скачивание готового видео
- 🎯 **Надежность** - обработка ошибок и возможность повтора

Система AI Course Builder теперь предоставляет полноценную функциональность генерации видео для каждого урока! 🚀
