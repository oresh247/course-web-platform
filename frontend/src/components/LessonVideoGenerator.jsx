import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Modal, 
  Progress, 
  Space, 
  Typography, 
  Card, 
  Select, 
  Form, 
  App,
  Alert,
  Spin,
  Input
} from 'antd';
import { 
  VideoCameraOutlined, 
  PlayCircleOutlined, 
  DownloadOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { getVideoApiUrl } from '../config/api';
import { coursesApi } from '../api/coursesApi';

const { Text, Paragraph } = Typography;
const { Option } = Select;

const LessonVideoGenerator = ({ lesson, courseId, moduleNumber, lessonIndex, onVideoGenerated, onVideoStatusChange }) => {
  const { message } = App.useApp();
  
  // Состояния для генерации видео
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [videoStatus, setVideoStatus] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  
  // Состояния для детального контента урока
  const [lessonContent, setLessonContent] = useState(null);
  const [loadingLessonContent, setLoadingLessonContent] = useState(false);
  const [lessonContentError, setLessonContentError] = useState(null);
  const [isContentFromCache, setIsContentFromCache] = useState(false);
  
  // Состояние для редактируемого скрипта
  const [videoScript, setVideoScript] = useState('');

  // Функции для работы с кэшем контента урока
  const getLessonContentCacheKey = (courseId, moduleNumber, lessonIndex) => {
    return `lesson_content_${courseId}_${moduleNumber}_${lessonIndex}`;
  };

  // === Умный индикатор (оценочный прогресс) ===
  const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
  const wordsCount = (text) => String(text || '').trim().split(/\s+/).filter(Boolean).length;
  const estimateExpectedDuration = (text) => {
    const wc = wordsCount(text);
    const speechSec = (wc / 130) * 60; // ~130 слов/мин
    const base = 25; // базовые накладные
    const k = 0.9;   // множитель
    const total = base + k * speechSec;
    return clamp(total, 30, 300);
  };
  const calcPseudoProgress = (status, apiProgress = 0) => {
    const now = Date.now();
    const started = generationStartTs || now;
    const elapsedSec = (now - started) / 1000;
    const expected = expectedDurationSec || estimateExpectedDuration(getVideoScript());
    let est = 0;
    const s = String(status || '').toLowerCase();
    if (s === 'pending' || s === 'queued') {
      est = clamp((elapsedSec / Math.max(expected * 0.15, 5)) * 15, 0, 15);
    } else if (s === 'generating' || s === 'processing' || s === 'in_progress' || s === 'working') {
      est = 15 + (elapsedSec / expected) * 80;
      est = clamp(est, 15, 95);
    } else if (s === 'completed') {
      est = 100;
    } else if (s === 'failed' || s === 'unknown_error' || s === 'api_error') {
      est = 0;
    } else {
      est = 0;
    }
    return Math.max((est | 0), (apiProgress | 0));
  };

  const getCachedLessonContent = (courseId, moduleNumber, lessonIndex) => {
    try {
      const cacheKey = getLessonContentCacheKey(courseId, moduleNumber, lessonIndex);
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const parsedCache = JSON.parse(cached);
        // Проверяем актуальность кэша (24 часа)
        const cacheAge = Date.now() - parsedCache.timestamp;
        const maxAge = 24 * 60 * 60 * 1000; // 24 часа в миллисекундах
        
        if (cacheAge < maxAge) {
          return parsedCache.content;
        } else {
          // Удаляем устаревший кэш
          localStorage.removeItem(cacheKey);
        }
      }
    } catch (error) {
      console.warn('Ошибка чтения кэша контента урока:', error);
    }
    return null;
  };

  const setCachedLessonContent = (courseId, moduleNumber, lessonIndex, content) => {
    try {
      const cacheKey = getLessonContentCacheKey(courseId, moduleNumber, lessonIndex);
      const cacheData = {
        content,
        timestamp: Date.now()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Ошибка сохранения кэша контента урока:', error);
    }
  };
  
  // Состояния для аватаров и голосов
  const [avatars, setAvatars] = useState([]);
  const [voices, setVoices] = useState([]);
  const [selectedAvatar, setSelectedAvatar] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [loadingAvatars, setLoadingAvatars] = useState(false);
  const [loadingVoices, setLoadingVoices] = useState(false);
  
  // Состояния для управления процессом
  const [generationAbortController, setGenerationAbortController] = useState(null);
  const [generationTimeout, setGenerationTimeout] = useState(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);
  // Для оценочного прогресса
  const [generationStartTs, setGenerationStartTs] = useState(null);
  const [expectedDurationSec, setExpectedDurationSec] = useState(null);
  const [isOpeningVideo, setIsOpeningVideo] = useState(false);

  // Загружаем аватары, голоса и детальный контент урока при открытии модального окна
  useEffect(() => {
    if (isModalVisible) {
      loadAvatars();
      loadVoices();
      loadLessonContent();
      loadVideoInfoFromDB();
      
      // ВСЕГДА инициализируем скрипт из плана контента урока при открытии модального окна
      // Используем план контента (content_outline) как основной источник для скрипта
      let scriptFromOutline = '';
      
      if (lesson.content_outline) {
        if (Array.isArray(lesson.content_outline) && lesson.content_outline.length > 0) {
          // Массив строк
          scriptFromOutline = lesson.content_outline.join('. ');
        } else if (typeof lesson.content_outline === 'string' && lesson.content_outline.trim()) {
          // Строка - разбиваем по переносам или разделителям
          scriptFromOutline = lesson.content_outline
            .split(/\n|,|;|\./)
            .map(item => item.trim())
            .filter(item => item.length > 0)
            .join('. ');
        }
      }
      
      if (scriptFromOutline) {
        console.log('📝 Инициализируем скрипт из плана контента при открытии модального окна:', scriptFromOutline);
        setVideoScript(scriptFromOutline);
      } else {
        // Fallback на другие источники только если content_outline недоступен
        if (!videoScript) {
          console.warn('⚠️ План контента недоступен при открытии модального окна, используем fallback');
          setVideoScript(lesson.content || lesson.lesson_content || lesson.lesson_goal || 'Содержание урока');
        }
      }
      
      // Проверяем кэшированное видео для этого урока
      checkCachedVideo();
    }
  }, [isModalVisible]);
  
  // Загружаем информацию о видео из базы данных
  const loadVideoInfoFromDB = async () => {
    if (!courseId || !moduleNumber || lessonIndex === undefined) return;
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/video/lesson/${courseId}/${moduleNumber}/${lessonIndex}/info`
      );
      const data = await response.json();
      
      if (data.success && data.data) {
        const videoData = data.data;
        if (videoData.video_status === 'completed' && videoData.video_download_url) {
          setVideoStatus({
            video_id: videoData.video_id,
            status: 'completed',
            download_url: videoData.video_download_url,
            progress: 100
          });
          setProgress(100);
        } else if (videoData.video_status === 'generating' && videoData.video_id) {
          setVideoStatus({
            video_id: videoData.video_id,
            status: 'generating',
            progress: 0
          });
          setIsGenerating(true);
          if (!generationStartTs) setGenerationStartTs(Date.now());
          if (!expectedDurationSec) setExpectedDurationSec(estimateExpectedDuration(getVideoScript()));
          trackVideoProgress(videoData.video_id);
        }
      }
    } catch (error) {
      console.warn('Ошибка загрузки информации о видео из БД:', error);
    }
  };
  
  // Функция для проверки кэшированного видео
  const checkCachedVideo = async () => {
    if (!courseId || !moduleNumber || lessonIndex === undefined) {
      return;
    }
    
    try {
      // Проверяем, есть ли уже сгенерированное видео для этого урока
      const cacheKey = `video_status_${courseId}_${moduleNumber}_${lessonIndex}`;
      const cachedStatus = localStorage.getItem(cacheKey);
      
      if (cachedStatus) {
        try {
          const parsed = JSON.parse(cachedStatus);
          if (parsed.video_id) {
            // Проверяем актуальный статус видео
            const status = await checkVideoStatus(parsed.video_id);
            if (status) {
              setVideoStatus(status);
              if (status.status === 'completed') {
                setProgress(100);
              } else if (status.status === 'generating') {
                const pseudo = calcPseudoProgress(status.status, status.progress || 0);
                setProgress(pseudo);
                setIsGenerating(true);
                if (!generationStartTs) setGenerationStartTs(Date.now());
                if (!expectedDurationSec) setExpectedDurationSec(estimateExpectedDuration(getVideoScript()));
                trackVideoProgress(status.video_id);
              }
            }
          }
        } catch (e) {
          console.warn('Ошибка парсинга кэшированного статуса:', e);
        }
      }
    } catch (error) {
      console.warn('Ошибка проверки кэшированного видео:', error);
    }
  };

  // Cleanup функция
  useEffect(() => {
    return () => {
      if (generationAbortController) {
        generationAbortController.abort();
      }
      if (generationTimeout) {
        clearTimeout(generationTimeout);
      }
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, [generationAbortController, generationTimeout, statusCheckInterval]);

  const loadLessonContent = async (forceRefresh = false) => {
    if (!courseId || !moduleNumber || lessonIndex === undefined) {
      setLessonContentError('Недостаточно данных для загрузки контента урока');
      return;
    }

    // Проверяем кэш, если не принудительное обновление
    if (!forceRefresh) {
      const cachedContent = getCachedLessonContent(courseId, moduleNumber, lessonIndex);
      if (cachedContent) {
        console.log('📦 Используем кэшированный контент урока');
        setLessonContent(cachedContent);
        setIsContentFromCache(true);
        
        // ВСЕГДА используем план контента урока (content_outline) в приоритете
        let scriptFromOutline = '';
        if (lesson.content_outline) {
          if (Array.isArray(lesson.content_outline) && lesson.content_outline.length > 0) {
            scriptFromOutline = lesson.content_outline.join('. ');
          } else if (typeof lesson.content_outline === 'string' && lesson.content_outline.trim()) {
            scriptFromOutline = lesson.content_outline
              .split(/\n|,|;|\./)
              .map(item => item.trim())
              .filter(item => item.length > 0)
              .join('. ');
          }
        }
        
        if (scriptFromOutline) {
          console.log('📝 Используем план контента для скрипта (из кэша):', scriptFromOutline);
          setVideoScript(scriptFromOutline);
        } else if (cachedContent.learning_objectives && Array.isArray(cachedContent.learning_objectives)) {
          // Fallback на цели обучения, если план контента недоступен
          console.warn('⚠️ План контента недоступен, используем цели обучения');
          setVideoScript(cachedContent.learning_objectives.join('. ') + '.');
        } else {
          console.warn('⚠️ План контента и цели обучения недоступны, используем fallback');
          setVideoScript(lesson.content || lesson.lesson_content || lesson.lesson_goal || 'Содержание урока');
        }
        return;
      }
    }

    setLoadingLessonContent(true);
    setLessonContentError(null);
    setIsContentFromCache(false);
    
    try {
      const response = await coursesApi.getLessonContent(courseId, moduleNumber, lessonIndex);
      
      if (response.status === 'found' && response.lesson_content) {
        setLessonContent(response.lesson_content);
        
        // Сохраняем в кэш
        setCachedLessonContent(courseId, moduleNumber, lessonIndex, response.lesson_content);
        
        // ВСЕГДА используем план контента урока (content_outline) в приоритете
        let scriptFromOutline = '';
        if (lesson.content_outline) {
          if (Array.isArray(lesson.content_outline) && lesson.content_outline.length > 0) {
            scriptFromOutline = lesson.content_outline.join('. ');
          } else if (typeof lesson.content_outline === 'string' && lesson.content_outline.trim()) {
            scriptFromOutline = lesson.content_outline
              .split(/\n|,|;|\./)
              .map(item => item.trim())
              .filter(item => item.length > 0)
              .join('. ');
          }
        }
        
        if (scriptFromOutline) {
          console.log('📝 Используем план контента для скрипта (с сервера):', scriptFromOutline);
          setVideoScript(scriptFromOutline);
        } else if (response.lesson_content.learning_objectives && Array.isArray(response.lesson_content.learning_objectives)) {
          // Fallback на цели обучения, если план контента недоступен
          console.warn('⚠️ План контента недоступен, используем цели обучения');
          setVideoScript(response.lesson_content.learning_objectives.join('. ') + '.');
        } else {
          console.warn('⚠️ План контента и цели обучения недоступны, используем fallback');
          setVideoScript(lesson.content || lesson.lesson_content || lesson.lesson_goal || 'Содержание урока');
        }
      } else {
        setLessonContentError('Контент урока не найден');
        setVideoScript(lesson.content || lesson.lesson_content || 'Содержание урока');
      }
    } catch (error) {
      console.error('Ошибка загрузки контента урока:', error);
      
      // Если контент урока не найден (404), используем fallback контент
      if (error.response?.status === 404) {
        setLessonContentError('Контент урока не сгенерирован. Используется базовый контент.');
        
        // ВСЕГДА инициализируем videoScript из плана контента урока
        // Приоритет: план контента (content_outline)
        let scriptFromOutline = '';
        if (lesson.content_outline) {
          if (Array.isArray(lesson.content_outline) && lesson.content_outline.length > 0) {
            scriptFromOutline = lesson.content_outline.join('. ');
          } else if (typeof lesson.content_outline === 'string' && lesson.content_outline.trim()) {
            scriptFromOutline = lesson.content_outline
              .split(/\n|,|;|\./)
              .map(item => item.trim())
              .filter(item => item.length > 0)
              .join('. ');
          }
        }
        
        if (scriptFromOutline) {
          console.log('📝 Используем план контента для скрипта (404 fallback):', scriptFromOutline);
          setVideoScript(scriptFromOutline);
        } else if (!videoScript) {
          // Fallback на другие источники только если content_outline недоступен
          console.warn('⚠️ План контента недоступен, используем fallback');
          const fallbackContent = lesson.content || 
            lesson.lesson_goal || 
            lesson.lesson_title || 
            'Содержание урока';
          setVideoScript(fallbackContent);
        }
      } else {
        setLessonContentError(error.message || 'Не удалось загрузить контент урока');
      }
    } finally {
      setLoadingLessonContent(false);
    }
  };

  const getVideoScript = () => {
    // Используем редактируемый скрипт, если он есть
    if (videoScript && videoScript.trim()) {
      return String(videoScript.trim());
    }
    
    // Приоритет: план контента урока (content_outline)
    // Обрабатываем разные форматы: массив, строка с переносами, строка с разделителями
    if (lesson.content_outline) {
      let outlineText = '';
      
      if (Array.isArray(lesson.content_outline) && lesson.content_outline.length > 0) {
        // Массив строк
        outlineText = lesson.content_outline.join('. ');
      } else if (typeof lesson.content_outline === 'string' && lesson.content_outline.trim()) {
        // Строка - разбиваем по переносам или разделителям
        outlineText = lesson.content_outline
          .split(/\n|,|;|\./)
          .map(item => item.trim())
          .filter(item => item.length > 0)
          .join('. ');
      }
      
      if (outlineText) {
        console.log('📝 Используем план контента для скрипта (getVideoScript):', outlineText);
        return String(outlineText);
      }
    }
    
    // Fallback на цели обучения из детального контента
    if (lessonContent && lessonContent.learning_objectives && Array.isArray(lessonContent.learning_objectives)) {
      console.warn('⚠️ План контента недоступен, используем цели обучения (getVideoScript)');
      return String(lessonContent.learning_objectives.join('. ') + '.');
    }
    
    // Fallback на другие источники
    console.warn('⚠️ План контента и цели обучения недоступны, используем fallback (getVideoScript)');
    const content = lesson.content || lesson.lesson_content || lesson.lesson_goal || 'Содержание урока';
    return String(content);
  };

  const loadAvatars = async () => {
    setLoadingAvatars(true);
    try {
      const response = await fetch(getVideoApiUrl('AVATARS'));
      const data = await response.json();
      
      // Проверяем разные варианты структуры ответа
      let avatarsArray = null;
      if (data.success && data.data) {
        // Если data.data - это массив
        if (Array.isArray(data.data)) {
          avatarsArray = data.data;
        } 
        // Если data.data - это объект с полем avatars
        else if (data.data.avatars && Array.isArray(data.data.avatars)) {
          avatarsArray = data.data.avatars;
        }
        // Если data.data - это объект и мы можем извлечь массив
        else if (Array.isArray(data.data.list)) {
          avatarsArray = data.data.list;
        }
      }
      
      // Фоллбек: если бэкенд уже нормализует в avatars (массив или объект)
      if (!avatarsArray && data.avatars) {
        if (Array.isArray(data.avatars)) {
          avatarsArray = data.avatars;
        } else if (typeof data.avatars === 'object') {
          // ищем первый массив в значениях объекта
          const firstArray = Object.values(data.avatars).find(v => Array.isArray(v));
          if (Array.isArray(firstArray)) avatarsArray = firstArray;
        }
      }

      if (avatarsArray && avatarsArray.length > 0) {
        setAvatars(avatarsArray);
        if (!selectedAvatar) {
          setSelectedAvatar(avatarsArray[0].avatar_id || avatarsArray[0].id || avatarsArray[0].value);
        }
      } else {
        console.warn('Аватары не найдены в ответе API:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки аватаров:', error);
      message.error('Ошибка загрузки аватаров');
    } finally {
      setLoadingAvatars(false);
    }
  };

  const loadVoices = async () => {
    setLoadingVoices(true);
    try {
      const response = await fetch(getVideoApiUrl('VOICES'));
      const data = await response.json();
      
      // Проверяем разные варианты структуры ответа
      let voicesArray = null;
      if (data.success && data.data) {
        // Если data.data - это массив
        if (Array.isArray(data.data)) {
          voicesArray = data.data;
        } 
        // Если data.data - это объект с полем list
        else if (data.data.list && Array.isArray(data.data.list)) {
          voicesArray = data.data.list;
        }
        // Если data.data - это объект с полем voices
        else if (data.data.voices && Array.isArray(data.data.voices)) {
          voicesArray = data.data.voices;
        }
      }
      
      // Фоллбек: если бэкенд уже нормализует в voices (массив или объект)
      if (!voicesArray && data.voices) {
        if (Array.isArray(data.voices)) {
          voicesArray = data.voices;
        } else if (typeof data.voices === 'object') {
          const firstArray = Object.values(data.voices).find(v => Array.isArray(v));
          if (Array.isArray(firstArray)) voicesArray = firstArray;
        }
      }

      if (voicesArray && voicesArray.length > 0) {
        setVoices(voicesArray);
        if (!selectedVoice) {
          setSelectedVoice(voicesArray[0].voice_id || voicesArray[0].id || voicesArray[0].value);
        }
      } else {
        console.warn('Голоса не найдены в ответе API:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки голосов:', error);
      message.error('Ошибка загрузки голосов');
    } finally {
      setLoadingVoices(false);
    }
  };

  const checkVideoStatus = async (videoId) => {
    try {
      const response = await fetch(`${getVideoApiUrl('STATUS')}/${videoId}`);
      const data = await response.json();
      
      if (data.success && data.data) {
        setVideoStatus(data.data);
        
        // Сохраняем статус в localStorage для этого урока
        if (courseId !== undefined && moduleNumber !== undefined && lessonIndex !== undefined) {
          const cacheKey = `video_status_${courseId}_${moduleNumber}_${lessonIndex}`;
          localStorage.setItem(cacheKey, JSON.stringify({
            video_id: videoId,
            status: data.data.status,
            progress: data.data.progress || 0,
            download_url: data.data.download_url,
            error: data.data.error,
            updated_at: Date.now()
          }));
        }
        
        return data.data;
      }
    } catch (error) {
      console.error('Ошибка проверки статуса:', error);
    }
    return null;
  };

  const trackVideoProgress = async (videoId) => {
    let attempts = 0;
    const maxAttempts = 60; // 5 минут
    
    const interval = setInterval(async () => {
      attempts++;
      
      try {
        const status = await checkVideoStatus(videoId);
        
        if (status) {
          setVideoStatus(status);
          
          // Останавливаем при ошибках
          if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error', 'unknown'].includes(status.status)) {
            clearInterval(interval);
            setStatusCheckInterval(null);
            setIsGenerating(false);
            setProgress(0);
            message.error(`Ошибка генерации: ${status.error || 'Неизвестная ошибка'}`);
            return;
          }
          
          if (status.status === 'completed') {
            setProgress(100);
            setIsGenerating(false);
            clearInterval(interval);
            setStatusCheckInterval(null);
            message.success('Видео готово!');
            onVideoGenerated?.(status);
            
            // Обновляем информацию в родительском компоненте
            if (onVideoStatusChange) {
              onVideoStatusChange(status);
            }
          } else {
            const apiProgress = typeof status.progress === 'number' ? status.progress : 0;
            const pseudo = calcPseudoProgress(status.status, apiProgress);
            setProgress(pseudo);
          }
        }
        
        if (attempts >= maxAttempts) {
          clearInterval(interval);
          setStatusCheckInterval(null);
          setIsGenerating(false);
          setProgress(0);
          message.error('Превышено время ожидания');
        }
      } catch (error) {
        console.error('Ошибка проверки статуса:', error);
        if (attempts >= 10) {
          clearInterval(interval);
          setStatusCheckInterval(null);
          setIsGenerating(false);
          setProgress(0);
          message.error('Не удается получить статус видео');
        }
      }
    }, 5000);
    
    setStatusCheckInterval(interval);
  };

  const generateVideo = async (regenerate = false) => {
    if (!selectedAvatar || !selectedVoice) {
      message.error('Выберите аватар и голос');
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setVideoStatus(null);
    setGenerationStartTs(Date.now());
    setExpectedDurationSec(estimateExpectedDuration(getVideoScript()));

    const abortController = new AbortController();
    setGenerationAbortController(abortController);

    const timeout = setTimeout(() => {
      abortController.abort();
      setIsGenerating(false);
      setProgress(0);
      message.error('Превышено время ожидания');
    }, 5 * 60 * 1000);
    setGenerationTimeout(timeout);

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/video/generate-lesson-cached?course_id=${courseId}&module_number=${moduleNumber}&lesson_index=${lessonIndex}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: String(lesson.lesson_title || lesson.title || 'Урок'),
          content: String(getVideoScript()),
          avatar_id: String(selectedAvatar),
          voice_id: String(selectedVoice),
          language: 'ru',
          quality: 'low',
          regenerate: Boolean(regenerate)
        }),
        signal: abortController.signal
      });

      const data = await response.json();
      
      if (!response.ok) {
        const errorMessage = data.detail || data.message || `HTTP ${response.status}`;
        message.error(errorMessage);
        setIsGenerating(false);
        setProgress(0);
        return;
      }
      
      if (data.success) {
        if (data.is_cached) {
          message.success('Видео найдено в кэше');
          const videoStatusData = {
            video_id: data.video_id,
            status: data.status,
            download_url: data.download_url,
            progress: data.status === 'completed' ? 100 : 0
          };
          setVideoStatus(videoStatusData);
          
          // Сохраняем статус в localStorage для этого урока
          if (courseId !== undefined && moduleNumber !== undefined && lessonIndex !== undefined) {
            const cacheKey = `video_status_${courseId}_${moduleNumber}_${lessonIndex}`;
            localStorage.setItem(cacheKey, JSON.stringify({
              ...videoStatusData,
              updated_at: Date.now()
            }));
          }
          
          if (data.status === 'completed') {
            setProgress(100);
            setIsGenerating(false);
          } else if (data.status === 'generating') {
            setProgress(calcPseudoProgress('generating', 0));
            setIsGenerating(true);
            trackVideoProgress(data.video_id);
          }
          
          // Вызываем callback для обновления списка уроков
          if (onVideoGenerated) {
            onVideoGenerated(data);
          }
        } else {
          if (data.status === 'failed') {
            const errorMsg = data.error || 'Ошибка генерации видео';
            message.error(`Ошибка генерации: ${errorMsg}`);
            setIsGenerating(false);
            setProgress(0);
          } else {
            message.success('Видео поставлено в очередь генерации');
            const videoStatusData = {
              video_id: data.video_id,
              status: data.status,
            progress: calcPseudoProgress(data.status || 'pending', 0),
              download_url: data.download_url || null
            };
            setVideoStatus(videoStatusData);
            
            // Сохраняем статус в localStorage для этого урока
            if (courseId !== undefined && moduleNumber !== undefined && lessonIndex !== undefined) {
              const cacheKey = `video_status_${courseId}_${moduleNumber}_${lessonIndex}`;
              localStorage.setItem(cacheKey, JSON.stringify({
                ...videoStatusData,
                updated_at: Date.now()
              }));
            }
            
            if (data.video_id) {
              trackVideoProgress(data.video_id);
            }
          }
        }
      } else {
        message.error('Ошибка при генерации видео');
        setIsGenerating(false);
        setProgress(0);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        message.warning('Генерация видео отменена');
      } else {
        console.error('Ошибка генерации видео:', error);
        message.error('Ошибка при генерации видео');
        setIsGenerating(false);
        setProgress(0);
      }
    } finally {
      clearTimeout(timeout);
      setGenerationTimeout(null);
      setGenerationAbortController(null);
    }
  };

  const cancelGeneration = () => {
    if (generationAbortController) {
      generationAbortController.abort();
      setGenerationAbortController(null);
    }
    if (generationTimeout) {
      clearTimeout(generationTimeout);
      setGenerationTimeout(null);
    }
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
    setIsGenerating(false);
    setProgress(0);
    message.warning('Генерация отменена');
  };

  const resetVideoState = () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
    if (generationTimeout) {
      clearTimeout(generationTimeout);
      setGenerationTimeout(null);
    }
    if (generationAbortController) {
      generationAbortController.abort();
      setGenerationAbortController(null);
    }
    setVideoStatus(null);
    setIsGenerating(false);
    setProgress(0);
    message.info('Состояние сброшено');
  };

  const downloadVideo = async () => {
    const downloadUrl = videoStatus?.download_url;
    
    if (!downloadUrl || downloadUrl.trim() === '') {
      console.warn('download_url не найден для скачивания', videoStatus);
      message.error('Ссылка на видео для скачивания не найдена');
      return;
    }
    
    try {
      console.log('Скачивание видео по URL:', downloadUrl);
      
      // Проверяем, что URL валидный
      try {
        new URL(downloadUrl);
      } catch (e) {
        console.error('Некорректный URL:', downloadUrl);
        message.error('Некорректная ссылка на видео');
        return;
      }
      
      // Используем fetch для получения файла как blob, чтобы гарантировать скачивание
      message.loading('Загрузка видео...', 0);
      
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
      
      // Освобождаем ресурсы
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        try {
          document.body.removeChild(a);
        } catch (e) {
          // Игнорируем ошибку, если элемент уже удален
        }
        message.destroy();
        message.success('Видео успешно скачано');
      }, 100);
      
    } catch (error) {
      console.error('Ошибка скачивания видео:', error);
      message.destroy();
      message.error(`Ошибка скачивания видео: ${error.message || 'Неизвестная ошибка'}`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'generating':
      case 'processing':
      case 'in_progress':
      case 'queued':
      case 'pending':
        return 'processing';
      case 'failed': 
      case 'not_found':
      case 'timeout':
      case 'connection_error':
      case 'api_error':
      case 'unknown_error':
      case 'unknown':
        return 'exception';
      default: return 'normal';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Готово';
      case 'generating':
      case 'processing':
      case 'in_progress':
      case 'queued':
      case 'pending':
        return 'Генерируется';
      case 'failed': return 'Ошибка генерации';
      case 'not_found': return 'Видео не найдено';
      case 'timeout': return 'Таймаут';
      case 'connection_error': return 'Ошибка подключения';
      case 'api_error': return 'Ошибка API';
      case 'unknown_error': return 'Неизвестная ошибка';
      case 'unknown': return 'Неизвестно';
      case 'limit_exceeded': return 'Превышен лимит HeyGen';
      default: return 'Неизвестно';
    }
  };

  const renderVideoIcon = () => {
    // Единый внешний триггер: только иконка камеры.
    // Никаких дополнительных кнопок "Смотреть/Скачать" вне модалки.
    return (
      <Button 
        type="primary" 
        size="small" 
        icon={<VideoCameraOutlined />}
        onClick={() => setIsModalVisible(true)}
        loading={!!isGenerating}
        title={isGenerating ? 'Генерация...' : 'Генерировать видео'}
      />
    );
  };

  return (
    <>
      {renderVideoIcon()}
      
      <Modal
        title={`Генерация видео: ${lesson.lesson_title}`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            Закрыть
          </Button>,
          ...(isGenerating ? [
            <Button key="stop" danger onClick={cancelGeneration}>
              <StopOutlined /> Отменить
            </Button>
          ] : [
            <Button 
              key="generate" 
              type="primary" 
              onClick={generateVideo}
              disabled={!selectedAvatar || !selectedVoice}
            >
              <VideoCameraOutlined /> Генерировать видео
            </Button>,
            <Button 
              key="regenerate" 
              type="default" 
              onClick={() => generateVideo(true)}
              disabled={!selectedAvatar || !selectedVoice}
              title="Принудительно перегенерировать видео (игнорировать кэш)"
            >
              <ReloadOutlined /> Перегенерировать
            </Button>
          ])
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Скрипт для генерации */}
          <Card 
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>Скрипт для генерации видео</span>
                {isContentFromCache && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: '#52c41a', 
                    fontWeight: 'normal',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    📦 Из кэша
                  </span>
                )}
              </div>
            } 
            size="small"
          >
            {loadingLessonContent ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Spin size="small" />
                <div style={{ marginTop: '8px' }}>
                  <Text type="secondary">Загрузка детального контента урока...</Text>
                </div>
              </div>
            ) : lessonContentError ? (
              <Alert
                message="Информация о контенте урока"
                description={lessonContentError}
                type="info"
                showIcon
                action={
                  <Button size="small" onClick={() => loadLessonContent(true)}>
                    Обновить
                  </Button>
                }
              />
            ) : (
              <div>
                {isContentFromCache && (
                  <div style={{ marginBottom: '8px', textAlign: 'right' }}>
                    <Button 
                      size="small" 
                      type="link" 
                      onClick={() => loadLessonContent(true)}
                      style={{ padding: '0', height: 'auto' }}
                    >
                      🔄 Обновить контент
                    </Button>
                  </div>
                )}
                <Input.TextArea
                  value={videoScript}
                  onChange={(e) => setVideoScript(e.target.value)}
                  placeholder="Введите текст для озвучивания видео..."
                  rows={6}
                  style={{
                    backgroundColor: '#f5f5f5',
                    border: '1px solid #d9d9d9',
                    borderRadius: '6px',
                    color: '#333333'
                  }}
                  styles={{
                    textarea: {
                      backgroundColor: '#f5f5f5 !important',
                      color: '#333333 !important',
                      borderColor: '#d9d9d9 !important'
                    }
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px', display: 'block' }}>
                  💡 Совет: Используйте короткие предложения для лучшего качества озвучивания
                </Text>
              </div>
            )}
          </Card>

          {/* Выбор аватара и голоса */}
          <Card title="Настройки видео" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>Аватар:</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="Выберите аватар"
                  value={selectedAvatar}
                  onChange={setSelectedAvatar}
                  loading={loadingAvatars}
                >
                  {avatars.map(avatar => {
                    const avatarId = avatar.avatar_id || avatar.id || avatar.value || '';
                    const avatarName = avatar.avatar_name || avatar.name || avatar.display_name || avatarId;
                    return (
                      <Option key={avatarId} value={avatarId}>
                        {avatarName}
                      </Option>
                    );
                  })}
                </Select>
              </div>
              
              <div>
                <Text strong>Голос:</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="Выберите голос"
                  value={selectedVoice}
                  onChange={setSelectedVoice}
                  loading={loadingVoices}
                >
                  {voices.map(voice => {
                    const voiceId = voice.voice_id || voice.id || voice.value || '';
                    const language = voice.language || voice.lang || 'ru';
                    const gender = voice.gender || voice.sex || '';
                    const voiceName = voice.voice_name || voice.name || voice.display_name || 
                      (language && gender ? `${language} - ${gender}` : voiceId);
                    return (
                      <Option key={voiceId} value={voiceId}>
                        {voiceName}
                      </Option>
                    );
                  })}
                </Select>
              </div>
            </Space>
          </Card>

          {/* Прогресс генерации */}
          {isGenerating && (
            <Card title="Прогресс генерации" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Progress 
                  percent={progress} 
                  status={progress === 100 ? 'success' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <Text type="secondary">
                  {progress === 100 ? 'Видео готово!' : 'Генерируется видео...'}
                </Text>
              </Space>
            </Card>
          )}

          {/* Статус видео */}
          {videoStatus && (
            <Card title="Статус видео" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Статус:</Text>
                  <Text 
                    style={{ 
                      color: getStatusColor(videoStatus.status) === 'success' ? '#52c41a' : 
                             getStatusColor(videoStatus.status) === 'exception' ? '#ff4d4f' : '#1890ff'
                    }}
                  >
                    {getStatusText(videoStatus.status)}
                  </Text>
                </div>
                
                {videoStatus.error && (
                  <Alert
                    message="Ошибка генерации"
                    description={videoStatus.error}
                    type="error"
                    showIcon
                  />
                )}
                
                {videoStatus.download_url && (
                  <Space direction="vertical" style={{ width: '100%' }} size="middle">
                    <Button 
                      type="primary" 
                      icon={<PlayCircleOutlined />}
                      loading={isOpeningVideo}
                      onClick={async () => {
                        try {
                          setIsOpeningVideo(true);
                          message.loading({ content: 'Открываем видео...', key: 'open-video', duration: 0 });
                          await new Promise(r => setTimeout(r, 300));
                          window.open(videoStatus.download_url, '_blank');
                          message.success({ content: 'Видео открыто', key: 'open-video', duration: 1.5 });
                        } catch (e) {
                          message.error({ content: 'Не удалось открыть видео', key: 'open-video' });
                        } finally {
                          setIsOpeningVideo(false);
                        }
                      }}
                      block
                    >
                      Смотреть видео
                    </Button>
                    <Button 
                      icon={<DownloadOutlined />}
                      onClick={downloadVideo}
                      block
                    >
                      Скачать видео
                    </Button>
                    <Button 
                      icon={<ReloadOutlined />}
                      onClick={() => generateVideo(true)}
                      block
                      disabled={isGenerating}
                    >
                      Перегенерировать видео
                    </Button>
                  </Space>
                )}
              </Space>
            </Card>
          )}
        </Space>
      </Modal>
    </>
  );
};

export default LessonVideoGenerator;
