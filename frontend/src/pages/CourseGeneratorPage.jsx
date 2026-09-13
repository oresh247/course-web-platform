import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { coursesApi } from '../api/coursesApi'
import './CourseGeneratorPage.css'

const DEPTH_OPTIONS = [
  { value: 'skip', label: 'Пропустить раздел', hint: 'Не включать в курс' },
  { value: 'brief', label: 'Кратко', hint: 'Обзор и основа' },
  { value: 'standard', label: 'Стандартно', hint: 'Теория и практика' },
  { value: 'deep', label: 'Глубоко', hint: 'Подробно и с кейсами' },
]

const KNOWLEDGE_OPTIONS = [
  { value: 'junior', label: 'Начинающий' },
  { value: 'middle', label: 'Средний' },
  { value: 'senior', label: 'Продвинутый' },
]

const EMPTY_PROGRESS = {
  completedQuestions: 0,
  totalQuestions: 0,
  percentage: 0,
  remainingQuestions: 0,
}

const EMPTY_CONFIDENCE = {
  currentModulePercentage: null,
  structurePercentage: null,
  currentModuleStatus: null,
}

const ACTIVE_COURSE_BRIEF_SESSION_KEY = 'course-brief.active-session-id'

const CONFIDENCE_STATUS_LABELS = {
  high: 'достаточно данных',
  medium: 'есть что уточнить',
  low: 'нужно уточнение',
  confirmed: 'подтверждено',
  missing: 'не хватает данных',
  conflict: 'нужно устранить противоречие',
}

const VOLUME_OPTIONS = [
  { value: 2, label: '2 раздела', hint: 'Короткий курс' },
  { value: 3, label: '3 раздела', hint: 'Сжатый объём' },
  { value: 4, label: '4 раздела', hint: 'Стандарт' },
  { value: 6, label: '6 разделов', hint: 'Развёрнуто' },
  { value: 8, label: '8 разделов', hint: 'Большой курс' },
]

const PREBRIEF_GOALS_QUESTION = 'Какую основную цель должен закрывать курс?'
const PREBRIEF_LEVEL_QUESTION = 'На какой уровень аудитории рассчитан курс?'
const PREBRIEF_VOLUME_QUESTION = 'Сколько примерно разделов заложить в черновик структуры?'

const WELCOME_MESSAGE_TEXT = (
  'Начнём с темы, цели, уровня аудитории и объёма. По ним я подготовлю скрытый черновик, а затем уточню каждый раздел — без показа полной структуры до финала.'
)

function createMessage(role, text, isComplete = false) {
  return {
    id: `${Date.now()}-${Math.random()}`,
    role,
    text,
    isComplete,
  }
}

function mapServerMessages(serverMessages, { isComplete = false } = {}) {
  if (!Array.isArray(serverMessages) || !serverMessages.length) return null
  return serverMessages
    .filter((item) => item && (item.role === 'user' || item.role === 'assistant') && item.content)
    .map((item) => createMessage(item.role, item.content, isComplete && item.role === 'assistant'))
}

function normalizeProgress(progress = {}) {
  const toNumber = (value) => {
    const parsed = Number(value)
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0
  }

  const completedQuestions = toNumber(progress.completed_questions ?? progress.completed_modules)
  const totalQuestions = toNumber(progress.total_questions ?? progress.total_modules)
  const responsePercentage = Number(progress.percentage ?? progress.structure_progress_percentage)
  const percentage = Number.isFinite(responsePercentage)
    ? Math.max(0, Math.min(100, Math.round(responsePercentage)))
    : totalQuestions > 0
      ? Math.round((completedQuestions / totalQuestions) * 100)
      : 0
  const remainingValue = progress.remaining_questions ?? progress.remaining_modules
  const remainingQuestions = Number.isFinite(Number(remainingValue))
    ? toNumber(remainingValue)
    : Math.max(totalQuestions - completedQuestions, 0)

  return {
    completedQuestions,
    totalQuestions,
    percentage,
    remainingQuestions,
  }
}

function getPercentage(value) {
  const candidate = typeof value === 'object' && value !== null
    ? value.percentage ?? value.value ?? value.score
    : value
  const number = Number(candidate)

  return Number.isFinite(number) ? Math.max(0, Math.min(100, Math.round(number))) : null
}

function firstPercentage(...values) {
  for (const value of values) {
    const percentage = getPercentage(value)
    if (percentage !== null) return percentage
  }

  return null
}

