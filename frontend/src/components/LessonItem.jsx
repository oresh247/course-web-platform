import { Space, Tag, Button, Dropdown } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useState, useEffect } from 'react'
import LessonVideoGenerator from './LessonVideoGenerator'
import { getVideoApiUrl } from '../config/api'

const LessonItem = ({ 
  lesson, 
  index, 
  moduleNumber,
  courseId,
  onGenerateContent,
  onViewContent,
  onExportContent,
  onEdit,
  isGenerating
}) => {
  const [videoInfo, setVideoInfo] = useState(null);
  const [loadingVideoInfo, setLoadingVideoInfo] = useState(false);
  
  // Загружаем информацию о видео при монтировании
  useEffect(() => {
    if (courseId && moduleNumber !== undefined && index !== undefined) {
      loadVideoInfo();
    }
  }, [courseId, moduleNumber, index]);
  
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
  
  const handleWatchVideo = () => {
    console.log('handleWatchVideo вызвана', videoInfo);
    // Перед просмотром проверяем актуальный статус по video_id
    checkAndRefreshVideoStatus().then((readyInfo) => {
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
    });
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
            onClick={onGenerateContent}
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
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={(e) => {
                    console.log('Кнопка "Смотреть" нажата', { videoInfo, event: e });
                    handleWatchVideo();
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
            title="Просмотр детального контента"
          />
          <Dropdown menu={{ items: exportMenuItems }}>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              title="Экспортировать контент урока"
            />
          </Dropdown>
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={onEdit}
            title="Редактировать урок"
          />
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
    </div>
  )
}

export default LessonItem

