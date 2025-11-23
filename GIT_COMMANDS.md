# Команды для загрузки изменений в GitHub

## Базовые команды Git

### 1. Проверка статуса
```bash
git status
```

### 2. Добавление изменений
```bash
# Добавить все изменения
git add .

# Или добавить конкретные файлы
git add backend/requirements.txt
git add frontend/src/components/LessonTestGenerator.jsx
```

### 3. Коммит изменений
```bash
git commit -m "Описание изменений"
```

### 4. Загрузка в GitHub
```bash
# Если это первый push или нужно установить upstream
git push -u origin main

# Для последующих push
git push
```

## Полная последовательность команд

```bash
# 1. Проверить статус
git status

# 2. Добавить все изменения
git add .

# 3. Создать коммит
git commit -m "Добавлена функциональность генерации тестов для уроков"

# 4. Загрузить в GitHub
git push
```

## Если requirements.txt был изменен для тестовой среды

Если вы меняли `backend/requirements.txt` для тестовой среды, убедитесь, что версии пакетов подходят для production:

### Проверка изменений в requirements.txt
```bash
git diff backend/requirements.txt
```

### Если нужно откатить изменения в requirements.txt
```bash
# Посмотреть историю
git log backend/requirements.txt

# Откатить к последней версии из репозитория
git checkout HEAD -- backend/requirements.txt

# Или восстановить конкретную версию
git checkout <commit-hash> -- backend/requirements.txt
```

### Если изменения в requirements.txt нужны для production
Просто добавьте файл в коммит:
```bash
git add backend/requirements.txt
git commit -m "Обновлены зависимости в requirements.txt"
git push
```

## Работа с ветками (опционально)

Если хотите создать отдельную ветку для изменений:

```bash
# Создать новую ветку
git checkout -b feature/test-generation

# Внести изменения и закоммитить
git add .
git commit -m "Добавлена генерация тестов"

# Загрузить ветку в GitHub
git push -u origin feature/test-generation

# Затем создать Pull Request на GitHub
```

## Отмена изменений (если нужно)

```bash
# Отменить изменения в рабочей директории (не закоммиченные)
git checkout -- <файл>

# Отменить все незакоммиченные изменения
git checkout -- .

# Отменить последний коммит (но оставить изменения)
git reset --soft HEAD~1

# Отменить последний коммит и все изменения
git reset --hard HEAD~1
```

## Полезные команды

```bash
# Посмотреть историю коммитов
git log --oneline

# Посмотреть изменения в файле
git diff <файл>

# Посмотреть, какие файлы изменены
git status --short

# Проверить удаленный репозиторий
git remote -v
```

## Типичная последовательность для вашего случая

```bash
# 1. Проверить, что изменилось
git status

# 2. Если requirements.txt изменен для тестов - решить, нужен ли он в production
# Если да - добавить, если нет - откатить:
git checkout HEAD -- backend/requirements.txt

# 3. Добавить все изменения (кроме requirements.txt, если откатили)
git add .

# 4. Создать коммит
git commit -m "Добавлена функциональность генерации тестов:
- Генерация тестов с помощью AI
- Редактирование тестов
- Прохождение тестов
- Интеграция тестов в SCORM экспорт
- Упрощенная форма генерации (только количество вопросов)"

# 5. Загрузить в GitHub
git push
```