function normalizeConfidence(response = {}) {
  const confidence = response.confidence && typeof response.confidence === 'object'
    ? response.confidence
    : {}
  const progress = response.progress && typeof response.progress === 'object'
    ? response.progress
    : {}

  return {
    currentModulePercentage: firstPercentage(
      confidence.current_module_percentage,
      confidence.currentModulePercentage,
      confidence.module_percentage,
      confidence.modulePercentage,
      response.current_module_confidence,
      response.currentModuleConfidence,
      response.module_confidence,
      response.moduleConfidence,
    ),
    structurePercentage: firstPercentage(
      confidence.structure_percentage,
      confidence.structurePercentage,
      confidence.course_percentage,
      confidence.coursePercentage,
      response.structure_confidence,
      response.structureConfidence,
      response.course_confidence,
      response.courseConfidence,
      progress.confidence_percentage,
      progress.structure_confidence,
    ),
    currentModuleStatus: confidence.current_module_status
      ?? confidence.currentModuleStatus
      ?? response.current_module_status
      ?? response.currentModuleStatus
      ?? null,
  }
}

function normalizeQuestion(question, response = {}) {
  const source = question && typeof question === 'object' ? question : {}
  const fallbackText = typeof question === 'string'
    ? question
    : response.follow_up_question ?? response.followUpQuestion ?? null
  const text = source.text ?? source.question ?? source.follow_up_question ?? fallbackText

  if (!text) return null

  return {
    ...source,
    text,
    kind: source.kind
      ?? source.type
      ?? source.question_kind
      ?? response.question_kind
      ?? response.questionKind
      ?? response.action
      ?? null,
    answer_controls: source.answer_controls
      ?? source.answerControls
      ?? response.answer_controls
      ?? response.answerControls
      ?? null,
  }
}

function getQuestionKind(question) {
  return String(question?.kind || '').trim().toLowerCase().replace(/-/g, '_')
}

function getQuestionLabel(question) {
  const kind = getQuestionKind(question)

  if (kind === 'follow_up' || kind === 'followup' || kind === 'clarification' || kind === 'ask') {
    return 'Дополнительное уточнение'
  }
  if (kind === 'lesson_scope') {
    return 'Уроки блока'
  }
  if (kind === 'lesson_extras') {
    return 'Дополнения к блоку'
  }
  if (kind === 'add_module') {
    return 'Новый раздел'
  }
  if (kind === 'split_module') {
    return 'Разделение раздела'
  }
  if (kind === 'revise_goal' || kind === 'goal_revision') {
    return 'Уточнение цели курса'
  }
  if (kind === 'module') return 'Уточнение раздела'

  return null
}

function isGoalRevisionQuestion(question) {
  const kind = getQuestionKind(question)
  return kind === 'revise_goal' || kind === 'goal_revision'
}

function showsModuleGateControls(question) {
  const controls = getAnswerControls(question)
  return controls === 'module_gate'
}

function getAnswerControls(question) {
  const raw = String(
    question?.answer_controls
    || question?.answerControls
    || ''
  ).trim().toLowerCase().replace(/-/g, '_')

  if (raw === 'module_gate' || raw === 'knowledge' || raw === 'depth' || raw === 'text') {
    return raw
  }
  const kind = getQuestionKind(question)
  if (kind === 'module') return 'module_gate'
  if (kind === 'split_module' || kind === 'add_module' || kind === 'lesson_scope' || kind === 'lesson_extras') {
    return 'text'
  }
  const text = String(question?.text || '').toLowerCase()
  if (text.includes('уровен') || text.includes('опыт')) return 'knowledge'
  if (text.includes('глубин') || text.includes('нужен ли')) return 'depth'
  return 'text'
}

function showsKnowledgeControls(question) {
  const controls = getAnswerControls(question)
  return controls === 'module_gate' || controls === 'knowledge'
}

function showsDepthControls(question) {
  const controls = getAnswerControls(question)
  return controls === 'module_gate' || controls === 'depth'
}

function getApiErrorMessage(error) {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg).filter(Boolean)
    if (messages.length) return messages.join('. ')
  }

  return error?.message || 'Не удалось продолжить опрос. Попробуйте ещё раз.'
}

function questionWord(count) {
  const lastTwo = count % 100
  const last = count % 10

  if (lastTwo >= 11 && lastTwo <= 14) return 'вопросов'
  if (last === 1) return 'вопрос'
  if (last >= 2 && last <= 4) return 'вопроса'
  return 'вопросов'
}

function getAnswerSummary(depth, knowledgeLevel, comment) {
  const depthLabel = DEPTH_OPTIONS.find((option) => option.value === depth)?.label || depth
  const knowledgeLabel = KNOWLEDGE_OPTIONS.find((option) => option.value === knowledgeLevel)?.label
  const parts = []

  if (depthLabel) parts.push(depthLabel)
  if (knowledgeLabel) parts.push(`уровень: ${knowledgeLabel.toLowerCase()}`)
  if (comment) parts.push(comment)

  return parts.join(' · ') || 'Ответ на уточняющий вопрос'
}

