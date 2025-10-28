/*
Frontend компонент для управления видео-генерацией
*/

import React, { useState, useEffect } from 'react';
import { Button, Card, Progress, Select, message, Space, Typography, Row, Col, Statistic } from 'antd';
import { PlayCircleOutlined, DownloadOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const VideoGenerationPanel = ({ lesson, onVideoGenerated }) => {
  const [videoStatus, setVideoStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [avatars, setAvatars] = useState([]);
  const [voices, setVoices] = useState([]);
  const [selectedAvatar, setSelectedAvatar] = useState('default');
  const [selectedVoice, setSelectedVoice] = useState('default');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    loadAvatars();
    loadVoices();
    if (lesson?.video?.video_id) {
      checkVideoStatus(lesson.video.video_id);
    }
  }, [lesson]);

  const loadAvatars = async () => {
    try {
      console.log('Загрузка аватаров...');
      const response = await fetch('http://localhost:8000/api/video/avatars');
      console.log('Ответ от API аватаров:', response.status);
      const data = await response.json();
      console.log('Данные аватаров:', data);
      if (data.success) {
        console.log('Аватары загружены:', data.data.avatars?.length || 0);
        setAvatars(data.data.avatars || []);
      } else {
        console.error('Ошибка в ответе API аватаров:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки аватаров:', error);
    }
  };

  const loadVoices = async () => {
    try {
      console.log('Загрузка голосов...');
      const response = await fetch('http://localhost:8000/api/video/voices');
      console.log('Ответ от API голосов:', response.status);
      const data = await response.json();
      console.log('Данные голосов:', data);
      if (data.success) {
        console.log('Голоса загружены:', data.data.list?.length || 0);
        setVoices(data.data.list || []);
      } else {
        console.error('Ошибка в ответе API голосов:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки голосов:', error);
    }
  };

  const generateVideo = async () => {
    if (!lesson) return;

    setIsGenerating(true);
    setProgress(0);

    try {
      const response = await fetch('http://localhost:8000/api/video/generate-lesson', {
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
      });

      const data = await response.json();
      
      if (data.success) {
        message.success('Видео поставлено в очередь генерации');
        setVideoStatus(data.data.video);
        
        // Начинаем отслеживание прогресса
        if (data.data.video.video_id) {
          trackVideoProgress(data.data.video.video_id);
        }
        
        onVideoGenerated?.(data.data);
      } else {
        message.error('Ошибка при генерации видео');
      }
    } catch (error) {
      console.error('Ошибка генерации видео:', error);
      message.error('Ошибка при генерации видео');
    } finally {
      setIsGenerating(false);
    }
  };

  const checkVideoStatus = async (videoId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/video/status/${videoId}`);
      const data = await response.json();
      
      if (data.success) {
        setVideoStatus(data.data);
        return data.data;
      }
    } catch (error) {
      console.error('Ошибка проверки статуса:', error);
    }
    return null;
  };

  const trackVideoProgress = async (videoId) => {
    const interval = setInterval(async () => {
      const status = await checkVideoStatus(videoId);
      
      if (status) {
        if (status.status === 'completed') {
          setProgress(100);
          clearInterval(interval);
          message.success('Видео готово!');
        } else if (status.status === 'failed') {
          setProgress(0);
          clearInterval(interval);
          message.error('Ошибка генерации видео');
        } else if (status.progress) {
          setProgress(status.progress);
        }
      }
    }, 5000); // Проверяем каждые 5 секунд
  };

  const downloadVideo = async () => {
    if (!videoStatus?.download_url) return;

    try {
      const response = await fetch(`http://localhost:8000/api/video/download/${videoStatus.video_id}`, {
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
      case 'failed': return 'exception';
      default: return 'normal';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Готово';
      case 'generating': return 'Генерируется';
      case 'failed': return 'Ошибка';
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
                {avatars.map(avatar => (
                  <Option key={avatar.avatar_id} value={avatar.avatar_id}>
                    {avatar.avatar_name || avatar.avatar_id}
                  </Option>
                ))}
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
                {voices.map(voice => (
                  <Option key={voice.voice_id} value={voice.voice_id}>
                    {voice.language} - {voice.gender} ({voice.voice_id})
                  </Option>
                ))}
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
            <Card size="small" style={{ backgroundColor: '#f5f5f5' }}>
              <Text style={{ fontFamily: 'monospace', fontSize: '12px' }}>
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
