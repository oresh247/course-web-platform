import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, 
  Spin, 
  Typography, 
  Collapse,
  Button,
  Space,
  Tag,
  App,
  Descriptions,
  List,
  Modal,
  Alert,
  Dropdown,
  Form,
  Input,
  InputNumber,
  Empty
} from 'antd'
import { 
  ArrowLeftOutlined,
  BookOutlined,
  EditOutlined,
  MoreOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  FileAddOutlined
} from '@ant-design/icons'
import { coursesApi } from '../api/coursesApi'
import LessonItem from '../components/LessonItem'

const { Title, Paragraph, Text } = Typography

function CourseViewPage() {
  const { message, modal } = App.useApp();
  const { id } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generatingModule, setGeneratingModule] = useState(null)
  const [generatingModuleTests, setGeneratingModuleTests] = useState(null)
  const [isEditModalVisible, setIsEditModalVisible] = useState(false)
  const [editForm, setEditForm] = useState(null)
  const [editModuleModal, setEditModuleModal] = useState({ visible: false, module: null })
  const [editLessonModal, setEditLessonModal] = useState({ visible: false, module: null, lesson: null, lessonIndex: null })
  const [duplicateModuleModal, setDuplicateModuleModal] = useState({ visible: false, module: null })
  const [duplicateModuleForm] = Form.useForm()
  const [duplicating, setDuplicating] = useState(false)
  const [duplicateCancelRequested, setDuplicateCancelRequested] = useState(false)
  const duplicateAbortRef = useRef(null)

  // Дублирование урока: индикаторы/отмена
  const [duplicatingLesson, setDuplicatingLesson] = useState({ inProgress: false, moduleNumber: null, lessonIndex: null })
  const [duplicateLessonCancelRequested, setDuplicateLessonCancelRequested] = useState(false)
  const duplicateLessonAbortRef = useRef(null)
  const [duplicateLessonModal, setDuplicateLessonModal] = useState({ visible: false, module: null, lessonIndex: null })
  const [duplicateLessonForm] = Form.useForm()
  const [editLessonForm] = Form.useForm()
  const [regenerating, setRegenerating] = useState(false)
  const [detailContentModal, setDetailContentModal] = useState({ visible: false, moduleNumber: null, content: null })
  const [loadingContent, setLoadingContent] = useState(false)
  const [generatingLesson, setGeneratingLesson] = useState(null)
  const [lessonContentModal, setLessonContentModal] = useState({ visible: false, lesson: null, content: null })
  const [contentRefreshKey, setContentRefreshKey] = useState(0)

  useEffect(() => {
    // Проверяем, что id есть и валиден перед загрузкой
    if (id && id !== 'null' && id !== 'undefined' && String(id).trim() !== '') {
      loadCourse()
    } else {
      console.warn('Course ID is invalid or missing, redirecting to courses list', { id: id, idType: typeof id, idStringified: String(id) })
      setLoading(false)
      navigate('/courses')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadCourse = async () => {
    // Проверяем валидность ID из URL
    if (!id || id === 'null' || id === 'undefined' || String(id).trim() === '') {
      console.warn('Invalid course ID from URL:', id)
      message.warning('ID курса не указан. Перенаправление на список курсов...')
      setTimeout(() => {
        navigate('/courses')
      }, 2000)
      setLoading(false)
      return
    }
    
    setLoading(true)
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        console.error(`Неверный формат ID курса: "${id}"`)
        message.error(`Неверный формат ID курса: "${id}"`)
        navigate('/courses')
        setLoading(false)
        return
      }
      
      const response = await coursesApi.getCourse(courseId)
      if (response && response.course) {
        setCourse(response.course)
      } else {
        throw new Error('Курс не найден')
      }
    } catch (error) {
      console.error('Error loading course:', error)
      
      // Если курс не найден, перенаправляем на список
      if (error.response?.status === 404 || error.message?.includes('не найден')) {
        message.error('Курс не найден')
        setTimeout(() => {
          navigate('/courses')
        }, 2000)
      } else {
        message.error('Ошибка загрузки курса. Попробуйте позже.')
      }
      
      setCourse(null)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateContent = async (moduleNumber) => {
    if (!id || id === 'null' || id === 'undefined') {
      message.error('Неверный ID курса')
      return
    }
    setGeneratingModule(moduleNumber)
    try {
      const courseId = parseInt(id, 10)
      const response = await coursesApi.generateModuleContent(courseId, moduleNumber)
      const failedCount = response.failed_lessons?.length || 0
      const skippedCount = response.skipped_lessons?.length || 0
      const generatedCount = response.generated_lessons?.length || 0
      if (failedCount > 0) {
        message.warning(`Контент модуля сгенерирован частично. Сгенерировано: ${generatedCount}, пропущено: ${skippedCount}, ошибки: ${failedCount}`)
      } else {
        message.success('Контент модуля успешно сгенерирован!')
      }
      
      // Показываем модальное окно с результатом
      Modal.info({
        title: 'Контент сгенерирован',
        width: 800,
        content: (
          <div>
            <p>Создано лекций: {response.module_content.lectures.length}</p>
            <p>Всего слайдов: {response.module_content.total_slides}</p>
            <p>Длительность: {response.module_content.estimated_duration_minutes} минут</p>
          </div>
        ),
      })
      setContentRefreshKey((prev) => prev + 1)
    } catch (error) {
      console.error('Error generating content:', error)
      message.error('Ошибка генерации контента')
    } finally {
      setGeneratingModule(null)
    }
  }

  const handleGenerateModuleTests = async (moduleNumber) => {
    if (!id || id === 'null' || id === 'undefined') {
      message.error('Неверный ID курса')
      return
    }
    setGeneratingModuleTests(moduleNumber)
    try {
      const courseId = parseInt(id, 10)
      const response = await coursesApi.generateModuleTests(courseId, moduleNumber, { num_questions: 10 })
      const failedCount = response.failed_lessons?.length || 0
      const skippedCount = response.skipped_lessons?.length || 0
      const generatedCount = response.generated_lessons?.length || 0
      if (failedCount > 0) {
        message.warning(`Тесты сгенерированы частично. Сгенерировано: ${generatedCount}, пропущено: ${skippedCount}, ошибки: ${failedCount}`)
      } else {
        message.success('Тесты модуля успешно сгенерированы!')
      }
      setContentRefreshKey((prev) => prev + 1)
    } catch (error) {
      console.error('Error generating module tests:', error)
      message.error('Ошибка генерации тестов модуля')
    } finally {
      setGeneratingModuleTests(null)
    }
  }

  const scormFormats = ['scorm', 'scorm2004', 'scorm_single']
  const isScormFormat = (format) => scormFormats.includes(format)
  const getExportFormatLabel = (format) => {
    if (format === 'scorm') return 'SCORM 1.2'
    if (format === 'scorm2004') return 'SCORM 2004'
    if (format === 'scorm_single') return 'SCORM 1.2 Single SCO'
    return format.toUpperCase()
  }

  const handleExport = (format) => {
    if (!id || id === 'null' || id === 'undefined') {
      message.error('Неверный ID курса')
      return
    }
    
    const exportLabel = getExportFormatLabel(format)

    // Для SCORM формата спрашиваем о включении видео
    if (isScormFormat(format)) {
      Modal.confirm({
        title: `Экспорт в ${exportLabel}`,
        content: (
          <div>
            <p>Включить видеоматериалы в SCORM пакет?</p>
            <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Видео будут скачаны и включены в пакет. Это увеличит размер файла и время экспорта.
            </p>
          </div>
        ),
        okText: 'Да, включить видео',
        cancelText: 'Нет, без видео',
        onOk: () => {
          performExport(format, true)
        },
        onCancel: () => {
          performExport(format, false)
        }
      })
    } else {
      performExport(format, false)
    }
  }
  
  const performExport = (format, includeVideos) => {
    if (!id || id === 'null' || id === 'undefined') {
      message.error('Неверный ID курса')
      return
    }
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const courseId = parseInt(id, 10)
    let url = `${baseUrl}/api/courses/${courseId}/export/${format}`
    
    // Добавляем параметр include_videos для SCORM
    if (isScormFormat(format) && includeVideos) {
      url += '?include_videos=true'
    }
    
    window.open(url, '_blank')
    const exportLabel = getExportFormatLabel(format)
    message.success(`Экспорт в формате ${exportLabel} начат${includeVideos ? ' (с видео)' : ''}`)
  }

  const handleEditClick = () => {
    setEditForm({
      course_title: course.course_title,
      target_audience: course.target_audience,
      duration_weeks: course.duration_weeks,
      duration_hours: course.duration_hours
    })
    setIsEditModalVisible(true)
  }

  const handleEditSave = async (values) => {
    try {
      // Обновляем только базовую информацию о курсе
      const updatedCourse = {
        ...course,
        ...values
      }
      
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        throw new Error(`Неверный формат ID курса: ${id}`)
      }
      await coursesApi.updateCourse(courseId, updatedCourse)
      message.success('Курс успешно обновлен!')
      setIsEditModalVisible(false)
      loadCourse() // Перезагружаем курс
    } catch (error) {
      console.error('Error updating course:', error)
      message.error('Ошибка обновления курса')
    }
  }

  // Редактирование модуля
  const handleEditModule = (module) => {
    setEditModuleModal({ visible: true, module })
  }

  // Дублирование модуля
  const handleDuplicateModuleOpen = (module) => {
    const copyTitle = `КОПИЯ ${module.module_title}`
    setDuplicateModuleModal({ visible: true, module })
    setDuplicateCancelRequested(false)
    // проставим значения в форму
    setTimeout(() => {
      try {
        duplicateModuleForm.setFieldsValue({
          module_title: copyTitle,
          module_goal: module.module_goal
        })
      } catch (e) {}
    }, 0)
  }

  const handleDuplicateModuleSave = async (values) => {
    try {
      setDuplicating(true)
      setDuplicateCancelRequested(false)
      // Создаём AbortController для возможности отмены
      const controller = new AbortController()
      duplicateAbortRef.current = controller
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        throw new Error(`Неверный формат ID курса: ${id}`)
      }
      const payload = {
        module_title: values.module_title,
        module_goal: values.module_goal,
      }
      const resp = await coursesApi.duplicateModule(
        courseId,
        duplicateModuleModal.module.module_number,
        payload,
        { signal: controller.signal }
      )
      const newNum = resp?.new_module_number
      if (duplicateCancelRequested && newNum) {
        try {
          await coursesApi.deleteModule(courseId, newNum)
          message.info('Дублирование было отменено. Копия удалена.')
        } catch (e) {
          console.warn('Не удалось удалить копию после отмены:', e)
        }
      } else {
        setDuplicateModuleModal({ visible: false, module: null })
        await loadCourse()
        message.success('Модуль успешно продублирован')
      }
    } catch (error) {
      console.error('Error duplicating module:', error)
      if (error?.name === 'CanceledError' || error?.message?.includes('canceled')) {
        message.info('Дублирование отменено')
      } else {
        message.error('Ошибка дублирования модуля')
      }
    } finally {
      setDuplicating(false)
      duplicateAbortRef.current = null
    }
  }

  const handleModuleSave = async (values) => {
    try {
      const updatedCourse = { ...course }
      const moduleIndex = updatedCourse.modules.findIndex(m => m.module_number === editModuleModal.module.module_number)
      
      if (moduleIndex !== -1) {
        updatedCourse.modules[moduleIndex] = {
          ...updatedCourse.modules[moduleIndex],
          ...values
        }
        
        const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        throw new Error(`Неверный формат ID курса: ${id}`)
      }
      await coursesApi.updateCourse(courseId, updatedCourse)
        message.success('Модуль обновлен!')
        setEditModuleModal({ visible: false, module: null })
        loadCourse()
      }
    } catch (error) {
      console.error('Error updating module:', error)
      message.error('Ошибка обновления модуля')
    }
  }

  const handleRegenerateModuleGoal = async (moduleNumber) => {
    setRegenerating(true)
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      const response = await coursesApi.regenerateModuleGoal(courseId, moduleNumber)
      message.success('Цель модуля регенерирована!')
      loadCourse()
      
      // Обновляем в модальном окне
      if (editModuleModal.visible) {
        setEditModuleModal(prev => ({
          ...prev,
          module: { ...prev.module, module_goal: response.new_goal }
        }))
      }
    } catch (error) {
      console.error('Error regenerating module goal:', error)
      message.error('Ошибка регенерации цели')
    } finally {
      setRegenerating(false)
    }
  }

  // Редактирование урока
  const handleEditLesson = (module, lesson, lessonIndex) => {
    setEditLessonModal({ visible: true, module, lesson, lessonIndex })
  }

  const handleLessonSave = async (values) => {
    try {
      const updatedCourse = { ...course }
      const moduleIndex = updatedCourse.modules.findIndex(m => m.module_number === editLessonModal.module.module_number)
      
      if (moduleIndex !== -1) {
        // Преобразуем content_outline из строки в массив
        const contentOutline = typeof values.content_outline === 'string'
          ? values.content_outline.split('\n').filter(line => line.trim())
          : values.content_outline
        
        updatedCourse.modules[moduleIndex].lessons[editLessonModal.lessonIndex] = {
          ...updatedCourse.modules[moduleIndex].lessons[editLessonModal.lessonIndex],
          ...values,
          content_outline: contentOutline
        }
        
        const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        throw new Error(`Неверный формат ID курса: ${id}`)
      }
      await coursesApi.updateCourse(courseId, updatedCourse)
        message.success('Урок обновлен!')
        setEditLessonModal({ visible: false, module: null, lesson: null, lessonIndex: null })
        loadCourse()
      }
    } catch (error) {
      console.error('Error updating lesson:', error)
      message.error('Ошибка обновления урока')
    }
  }

  // Дублирование урока
  const handleOpenDuplicateLesson = (module, lessonIndex, lesson) => {
    setDuplicateLessonModal({ visible: true, module, lessonIndex })
    setTimeout(() => {
      try {
        duplicateLessonForm.setFieldsValue({
          lesson_title: `КОПИЯ ${lesson.lesson_title}`,
          lesson_goal: lesson.lesson_goal,
          content_outline: Array.isArray(lesson.content_outline) ? lesson.content_outline.join('\n') : '',
          assessment: lesson.assessment || ''
        })
      } catch (_) {}
    }, 0)
  }

  const handleDuplicateLesson = async (module, lessonIndex, values) => {
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      setDuplicatingLesson({ inProgress: true, moduleNumber: module.module_number, lessonIndex })
      setDuplicateLessonCancelRequested(false)
      const controller = new AbortController()
      duplicateLessonAbortRef.current = controller
      const payload = {
        lesson_title: values.lesson_title,
        lesson_goal: values.lesson_goal,
        content_outline: typeof values.content_outline === 'string' ? values.content_outline.split('\n').filter(l => l.trim()) : (values.content_outline || []),
        assessment: values.assessment,
      }
      const resp = await coursesApi.duplicateLesson(courseId, module.module_number, lessonIndex, payload, { signal: controller.signal })
      const newIndex = resp?.new_lesson_index
      if (duplicateLessonCancelRequested && (newIndex !== undefined && newIndex !== null)) {
        try {
          await coursesApi.deleteLesson(courseId, module.module_number, newIndex)
          message.info('Дублирование было отменено. Копия урока удалена.')
        } catch (e) {
          console.warn('Не удалось удалить копию урока после отмены:', e)
        }
      } else if (newIndex === undefined || newIndex === null) {
        await loadCourse()
        message.success('Урок продублирован')
        return
      }
      await loadCourse()
      setDuplicateLessonModal({ visible: false, module: null, lessonIndex: null })
      message.success('Урок продублирован')
    } catch (e) {
      console.error('Error duplicating lesson:', e)
      if (e?.name === 'CanceledError' || e?.message?.includes('canceled')) {
        message.info('Дублирование урока отменено')
      } else {
        message.error('Ошибка дублирования урока')
      }
    }
    finally {
      setDuplicatingLesson({ inProgress: false, moduleNumber: null, lessonIndex: null })
      duplicateLessonAbortRef.current = null
    }
  }

  const handleDeleteLesson = async (module, lessonIndex) => {
    modal.confirm({
      title: 'Удалить урок?',
      content: 'Урок и его детальный контент будут удалены без возможности восстановления.',
      okText: 'Удалить',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: async () => {
        try {
          const courseId = parseInt(id, 10)
          if (isNaN(courseId)) throw new Error('Неверный ID курса')
          await coursesApi.deleteLesson(courseId, module.module_number, lessonIndex)
          await loadCourse()
          message.success('Урок удалён')
        } catch (e) {
          console.error('Error deleting lesson:', e)
          message.error('Ошибка удаления урока')
        }
      }
    })
  }

  // Модалка-индикатор для дублирования урока
  const renderDuplicateLessonModal = () => (
    <Modal
      title={`Дублирование урока${duplicatingLesson.lessonIndex !== null ? ` #${duplicatingLesson.lessonIndex + 1}` : ''}`}
      open={duplicateLessonModal.visible}
      onCancel={() => {
        if (duplicatingLesson.inProgress) {
          try { duplicateLessonAbortRef.current?.abort() } catch (_) {}
          setDuplicateLessonCancelRequested(true)
        }
        setDuplicateLessonModal({ visible: false, module: null, lessonIndex: null })
      }}
      footer={null}
      width={480}
    >
      <Spin spinning={duplicatingLesson.inProgress}>
      <Form
        form={duplicateLessonForm}
        layout="vertical"
        onFinish={(vals) => duplicateLessonModal.module && handleDuplicateLesson(duplicateLessonModal.module, duplicateLessonModal.lessonIndex, vals)}
        disabled={duplicatingLesson.inProgress}
      >
          {duplicatingLesson.inProgress && (
            <div style={{ marginBottom: 8 }}>
              <Space>
                <Spin size="small" />
                <span>Дублирование...</span>
              </Space>
            </div>
          )}
        <Form.Item
          label="Название урока"
          name="lesson_title"
          rules={[{ required: true, message: 'Введите название урока' }]}
        >
          <Input placeholder="Например: КОПИЯ Введение в Python" />
        </Form.Item>
        <Form.Item
          label="Цель урока"
          name="lesson_goal"
          rules={[{ required: true, message: 'Введите цель урока' }]}
        >
          <Input.TextArea rows={2} placeholder="Опишите цель урока" />
        </Form.Item>
        <Form.Item
          label="План контента (по строке на пункт)"
          name="content_outline"
        >
          <Input.TextArea rows={6} placeholder="Пункты плана, по одному на строку" />
        </Form.Item>
        <Form.Item
          label="Оценка"
          name="assessment"
        >
          <Input.TextArea rows={2} placeholder="Например: Тест из 10 вопросов" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={duplicatingLesson.inProgress}>
            Дублировать
          </Button>
          <Button
            onClick={() => {
              if (duplicatingLesson.inProgress) {
                try { duplicateLessonAbortRef.current?.abort() } catch (_) {}
                setDuplicateLessonCancelRequested(true)
              }
              setDuplicateLessonModal({ visible: false, module: null, lessonIndex: null })
            }}
            disabled={duplicatingLesson.inProgress}
          >
            Отмена
          </Button>
        </Space>
      </Form>
      </Spin>
    </Modal>
  )

  const handleRegenerateLessonContent = async (moduleNumber, lessonIndex, formInstance = null) => {
    setRegenerating(true)
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      
      // Получаем актуальные значения из формы, если она передана
      let lessonTitle = null
      let lessonGoal = null
      if (formInstance) {
        try {
          const formValues = await formInstance.validateFields(['lesson_title', 'lesson_goal'])
          lessonTitle = formValues.lesson_title
          lessonGoal = formValues.lesson_goal
        } catch (e) {
          // Если валидация не прошла, используем значения из базы данных
          console.warn('Не удалось получить значения из формы, используем значения из базы данных')
        }
      }
      
      const response = await coursesApi.regenerateLessonContent(
        courseId, 
        moduleNumber, 
        lessonIndex,
        lessonTitle ? { lesson_title: lessonTitle, lesson_goal: lessonGoal } : null
      )
      message.success('План контента регенерирован!')
      loadCourse()
      
      // Обновляем в модальном окне
      if (editLessonModal.visible) {
        setEditLessonModal(prev => ({
          ...prev,
          lesson: { 
            ...prev.lesson, 
            content_outline: response.new_content_outline,
            lesson_title: lessonTitle || prev.lesson.lesson_title,
            lesson_goal: lessonGoal || prev.lesson.lesson_goal
          }
        }))
        // Обновляем форму с новым планом контента
        if (formInstance) {
          formInstance.setFieldsValue({
            content_outline: Array.isArray(response.new_content_outline) 
              ? response.new_content_outline.join('\n')
              : response.new_content_outline
          })
        }
      }
    } catch (error) {
      console.error('Error regenerating lesson content:', error)
      message.error('Ошибка регенерации плана контента')
    } finally {
      setRegenerating(false)
    }
  }

  // Просмотр детального контента модуля
  const handleViewDetailContent = async (moduleNumber) => {
    setLoadingContent(true)
    const loadingKey = 'view-module-content'
    try { message.loading({ content: 'Загрузка детального контента модуля...', key: loadingKey, duration: 0 }) } catch (_) {}
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      const response = await coursesApi.getModuleContent(courseId, moduleNumber)
      setDetailContentModal({
        visible: true,
        moduleNumber,
        content: response.module_content
      })
    } catch (error) {
      console.error('Error loading module content:', error)
      message.error('Детальный контент еще не сгенерирован. Сначала сгенерируйте контент.')
    } finally {
      setLoadingContent(false)
      try { message.destroy(loadingKey) } catch (_) {}
    }
  }

  // Экспорт детального контента модуля
  const handleExportModuleContent = (moduleNumber, format) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/courses/${id}/modules/${moduleNumber}/export/${format}`
    window.open(url, '_blank')
    message.success(`Экспорт контента модуля в формате ${format.toUpperCase()} начат`)
  }

  // Генерация детального контента урока
  const handleGenerateLessonContent = async (moduleNumber, lessonIndex) => {
    setGeneratingLesson(`${moduleNumber}-${lessonIndex}`)
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      const response = await coursesApi.generateLessonDetailedContent(courseId, moduleNumber, lessonIndex)
      message.success('Детальный контент урока успешно сгенерирован!')
      
      // Обновляем ключ для обновления проверки наличия контента
      // Используем setTimeout, чтобы дать время серверу сохранить контент
      setTimeout(() => {
        setContentRefreshKey((prev) => prev + 1)
      }, 500)
      
      Modal.info({
        title: 'Контент урока сгенерирован',
        width: 600,
        content: (
          <div>
            <p>Создано слайдов: {response.lesson_content.slides?.length || 0}</p>
            {response.lesson_content.learning_objectives && (
              <p>Целей обучения: {response.lesson_content.learning_objectives.length}</p>
            )}
          </div>
        ),
      })
    } catch (error) {
      console.error('Error generating lesson content:', error)
      message.error('Ошибка генерации контента урока')
    } finally {
      setGeneratingLesson(null)
    }
  }

  // Просмотр детального контента урока
  const handleViewLessonContent = async (moduleNumber, lessonIndex, lesson) => {
    setLoadingContent(true)
    const loadingKey = 'view-lesson-content'
    try { message.loading({ content: 'Загрузка детального контента урока...', key: loadingKey, duration: 0 }) } catch (_) {}
    try {
      const courseId = parseInt(id, 10)
      if (isNaN(courseId)) {
        message.error('Неверный ID курса')
        return
      }
      const response = await coursesApi.getLessonContent(courseId, moduleNumber, lessonIndex)
      setLessonContentModal({
        visible: true,
        lesson: lesson,
        content: response.lesson_content
      })
    } catch (error) {
      console.error('Error loading lesson content:', error)
      message.error('Детальный контент урока еще не сгенерирован. Сначала сгенерируйте контент.')
    } finally {
      setLoadingContent(false)
      try { message.destroy(loadingKey) } catch (_) {}
    }
  }

  // Экспорт детального контента урока
  const normalizeSlideText = (value) => {
    if (typeof value !== 'string') {
      return value
    }
    return value.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
  }

  const renderSlideContent = (value) => (
    <Paragraph style={{ whiteSpace: 'pre-line' }}>{normalizeSlideText(value)}</Paragraph>
  )

  const handleExportLessonContent = (moduleNumber, lessonIndex, format) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/courses/${id}/modules/${moduleNumber}/lessons/${lessonIndex}/export/${format}`
    window.open(url, '_blank')
    message.success(`Экспорт контента урока в формате ${format.toUpperCase()} начат`)
  }

  const exportMenuItems = [
    {
      key: 'scorm',
      label: '🎓 SCORM 1.2 (LMS пакет)',
      onClick: () => handleExport('scorm')
    },
    {
      key: 'scorm2004',
      label: '🎓 SCORM 2004 (LMS пакет)',
      onClick: () => handleExport('scorm2004')
    },
    {
      key: 'scorm_single',
      label: '🎓 SCORM 1.2 Single SCO',
      onClick: () => handleExport('scorm_single')
    },
    {
      type: 'divider'
    },
    {
      key: 'html',
      label: '📄 HTML (веб-страница)',
      onClick: () => handleExport('html')
    },
    {
      key: 'pptx',
      label: '📊 PowerPoint (презентация)',
      onClick: () => handleExport('pptx')
    },
    {
      type: 'divider'
    },
    {
      key: 'markdown',
      label: '📝 Markdown (документация)',
      onClick: () => handleExport('markdown')
    },
    {
      key: 'json',
      label: '🔧 JSON (структурированные данные)',
      onClick: () => handleExport('json')
    },
    {
      key: 'txt',
      label: '📃 Текстовый файл',
      onClick: () => handleExport('txt')
    }
  ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large">
          <div style={{ padding: '50px', minHeight: '200px' }} />
        </Spin>
        <div style={{ marginTop: 16 }}>
          <Text>Загрузка курса...</Text>
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <Card>
        <Empty description="Курс не найден">
          <Button onClick={() => navigate('/courses')}>
            Вернуться к списку курсов
          </Button>
        </Empty>
      </Card>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }} wrap>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/courses')}
        >
          К списку курсов
        </Button>
        <Button 
          type="primary"
          icon={<EditOutlined />}
          onClick={() => navigate(`/courses/${id}/content`)}
        >
          Редактор слайдов
        </Button>
      </Space>

      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>
            <BookOutlined /> {course.course_title}
          </Title>
          <Space size="large" wrap>
            <Tag color="green">{course.target_audience}</Tag>
            {course.duration_weeks && (
              <Tag color="green" icon={<ClockCircleOutlined />}>
                {course.duration_weeks} недель
              </Tag>
            )}
            {course.duration_hours && (
              <Tag color="green">{course.duration_hours} часов</Tag>
            )}
          </Space>
        </div>


        <Title level={3}>Модули курса ({course.modules.length})</Title>

        <Collapse 
          accordion
          items={course.modules.map((module) => ({
            key: module.module_number,
            label: (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <strong>Модуль {module.module_number}:</strong> {module.module_title}
                </span>
                <Space>
                  <Tag color="green">{module.lessons.length} уроков</Tag>
                  <Button 
                    size="small" 
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleEditModule(module)
                    }}
                    title="Редактировать модуль"
                  />
                  <Dropdown
                    trigger={["hover"]}
                    menu={{
                      items: [
                        {
                          key: 'duplicate',
                          label: 'Дублировать модуль',
                          onClick: (info) => handleDuplicateModuleOpen(module)
                        },
                        {
                          type: 'divider'
                        },
                        {
                          key: 'delete',
                          label: 'Удалить модуль',
                          danger: true,
                          onClick: () => {
                            modal.confirm({
                              title: 'Удалить модуль?',
                              content: 'Модуль и весь связанный детальный контент уроков будет удалён без возможности восстановления.',
                              okText: 'Удалить',
                              okType: 'danger',
                              cancelText: 'Отмена',
                              onOk: async () => {
                                try {
                                  const courseId = parseInt(id, 10)
                                  if (isNaN(courseId)) throw new Error('Неверный ID курса')
                                  await coursesApi.deleteModule(courseId, module.module_number)
                                  message.success('Модуль удалён')
                                  await loadCourse()
                                } catch (e) {
                                  console.error('Error deleting module:', e)
                                  message.error('Ошибка удаления модуля')
                                }
                              }
                            })
                          }
                        }
                      ]
                    }}
                  >
                    <Button 
                      size="small"
                      icon={<MoreOutlined />}
                      onClick={(e) => { e.stopPropagation() }}
                      title="Дополнительно"
                    />
                  </Dropdown>
                </Space>
              </div>
            ),
            children: (
              <div>
                <Paragraph>
                  <strong>Цель модуля:</strong> {module.module_goal}
                </Paragraph>

                <Title level={5}>Уроки:</Title>
                <List
                  dataSource={module.lessons}
                  renderItem={(lesson, index) => (
                    <List.Item style={{ display: 'block', padding: '16px 0' }}>
                      <LessonItem
                        lesson={lesson}
                        index={index}
                        moduleNumber={module.module_number}
                        courseId={id ? parseInt(id, 10) : null}
                        contentRefreshKey={contentRefreshKey}
                        onGenerateContent={() => handleGenerateLessonContent(module.module_number, index)}
                        onViewContent={() => handleViewLessonContent(module.module_number, index, lesson)}
                        onExportContent={(format) => handleExportLessonContent(module.module_number, index, format)}
                        onEdit={() => handleEditLesson(module, lesson, index)}
                        onDuplicate={(lessonIndex, lsn) => handleOpenDuplicateLesson(module, lessonIndex, lsn || lesson)}
                        onDelete={(lessonIndex) => handleDeleteLesson(module, lessonIndex)}
                        isGenerating={generatingLesson === `${module.module_number}-${index}`}
                      />
                    </List.Item>
                  )}
                />

                <div style={{ marginTop: 16 }}>
                  <Space>
                    <Button
                      type="primary"
                      icon={<ThunderboltOutlined style={{ color: '#5E8A30' }} />}
                      loading={generatingModule === module.module_number}
                      onClick={() => handleGenerateContent(module.module_number)}
                    >
                      Сгенерировать слайды
                    </Button>
                    <Button
                      icon={<FileAddOutlined />}
                      loading={generatingModuleTests === module.module_number}
                      onClick={() => handleGenerateModuleTests(module.module_number)}
                    >
                      Сгенерировать тесты
                    </Button>
                    <Button
                      icon={<BookOutlined />}
                      loading={loadingContent}
                      onClick={() => handleViewDetailContent(module.module_number)}
                    >
                      Посмотреть контент
                    </Button>
                    <Dropdown 
                      menu={{ 
                        items: [
                          {
                            key: 'pptx',
                            label: '📊 PowerPoint (слайды)',
                            onClick: () => handleExportModuleContent(module.module_number, 'pptx')
                          },
                          {
                            key: 'html',
                            label: '📄 HTML',
                            onClick: () => handleExportModuleContent(module.module_number, 'html')
                          },
                          {
                            type: 'divider'
                          },
                          {
                            key: 'markdown',
                            label: '📝 Markdown',
                            onClick: () => handleExportModuleContent(module.module_number, 'markdown')
                          },
                          {
                            key: 'json',
                            label: '🔧 JSON',
                            onClick: () => handleExportModuleContent(module.module_number, 'json')
                          }
                        ]
                      }} 
                      placement="bottomRight"
                    >
                      <Button icon={<DownloadOutlined />}>
                        Экспортировать
                      </Button>
                    </Dropdown>
                  </Space>
                </div>
              </div>
            )
          }))}
        />

        <div style={{ marginTop: 24 }}>
          <Space>
            <Button 
              icon={<EditOutlined />}
              size="large"
              onClick={handleEditClick}
            >
              Редактировать курс
            </Button>
            <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
              <Button 
                icon={<DownloadOutlined style={{ color: '#5E8A30' }} />}
                size="large"
                type="primary"
              >
                Экспортировать курс
              </Button>
            </Dropdown>
          </Space>
        </div>
      </Card>

      {/* Модальное окно редактирования курса */}
      <Modal
        title="Редактировать курс"
        open={isEditModalVisible}
        onCancel={() => setIsEditModalVisible(false)}
        footer={null}
        width={600}
      >
        {editForm && (
          <Form
            layout="vertical"
            initialValues={editForm}
            onFinish={handleEditSave}
          >
            <Form.Item
              label="Название курса"
              name="course_title"
              rules={[{ required: true, message: 'Введите название курса' }]}
            >
              <Input placeholder="Например: Python для начинающих" />
            </Form.Item>

            <Form.Item
              label="Целевая аудитория"
              name="target_audience"
              rules={[{ required: true, message: 'Укажите целевую аудиторию' }]}
            >
              <Input placeholder="Например: Junior разработчики" />
            </Form.Item>

            <Form.Item
              label="Длительность (недели)"
              name="duration_weeks"
            >
              <InputNumber min={1} max={52} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="Всего часов"
              name="duration_hours"
            >
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  Сохранить изменения
                </Button>
                <Button onClick={() => setIsEditModalVisible(false)}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Модальное окно дублирования модуля */}
      <Modal
        title="Дублировать модуль"
        open={duplicateModuleModal.visible}
        onCancel={() => {
          if (duplicating) {
            setDuplicateCancelRequested(true)
            try { duplicateAbortRef.current?.abort() } catch (_) {}
          }
          setDuplicateModuleModal({ visible: false, module: null })
        }}
        footer={null}
        width={700}
      >
        {duplicateModuleModal.module && (
          <Spin spinning={duplicating} tip="Дублирование...">
          <Form
            form={duplicateModuleForm}
            layout="vertical"
            initialValues={{
              module_title: `КОПИЯ ${duplicateModuleModal.module.module_title}`,
              module_goal: duplicateModuleModal.module.module_goal
            }}
            onFinish={handleDuplicateModuleSave}
            disabled={duplicating}
          >
            <Form.Item
              label="Название модуля"
              name="module_title"
              rules={[{ required: true, message: 'Введите название модуля' }]}
            >
              <Input placeholder="Например: КОПИЯ Основы Python" />
            </Form.Item>

            <Form.Item
              label={
                <Space>
                  <span>Цель модуля</span>
                  <Button 
                    size="small" 
                    type="link" 
                    icon={<ThunderboltOutlined style={{ color: '#5E8A30' }} />}
                    loading={regenerating}
                    onClick={async () => {
                      try {
                        setRegenerating(true)
                        await handleRegenerateModuleGoal(duplicateModuleModal.module.module_number)
                        // В форму можно проставить новое значение при необходимости —
                        // если бэкенд вернул его в состоянии, пере-открытие/перезагрузка курса обновит модал.
                      } finally {
                        setRegenerating(false)
                      }
                    }}
                  >
                    Сгенерировать с помощью AI
                  </Button>
                </Space>
              }
              name="module_goal"
              rules={[{ required: true, message: 'Введите цель модуля' }]}
            >
              <Input.TextArea 
                rows={3} 
                placeholder="Опишите цель модуля"
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={duplicating}>
                  Дублировать
                </Button>
                <Button onClick={() => setDuplicateModuleModal({ visible: false, module: null })} disabled={duplicating}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
          </Spin>
        )}
      </Modal>

      {/* Модальное окно редактирования модуля */}
      <Modal
        title="Редактировать модуль"
        open={editModuleModal.visible}
        onCancel={() => setEditModuleModal({ visible: false, module: null })}
        footer={null}
        width={700}
      >
        {editModuleModal.module && (
          <Form
            layout="vertical"
            initialValues={{
              module_title: editModuleModal.module.module_title,
              module_goal: editModuleModal.module.module_goal
            }}
            onFinish={handleModuleSave}
          >
            <Form.Item
              label="Название модуля"
              name="module_title"
              rules={[{ required: true, message: 'Введите название модуля' }]}
            >
              <Input placeholder="Например: Основы Python" />
            </Form.Item>

            <Form.Item
              label={
                <Space>
                  <span>Цель модуля</span>
                  <Button 
                    size="small" 
                    type="link" 
                    icon={<ThunderboltOutlined style={{ color: '#5E8A30' }} />}
                    loading={regenerating}
                    onClick={() => handleRegenerateModuleGoal(editModuleModal.module.module_number)}
                  >
                    Сгенерировать с помощью AI
                  </Button>
                </Space>
              }
              name="module_goal"
              rules={[{ required: true, message: 'Введите цель модуля' }]}
            >
              <Input.TextArea 
                rows={3} 
                placeholder="Например: Изучить базовый синтаксис Python и научиться писать простые программы" 
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  Сохранить изменения
                </Button>
                <Button onClick={() => setEditModuleModal({ visible: false, module: null })}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Модальное окно редактирования урока */}
      <Modal
        title="Редактировать урок"
        open={editLessonModal.visible}
        onCancel={() => setEditLessonModal({ visible: false, module: null, lesson: null, lessonIndex: null })}
        footer={null}
        width={800}
      >
        {editLessonModal.lesson && (
          <Form
            form={editLessonForm}
            layout="vertical"
            initialValues={{
              lesson_title: editLessonModal.lesson.lesson_title,
              lesson_goal: editLessonModal.lesson.lesson_goal,
              format: editLessonModal.lesson.format,
              estimated_time_minutes: editLessonModal.lesson.estimated_time_minutes,
              content_outline: Array.isArray(editLessonModal.lesson.content_outline) 
                ? editLessonModal.lesson.content_outline.join('\n')
                : editLessonModal.lesson.content_outline,
              assessment: editLessonModal.lesson.assessment
            }}
            onFinish={handleLessonSave}
          >
            <Form.Item
              label="Название урока"
              name="lesson_title"
              rules={[{ required: true, message: 'Введите название урока' }]}
            >
              <Input placeholder="Например: Введение в Python" />
            </Form.Item>

            <Form.Item
              label="Цель урока"
              name="lesson_goal"
              rules={[{ required: true, message: 'Введите цель урока' }]}
            >
              <Input.TextArea rows={2} placeholder="Например: Познакомиться с синтаксисом Python" />
            </Form.Item>

            <Space style={{ width: '100%' }} size="large">
              <Form.Item
                label="Формат"
                name="format"
                style={{ width: 200 }}
              >
                <Input placeholder="lecture, practice, test" />
              </Form.Item>

              <Form.Item
                label="Время (минуты)"
                name="estimated_time_minutes"
              >
                <InputNumber min={1} max={300} />
              </Form.Item>
            </Space>

            <Form.Item
              label={
                <Space>
                  <span>План контента</span>
                  <Button 
                    size="small" 
                    type="link" 
                    icon={<ThunderboltOutlined style={{ color: '#5E8A30' }} />}
                    loading={regenerating}
                    onClick={() => handleRegenerateLessonContent(
                      editLessonModal.module.module_number, 
                      editLessonModal.lessonIndex,
                      editLessonForm
                    )}
                  >
                    Перегенерировать с помощью AI
                  </Button>
                </Space>
              }
              name="content_outline"
            >
              <Input.TextArea 
                rows={6} 
                placeholder="Введите пункты плана, каждый с новой строки" 
                onChange={(e) => {
                  const lines = e.target.value.split('\n').filter(line => line.trim())
                  e.target.value = lines.join('\n')
                }}
              />
            </Form.Item>

            <Form.Item
              label="Оценка"
              name="assessment"
            >
              <Input.TextArea rows={2} placeholder="Например: Тест из 10 вопросов" />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  Сохранить изменения
                </Button>
                <Button onClick={() => setEditLessonModal({ visible: false, module: null, lesson: null, lessonIndex: null })}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Модальное окно просмотра детального контента */}
      <Modal
        title={`Детальный контент модуля ${detailContentModal.moduleNumber}`}
        open={detailContentModal.visible}
        onCancel={() => setDetailContentModal({ visible: false, moduleNumber: null, content: null })}
        footer={null}
        width={1000}
      >
        {detailContentModal.content && (
          <div>
            <Alert
              message="Детальный контент модуля"
              description={`Лекций: ${detailContentModal.content.lectures?.length || 0} | Слайдов: ${detailContentModal.content.total_slides || 0} | Длительность: ${detailContentModal.content.estimated_duration_minutes || 0} минут`}
              type="info"
              showIcon
              style={{ marginBottom: 20 }}
            />

            {detailContentModal.content.lectures && detailContentModal.content.lectures.map((lecture, lectureIndex) => (
              <Card 
                key={lectureIndex} 
                title={`Лекция ${lectureIndex + 1}: ${lecture.lecture_title}`}
                style={{ marginBottom: 16 }}
                type="inner"
              >
                {lecture.learning_objectives && lecture.learning_objectives.length > 0 && (
                  <Alert
                    message="Цели обучения"
                    description={
                      <ul style={{ marginBottom: 0 }}>
                        {lecture.learning_objectives.map((obj, i) => (
                          <li key={i}>{obj}</li>
                        ))}
                      </ul>
                    }
                    type="info"
                    showIcon
                    style={{ marginBottom: 12 }}
                  />
                )}

                {lecture.key_takeaways && lecture.key_takeaways.length > 0 && (
                  <Alert
                    message="Ключевые выводы"
                    description={
                      <ul style={{ marginBottom: 0 }}>
                        {lecture.key_takeaways.map((key, i) => (
                          <li key={i}>{key}</li>
                        ))}
                      </ul>
                    }
                    type="warning"
                    showIcon
                    style={{ marginBottom: 12 }}
                  />
                )}
                
                <Title level={5}>Слайды:</Title>
                <List
                  dataSource={lecture.slides}
                  renderItem={(slide, slideIndex) => (
                    <List.Item>
                      <List.Item.Meta
                        title={`Слайд ${slideIndex + 1}: ${slide.slide_title || slide.title || 'Без названия'}`}
                        description={
                          <div>
                            {(slide.slide_content || slide.content) && (
                              renderSlideContent(slide.slide_content || slide.content)
                            )}
                            {slide.code_example && (
                              <pre style={{ 
                                background: '#282c34',
                                color: '#abb2bf',
                                padding: 12, 
                                borderRadius: 4,
                                overflow: 'auto'
                              }}>
                                <code>{normalizeSlideText(slide.code_example)}</code>
                              </pre>
                            )}
                            {slide.visual_description && (
                              <Alert 
                                message="📊 Визуализация" 
                                description={slide.visual_description} 
                                type="success" 
                                showIcon 
                                style={{ marginTop: 8 }}
                              />
                            )}
                            {slide.notes && (
                              <div style={{ 
                                background: '#f0f0f0', 
                                padding: 8, 
                                marginTop: 8, 
                                borderRadius: 4,
                                fontSize: '0.9em',
                                fontStyle: 'italic'
                              }}>
                                <strong>📝 Заметки преподавателя:</strong> {slide.notes}
                              </div>
                            )}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            ))}
          </div>
        )}
      </Modal>

      {/* Модальное окно просмотра детального контента урока */}
      <Modal
        title={`Детальный контент урока: ${lessonContentModal.lesson?.lesson_title || ''}`}
        open={lessonContentModal.visible}
        onCancel={() => setLessonContentModal({ visible: false, lesson: null, content: null })}
        footer={null}
        width={900}
      >
        {lessonContentModal.content && (
          <div>
            <Alert
              message="Детальный контент урока"
              description={`Слайдов: ${lessonContentModal.content.slides?.length || 0} | Длительность: ${lessonContentModal.content.duration_minutes || 0} минут`}
              type="info"
              showIcon
              style={{ marginBottom: 20 }}
            />

            {lessonContentModal.content.learning_objectives && lessonContentModal.content.learning_objectives.length > 0 && (
              <Alert
                message="Цели обучения"
                description={
                  <ul style={{ marginBottom: 0 }}>
                    {lessonContentModal.content.learning_objectives.map((obj, i) => (
                      <li key={i}>{obj}</li>
                    ))}
                  </ul>
                }
                type="info"
                showIcon
                style={{ marginBottom: 12 }}
              />
            )}

            <Title level={5}>Слайды:</Title>
            <List
              dataSource={lessonContentModal.content.slides || []}
              renderItem={(slide, slideIndex) => (
                <List.Item>
                  <List.Item.Meta
                    title={`Слайд ${slideIndex + 1}: ${slide.slide_title || slide.title || 'Без названия'}`}
                    description={
                      <div>
                        {(slide.slide_content || slide.content) && (
                          renderSlideContent(slide.slide_content || slide.content)
                        )}
                        {slide.code_example && (
                          <pre style={{ 
                            background: '#282c34',
                            color: '#abb2bf',
                            padding: 12, 
                            borderRadius: 4,
                            overflow: 'auto'
                          }}>
                            <code>{normalizeSlideText(slide.code_example)}</code>
                          </pre>
                        )}
                        {slide.notes && (
                          <div style={{ 
                            background: '#f0f0f0', 
                            padding: 8, 
                            marginTop: 8, 
                            borderRadius: 4,
                            fontSize: '0.9em',
                            fontStyle: 'italic'
                          }}>
                            <strong>📝 Заметки:</strong> {slide.notes}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />

            {lessonContentModal.content.key_takeaways && lessonContentModal.content.key_takeaways.length > 0 && (
              <Alert
                message="Ключевые выводы"
                description={
                  <ul style={{ marginBottom: 0 }}>
                    {lessonContentModal.content.key_takeaways.map((key, i) => (
                      <li key={i}>{key}</li>
                    ))}
                  </ul>
                }
                type="warning"
                showIcon
                style={{ marginTop: 20 }}
              />
            )}
          </div>
        )}
      </Modal>

      {renderDuplicateLessonModal()}
    </div>
  )
}

export default CourseViewPage