function getActiveCourseBriefSessionId() {
  if (typeof window === 'undefined') return null

  try {
    return window.sessionStorage.getItem(ACTIVE_COURSE_BRIEF_SESSION_KEY)
  } catch {
    return null
  }
}

function saveActiveCourseBriefSessionId(sessionId) {
  if (typeof window === 'undefined' || !sessionId) return

  try {
    window.sessionStorage.setItem(ACTIVE_COURSE_BRIEF_SESSION_KEY, String(sessionId))
  } catch {
    // Ограничения браузера на storage не должны блокировать сам опрос.
  }
}

function clearActiveCourseBriefSessionId() {
  if (typeof window === 'undefined') return

  try {
    window.sessionStorage.removeItem(ACTIVE_COURSE_BRIEF_SESSION_KEY)
  } catch {
    // Если storage недоступен, UI всё равно можно безопасно сбросить.
  }
}

function CourseGeneratorPage() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [preBriefStep, setPreBriefStep] = useState('topic')
  const [courseGoals, setCourseGoals] = useState('')
  const [audienceLevel, setAudienceLevel] = useState(null)
  const [moduleCount, setModuleCount] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [question, setQuestion] = useState(null)
  const [revision, setRevision] = useState(1)
  const [progress, setProgress] = useState(EMPTY_PROGRESS)
  const [confidence, setConfidence] = useState(EMPTY_CONFIDENCE)
  const [phase, setPhase] = useState('idle')
  const [finalCourse, setFinalCourse] = useState(null)
  const [selectedDepth, setSelectedDepth] = useState(null)
  const [selectedKnowledgeLevel, setSelectedKnowledgeLevel] = useState(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [messages, setMessages] = useState(() => [
    createMessage('assistant', WELCOME_MESSAGE_TEXT),
  ])
  const messagesContainerRef = useRef(null)
  const submitLockRef = useRef(false)

  const isPreBrief = phase === 'idle' || phase === 'prebrief'
  const isQuestioning = phase === 'questioning'
  const isCompleted = phase === 'completed'
  const isGoalRevision = isGoalRevisionQuestion(question)
  const answerControls = getAnswerControls(question)
  const showDepthControls = showsDepthControls(question)
  const showKnowledgeControls = showsKnowledgeControls(question)
  const showChoiceControls = showDepthControls || showKnowledgeControls
  const questionLabel = getQuestionLabel(question)
  const questionNumber = question?.number ?? (
    progress.totalQuestions > 0
      ? Math.min(progress.completedQuestions + 1, progress.totalQuestions)
      : null
  )
  const questionTotal = question?.total ?? progress.totalQuestions
  const finalModules = Array.isArray(finalCourse?.modules) ? finalCourse.modules : []
  const trimmedComment = comment.trim()
  const canSubmitAnswer = showChoiceControls
    ? Boolean(selectedDepth || selectedKnowledgeLevel || trimmedComment)
    : Boolean(trimmedComment)
  const hasConfidence = confidence.currentModulePercentage !== null
    || confidence.structurePercentage !== null
    || Boolean(confidence.currentModuleStatus)

  useEffect(() => {
    const messagesContainer = messagesContainerRef.current
    if (!messagesContainer) return

    // Прокручиваем только внутреннюю область сообщений. scrollIntoView у
    // маркера внизу чата мог прокручивать весь документ после каждого ответа.
    messagesContainer.scrollTo({
      top: messagesContainer.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages.length])

  const applyBriefResponse = (response, { mode = 'append' } = {}) => {
    if (response.session_id) {
      setSessionId(response.session_id)
      saveActiveCourseBriefSessionId(response.session_id)
    }
    if (response.topic) setTopic(response.topic)
    if (Number.isInteger(Number(response.revision)) && Number(response.revision) >= 1) {
      setRevision(Number(response.revision))
    }

    const nextProgress = normalizeProgress(response.progress)
    const isResponseComplete = response.status === 'completed' || response.action === 'finish'
    const nextQuestion = normalizeQuestion(response.question, response)

    setProgress(nextProgress)
    setConfidence(normalizeConfidence(response))
    setQuestion(isResponseComplete ? null : nextQuestion)
    setFinalCourse(isResponseComplete ? response.final_course || null : null)
    setPhase(isResponseComplete ? 'completed' : 'questioning')

    const agentText = isResponseComplete
      ? response.final_course
        ? 'Уточнение завершено. Я сформировал финальную структуру курса на основе ваших ответов.'
        : 'Уточнение завершено. Финальная структура будет доступна после завершения обработки.'
      : nextQuestion?.text || 'Продолжим уточнение структуры курса.'

    const historyFromServer = mapServerMessages(response.messages, { isComplete: isResponseComplete })

    setMessages((currentMessages) => {
      if (mode === 'restore' && historyFromServer) {
        return [
          createMessage('assistant', WELCOME_MESSAGE_TEXT),
          ...historyFromServer,
        ]
      }

      const last = currentMessages[currentMessages.length - 1]
      if (last?.role === 'assistant' && last.text === agentText) {
        return currentMessages
      }
      return [
        ...currentMessages,
        createMessage('assistant', agentText, isResponseComplete),
      ]
    })
  }

  useEffect(() => {
    const storedSessionId = getActiveCourseBriefSessionId()
    if (!storedSessionId) return undefined

    let isCurrent = true

    const restoreCourseBrief = async () => {
      setError('')
      setPhase('starting')
      setIsSubmitting(true)

      try {
        const response = await coursesApi.getCourseBrief(storedSessionId)
        if (isCurrent) applyBriefResponse(response, { mode: 'restore' })
      } catch (requestError) {
        if (!isCurrent) return

        if (requestError?.response?.status === 404) {
          clearActiveCourseBriefSessionId()
          setError('Сохранённая сессия больше недоступна. Начните новый диалог.')
        } else {
          setError('Не удалось восстановить сохранённую сессию. Попробуйте обновить страницу.')
        }
        setPhase('idle')
      } finally {
        if (isCurrent) setIsSubmitting(false)
      }
    }

    restoreCourseBrief()

    return () => {
      isCurrent = false
    }
  }, [])

  const startBriefWithPreBrief = async ({
    topicValue,
    goalsValue,
    levelValue,
    moduleCountValue,
  }) => {
    setError('')
    setPhase('starting')
    setIsSubmitting(true)

    try {
      const response = await coursesApi.startCourseBrief({
        topic: topicValue,
        course_goals: goalsValue,
        audience_level: levelValue,
        module_count: moduleCountValue,
      })
      applyBriefResponse(response, { mode: 'append' })
    } catch (requestError) {
      setPhase('prebrief')
      setPreBriefStep('volume')
      setError(getApiErrorMessage(requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTopicSubmit = async (event) => {
    event.preventDefault()
    const trimmedTopic = topic.trim()

    if (trimmedTopic.length < 3) {
      setError('Введите тему курса не короче трёх символов.')
      return
    }

    setError('')
    setPhase('prebrief')
    setPreBriefStep('goals')
    setMessages((currentMessages) => [
      ...currentMessages,
      createMessage('user', trimmedTopic),
      createMessage('assistant', PREBRIEF_GOALS_QUESTION),
    ])
  }

  const handlePreBriefGoalsSubmit = (event) => {
    event.preventDefault()
    const trimmedGoals = courseGoals.trim()
    if (trimmedGoals.length < 3) {
      setError('Опишите цель курса не короче трёх символов.')
      return
    }

    setError('')
    setPreBriefStep('level')
    setMessages((currentMessages) => [
      ...currentMessages,
      createMessage('user', trimmedGoals),
      createMessage('assistant', PREBRIEF_LEVEL_QUESTION),
    ])
  }

  const handlePreBriefLevelSelect = (level) => {
    setAudienceLevel(level)
    setError('')
    setPreBriefStep('volume')
    const label = KNOWLEDGE_OPTIONS.find((item) => item.value === level)?.label || level
    setMessages((currentMessages) => [
      ...currentMessages,
      createMessage('user', label),
      createMessage('assistant', PREBRIEF_VOLUME_QUESTION),
    ])
  }

  const handlePreBriefVolumeSelect = async (count) => {
    if (isSubmitting) return
    setModuleCount(count)
    const option = VOLUME_OPTIONS.find((item) => item.value === count)
    setMessages((currentMessages) => [
      ...currentMessages,
      createMessage('user', option?.label || `${count} разделов`),
    ])
    await startBriefWithPreBrief({
      topicValue: topic.trim(),
      goalsValue: courseGoals.trim(),
      levelValue: audienceLevel,
      moduleCountValue: count,
    })
  }

  const handleAnswerSubmit = async (event) => {
    event.preventDefault()

    if (!sessionId) {
      setError('Сессия опроса не найдена. Начните новый диалог.')
      return
    }
    if (submitLockRef.current || isSubmitting) {
      return
    }

    const trimmedComment = comment.trim()
    const useDepth = showsDepthControls(question)
    const useKnowledge = showsKnowledgeControls(question)
    const useChoiceControls = useDepth || useKnowledge

    if (useChoiceControls) {
      if (!selectedDepth && !selectedKnowledgeLevel && !trimmedComment) {
        setError(useKnowledge && !useDepth
          ? 'Выберите уровень знаний или напишите ответ.'
          : useDepth && !useKnowledge
            ? 'Выберите глубину раздела или напишите ответ.'
            : 'Выберите глубину, уровень знаний или напишите ответ.')
        return
      }
    } else if (!trimmedComment) {
      setError('Напишите ответ на текущий вопрос.')
      return
    }

    const answer = {
      expected_revision: revision,
      ...(useDepth && selectedDepth ? { depth: selectedDepth } : {}),
      ...(useKnowledge && selectedKnowledgeLevel
        ? { knowledge_level: selectedKnowledgeLevel }
        : {}),
      ...(trimmedComment ? { comment: trimmedComment } : {}),
    }

    setError('')
    setMessages((currentMessages) => [
      ...currentMessages,
      createMessage(
        'user',
        useChoiceControls
          ? getAnswerSummary(
            useDepth ? selectedDepth : null,
            useKnowledge ? selectedKnowledgeLevel : null,
            trimmedComment,
          )
          : trimmedComment,
      ),
    ])
    submitLockRef.current = true
    setIsSubmitting(true)

    try {
      const response = await coursesApi.answerCourseBrief(sessionId, answer)
      setSelectedDepth(null)
      setSelectedKnowledgeLevel(null)
      setComment('')
      applyBriefResponse(response, { mode: 'append' })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      submitLockRef.current = false
      setIsSubmitting(false)
    }
  }

  const startNewBrief = () => {
    clearActiveCourseBriefSessionId()
    setTopic('')
    setSessionId(null)
    setQuestion(null)
    setRevision(1)
    setProgress(EMPTY_PROGRESS)
    setConfidence(EMPTY_CONFIDENCE)
    setPhase('idle')
    setFinalCourse(null)
    setSelectedDepth(null)
    setSelectedKnowledgeLevel(null)
    setComment('')
    setError('')
    setMessages([
      createMessage('assistant', WELCOME_MESSAGE_TEXT),
    ])
  }

  const pageTitle = isCompleted
    ? finalCourse?.course_title || 'Структура курса готова'
    : topic
      ? `Курс: ${topic}`
      : 'Чему вы хотите научиться?'
  const pageSummary = isCompleted
    ? 'Финальная программа сформирована на основе ваших ответов.'
    : 'Ответьте на короткие вопросы. Мы уточним глубину каждого раздела и уровень знаний слушателей.'

  return (
    <div className="course-generator-page">
      <header className="course-generator-page__topbar">
        <Link className="course-generator-page__brand" to="/" aria-label="AI Course Builder — главная">
          <span className="course-generator-page__brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M4 7.5h16M6.5 12h11M9 16.5h6" />
              <path d="M5 4h14a1 1 0 0 1 1 1v14l-4-3H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" />
            </svg>
          </span>
          <span>
            <strong>AI Course Builder</strong>
            <small>уточнение структуры курса</small>
          </span>
        </Link>

        <nav className="course-generator-page__topbar-actions" aria-label="Действия страницы">
          <button className="course-generator-page__ghost-button" type="button" onClick={() => navigate('/courses')}>
            Мои курсы
          </button>
          <button className="course-generator-page__secondary-button" type="button" onClick={startNewBrief} disabled={isSubmitting}>
            Новый диалог
          </button>
        </nav>
      </header>

      <main className="course-generator-page__workspace">
        <aside className="course-generator-page__sidebar" aria-label="Этапы создания курса">
          <div>
            <p className="course-generator-page__eyebrow">Создание курса</p>
            <h2>Рабочий процесс</h2>
          </div>

          <ol className="course-generator-page__steps">
            <li className={phase !== 'idle' ? 'is-complete' : 'is-active'}>
              <span>01</span>
              <div>
                <strong>Тема курса</strong>
                <p>{topic || 'Опишите навык или задачу'}</p>
              </div>
            </li>
            <li className={isQuestioning ? 'is-active' : isCompleted ? 'is-complete' : ''}>
              <span>02</span>
              <div>
                <strong>Уточнение разделов</strong>
                <p>{isQuestioning ? 'Идёт опрос' : 'Настроим глубину и уровень'}</p>
              </div>
            </li>
            <li className={isCompleted ? 'is-active' : ''}>
              <span>03</span>
              <div>
                <strong>Финальная структура</strong>
                <p>{isCompleted ? 'Готова к просмотру' : 'Покажем после опроса'}</p>
              </div>
            </li>
          </ol>

          <div className="course-generator-page__sidebar-note">
            <span className="course-generator-page__note-dot" aria-hidden="true" />
            Черновая структура остаётся скрытой, пока вы не завершите уточнение.
          </div>
        </aside>

        <section className="course-generator-page__chat" aria-labelledby="course-generator-title">
          <header className="course-generator-page__chat-head">
            <p className="course-generator-page__status">
              <span className="course-generator-page__live-dot" aria-hidden="true" />
              {isCompleted ? 'структура готова' : isQuestioning ? 'агент уточняет потребность' : 'начало диалога'}
            </p>
            <h1 id="course-generator-title">{pageTitle}</h1>
            <p>{pageSummary}</p>
          </header>

          <div ref={messagesContainerRef} className="course-generator-page__messages" aria-live="polite">
            {messages.map((message) => (
              <article
                className={`course-generator-page__message course-generator-page__message--${message.role}`}
                key={message.id}
              >
                <span className="course-generator-page__avatar" aria-hidden="true">
                  {message.role === 'assistant' ? 'AI' : 'Вы'}
                </span>
                <div className="course-generator-page__bubble">
                  <p>{message.text}</p>
                  {message.isComplete && <span className="course-generator-page__complete-label">Опрос завершён</span>}
                </div>
              </article>
            ))}

            {isSubmitting && (
              <article className="course-generator-page__message course-generator-page__message--assistant" aria-label="Агент готовит ответ">
                <span className="course-generator-page__avatar" aria-hidden="true">AI</span>
                <div className="course-generator-page__bubble course-generator-page__bubble--loading">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            )}
          </div>

          <div className="course-generator-page__composer-area">
            {error && <p className="course-generator-page__error" role="alert">{error}</p>}

            {isPreBrief ? (
              preBriefStep === 'topic' ? (
                <form className="course-generator-page__composer" onSubmit={handleTopicSubmit}>
                  <label className="course-generator-page__field-label" htmlFor="course-topic">
                    Тема будущего курса
                  </label>
                  <div className="course-generator-page__composer-box">
                    <textarea
                      id="course-topic"
                      className="course-generator-page__textarea"
                      value={topic}
                      onChange={(event) => setTopic(event.target.value)}
                      placeholder="Например: запускать AI-продукты, управлять командой, работать с данными…"
                      rows="2"
                      maxLength="200"
                      disabled={isSubmitting}
                    />
                    <button className="course-generator-page__primary-button" type="submit" disabled={isSubmitting}>
                      Далее
                    </button>
                  </div>
                </form>
              ) : preBriefStep === 'goals' ? (
                <form className="course-generator-page__composer" onSubmit={handlePreBriefGoalsSubmit}>
                  <label className="course-generator-page__field-label" htmlFor="course-goals">
                    Цель курса
                  </label>
                  <div className="course-generator-page__composer-box">
                    <textarea
                      id="course-goals"
                      className="course-generator-page__textarea"
                      value={courseGoals}
                      onChange={(event) => setCourseGoals(event.target.value)}
                      placeholder="Например: научиться строить отчёты и принимать решения на данных"
                      rows="2"
                      maxLength="1000"
                      disabled={isSubmitting}
                    />
                    <button className="course-generator-page__primary-button" type="submit" disabled={isSubmitting}>
                      Далее
                    </button>
                  </div>
                </form>
              ) : preBriefStep === 'level' ? (
                <div className="course-generator-page__answer-form">
                  <div className="course-generator-page__question-meta">
                    <span>Перед черновиком</span>
                    <strong>{PREBRIEF_LEVEL_QUESTION}</strong>
                  </div>
                  <fieldset disabled={isSubmitting}>
                    <legend>Уровень аудитории</legend>
                    <div className="course-generator-page__choice-list course-generator-page__choice-list--compact">
                      {KNOWLEDGE_OPTIONS.map((option) => (
                        <button
                          className={`course-generator-page__choice ${audienceLevel === option.value ? 'is-selected' : ''}`}
                          type="button"
                          key={option.value}
                          aria-pressed={audienceLevel === option.value}
                          onClick={() => handlePreBriefLevelSelect(option.value)}
                        >
                          <strong>{option.label}</strong>
                        </button>
                      ))}
                    </div>
                  </fieldset>
                </div>
              ) : (
                <div className="course-generator-page__answer-form">
                  <div className="course-generator-page__question-meta">
                    <span>Перед черновиком</span>
                    <strong>{PREBRIEF_VOLUME_QUESTION}</strong>
                  </div>
                  <fieldset disabled={isSubmitting}>
                    <legend>Объём черновика</legend>
                    <div className="course-generator-page__choice-list">
                      {VOLUME_OPTIONS.map((option) => (
                        <button
                          className={`course-generator-page__choice ${moduleCount === option.value ? 'is-selected' : ''}`}
                          type="button"
                          key={option.value}
                          aria-pressed={moduleCount === option.value}
                          onClick={() => handlePreBriefVolumeSelect(option.value)}
                        >
                          <strong>{option.label}</strong>
                          <span>{option.hint}</span>
                        </button>
                      ))}
                    </div>
                  </fieldset>
                </div>
              )
            ) : isQuestioning ? (
              <form className="course-generator-page__answer-form" onSubmit={handleAnswerSubmit}>
                <div className="course-generator-page__question-meta">
                  <span>
                    {questionLabel || (questionNumber && questionTotal
                      ? `Вопрос ${questionNumber} из ${questionTotal}`
                      : 'Следующее уточнение')}
                    {questionLabel && questionNumber && questionTotal ? ` · раздел ${questionNumber} из ${questionTotal}` : ''}
                  </span>
                  <strong>{question?.text || 'Насколько подробно нужен этот раздел?'}</strong>
                </div>

                {!isGoalRevision && showChoiceControls && (
                  <>
                    {showDepthControls && (
                      <fieldset disabled={isSubmitting}>
                        <legend>Глубина раздела</legend>
                        <div className="course-generator-page__choice-list">
                          {DEPTH_OPTIONS.map((option) => (
                            <button
                              className={`course-generator-page__choice ${selectedDepth === option.value ? 'is-selected' : ''}`}
                              type="button"
                              key={option.value}
                              aria-pressed={selectedDepth === option.value}
                              onClick={() => setSelectedDepth((currentValue) => (
                                currentValue === option.value ? null : option.value
                              ))}
                            >
                              <strong>{option.label}</strong>
                              <span>{option.hint}</span>
                            </button>
                          ))}
                        </div>
                      </fieldset>
                    )}

                    {showKnowledgeControls && (
                      <fieldset disabled={isSubmitting}>
                        <legend>
                          Уровень знаний
                          {answerControls === 'module_gate' ? <span> (необязательно)</span> : null}
                        </legend>
                        <div className="course-generator-page__choice-list course-generator-page__choice-list--compact">
                          {KNOWLEDGE_OPTIONS.map((option) => (
                            <button
                              className={`course-generator-page__choice ${selectedKnowledgeLevel === option.value ? 'is-selected' : ''}`}
                              type="button"
                              key={option.value}
                              aria-pressed={selectedKnowledgeLevel === option.value}
                              onClick={() => setSelectedKnowledgeLevel((currentValue) => (
                                currentValue === option.value ? null : option.value
                              ))}
                            >
                              <strong>{option.label}</strong>
                            </button>
                          ))}
                        </div>
                      </fieldset>
                    )}
                  </>
                )}

                <label className="course-generator-page__comment-label" htmlFor="course-brief-comment">
                  {isGoalRevision ? 'Опишите цель курса' : showChoiceControls ? 'Комментарий' : 'Ваш ответ'}
                  {showChoiceControls ? <span> (необязательно)</span> : null}
                  <textarea
                    id="course-brief-comment"
                    className="course-generator-page__textarea course-generator-page__textarea--comment"
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    placeholder={isGoalRevision
                      ? 'Например: хочу решать задачу … для …'
                      : showChoiceControls
                        ? 'Дополнительно текстом, если нужно'
                        : 'Ответьте на вопрос выше'}
                    rows="2"
                    maxLength="2000"
                    disabled={isSubmitting}
                  />
                </label>

                <div className="course-generator-page__answer-actions">
                  <span>{isGoalRevision
                    ? 'Опишите новую цель, чтобы продолжить.'
                    : answerControls === 'knowledge'
                      ? 'Выберите уровень знаний.'
                      : answerControls === 'depth'
                        ? 'Выберите глубину раздела.'
                        : showChoiceControls
                          ? 'Выберите глубину, уровень или опишите требование текстом.'
                          : 'Ответьте текстом на текущий вопрос.'}</span>
                  <button className="course-generator-page__primary-button" type="submit" disabled={isSubmitting || !canSubmitAnswer}>
                    {isSubmitting ? 'Сохраняем…' : 'Продолжить'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="course-generator-page__completed-actions">
                <p>Структура доступна в панели справа.</p>
                <button className="course-generator-page__primary-button" type="button" onClick={startNewBrief}>
                  Создать ещё один курс
                </button>
              </div>
            )}
          </div>
        </section>

        <aside className="course-generator-page__inspector" aria-label="Прогресс уточнения структуры">
          <section className="course-generator-page__panel course-generator-page__progress-panel">
            <div className="course-generator-page__panel-heading">
              <div>
                <p className="course-generator-page__eyebrow">Прогресс</p>
                <h2>Уточнение структуры</h2>
              </div>
              <strong>{progress.percentage}%</strong>
            </div>
            <div
              className="course-generator-page__meter"
              role="progressbar"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow={progress.percentage}
              aria-label={`Уточнение структуры выполнено на ${progress.percentage} процентов`}
            >
              <span style={{ width: `${progress.percentage}%` }} />
            </div>
            <div className="course-generator-page__progress-details">
              <span>{progress.totalQuestions ? `${progress.completedQuestions} из ${progress.totalQuestions} уточнений` : 'Вопросы появятся после темы'}</span>
              <strong>{progress.remainingQuestions ? `Осталось ${progress.remainingQuestions} ${questionWord(progress.remainingQuestions)}` : isCompleted ? 'Всё готово' : 'Осталось уточнить план'}</strong>
            </div>
          </section>

          {hasConfidence && (
            <section className="course-generator-page__panel course-generator-page__confidence-panel" aria-label="Уверенность в настройке курса">
              <div className="course-generator-page__confidence-heading">
                <div>
                  <p className="course-generator-page__eyebrow">Качество данных</p>
                  <h2>Уверенность в настройке</h2>
                </div>
                {confidence.currentModuleStatus && (
                  <span className="course-generator-page__confidence-status">
                    {CONFIDENCE_STATUS_LABELS[String(confidence.currentModuleStatus).toLowerCase()] || confidence.currentModuleStatus}
                  </span>
                )}
              </div>

              <div className="course-generator-page__confidence-values">
                {confidence.currentModulePercentage !== null && (
                  <div>
                    <div className="course-generator-page__confidence-value-heading">
                      <span>Текущий раздел</span>
                      <strong>{confidence.currentModulePercentage}%</strong>
                    </div>
                    <div
                      className="course-generator-page__meter course-generator-page__meter--confidence"
                      role="progressbar"
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-valuenow={confidence.currentModulePercentage}
                      aria-label={`Уверенность в настройке текущего раздела: ${confidence.currentModulePercentage} процентов`}
                    >
                      <span style={{ width: `${confidence.currentModulePercentage}%` }} />
                    </div>
                  </div>
                )}

                {confidence.structurePercentage !== null && (
                  <div>
                    <div className="course-generator-page__confidence-value-heading">
                      <span>Вся структура</span>
                      <strong>{confidence.structurePercentage}%</strong>
                    </div>
                    <div
                      className="course-generator-page__meter course-generator-page__meter--confidence"
                      role="progressbar"
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-valuenow={confidence.structurePercentage}
                      aria-label={`Уверенность в настройке структуры курса: ${confidence.structurePercentage} процентов`}
                    >
                      <span style={{ width: `${confidence.structurePercentage}%` }} />
                    </div>
                  </div>
                )}
              </div>
              <p className="course-generator-page__confidence-note">Это полнота подтверждённых требований, а не оценка знаний пользователя.</p>
            </section>
          )}

          {isCompleted && (
            <section className="course-generator-page__panel course-generator-page__outline-panel">
              <div className="course-generator-page__outline-heading">
                <div>
                  <p className="course-generator-page__eyebrow">Результат</p>
                  <h2>Финальная структура</h2>
                </div>
                <span>готово</span>
              </div>

              {finalCourse ? (
                <>
                  <p className="course-generator-page__course-goal">
                    {finalCourse.course_goals || `Курс для аудитории: ${finalCourse.target_audience || 'уточнённой в диалоге'}.`}
                  </p>
                  <ol className="course-generator-page__outline-list">
                    {finalModules.map((module, index) => (
                      <li key={module.module_number ?? `${module.module_title}-${index}`}>
                        <span>{String(module.module_number ?? index + 1).padStart(2, '0')}</span>
                        <div>
                          <strong>{module.module_title}</strong>
                          {module.module_goal && <p>{module.module_goal}</p>}
                          {Array.isArray(module.lessons) && module.lessons.length > 0 && (
                            <ul>
                              {module.lessons.map((lesson, lessonIndex) => (
                                <li key={`${lesson.lesson_title}-${lessonIndex}`}>{lesson.lesson_title}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </li>
                    ))}
                  </ol>
                  {finalModules.length === 0 && <p className="course-generator-page__empty-outline">Структура сформирована, но пока не содержит модулей.</p>}
                </>
              ) : (
                <p className="course-generator-page__empty-outline">Финальная структура ещё обрабатывается. Обновите страницу через несколько секунд.</p>
              )}
            </section>
          )}

          {!isCompleted && (
            <section className="course-generator-page__panel course-generator-page__privacy-panel">
              <h2>Что происходит сейчас</h2>
              <p>Агент использует тему и ответы, чтобы уточнить содержание каждого раздела. Черновик останется скрытым до конца опроса.</p>
            </section>
          )}
        </aside>
      </main>
    </div>
  )
}

export default CourseGeneratorPage
