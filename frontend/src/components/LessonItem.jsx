import { Space, Tag, Button, Dropdown } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  MoreOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  FileAddOutlined,
  ReadOutlined
} from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { App } from 'antd'
import LessonVideoGenerator from './LessonVideoGenerator'
import LessonTestGenerator from './LessonTestGenerator'
import LessonTestEditor from './LessonTestEditor'
import LessonTestRunner from './LessonTestRunner'
import { getVideoApiUrl } from '../config/api'

const LessonItem = ({ 
  lesson, 
  index, 
  moduleNumber,
  courseId,
  contentRefreshKey = 0,
  onGenerateContent,
  onViewContent,
  onExportContent,
  onEdit,
  onDuplicate,
  onDelete,
  isGenerating
}) => {
  const { message } = App.useApp ? App.useApp() : { message: { loading: () => {}, destroy: () => {}, success: () => {}, error: () => {} } };
  const [videoInfo, setVideoInfo] = useState(null);
  const [loadingVideoInfo, setLoadingVideoInfo] = useState(false);
  const [openingVideo, setOpeningVideo] = useState(false);
  const [hasDetailContent, setHasDetailContent] = useState(false);
  const [hasTest, setHasTest] = useState(false);
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);
  const [testGeneratorVisible, setTestGeneratorVisible] = useState(false);
  const [testEditorVisible, setTestEditorVisible] = useState(false);
  const [testRunnerVisible, setTestRunnerVisible] = useState(false);
  const [currentTest, setCurrentTest] = useState(null);
  
  // Загружаем информацию о видео при монтировании
  useEffect(() => {
    if (courseId && moduleNumber !== undefined && index !== undefined) {
      loadVideoInfo();
    }
  }, [courseId, moduleNumber, index]);

  const checkDetailContent = async () => {
    try {
      if (!courseId || moduleNumber === undefined || index === undefined) return;
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const resp = await fetch(`${baseUrl}/api/courses/${courseId}/modules/${moduleNumber}/lessons/${index}/content`);
      setHasDetailContent(resp.ok);
    } catch (e) {
      setHasDetailContent(false);
    }
  };

  // Проверяем наличие детального контента для подсветки иконки
  useEffect(() => {
    checkDetailContent();
  }, [courseId, moduleNumber, index, contentRefreshKey]);

  // Проверяем наличие теста для подсветки иконки
  useEffect(() => {
    const checkTest = async () => {
      try {
        if (!courseId || moduleNumber === undefined || index === undefined) return;
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const resp = await fetch(`${baseUrl}/api/courses/${courseId}/modules/${moduleNumber}/lessons/${index}/test`);
        if (resp.ok) {
          const data = await resp.json();
          setHasTest(true);
          setCurrentTest(data.test);
        } else {
          setHasTest(false);
          setCurrentTest(null);
        }
      } catch (e) {
        setHasTest(false);
        setCurrentTest(null);
      }
    };
    checkTest();
  }, [courseId, moduleNumber, index, contentRefreshKey]);
  
  const loadVideoInfo = async () => {
    if (!courseId || courseId === null || !moduleNumber || moduleNumber === null || index === undefined || index === null) {
      console.log('Пропуск загрузки информации о видео - недостаточно данных', { courseId, moduleNumber, index });
      return;
    }
    
    setLoadingVideoInfo(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/video/lesson/${courseId}/${moduleNumber}/${index}/info`
      );
      const data = await response.json();
      console.log('Ответ API информации о видео:', data);
      
      if (data.success && data.data) {
        // Проверяем, что данные не null
        if (data.data && typeof data.data === 'object') {
          console.log('Информация о видео загружена:', data.data);
          setVideoInfo(data.data);
        } else {
          console.log('Данные о видео пустые:', data.data);
          setVideoInfo(null);
        }
      } else {
        console.log('Информация о видео не найдена для урока', courseId, moduleNumber, index, data);
        // Фоллбэк: пробуем взять сохранённый ранее статус из localStorage,
        // который кладёт LessonVideoGenerator под ключом video_status_{courseId}_{moduleNumber}_{lessonIndex}
        try {
          const cacheKey = `video_status_${courseId}_${moduleNumber}_${index}`;
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            const parsed = JSON.parse(cached);
            if (parsed && parsed.video_id) {
              console.log('Используем кэшированный video_id из localStorage:', parsed);
              setVideoInfo({
                video_id: parsed.video_id,
                video_status: parsed.status,
                video_download_url: parsed.download_url,
                video_generated_at: parsed.updated_at ? new Date(parsed.updated_at).toISOString() : undefined
              });
            } else {
              setVideoInfo(null);
            }
          } else {
            setVideoInfo(null);
          }
        } catch (e) {
          console.warn('Ошибка чтения кэша статуса видео из localStorage:', e);
          setVideoInfo(null);
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки информации о видео:', error);
      setVideoInfo(null);
    } finally {
      setLoadingVideoInfo(false);
    }
  };
  
  const handleDownloadVideo = async () => {
    console.log('handleDownloadVideo вызвана', videoInfo);
    // Перед скачиванием проверяем актуальный статус по video_id
    const readyInfo = await checkAndRefreshVideoStatus();
    if (!readyInfo?.isReady) {
      alert(readyInfo?.message || 'Видео еще не готово. Попробуйте позже.');
      return;
    }

    const downloadUrl = readyInfo.downloadUrl;
    if (!downloadUrl || downloadUrl.trim() === '') {
      console.warn('video_download_url не найден или пуст', videoInfo);
      alert('Ссылка на видео для скачивания не найдена');
      return;
    }

    try {
      console.log('Скачивание видео по URL:', downloadUrl);

      try {
        new URL(downloadUrl);
      } catch (e) {
        console.error('Некорректный URL:', downloadUrl);
        alert('Некорректная ссылка на видео');
        return;
      }

      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Accept': 'video/mp4, video/*, */*'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${lesson.lesson_title || 'lesson'}.mp4`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();

      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        try {
          document.body.removeChild(a);
        } catch (e) {
        }
      }, 100);
    } catch (error) {
      console.error('Ошибка скачивания видео:', error);
      alert(`Ошибка скачивания видео: ${error.message || 'Неизвестная ошибка'}`);
    }
  };
  
  const handleWatchVideo = async () => {
    console.log('handleWatchVideo вызвана', videoInfo);
    const readyInfo = await checkAndRefreshVideoStatus();
    if (!readyInfo?.isReady) {
      alert(readyInfo?.message || 'Видео еще не готово. Попробуйте позже.');
      return;
    }

    const watchUrl = readyInfo.downloadUrl;
    if (!watchUrl || watchUrl.trim() === '') {
      console.warn('video_download_url не найден или пуст для просмотра', videoInfo);
      alert('Ссылка на видео не найдена');
      return;
    }

    try {
      try {
        new URL(watchUrl);
      } catch (e) {
        console.error('Некорректный URL:', watchUrl);
        alert('Некорректная ссылка на видео');
        return;
      }

      console.log('Открытие видео по URL:', watchUrl);
      const newWindow = window.open(watchUrl, '_blank');
      if (!newWindow) {
        alert('Не удалось открыть видео. Возможно, браузер блокирует всплывающие окна.');
      }
    } catch (error) {
      console.error('Ошибка открытия видео:', error);
      alert(`Ошибка открытия видео: ${error.message || 'Неизвестная ошибка'}`);
    }
  };
  
  const handleRegenerateVideo = () => {
    // Открываем модальное окно генерации видео с флагом перегенерации
    // Это будет обработано в LessonVideoGenerator через пропс
  };
  const exportMenuItems = [
    {
      key: 'video',
      label: '🎬 Скачать видео (MP4)',
      onClick: () => handleDownloadVideo()
    },
    {
      type: 'divider'
    },
    {
      key: 'pptx',
      label: '📊 PowerPoint',
      onClick: () => onExportContent('pptx')
    },
    {
      key: 'html',
      label: '📄 HTML',
      onClick: () => onExportContent('html')
    },
    {
      key: 'markdown',
      label: '📝 Markdown',
      onClick: () => onExportContent('markdown')
    }
  ]

  // Хелпер: проверяет статус видео через API, при наличии video_id
  const checkAndRefreshVideoStatus = async () => {
    const videoId = videoInfo?.video_id;
    if (!videoId || String(videoId).trim() === '') {
      return { isReady: false, message: 'Видео для этого урока не найдено' };
    }

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const resp = await fetch(`${baseUrl}/api/video/status/${videoId}`);
      const json = await resp.json();
      const statusData = json?.data || {};

      // Обновляем локальный videoInfo исходя из ответа статуса
      const updated = {
        ...videoInfo,
        video_id: videoId,
        video_status: statusData.status || videoInfo?.video_status,
        video_download_url: statusData.download_url || videoInfo?.video_download_url,
      };
      setVideoInfo(updated);

      const isReady = updated.video_status === 'completed' && updated.video_download_url && updated.video_download_url.trim() !== '';
      return {
        isReady,
        downloadUrl: updated.video_download_url,
        message: isReady ? undefined : `Текущий статус видео: ${updated.video_status || 'unknown'}`
      };
    } catch (e) {
      console.error('Ошибка проверки статуса видео:', e);
      return { isReady: false, message: 'Не удалось проверить статус видео' };
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: '16px', fontWeight: 500 }}>
          {index + 1}. {lesson.lesson_title}
        </span>
        <Space size="small">
          <Button 
            type="primary"
            size="small" 
            icon={<ThunderboltOutlined />}
            loading={isGenerating}
            onClick={async () => {
              try {
                await onGenerateContent();
              } finally {
                await checkDetailContent();
              }
            }}
            title="Сгенерировать слайды"
          />
          <LessonVideoGenerator 
            lesson={lesson} 
            courseId={courseId}
            moduleNumber={moduleNumber}
            lessonIndex={index}
            onVideoGenerated={loadVideoInfo}
            onVideoStatusChange={loadVideoInfo}
          />
          {/* Кнопки для видео, если оно сгенерировано */}
          {(() => {
            // Добавляем логирование для диагностики
            if (videoInfo) {
              console.log('LessonItem videoInfo:', {
                video_status: videoInfo.video_status,
                video_download_url: videoInfo.video_download_url,
                video_id: videoInfo.video_id,
                hasUrl: !!videoInfo.video_download_url,
                urlLength: videoInfo.video_download_url?.length,
                fullVideoInfo: videoInfo
              });
            }
            
            // Показываем кнопки, если в базе есть идентификатор видео
            // Фактическую готовность проверяем при клике через статус-эндпоинт
            const showButtons = !!(videoInfo && videoInfo.video_id && String(videoInfo.video_id).trim() !== '');
            
            if (!showButtons && videoInfo) {
              console.log('Кнопки не показываются, причина:', {
                hasVideoInfo: !!videoInfo,
                status: videoInfo.video_status,
                hasUrl: !!videoInfo.video_download_url,
                urlEmpty: !videoInfo.video_download_url || videoInfo.video_download_url.trim() === '',
                fullVideoInfo: videoInfo
              });
            }
            
            return showButtons ? (
              <>
                <Button 
                  size="small" 
                  icon={<PlayCircleOutlined />}
                  loading={openingVideo}
                  onClick={async (e) => {
                    console.log('Кнопка "Смотреть" нажата', { videoInfo, event: e });
                    setOpeningVideo(true);
                    try { message.loading({ content: 'Открываем видео...', key: 'open-video-inline', duration: 0 }); } catch (_) {}
                    try {
                      await handleWatchVideo();
                    } finally {
                      setOpeningVideo(false);
                      try { message.destroy('open-video-inline'); } catch (_) {}
                    }
                  }}
                  title={`Смотреть видео (${videoInfo.video_download_url})`}
                />
              </>
            ) : null;
          })()}
          <Button 
            size="small" 
            icon={<BookOutlined />}
            onClick={onViewContent}
            disabled={!hasDetailContent}
            title={hasDetailContent ? "Просмотр детального контента" : "Недоступно: контент не сгенерирован"}
          />
          <Dropdown menu={{ items: exportMenuItems }} disabled={!hasDetailContent}>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              disabled={!hasDetailContent}
              title={hasDetailContent ? "Экспортировать контент урока" : "Экспорт недоступен: сначала сгенерируйте детальный контент"}
            />
          </Dropdown>
          {/* Иконки для работы с тестами */}
          <Button 
            type="primary"
            size="small" 
            icon={<FileAddOutlined />}
            onClick={() => setTestGeneratorVisible(true)}
            title="Сгенерировать тест"
          />
          <Button 
            size="small" 
            icon={<FileTextOutlined />}
            onClick={async () => {
              if (!currentTest) {
                try {
                  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                  const resp = await fetch(`${baseUrl}/api/courses/${courseId}/modules/${moduleNumber}/lessons/${index}/test`);
                  if (resp.ok) {
                    const data = await resp.json();
                    setCurrentTest(data.test);
                    setTestEditorVisible(true);
                  }
                } catch (e) {
                  message.error('Ошибка загрузки теста');
                }
              } else {
                setTestEditorVisible(true);
              }
            }}
            disabled={!hasTest}
            title={hasTest ? "Просмотр и редактирование теста" : "Недоступно: тест не сгенерирован"}
          />
          <Button 
            size="small" 
            icon={<CheckCircleOutlined />}
            onClick={async () => {
              if (!currentTest) {
                try {
                  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                  const resp = await fetch(`${baseUrl}/api/courses/${courseId}/modules/${moduleNumber}/lessons/${index}/test`);
                  if (resp.ok) {
                    const data = await resp.json();
                    setCurrentTest(data.test);
                    setTestRunnerVisible(true);
                  }
                } catch (e) {
                  message.error('Ошибка загрузки теста');
                }
              } else {
                setTestRunnerVisible(true);
              }
            }}
            disabled={!hasTest}
            title={hasTest ? "Пройти тест" : "Недоступно: тест не сгенерирован"}
          />
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={onEdit}
            title="Редактировать урок"
          />
          <Dropdown
            trigger={["hover"]}
            menu={{
              items: [
                {
                  key: 'duplicate',
                  label: 'Дублировать урок',
                  onClick: () => onDuplicate && onDuplicate(index, lesson)
                },
                { type: 'divider' },
                {
                  key: 'delete',
                  label: 'Удалить урок',
                  danger: true,
                  onClick: () => onDelete && onDelete(index, lesson)
                }
              ]
            }}
          >
            <Button size="small" icon={<MoreOutlined />} title="Дополнительно" />
          </Dropdown>
        </Space>
      </div>
      
      <Space direction="vertical" style={{ width: '100%', paddingLeft: 20 }}>
        <div><strong>Цель:</strong> {lesson.lesson_goal}</div>
        <div>
          <Tag color="green">{lesson.format}</Tag>
          <Tag icon={<ClockCircleOutlined />}>
            {lesson.estimated_time_minutes} мин
          </Tag>
        </div>
        <div>
          <strong>План контента:</strong>
          <ul style={{ marginTop: 8, marginBottom: 0, marginLeft: 20, paddingLeft: 20 }}>
            {lesson.content_outline.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Оценка:</strong> {lesson.assessment}
        </div>
      </Space>
      
      {/* Модальные окна для работы с тестами */}
      <LessonTestGenerator
        visible={testGeneratorVisible}
        onCancel={() => setTestGeneratorVisible(false)}
        onSuccess={(test) => {
          setHasTest(true);
          setCurrentTest(test);
          setTestGeneratorVisible(false);
        }}
        courseId={courseId}
        moduleNumber={moduleNumber}
        lessonIndex={index}
        lessonTitle={lesson.lesson_title}
      />
      
      <LessonTestEditor
        visible={testEditorVisible}
        onCancel={() => setTestEditorVisible(false)}
        onSuccess={(test) => {
          setCurrentTest(test);
          setTestEditorVisible(false);
        }}
        courseId={courseId}
        moduleNumber={moduleNumber}
        lessonIndex={index}
        test={currentTest}
      />
      
      <LessonTestRunner
        visible={testRunnerVisible}
        onCancel={() => setTestRunnerVisible(false)}
        test={currentTest}
      />
    </div>
  )
}

export default LessonItem

