import { useState } from 'react'
import { Card, Button, Space, Typography, Row, Col, Select, message } from 'antd'
import { PlayCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import VideoGenerationPanel from '../components/VideoGenerationPanel'

const { Title, Text } = Typography
const { Option } = Select

function VideoTestPage() {
  const [lesson, setLesson] = useState({
    id: 1,
    title: "Основы Python программирования",
    content: `Добро пожаловать в мир Python!

Python - это мощный и простой язык программирования.

В этом уроке мы изучим основы синтаксиса Python.

Мы также рассмотрим переменные и типы данных.

В конце урока вы сможете написать свою первую программу.`,
    duration: "15 минут",
    difficulty: "Начальный"
  })

  const [avatars, setAvatars] = useState([
    { avatar_id: "Abigail_expressive_2024112501", name: "Abigail" },
    { avatar_id: "default", name: "Default Avatar" }
  ])

  const [voices, setVoices] = useState([
    { voice_id: "9799f1ba6acd4b2b993fe813a18f9a91", name: "Russian Voice" },
    { voice_id: "default", name: "Default Voice" }
  ])

  const handleVideoGenerated = (data) => {
    console.log('Video generated:', data)
    message.success('Видео успешно сгенерировано!')
  }

  const generateSlideVideos = async () => {
    try {
      const response = await fetch('/api/video/generate-lesson-slides', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: lesson.title,
          text: lesson.content,
          avatar_id: "Abigail_expressive_2024112501",
          voice_id: "9799f1ba6acd4b2b993fe813a18f9a91",
          quality: "low",
          test_mode: true
        }),
      })

      const data = await response.json()
      
      if (data.success) {
        message.success(`Видео для ${data.data.total_slides} слайдов поставлены в очередь!`)
        console.log('Slide videos:', data.data)
      } else {
        message.error('Ошибка при генерации видео для слайдов')
      }
    } catch (error) {
      console.error('Error generating slide videos:', error)
      message.error('Ошибка при генерации видео для слайдов')
    }
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      <Title level={2} style={{ color: '#5E8A30', marginBottom: '30px' }}>
        🎬 Тестирование генерации видео
      </Title>

      <Row gutter={[24, 24]}>
        {/* Информация об уроке */}
        <Col span={24}>
          <Card 
            title="Информация об уроке"
            style={{ marginBottom: '20px' }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Название: </Text>
                <Text>{lesson.title}</Text>
              </div>
              <div>
                <Text strong>Длительность: </Text>
                <Text>{lesson.duration}</Text>
              </div>
              <div>
                <Text strong>Уровень: </Text>
                <Text>{lesson.difficulty}</Text>
              </div>
              <div>
                <Text strong>Содержание: </Text>
                <Text>{lesson.content}</Text>
              </div>
            </Space>
          </Card>
        </Col>

        {/* Компонент генерации видео */}
        <Col span={24}>
          <VideoGenerationPanel 
            lesson={lesson}
            onVideoGenerated={handleVideoGenerated}
          />
        </Col>

        {/* Дополнительные действия */}
        <Col span={24}>
          <Card title="Дополнительные функции">
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={generateSlideVideos}
              >
                Создать видео для каждого слайда
              </Button>
              
              <Button
                icon={<ReloadOutlined />}
                onClick={() => window.location.reload()}
              >
                Обновить страницу
              </Button>
            </Space>
          </Card>
        </Col>

        {/* Статистика */}
        <Col span={24}>
          <Card title="Статистика">
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ color: '#5E8A30', margin: 0 }}>2</Title>
                    <Text>Доступных аватара</Text>
                  </div>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ color: '#5E8A30', margin: 0 }}>4</Title>
                    <Text>Доступных голоса</Text>
                  </div>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ color: '#5E8A30', margin: 0 }}>Low</Title>
                    <Text>Качество видео</Text>
                  </div>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ color: '#5E8A30', margin: 0 }}>Test</Title>
                    <Text>Режим работы</Text>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default VideoTestPage
