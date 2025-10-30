/*
Frontend компонент для управления видео-генерацией
*/

import React, { useState, useEffect } from 'react';
import { Button, Card, Progress, Select, Space, Typography, Row, Col, Statistic, App } from 'antd';
import { PlayCircleOutlined, DownloadOutlined, ReloadOutlined, EyeOutlined, StopOutlined } from '@ant-design/icons';
import { getVideoApiUrl } from '../config/api';

const { Title, Text } = Typography;
const { Option } = Select;

const VideoGenerationPanel = ({ lesson, onVideoGenerated }) => {
  const { message } = App.useApp();
  const [videoStatus, setVideoStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [avatars, setAvatars] = useState([]);
  const [voices, setVoices] = useState([]);
  const [selectedAvatar, setSelectedAvatar] = useState('default');
  const [selectedVoice, setSelectedVoice] = useState('default');
  const [progress, setProgress] = useState(0);
  const [isRestored, setIsRestored] = useState(false);
  const [generationAbortController, setGenerationAbortController] = useState(null);
  const [generationTimeout, setGenerationTimeout] = useState(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);

  // Функции для работы с localStorage
  const getStorageKey = () => `video_status_${lesson?.id || 'default'}`;
  
  const saveVideoStatus = (status) => {
    if (status) {
      localStorage.setItem(getStorageKey(), JSON.stringify({
        ...status,
        timestamp: Date.now()
      }));
    }
  };

  const loadVideoStatus = () => {
    try {
      const saved = localStorage.getItem(getStorageKey());
      if (saved) {
        const data = JSON.parse(saved);
        // Проверяем, не устарели ли данные (старше 24 часов)
        const isExpired = Date.now() - data.timestamp > 24 * 60 * 60 * 1000;
        if (!isExpired) {
          return data;
        } else {
          // Удаляем устаревшие данные
          localStorage.removeItem(getStorageKey());
        }
      }
    } catch (error) {
      console.error('Ошибка при загрузке состояния видео:', error);
    }
    return null;
  };

  const clearVideoStatus = () => {
    localStorage.removeItem(getStorageKey());
  };

  const resetVideoState = () => {
    // Останавливаем все активные процессы
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
    clearVideoStatus();
    message.info('Состояние видео сброшено');
  };

  const cancelVideoGeneration = () => {
    // Отменяем запрос если он еще выполняется
    if (generationAbortController) {
      generationAbortController.abort();
      setGenerationAbortController(null);
    }
    
    // Очищаем таймаут
    if (generationTimeout) {
      clearTimeout(generationTimeout);
      setGenerationTimeout(null);
    }
    
    // Очищаем интервал проверки статуса
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
    
    // Используем централизованную функцию остановки
    stopGenerationImmediately('Отменено пользователем');
  };

  // Функции для кэширования аватаров и голосов
  const getAvatarsCacheKey = () => 'video_avatars_cache';
  const getVoicesCacheKey = () => 'video_voices_cache';
  const CACHE_DURATION = 30 * 60 * 1000; // 30 минут

  const saveToCache = (key, data) => {
    localStorage.setItem(key, JSON.stringify({
      data,
      timestamp: Date.now()
    }));
  };

  const loadFromCache = (key) => {
    try {
      const cached = localStorage.getItem(key);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        const isExpired = Date.now() - timestamp > CACHE_DURATION;
        if (!isExpired) {
          return data;
        } else {
          localStorage.removeItem(key);
        }
      }
    } catch (error) {
      console.error('Ошибка при загрузке кэша:', error);
    }
    return null;
  };

  useEffect(() => {
    loadAvatars();
    loadVoices();
    
    // Восстанавливаем состояние видео из localStorage
    const savedStatus = loadVideoStatus();
    if (savedStatus) {
      setVideoStatus(savedStatus);
      // Если видео все еще генерируется, продолжаем отслеживание
      if (savedStatus.status === 'generating' || savedStatus.status === 'pending') {
        setIsGenerating(true);
        if (savedStatus.video_id) {
          trackVideoProgress(savedStatus.video_id);
        }
      }
    } else if (lesson?.video?.video_id) {
      checkVideoStatus(lesson.video.video_id);
    }
    
    setIsRestored(true);
    
    // Cleanup функция для очистки таймаутов и контроллеров при размонтировании
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
  }, [lesson]);

  const loadAvatars = async () => {
    // Сначала проверяем кэш
    const cachedAvatars = loadFromCache(getAvatarsCacheKey());
    if (cachedAvatars) {
      console.log('Аватары загружены из кэша:', cachedAvatars.length);
      setAvatars(cachedAvatars);
      return;
    }

    try {
      const apiUrl = getVideoApiUrl('AVATARS');
      console.log('Загрузка аватаров с URL:', apiUrl);
      const response = await fetch(apiUrl);
      console.log('Ответ от API аватаров:', response.status);
      const data = await response.json();
      console.log('Данные аватаров:', data);
      if (data.success && data.data) {
        // Проверяем разные варианты структуры ответа
        let avatarsArray = null;
        if (Array.isArray(data.data)) {
          avatarsArray = data.data;
        } else if (data.data.avatars && Array.isArray(data.data.avatars)) {
          avatarsArray = data.data.avatars;
        } else if (Array.isArray(data.data.list)) {
          avatarsArray = data.data.list;
        }
        
        if (avatarsArray && avatarsArray.length > 0) {
          console.log('Аватары загружены:', avatarsArray.length);
          setAvatars(avatarsArray);
          saveToCache(getAvatarsCacheKey(), avatarsArray); // Сохраняем в кэш
          
          // Устанавливаем первый аватар по умолчанию, если не выбран
          if (!selectedAvatar || selectedAvatar === 'default') {
            const firstAvatarId = avatarsArray[0].avatar_id || avatarsArray[0].id || avatarsArray[0].value || '';
            if (firstAvatarId) {
              setSelectedAvatar(firstAvatarId);
            }
          }
        } else {
          console.warn('Аватары не найдены в ответе API:', data);
        }
      } else {
        console.error('Ошибка в ответе API аватаров:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки аватаров:', error);
    }
  };

  const loadVoices = async () => {
    // Сначала проверяем кэш
    const cachedVoices = loadFromCache(getVoicesCacheKey());
    if (cachedVoices) {
      console.log('Голоса загружены из кэша:', cachedVoices.length);
      setVoices(cachedVoices);
      return;
    }

    try {
      const apiUrl = getVideoApiUrl('VOICES');
      console.log('Загрузка голосов с URL:', apiUrl);
      const response = await fetch(apiUrl);
      console.log('Ответ от API голосов:', response.status);
      const data = await response.json();
      console.log('Данные голосов:', data);
      if (data.success && data.data) {
        // Проверяем разные варианты структуры ответа
        let voicesArray = null;
        if (Array.isArray(data.data)) {
          voicesArray = data.data;
        } else if (data.data.list && Array.isArray(data.data.list)) {
          voicesArray = data.data.list;
        } else if (data.data.voices && Array.isArray(data.data.voices)) {
          voicesArray = data.data.voices;
        }
        
        if (voicesArray && voicesArray.length > 0) {
          console.log('Голоса загружены:', voicesArray.length);
          setVoices(voicesArray);
          saveToCache(getVoicesCacheKey(), voicesArray); // Сохраняем в кэш
          
          // Устанавливаем первый голос по умолчанию, если не выбран
          if (!selectedVoice || selectedVoice === 'default') {
            const firstVoiceId = voicesArray[0].voice_id || voicesArray[0].id || voicesArray[0].value || '';
            if (firstVoiceId) {
              setSelectedVoice(firstVoiceId);
            }
          }
        } else {
          console.warn('Голоса не найдены в ответе API:', data);
        }
      } else {
        console.error('Ошибка в ответе API голосов:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки голосов:', error);
    }
  };

  const generateVideo = async () => {
    if (!lesson) return;

    // Создаем AbortController для возможности отмены
    const abortController = new AbortController();
    setGenerationAbortController(abortController);

    setIsGenerating(true);
    setProgress(0);

    // Устанавливаем таймаут на 5 минут
    const timeout = setTimeout(() => {
      if (isGenerating) {
        abortController.abort();
        setIsGenerating(false);
        setProgress(0);
        message.error('Генерация видео превысила время ожидания (5 минут). Попробуйте еще раз.');
        clearVideoStatus();
      }
    }, 5 * 60 * 1000); // 5 минут
    setGenerationTimeout(timeout);

    try {
      const response = await fetch(getVideoApiUrl('GENERATE_LESSON'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: lesson.title,
          content: lesson.content,
          avatar_id: selectedAvatar,
          voice_id: selectedVoice,
          language: 'ru'
        }),
        signal: abortController.signal // Добавляем сигнал для отмены
      });

      const data = await response.json();
      
      // Проверяем HTTP статус ответа
      if (!response.ok) {
        const errorMessage = data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`;
        console.error(`HTTP ошибка ${response.status}:`, errorMessage);
        message.error(errorMessage);
        setIsGenerating(false);
        setProgress(0);
        clearVideoStatus();
        return;
      }
      
      if (data.success) {
        // Проверяем статус видео в ответе
        if (data.data.video && data.data.video.status === 'failed') {
          const errorMsg = data.data.video.error || 'Ошибка генерации видео';
          message.error(`Ошибка генерации: ${errorMsg}`);
          setIsGenerating(false);
          setProgress(0);
          clearVideoStatus();
        } else {
          message.success('Видео поставлено в очередь генерации');
          setVideoStatus(data.data.video);
          saveVideoStatus(data.data.video); // Сохраняем состояние
          
          // Начинаем отслеживание прогресса
          if (data.data.video.video_id) {
            trackVideoProgress(data.data.video.video_id);
          }
          
          onVideoGenerated?.(data.data);
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
        
        // Пытаемся получить детальную информацию об ошибке
        let errorMessage = 'Ошибка при генерации видео';
        try {
          if (error.message && error.message.includes('HeyGen API limit exceeded')) {
            errorMessage = 'Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра.';
          } else if (error.message && error.message.includes('HeyGen generation failed')) {
            errorMessage = `Ошибка HeyGen: ${error.message}`;
          } else if (error.message) {
            errorMessage = error.message;
          }
        } catch (e) {
          console.error('Ошибка при обработке сообщения об ошибке:', e);
        }
        
        message.error(errorMessage);
        setIsGenerating(false);
        setProgress(0);
        clearVideoStatus();
      }
    } finally {
      // Очищаем таймаут и контроллер
      clearTimeout(timeout);
      setGenerationTimeout(null);
      setGenerationAbortController(null);
    }
  };

  const checkVideoStatus = async (videoId) => {
    try {
      console.log(`🔍 Проверяем статус видео: ${videoId}`);
      const response = await fetch(`${getVideoApiUrl('STATUS')}/${videoId}`);
      const data = await response.json();
      
      console.log(`📊 Ответ API статуса:`, data);
      
      if (data.success) {
        setVideoStatus(data.data);
        return data.data;
      } else {
        console.error(`❌ Ошибка в ответе API статуса:`, data);
        return null;
      }
    } catch (error) {
      console.error('❌ Ошибка проверки статуса:', error);
    }
    return null;
  };

  const stopGenerationImmediately = (reason = 'Остановлено') => {
    setIsGenerating(false);
    setProgress(0);
    clearVideoStatus();
    message.warning(`Генерация остановлена: ${reason}`);
  };

  const trackVideoProgress = async (videoId) => {
    let attempts = 0;
    const maxAttempts = 60; // 5 минут / 5 секунд = 60 попыток
    
    console.log(`🎬 Начинаем отслеживание прогресса видео: ${videoId}`);
    
    const interval = setInterval(async () => {
      attempts++;
      console.log(`🔄 Попытка ${attempts}/${maxAttempts} для видео ${videoId}`);
      
      try {
        const status = await checkVideoStatus(videoId);
        
        if (status) {
          console.log(`📋 Получен статус:`, status);
          setVideoStatus(status);
          saveVideoStatus(status); // Сохраняем обновленное состояние
          
          // Немедленно останавливаем генерацию при любых ошибках
          if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error', 'unknown'].includes(status.status)) {
            console.log(`🛑 Останавливаем генерацию из-за статуса: ${status.status}`);
            clearInterval(interval);
            setStatusCheckInterval(null); // Очищаем состояние интервала
            stopGenerationImmediately(getStatusText(status.status));
            return; // Выходим из функции немедленно
          }
          
          if (status.status === 'completed') {
            console.log(`✅ Видео готово!`);
            setProgress(100);
            setIsGenerating(false);
            clearInterval(interval);
            setStatusCheckInterval(null); // Очищаем состояние интервала
            message.success('Видео готово!');
          } else if (status.progress !== undefined) {
            console.log(`📈 Прогресс: ${status.progress}%`);
            setProgress(status.progress);
          }
        } else {
          console.log(`⚠️ Статус не получен для видео ${videoId}`);
        }
        
        // Если превышено максимальное количество попыток
        if (attempts >= maxAttempts) {
          console.log(`⏰ Превышено максимальное количество попыток для видео ${videoId}`);
          clearInterval(interval);
          setStatusCheckInterval(null); // Очищаем состояние интервала
          stopGenerationImmediately('Превышено время ожидания');
        }
      } catch (error) {
        console.error(`❌ Ошибка при проверке статуса видео ${videoId}:`, error);
        
        // Если ошибка повторяется несколько раз подряд, останавливаем отслеживание
        if (attempts >= 10) { // После 50 секунд ошибок
          console.log(`🛑 Останавливаем из-за повторяющихся ошибок для видео ${videoId}`);
          clearInterval(interval);
          setStatusCheckInterval(null); // Очищаем состояние интервала
          stopGenerationImmediately('Не удается получить статус видео');
        }
      }
    }, 5000); // Проверяем каждые 5 секунд
    
    // Сохраняем ID интервала для возможности его очистки
    setStatusCheckInterval(interval);
  };

  const downloadVideo = async () => {
    if (!videoStatus?.download_url) return;

    try {
      const response = await fetch(`${getVideoApiUrl('DOWNLOAD')}/${videoStatus.video_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          output_path: `./downloads/${lesson.title}_video.mp4`
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        message.success('Видео скачано');
      } else {
        message.error('Ошибка при скачивании');
      }
    } catch (error) {
      console.error('Ошибка скачивания:', error);
      message.error('Ошибка при скачивании');
    }
  };

  const retryGeneration = async () => {
    await generateVideo();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'generating': return 'processing';
      case 'failed': 
      case 'not_found':
      case 'timeout':
      case 'connection_error':
      case 'api_error':
      case 'unknown_error':
      case 'unknown':
        return 'exception';
      case 'pending': return 'warning';
      default: return 'normal';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Готово';
      case 'generating': return 'Генерируется';
      case 'failed': return 'Ошибка генерации';
      case 'not_found': return 'Видео не найдено';
      case 'timeout': return 'Таймаут';
      case 'connection_error': return 'Ошибка подключения';
      case 'api_error': return 'Ошибка API';
      case 'unknown_error': return 'Неизвестная ошибка';
      case 'limit_exceeded': return 'Превышен лимит HeyGen';
      case 'pending': return 'Ожидание';
      default: return 'Неизвестно';
    }
  };

  return (
    <Card 
      title={
        <Space>
          <PlayCircleOutlined />
          <span>Видео-контент урока</span>
        </Space>
      }
      extra={
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={retryGeneration}
            disabled={isGenerating}
          >
            Пересоздать
          </Button>
        </Space>
      }
    >
      <Row gutter={[16, 16]}>
        {/* Настройки генерации */}
        <Col span={24}>
          <Title level={5}>Настройки видео</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>Аватар:</Text>
              <Select
                value={selectedAvatar}
                onChange={setSelectedAvatar}
                style={{ width: 200, marginLeft: 8 }}
                disabled={isGenerating}
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
                value={selectedVoice}
                onChange={setSelectedVoice}
                style={{ width: 200, marginLeft: 8 }}
                disabled={isGenerating}
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
        </Col>

        {/* Статус видео */}
        {videoStatus && (
          <Col span={24}>
            <Title level={5}>Статус генерации</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Статус: </Text>
                <Text type={getStatusColor(videoStatus.status)}>
                  {getStatusText(videoStatus.status)}
                </Text>
              </div>
              
              {videoStatus.status === 'generating' && (
                <div>
                  <Text strong>Прогресс: </Text>
                  <Progress 
                    percent={progress} 
                    status={getStatusColor(videoStatus.status)}
                    style={{ width: 200 }}
                  />
                </div>
              )}
              
              {videoStatus.duration && (
                <div>
                  <Text strong>Длительность: </Text>
                  <Text>{Math.round(videoStatus.duration / 60)} мин</Text>
                </div>
              )}
              
              {videoStatus.file_size && (
                <div>
                  <Text strong>Размер файла: </Text>
                  <Text>{(videoStatus.file_size / 1024 / 1024).toFixed(2)} MB</Text>
                </div>
              )}
              
              {/* Детальная информация об ошибках */}
              {['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error'].includes(videoStatus.status) && (
                <Card 
                  size="small" 
                  style={{ 
                    backgroundColor: '#2a1a1a',
                    border: '1px solid #5c2626'
                  }}
                >
                  <Title level={6} style={{ color: '#ff4d4f', margin: 0 }}>
                    Детали ошибки:
                  </Title>
                  <Text 
                    style={{ 
                      color: '#ff7875',
                      fontSize: '12px',
                      display: 'block',
                      marginTop: '8px'
                    }}
                  >
                    {videoStatus.error || 'Нет дополнительной информации об ошибке'}
                  </Text>
                  {videoStatus.error_code && (
                    <Text 
                      style={{ 
                        color: '#ff9c9c',
                        fontSize: '11px',
                        display: 'block',
                        marginTop: '4px',
                        fontFamily: 'monospace'
                      }}
                    >
                      Код ошибки: {videoStatus.error_code}
                    </Text>
                  )}
                  {videoStatus.error_details && (
                    <Text 
                      style={{ 
                        color: '#ff9c9c',
                        fontSize: '11px',
                        display: 'block',
                        marginTop: '4px',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap'
                      }}
                    >
                      {JSON.stringify(videoStatus.error_details, null, 2)}
                    </Text>
                  )}
                </Card>
              )}
            </Space>
          </Col>
        )}

        {/* Действия */}
        <Col span={24}>
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={generateVideo}
              loading={isGenerating}
              disabled={!lesson}
            >
              {videoStatus ? 'Пересоздать видео' : 'Создать видео'}
            </Button>
            
            {isGenerating && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={cancelVideoGeneration}
              >
                Отменить генерацию
              </Button>
            )}
            
            {videoStatus && (
              <Button
                icon={<ReloadOutlined />}
                onClick={resetVideoState}
                disabled={isGenerating}
              >
                Сбросить состояние
              </Button>
            )}
            
            {videoStatus?.video_id && (
              <Button
                icon={<EyeOutlined />}
                onClick={() => {
                  console.log('🔍 Проверяем статус вручную для видео:', videoStatus.video_id);
                  checkVideoStatus(videoStatus.video_id);
                }}
                disabled={isGenerating}
              >
                Проверить статус
              </Button>
            )}
            
            {videoStatus?.status === 'completed' && (
              <Button
                icon={<DownloadOutlined />}
                onClick={downloadVideo}
              >
                Скачать видео
              </Button>
            )}
            
            {videoStatus?.download_url && (
              <Button
                icon={<EyeOutlined />}
                href={videoStatus.download_url}
                target="_blank"
              >
                Предварительный просмотр
              </Button>
            )}
          </Space>
        </Col>

        {/* Скрипт видео */}
        {videoStatus?.script && (
          <Col span={24}>
            <Title level={5}>Скрипт видео</Title>
            <Card 
              size="small" 
              style={{ 
                backgroundColor: '#1a1a1a',
                border: '1px solid #2a2a2a'
              }}
            >
              <Text 
                style={{ 
                  fontFamily: 'monospace', 
                  fontSize: '12px',
                  color: '#ffffff',
                  backgroundColor: '#0a0a0a',
                  padding: '8px',
                  borderRadius: '4px',
                  display: 'block',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}
              >
                {videoStatus.script}
              </Text>
            </Card>
          </Col>
        )}
      </Row>
    </Card>
  );
};

export default VideoGenerationPanel;
