# Исправление проблем с отображением скрипта видео и предупреждениями message

## Проблемы

### 1. Скрипт видео белым шрифтом на белом фоне
Скрипт видео отображался невидимым из-за неправильных стилей в темной теме:
- `backgroundColor: '#f5f5f5'` (светло-серый фон)
- Белый текст на светлом фоне = невидимость

### 2. Неправильный контент в скрипте видео
В скрипт генерации видео передавался сгенерированный контент вместо оригинального:
- Использовался `lesson_content.get('content', '')` (фиктивные данные)
- Вместо `lesson_data.get('content', '')` (оригинальный контент)

### 3. Предупреждения о статических функциях message
Во всех компонентах использовался статический `message` API вместо хука `useApp`:
```
Warning: [antd: message] Static function can not consume context like dynamic theme. 
Please use 'App' component instead.
```

## Решение ✅

### 1. Исправлены стили скрипта видео

**VideoGenerationPanel.jsx:**
```javascript
<Card 
  size="small" 
  style={{ 
    backgroundColor: '#1a1a1a',        // Темный фон карточки
    border: '1px solid #2a2a2a'      // Темная граница
  }}
>
  <Text 
    style={{ 
      fontFamily: 'monospace', 
      fontSize: '12px',
      color: '#ffffff',               // Белый текст
      backgroundColor: '#0a0a0a',     // Темный фон текста
      padding: '8px',
      borderRadius: '4px',
      display: 'block',
      whiteSpace: 'pre-wrap',         // Сохраняем переносы строк
      wordBreak: 'break-word'         // Перенос длинных слов
    }}
  >
    {videoStatus.script}
  </Text>
</Card>
```

### 2. Исправлен контент для генерации видео

**video_generation_service.py:**
```python
def _prepare_video_config(self, lesson_data: Dict[str, Any], lesson_content: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'title': lesson_content.get('title', 'Урок'),
        'content': lesson_data.get('content', ''),  # ✅ Используем оригинальный контент
        'introduction': lesson_content.get('introduction', ''),
        'conclusion': lesson_content.get('conclusion', ''),
        'avatar_id': lesson_data.get('avatar_id', self.default_avatar_id),
        'voice_id': lesson_data.get('voice_id', self.default_voice_id),
        'language': lesson_data.get('language', 'ru'),
        'background_id': lesson_data.get('background_id')
    }
```

### 3. Исправлены предупреждения message API

**Обновлены все компоненты:**

**VideoTestPage.jsx:**
```javascript
import { App } from 'antd'

function VideoTestPage() {
  const { message } = App.useApp();  // ✅ Используем хук
  // ...
}
```

**CoursesListPage.jsx:**
```javascript
import { App } from 'antd'

function CoursesListPage() {
  const { message } = App.useApp();  // ✅ Используем хук
  // ...
}
```

**CourseViewPage.jsx:**
```javascript
import { App } from 'antd'

function CourseViewPage() {
  const { message } = App.useApp();  // ✅ Используем хук
  // ...
}
```

**CreateCoursePage.jsx:**
```javascript
import { App } from 'antd'

function CreateCoursePage() {
  const { message } = App.useApp();  // ✅ Используем хук
  // ...
}
```

## Результат

### Отображение скрипта:
- ✅ **Видимый текст** - белый текст на темном фоне
- ✅ **Правильный контент** - передается оригинальное содержание урока
- ✅ **Читаемость** - моноширинный шрифт, правильные отступы
- ✅ **Форматирование** - сохранены переносы строк и структура

### Консоль браузера:
- ✅ **Нет предупреждений** о статических функциях message
- ✅ **Правильная работа** с динамической темой
- ✅ **Чистые логи** без лишних предупреждений

### Функциональность:
- ✅ **Корректная генерация видео** - используется правильный контент
- ✅ **Уведомления работают** - message API функционирует правильно
- ✅ **Темная тема** - все элементы соответствуют дизайну

## Проверка

1. **Откройте** `http://localhost:3000/video-test`
2. **Сгенерируйте видео** - нажмите "Создать видео"
3. **Проверьте скрипт** - должен быть видимый текст с правильным содержанием
4. **Проверьте консоль** - не должно быть предупреждений о message

## Пример правильного скрипта

Теперь в скрипт видео будет передаваться только содержание урока:
```
Добро пожаловать в мир Python!

Python - это мощный и простой язык программирования.

В этом уроке мы изучим основы синтаксиса Python.

Мы также рассмотрим переменные и типы данных.

В конце урока вы сможете написать свою первую программу.
```

## Заключение

Все проблемы успешно исправлены! Система теперь:
- 🎯 **Корректно отображает скрипт** видео с правильными стилями
- 🎯 **Передает правильный контент** для генерации видео
- 🎯 **Не показывает предупреждения** в консоли браузера
- 🎯 **Полностью совместима** с темной темой Ant Design
