import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Spin,
  Typography,
  Button,
  Space,
  Collapse,
  Form,
  Input,
  InputNumber,
  Select,
  App,
  Empty,
  List,
  Modal,
  Progress,
  Tag,
} from 'antd'
import {
  ArrowLeftOutlined,
  SaveOutlined,
  ThunderboltOutlined,
  VideoCameraOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { coursesApi } from '../api/coursesApi'
import { getVideoApiUrl } from '../config/api'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select

const SLIDE_TYPES = [
  { value: 'title', label: 'Титульный' },
  { value: 'content', label: 'Контент' },
  { value: 'code', label: 'Код' },
  { value: 'diagram', label: 'Диаграмма' },
  { value: 'quiz', label: 'Викторина' },
  { value: 'summary', label: 'Итоги' },
]

// Значения по умолчанию для HeyGen, если API аватаров/голосов недоступен
const DEFAULT_AVATAR_ID = 'Abigail_expressive_2024112501'
const DEFAULT_VOICE_ID = '9799f1ba6acd4b2b993fe813a18f9a91'
const FALLBACK_AVATARS = [{ avatar_id: DEFAULT_AVATAR_ID, name: 'Abigail (по умолчанию)' }]
const FALLBACK_VOICES = [{ voice_id: DEFAULT_VOICE_ID, name: 'Русский голос (по умолчанию)' }]

const POLL_INTERVAL_MS = 4000
const MAX_POLL_ATTEMPTS = 120

/** Преобразует литеральные \n в строке в реальные переносы строк для отображения в TextArea */
function displayMultiline(str) {
  if (str == null || str === '') return ''
  return String(str).replace(/\\n/g, '\n')
}

function CourseContentEditorPage() {
  const { message } = App.useApp()
  const { id } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedLesson, setSelectedLesson] = useState(null)
  const [lessonContent, setLessonContent] = useState(null)
  const [contentLoading, setContentLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [generatingContent, setGeneratingContent] = useState(false)
  const [form] = Form.useForm()
  const [slideVideoModal, setSlideVideoModal] = useState({
    open: false,
    slideIndex: null,
    slideTitle: '',
    script: '',
    generating: false,
    videoId: null,
    progress: 0,
  })
  const [avatars, setAvatars] = useState(FALLBACK_AVATARS)
  const [voices, setVoices] = useState(FALLBACK_VOICES)
  const [selectedAvatar, setSelectedAvatar] = useState(DEFAULT_AVATAR_ID)
  const [selectedVoice, setSelectedVoice] = useState(DEFAULT_VOICE_ID)
  const [loadingAvatarsVoices, setLoadingAvatarsVoices] = useState(false)

  const courseId = id ? parseInt(id, 10) : null

  const loadCourse = useCallback(async () => {
    if (!courseId || isNaN(courseId)) {
      setLoading(false)
      navigate('/courses')
      return
    }
    setLoading(true)
    try {
      const res = await coursesApi.getCourse(courseId)
      if (res?.course) setCourse(res.course)
      else throw new Error('Курс не найден')
    } catch (e) {
      console.error(e)
      message.error('Ошибка загрузки курса')
      setCourse(null)
      navigate('/courses')
    } finally {
      setLoading(false)
    }
  }, [courseId, navigate, message])

  useEffect(() => {
    loadCourse()
  }, [loadCourse])

  const loadLessonContent = useCallback(async () => {
    if (!courseId || selectedLesson == null) return
    const { moduleNumber, lessonIndex } = selectedLesson
    setContentLoading(true)
    try {
      const res = await coursesApi.getLessonContent(courseId, moduleNumber, lessonIndex)
      const content = res?.lesson_content
      setLessonContent(content || null)
      if (content) {
        form.setFieldsValue({
          lecture_title: content.lecture_title ?? '',
          duration_minutes: content.duration_minutes ?? 45,
          learning_objectives: content.learning_objectives ?? [],
          key_takeaways: content.key_takeaways ?? [],
        })
      } else {
        form.resetFields()
      }
    } catch (e) {
      if (e.response?.status === 404) {
        setLessonContent(null)
        form.resetFields()
      } else {
        message.error('Ошибка загрузки контента урока')
      }
    } finally {
      setContentLoading(false)
    }
  }, [courseId, selectedLesson, form, message])

  useEffect(() => {
    if (selectedLesson != null) loadLessonContent()
    else setLessonContent(null)
  }, [selectedLesson, loadLessonContent])

  const loadAvatarsAndVoices = useCallback(async () => {
    setLoadingAvatarsVoices(true)
    try {
      const [avatarsResponse, voicesResponse] = await Promise.all([
        fetch(getVideoApiUrl('AVATARS')),
        fetch(getVideoApiUrl('VOICES')),
      ])
      const avatarsData = await avatarsResponse.json()
      const voicesData = await voicesResponse.json()

      let avatarsList = null
      if (avatarsData.success && avatarsData.data) {
        if (Array.isArray(avatarsData.data)) avatarsList = avatarsData.data
        else if (Array.isArray(avatarsData.data?.avatars)) avatarsList = avatarsData.data.avatars
        else if (Array.isArray(avatarsData.data?.list)) avatarsList = avatarsData.data.list
      }
      if (!avatarsList && avatarsData.avatars) {
        if (Array.isArray(avatarsData.avatars)) avatarsList = avatarsData.avatars
        else if (typeof avatarsData.avatars === 'object') {
          const first = Object.values(avatarsData.avatars).find((v) => Array.isArray(v))
          if (Array.isArray(first)) avatarsList = first
        }
      }
      if (Array.isArray(avatarsList) && avatarsList.length > 0) {
        setAvatars(avatarsList)
        const first = avatarsList[0]
        setSelectedAvatar(first?.avatar_id ?? first?.id ?? first?.value ?? DEFAULT_AVATAR_ID)
      } else {
        setAvatars(FALLBACK_AVATARS)
        setSelectedAvatar(DEFAULT_AVATAR_ID)
      }

      let voicesList = null
      if (voicesData.success && voicesData.data) {
        if (Array.isArray(voicesData.data)) voicesList = voicesData.data
        else if (Array.isArray(voicesData.data?.list)) voicesList = voicesData.data.list
        else if (Array.isArray(voicesData.data?.voices)) voicesList = voicesData.data.voices
      }
      if (!voicesList && voicesData.voices) {
        if (Array.isArray(voicesData.voices)) voicesList = voicesData.voices
        else if (typeof voicesData.voices === 'object') {
          const first = Object.values(voicesData.voices).find((v) => Array.isArray(v))
          if (Array.isArray(first)) voicesList = first
        }
      }
      if (Array.isArray(voicesList) && voicesList.length > 0) {
        setVoices(voicesList)
        const first = voicesList[0]
        setSelectedVoice(first?.voice_id ?? first?.id ?? first?.value ?? DEFAULT_VOICE_ID)
      } else {
        setVoices(FALLBACK_VOICES)
        setSelectedVoice(DEFAULT_VOICE_ID)
      }
    } catch (e) {
      console.warn('Не удалось загрузить аватары/голоса, используются значения по умолчанию:', e)
      setAvatars(FALLBACK_AVATARS)
      setVoices(FALLBACK_VOICES)
      setSelectedAvatar(DEFAULT_AVATAR_ID)
      setSelectedVoice(DEFAULT_VOICE_ID)
    } finally {
      setLoadingAvatarsVoices(false)
    }
  }, [])

  useEffect(() => {
    if (slideVideoModal.open) loadAvatarsAndVoices()
  }, [slideVideoModal.open, loadAvatarsAndVoices])

  const handleGenerateContent = async () => {
    if (!courseId || selectedLesson == null) return
    const { moduleNumber, lessonIndex } = selectedLesson
    setGeneratingContent(true)
    try {
      await coursesApi.generateLessonDetailedContent(courseId, moduleNumber, lessonIndex)
      message.success('Контент урока сгенерирован')
      await loadLessonContent()
    } catch (e) {
      message.error(e.response?.data?.detail || 'Ошибка генерации контента')
    } finally {
      setGeneratingContent(false)
    }
  }

  const handleSave = async () => {
    if (!courseId || selectedLesson == null || !lessonContent?.slides) return
    const { moduleNumber, lessonIndex } = selectedLesson
    const values = form.getFieldsValue()
    const slides = lessonContent.slides.map((s, i) => ({
      slide_number: i + 1,
      title: s.title ?? '',
      content: s.content ?? '',
      slide_type: s.slide_type ?? 'content',
      code_example: s.code_example ?? null,
      notes: s.notes ?? null,
      video_id: s.video_id ?? undefined,
      video_status: s.video_status ?? undefined,
      video_download_url: s.video_download_url ?? undefined,
    }))
    const body = {
      lecture_title: values.lecture_title ?? lessonContent.lecture_title,
      duration_minutes: values.duration_minutes ?? 45,
      learning_objectives: Array.isArray(values.learning_objectives) ? values.learning_objectives : (lessonContent.learning_objectives ?? []),
      key_takeaways: Array.isArray(values.key_takeaways) ? values.key_takeaways : (lessonContent.key_takeaways ?? []),
      slides,
    }
    setSaving(true)
    try {
      await coursesApi.updateLessonContent(courseId, moduleNumber, lessonIndex, body)
      message.success('Контент сохранён')
      setLessonContent((prev) => ({ ...prev, ...body, slides }))
    } catch (e) {
      message.error(e.response?.data?.detail || 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const openSlideVideoModal = (slideIndex) => {
    const slides = lessonContent?.slides ?? []
    const slide = slides[slideIndex]
    if (!slide) return
    const script = [slide.title, slide.content].filter(Boolean).join('\n\n').trim() || 'Текст слайда'
    setSlideVideoModal({
      open: true,
      slideIndex,
      slideTitle: slide.title || `Слайд ${slideIndex + 1}`,
      script,
      generating: false,
      videoId: null,
      progress: 0,
    })
  }

  const startSlideVideoGeneration = async () => {
    const { slideIndex, script } = slideVideoModal
    if (!courseId || selectedLesson == null || slideIndex == null) return
    const { moduleNumber, lessonIndex } = selectedLesson
    const content = (script || '').trim().slice(0, 2000)
    if (!content) {
      message.warning('Введите текст для озвучивания')
      return
    }
    setSlideVideoModal((m) => ({ ...m, generating: true, progress: 10 }))
    try {
      const res = await coursesApi.generateSlideVideo(courseId, moduleNumber, lessonIndex, slideIndex, {
        title: slideVideoModal.slideTitle,
        content,
        avatar_id: selectedAvatar || DEFAULT_AVATAR_ID,
        voice_id: selectedVoice || DEFAULT_VOICE_ID,
        language: 'ru',
        quality: 'low',
        regenerate: false,
      })
      if (!res?.success) {
        message.error(res?.message || res?.error || 'Ошибка генерации видео')
        setSlideVideoModal((m) => ({ ...m, generating: false }))
        return
      }
      const videoId = res.video_id
      setSlideVideoModal((m) => ({ ...m, videoId, progress: 30 }))
      let attempts = 0
      const poll = async () => {
        if (attempts >= MAX_POLL_ATTEMPTS) {
          message.warning('Превышено время ожидания генерации видео')
          setSlideVideoModal((m) => ({ ...m, generating: false }))
          return
        }
        try {
          const statusRes = await coursesApi.getVideoStatus(videoId)
          const status = statusRes?.data?.status || statusRes?.status
          setSlideVideoModal((m) => ({
            ...m,
            progress: status === 'completed' ? 100 : Math.min(30 + (attempts * 2), 95),
          }))
          if (status === 'completed') {
            message.success('Видео для слайда готово')
            setSlideVideoModal((m) => ({ ...m, generating: false, progress: 100 }))
            loadLessonContent()
            return
          }
          if (status === 'failed' || status === 'error') {
            message.error(statusRes?.data?.error || 'Генерация видео завершилась с ошибкой')
            setSlideVideoModal((m) => ({ ...m, generating: false }))
            return
          }
        } catch (_) {}
        attempts++
        setTimeout(poll, POLL_INTERVAL_MS)
      }
      setTimeout(poll, POLL_INTERVAL_MS)
    } catch (e) {
      message.error(e.response?.data?.detail || e.message || 'Ошибка запроса генерации видео')
      setSlideVideoModal((m) => ({ ...m, generating: false }))
    }
  }

  const updateSlide = (slideIndex, field, value) => {
    setLessonContent((prev) => {
      if (!prev?.slides) return prev
      const slides = [...prev.slides]
      const slide = { ...(slides[slideIndex] || {}), [field]: value }
      slides[slideIndex] = slide
      return { ...prev, slides }
    })
  }

  const addSlide = () => {
    setLessonContent((prev) => {
      const slides = [...(prev?.slides || [])]
      slides.push({
        slide_number: slides.length + 1,
        title: '',
        content: '',
        slide_type: 'content',
        code_example: null,
        notes: null,
      })
      return { ...prev, slides }
    })
  }

  const removeSlide = (slideIndex) => {
    setLessonContent((prev) => {
      const slides = (prev?.slides || []).filter((_, i) => i !== slideIndex)
      slides.forEach((s, i) => { s.slide_number = i + 1 })
      return { ...prev, slides }
    })
  }

  const getLessonTitle = (moduleNumber, lessonIndex) => {
    const mod = course?.modules?.find((m) => Number(m.module_number) === Number(moduleNumber))
    const lesson = mod?.lessons?.[lessonIndex]
    return lesson?.lesson_title ?? `Урок ${lessonIndex + 1}`
  }

  if (loading || !course) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Space>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/courses/${courseId}`)}>
          К курсу
        </Button>
        <Title level={4} style={{ margin: 0 }}>
          Редактор контента: {course.course_title}
        </Title>
      </Space>

      <div style={{ display: 'flex', gap: 24, minHeight: 500 }}>
        {/* Левая панель: дерево уроков */}
        <Card style={{ width: 280, flexShrink: 0 }} bodyStyle={{ padding: 12 }}>
          <Typography.Text strong>Уроки</Typography.Text>
          <Collapse
            ghost
            style={{ marginTop: 8 }}
            items={course.modules?.map((mod, modIdx) => ({
              key: mod.module_number,
              label: `Модуль ${mod.module_number}: ${mod.module_title || ''}`,
              children: (
                <List
                  size="small"
                  dataSource={mod.lessons || []}
                  renderItem={(lesson, lessonIdx) => {
                    const isSelected =
                      selectedLesson?.moduleNumber === mod.module_number &&
                      selectedLesson?.lessonIndex === lessonIdx
                    return (
                      <List.Item
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? 'rgba(94, 138, 48, 0.2)' : undefined,
                          borderRadius: 4,
                          padding: '4px 8px',
                        }}
                        onClick={() =>
                          setSelectedLesson({
                            moduleNumber: mod.module_number,
                            lessonIndex: lessonIdx,
                          })
                        }
                      >
                        <Text ellipsis>{lesson.lesson_title || `Урок ${lessonIdx + 1}`}</Text>
                      </List.Item>
                    )
                  }}
                />
              ),
            }))}
          />
        </Card>

        {/* Правая панель: редактор */}
        <Card style={{ flex: 1 }} bodyStyle={{ padding: 24 }}>
          {selectedLesson == null ? (
            <Empty description="Выберите урок слева" />
          ) : contentLoading ? (
            <Spin />
          ) : !lessonContent ? (
            <Space direction="vertical">
              <Text>Контент урока ещё не сгенерирован.</Text>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                loading={generatingContent}
                onClick={handleGenerateContent}
              >
                Сгенерировать контент
              </Button>
            </Space>
          ) : (
            <>
              <Form form={form} layout="vertical" style={{ marginBottom: 24 }}>
                <Form.Item name="lecture_title" label="Название лекции">
                  <Input
                    onChange={(e) =>
                      setLessonContent((p) => ({ ...p, lecture_title: e.target.value }))
                    }
                  />
                </Form.Item>
                <Form.Item name="duration_minutes" label="Длительность (мин)">
                  <InputNumber
                    min={15}
                    max={240}
                    style={{ width: 120 }}
                    onChange={(v) =>
                      setLessonContent((p) => ({ ...p, duration_minutes: v ?? 45 }))
                    }
                  />
                </Form.Item>
                <Form.Item name="learning_objectives" label="Цели обучения">
                  <Select
                    mode="tags"
                    placeholder="Добавьте цели"
                    onChange={(v) =>
                      setLessonContent((p) => ({ ...p, learning_objectives: v || [] }))
                    }
                  />
                </Form.Item>
                <Form.Item name="key_takeaways" label="Ключевые выводы">
                  <Select
                    mode="tags"
                    placeholder="Добавьте выводы"
                    onChange={(v) =>
                      setLessonContent((p) => ({ ...p, key_takeaways: v || [] }))
                    }
                  />
                </Form.Item>
              </Form>

              <Title level={5}>Слайды</Title>
              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={addSlide}
                style={{ marginBottom: 16 }}
              >
                Добавить слайд
              </Button>

              <List
                dataSource={lessonContent.slides || []}
                renderItem={(slide, slideIndex) => (
                  <Card
                    key={slideIndex}
                    size="small"
                    style={{ marginBottom: 12 }}
                    title={
                      <Space>
                        <EditOutlined />
                        Слайд {slideIndex + 1}
                        {(slide.video_status === 'completed' && slide.video_download_url) && (
                          <Tag color="green">Видео готово</Tag>
                        )}
                        {(slide.video_status === 'generating' || slide.video_status === 'pending') && (
                          <Tag color="blue">Генерация...</Tag>
                        )}
                      </Space>
                    }
                    extra={
                      <Space>
                        <Button
                          size="small"
                          type="primary"
                          icon={<VideoCameraOutlined />}
                          onClick={() => openSlideVideoModal(slideIndex)}
                        >
                          Видео
                        </Button>
                        <Button
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => removeSlide(slideIndex)}
                        />
                      </Space>
                    }
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Input
                        placeholder="Заголовок слайда"
                        value={slide.title}
                        onChange={(e) => updateSlide(slideIndex, 'title', e.target.value)}
                      />
                      <TextArea
                        placeholder="Текст слайда"
                        rows={3}
                        value={displayMultiline(slide.content)}
                        onChange={(e) => updateSlide(slideIndex, 'content', e.target.value)}
                      />
                      <Select
                        style={{ width: 160 }}
                        placeholder="Тип слайда"
                        value={slide.slide_type || 'content'}
                        onChange={(v) => updateSlide(slideIndex, 'slide_type', v)}
                        options={SLIDE_TYPES}
                      />
                      {(slide.slide_type === 'code' || slide.code_example) && (
                        <TextArea
                          placeholder="Пример кода"
                          rows={2}
                          value={displayMultiline(slide.code_example || '')}
                          onChange={(e) => updateSlide(slideIndex, 'code_example', e.target.value)}
                        />
                      )}
                      <TextArea
                        placeholder="Заметки для преподавателя"
                        rows={1}
                        value={slide.notes || ''}
                        onChange={(e) => updateSlide(slideIndex, 'notes', e.target.value)}
                      />
                      {slide.video_status === 'completed' && slide.video_download_url && (
                        <Space>
                          <a
                            href={slide.video_download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#5E8A30' }}
                          >
                            <PlayCircleOutlined /> Открыть видео
                          </a>
                          <a
                            href={slide.video_download_url}
                            download
                            style={{ color: '#5E8A30' }}
                          >
                            <DownloadOutlined /> Скачать
                          </a>
                        </Space>
                      )}
                    </Space>
                  </Card>
                )}
              />

              <div style={{ marginTop: 24 }}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={saving}
                  onClick={handleSave}
                >
                  Сохранить контент
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>

      <Modal
        title={`Видео для слайда: ${slideVideoModal.slideTitle}`}
        open={slideVideoModal.open}
        onCancel={() => {
          if (!slideVideoModal.generating) setSlideVideoModal((m) => ({ ...m, open: false }))
        }}
        footer={[
          <Button key="cancel" onClick={() => setSlideVideoModal((m) => ({ ...m, open: false }))}>
            Закрыть
          </Button>,
          <Button
            key="generate"
            type="primary"
            loading={slideVideoModal.generating}
            icon={<VideoCameraOutlined />}
            onClick={startSlideVideoGeneration}
          >
            Сгенерировать видео
          </Button>,
        ]}
        width={560}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Текст для озвучивания (HeyGen):</Text>
          <TextArea
            rows={6}
            value={slideVideoModal.script}
            onChange={(e) =>
              setSlideVideoModal((m) => ({ ...m, script: e.target.value }))
            }
            placeholder="Скрипт для видео..."
          />
          <Text strong>Аватар:</Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Выберите аватар"
            value={selectedAvatar || DEFAULT_AVATAR_ID}
            onChange={setSelectedAvatar}
            loading={loadingAvatarsVoices}
          >
            {avatars.map((avatar) => {
              const avatarId = avatar.avatar_id ?? avatar.id ?? avatar.value ?? DEFAULT_AVATAR_ID
              const avatarName = avatar.avatar_name ?? avatar.name ?? avatar.display_name ?? avatarId
              return (
                <Option key={avatarId} value={avatarId}>
                  {avatarName}
                </Option>
              )
            })}
          </Select>
          <Text strong>Голос:</Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Выберите голос"
            value={selectedVoice || DEFAULT_VOICE_ID}
            onChange={setSelectedVoice}
            loading={loadingAvatarsVoices}
          >
            {voices.map((voice) => {
              const voiceId = voice.voice_id ?? voice.id ?? voice.value ?? DEFAULT_VOICE_ID
              const language = voice.language ?? voice.lang ?? 'ru'
              const gender = voice.gender ?? voice.sex ?? ''
              const voiceName = voice.voice_name ?? voice.name ?? voice.display_name ??
                (language && gender ? `${language} - ${gender}` : voiceId)
              return (
                <Option key={voiceId} value={voiceId}>
                  {voiceName}
                </Option>
              )
            })}
          </Select>
          {slideVideoModal.generating && (
            <Progress percent={slideVideoModal.progress} status="active" />
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default CourseContentEditorPage
