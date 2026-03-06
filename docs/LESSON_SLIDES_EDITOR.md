# Редактор слайдов урока и видео по слайду

## Обзор

Редактор контента курса позволяет просматривать и редактировать детальный контент уроков (лекция, цели, слайды) и генерировать видео через HeyGen **для каждого слайда** отдельно.

## Маршрут и навигация

- **URL:** `/courses/:id/content` (например `/courses/24/content`)
- **Переход:** со страницы курса (`/courses/:id`) по кнопке **«Редактор слайдов»**

## Frontend

### Страница `CourseContentEditorPage.jsx`

- **Левая панель:** иерархическое дерево — курс → модули → уроки. Выбор урока загружает его контент справа.
- **Правая панель:**
  - Если контент не сгенерирован — кнопка «Сгенерировать контент» (POST generate).
  - Иначе — форма: название лекции, длительность, цели обучения, ключевые выводы, список слайдов.
- **Слайд:** заголовок, текст, тип (титульный/контент/код/диаграмма и т.д.), пример кода, заметки; кнопки «Видео» и «Удалить». Добавление слайда — «Добавить слайд».
- **Сохранение:** кнопка «Сохранить контент» отправляет `PUT .../lessons/{idx}/content` с телом в формате `LessonContentUpdate` (слайды с сохранением полей `video_id`, `video_status`, `video_download_url`).
- **Видео по слайду:** кнопка «Видео» открывает модальное окно с текстом для озвучки (заголовок + контент слайда), выбором аватара и голоса; генерация через `POST /api/video/generate-slide-cached`; опрос статуса по `GET /api/video/status/{video_id}`; после завершения отображаются ссылки «Открыть видео» и «Скачать».
- Загрузка аватаров/голосов — через `getVideoApiUrl('AVATARS')` и `getVideoApiUrl('VOICES')` (как на странице курса), с запасными значениями по умолчанию.
- В полях текста слайда литеральные `\n` отображаются как переносы строк (функция `displayMultiline`).

### API клиент (`coursesApi.js`)

- `getLessonContent(courseId, moduleNumber, lessonIndex)` — GET контента
- `updateLessonContent(courseId, moduleNumber, lessonIndex, lessonContent)` — PUT контента
- `generateSlideVideo(courseId, moduleNumber, lessonIndex, slideIndex, payload)` — POST генерации видео слайда
- `getVideoStatus(videoId)` — GET статуса видео

## Backend

### Уроки

- **PUT** ` /api/courses/{course_id}/modules/{module_number}/lessons/{lesson_index}/content`  
  Тело: `LessonContentUpdate` (Pydantic) — `lecture_title`, `duration_minutes`, `learning_objectives`, `key_takeaways`, `slides[]`.  
  При сохранении сохраняются поля видео в слайдах из существующего контента (мерж по индексу слайда).

### Видео по слайду

- **POST** `/api/video/generate-slide-cached?course_id=&module_number=&lesson_index=&slide_index=`  
  Тело: `VideoGenerationRequest` (title, content, avatar_id, voice_id, language, quality, regenerate).  
  Логика аналогична `generate-lesson-cached`: кэш по ключу с `slide_index`, вызов HeyGen, запись в БД через `update_lesson_slide_video_info`.

### База данных

- В `lesson_contents.content_data` хранится JSON с полем `slides` — массив слайдов. У каждого элемента могут быть поля `video_id`, `video_status`, `video_download_url`.
- Метод `update_lesson_slide_video_info(course_id, module_number, lesson_index, slide_index, video_id, video_status, video_download_url)` обновляет эти поля в `content_data.slides[slide_index]` и сохраняет запись (есть в `db.py` и `db_postgres.py`).

### Кэш видео

- Ключ кэша: `course_id_module_number_lesson_index` или с суффиксом `_slide_index` для видео слайда.
- При опросе статуса (`GET /api/video/status/{video_id}`) по ключу из 4 частей вызывается `update_lesson_slide_video_info` и в контент урока записывается готовый `video_download_url`.

## Модели

- **LessonContentUpdate** (`backend/models/domain.py`): запрос на обновление контента урока (лекция + слайды в формате `Slide`).
- **Slide**: slide_number, title, content, slide_type, code_example, notes; при сохранении в слайдах могут дополнительно храниться video_id, video_status, video_download_url.

## См. также

- [ARCHITECTURE_NEW.md](./ARCHITECTURE_NEW.md) — общая архитектура и API
- [HEYGEN_INTEGRATION.md](./HEYGEN_INTEGRATION.md) — интеграция HeyGen
- [LESSON_VIDEO_INTEGRATION.md](./LESSON_VIDEO_INTEGRATION.md) — интеграция видео на странице курса
