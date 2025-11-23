# Как проверить, что возвращает API /api/courses/{id}

## Способ 1: Через скрипт (рекомендуется)

```bash
# Для локального API
python backend/tools/check_course_api_response.py 12

# Для Render API
python backend/tools/check_course_api_response.py 12 --url https://course-builder-api.onrender.com
```

Скрипт покажет:
- ✅ Есть ли `content_outline` в каждом уроке
- 📋 Структуру данных урока
- 💾 Сохранит полный ответ в JSON файл

## Способ 2: Через браузер (DevTools)

1. Откройте страницу курса: `https://course-builder-frontend.onrender.com/courses/12`
2. Откройте DevTools (F12)
3. Перейдите на вкладку **Network** (Сеть)
4. Обновите страницу (F5)
5. Найдите запрос к `/api/courses/12`
6. Кликните на него
7. Перейдите на вкладку **Response** (Ответ)
8. Найдите в JSON структуре: `course.modules[].lessons[].content_outline`

## Способ 3: Через консоль браузера

1. Откройте страницу курса
2. Откройте консоль (F12 → Console)
3. Выполните:

```javascript
// Получить курс через API
fetch('https://course-builder-api.onrender.com/api/courses/12')
  .then(r => r.json())
  .then(data => {
    const course = data.course || data;
    console.log('Курс:', course.course_title);
    
    course.modules.forEach((module, mIdx) => {
      console.log(`\nМодуль ${module.module_number}: ${module.module_title}`);
      module.lessons.forEach((lesson, lIdx) => {
        console.log(`  Урок ${lIdx + 1}: ${lesson.lesson_title}`);
        console.log(`    content_outline:`, lesson.content_outline);
        console.log(`    Есть content_outline:`, !!lesson.content_outline);
        console.log(`    Тип:`, Array.isArray(lesson.content_outline) ? 'массив' : typeof lesson.content_outline);
      });
    });
  });
```

## Способ 4: Через curl (командная строка)

```bash
# Windows PowerShell
curl.exe https://course-builder-api.onrender.com/api/courses/12 | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Linux/Mac
curl https://course-builder-api.onrender.com/api/courses/12 | jq '.course.modules[].lessons[] | {title: .lesson_title, outline: .content_outline}'
```

## Способ 5: Через Postman или Insomnia

1. Создайте GET запрос
2. URL: `https://course-builder-api.onrender.com/api/courses/12`
3. Отправьте запрос
4. Проверьте ответ JSON

## Что проверить:

✅ **content_outline должен быть:**
- Массивом строк: `["пункт 1", "пункт 2", ...]`
- Или строкой с переносами: `"пункт 1\nпункт 2"`

❌ **content_outline НЕ должен быть:**
- `null`
- `undefined`
- Пустым массивом `[]`
- Пустой строкой `""`

## Результат проверки для курса 12:

✅ Все уроки имеют `content_outline` в виде массива строк
✅ Данные корректно возвращаются из API

Проблема, скорее всего, в том, как данные передаются в компонент `LessonVideoGenerator` на фронтенде.

