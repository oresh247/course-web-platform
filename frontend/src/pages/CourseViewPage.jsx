import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, 
  Spin, 
  Typography, 
  Collapse,
  Button,
  Space,
  Tag,
  message,
  Descriptions,
  List,
  Modal,
  Alert,
  Dropdown,
  Form,
  Input,
  InputNumber
} from 'antd'
import { 
  ArrowLeftOutlined,
  BookOutlined,
  EditOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import { coursesApi } from '../api/coursesApi'
import LessonItem from '../components/LessonItem'

const { Title, Paragraph, Text } = Typography
const { Panel } = Collapse

function CourseViewPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generatingModule, setGeneratingModule] = useState(null)
  const [isEditModalVisible, setIsEditModalVisible] = useState(false)
  const [editForm, setEditForm] = useState(null)
  const [editModuleModal, setEditModuleModal] = useState({ visible: false, module: null })
  const [editLessonModal, setEditLessonModal] = useState({ visible: false, module: null, lesson: null, lessonIndex: null })
  const [regenerating, setRegenerating] = useState(false)
  const [detailContentModal, setDetailContentModal] = useState({ visible: false, moduleNumber: null, content: null })
  const [loadingContent, setLoadingContent] = useState(false)
  const [generatingLesson, setGeneratingLesson] = useState(null)
  const [lessonContentModal, setLessonContentModal] = useState({ visible: false, lesson: null, content: null })

  useEffect(() => {
    loadCourse()
  }, [id])

  const loadCourse = async () => {
    setLoading(true)
    try {
      const response = await coursesApi.getCourse(id)
      setCourse(response.course)
    } catch (error) {
      console.error('Error loading course:', error)
      message.error('Ошибка загрузки курса')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateContent = async (moduleNumber) => {
    setGeneratingModule(moduleNumber)
    try {
      const response = await coursesApi.generateModuleContent(id, moduleNumber)
      message.success('Контент модуля успешно сгенерирован!')
      
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
    } catch (error) {
      console.error('Error generating content:', error)
      message.error('Ошибка генерации контента')
    } finally {
      setGeneratingModule(null)
    }
  }

  const handleExport = (format) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/courses/${id}/export/${format}`
    window.open(url, '_blank')
    message.success(`Экспорт в формате ${format.toUpperCase()} начат`)
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
      
      await coursesApi.updateCourse(id, updatedCourse)
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

  const handleModuleSave = async (values) => {
    try {
      const updatedCourse = { ...course }
      const moduleIndex = updatedCourse.modules.findIndex(m => m.module_number === editModuleModal.module.module_number)
      
      if (moduleIndex !== -1) {
        updatedCourse.modules[moduleIndex] = {
          ...updatedCourse.modules[moduleIndex],
          ...values
        }
        
        await coursesApi.updateCourse(id, updatedCourse)
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
      const response = await coursesApi.regenerateModuleGoal(id, moduleNumber)
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
        
        await coursesApi.updateCourse(id, updatedCourse)
        message.success('Урок обновлен!')
        setEditLessonModal({ visible: false, module: null, lesson: null, lessonIndex: null })
        loadCourse()
      }
    } catch (error) {
      console.error('Error updating lesson:', error)
      message.error('Ошибка обновления урока')
    }
  }

  const handleRegenerateLessonContent = async (moduleNumber, lessonIndex) => {
    setRegenerating(true)
    try {
      const response = await coursesApi.regenerateLessonContent(id, moduleNumber, lessonIndex)
      message.success('План контента регенерирован!')
      loadCourse()
      
      // Обновляем в модальном окне
      if (editLessonModal.visible) {
        setEditLessonModal(prev => ({
          ...prev,
          lesson: { ...prev.lesson, content_outline: response.new_content_outline }
        }))
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
    try {
      const response = await coursesApi.getModuleContent(id, moduleNumber)
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
      const response = await coursesApi.generateLessonDetailedContent(id, moduleNumber, lessonIndex)
      message.success('Детальный контент урока успешно сгенерирован!')
      
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
    try {
      const response = await coursesApi.getLessonContent(id, moduleNumber, lessonIndex)
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
    }
  }

  // Экспорт детального контента урока
  const handleExportLessonContent = (moduleNumber, lessonIndex, format) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/courses/${id}/modules/${moduleNumber}/lessons/${lessonIndex}/export/${format}`
    window.open(url, '_blank')
    message.success(`Экспорт контента урока в формате ${format.toUpperCase()} начат`)
  }

  const exportMenuItems = [
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
        <Spin size="large" tip="Загрузка курса..." />
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
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={() => navigate('/courses')}
        style={{ marginBottom: 16 }}
      >
        К списку курсов
      </Button>

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

        <Collapse accordion>
          {course.modules.map((module) => (
            <Panel
              key={module.module_number}
              header={
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
                    >
                      Редактировать
                    </Button>
                  </Space>
                </div>
              }
            >
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
                      onGenerateContent={() => handleGenerateLessonContent(module.module_number, index)}
                      onViewContent={() => handleViewLessonContent(module.module_number, index, lesson)}
                      onExportContent={(format) => handleExportLessonContent(module.module_number, index, format)}
                      onEdit={() => handleEditLesson(module, lesson, index)}
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
                    Сгенерировать детальный контент (лекции и слайды)
                  </Button>
                  <Button
                    icon={<BookOutlined />}
                    loading={loadingContent}
                    onClick={() => handleViewDetailContent(module.module_number)}
                  >
                    Просмотреть детальный контент
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
                      Экспортировать детальный контент
                    </Button>
                  </Dropdown>
                </Space>
              </div>
            </Panel>
          ))}
        </Collapse>

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
                      editLessonModal.lessonIndex
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
                              <Paragraph>{slide.slide_content || slide.content}</Paragraph>
                            )}
                            {slide.code_example && (
                              <pre style={{ 
                                background: '#282c34',
                                color: '#abb2bf',
                                padding: 12, 
                                borderRadius: 4,
                                overflow: 'auto'
                              }}>
                                <code>{slide.code_example}</code>
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
                          <Paragraph>{slide.slide_content || slide.content}</Paragraph>
                        )}
                        {slide.code_example && (
                          <pre style={{ 
                            background: '#282c34',
                            color: '#abb2bf',
                            padding: 12, 
                            borderRadius: 4,
                            overflow: 'auto'
                          }}>
                            <code>{slide.code_example}</code>
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
    </div>
  )
}

export default CourseViewPage

