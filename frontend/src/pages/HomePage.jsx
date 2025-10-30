import { Card, Row, Col, Typography, Button, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import { 
  PlusCircleOutlined, 
  BookOutlined, 
  RocketOutlined,
  ThunderboltOutlined,
  EditOutlined,
  ExportOutlined
} from '@ant-design/icons'

const { Title, Paragraph } = Typography

function HomePage() {
  const navigate = useNavigate()

  const features = [
    {
      icon: <ThunderboltOutlined style={{ fontSize: '48px', color: '#5E8A30' }} />,
      title: 'AI Генерация',
      description: 'Автоматическое создание структуры курса с помощью GPT-4'
    },
    {
      icon: <EditOutlined style={{ fontSize: '48px', color: '#6fa03c' }} />,
      title: 'Редактирование',
      description: 'Удобное редактирование курсов, модулей и уроков с AI перегенерацией'
    },
    {
      icon: <BookOutlined style={{ fontSize: '48px', color: '#4a6d26' }} />,
      title: 'Детальный контент',
      description: 'Генерация лекций, слайдов и учебных материалов для каждого урока'
    },
    {
      icon: <ExportOutlined style={{ fontSize: '48px', color: '#5E8A30' }} />,
      title: 'Экспорт',
      description: 'Экспорт в JSON, Markdown, TXT, HTML и PowerPoint'
    },
  ]

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Hero Section */}
      <div 
        style={{ 
          textAlign: 'center', 
          marginBottom: 60,
          padding: '60px 30px',
          background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
          borderRadius: '20px',
          color: 'white',
          boxShadow: '0 10px 40px rgba(94, 138, 48, 0.4)'
        }}
      >
        <Title level={1} style={{ color: 'white', fontSize: '3rem', marginBottom: '20px' }}>
          <RocketOutlined style={{ marginRight: '15px' }} />
          AI Course Builder
        </Title>
        <Paragraph style={{ fontSize: 20, color: 'rgba(255,255,255,0.95)', marginBottom: 40, maxWidth: 700, margin: '0 auto 40px' }}>
          Создавайте профессиональные IT-курсы с помощью искусственного интеллекта. 
          Быстро, качественно, эффективно.
        </Paragraph>
        <Space size="large">
          <Button 
            type="default"
            size="large" 
            icon={<PlusCircleOutlined />}
            onClick={() => navigate('/create')}
            style={{ 
              height: '50px', 
              fontSize: '16px',
              borderRadius: '8px',
              background: 'white',
              color: '#5E8A30',
              border: 'none',
              fontWeight: 600,
              padding: '0 30px'
            }}
          >
            Создать новый курс
          </Button>
          <Button 
            size="large" 
            icon={<BookOutlined />}
            onClick={() => navigate('/courses')}
            style={{ 
              height: '50px', 
              fontSize: '16px',
              borderRadius: '8px',
              background: 'transparent',
              color: 'white',
              borderColor: 'white',
              fontWeight: 600,
              padding: '0 30px'
            }}
          >
            Мои курсы
          </Button>
        </Space>
      </div>

      {/* Features Grid */}
      <div style={{ marginBottom: 60 }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 40, color: '#ffffff' }}>
          Возможности платформы
        </Title>
        <Row gutter={[24, 24]}>
          {features.map((feature, index) => (
            <Col xs={24} sm={12} md={6} key={index}>
              <Card 
                hoverable
                style={{ 
                  textAlign: 'center', 
                  height: '100%',
                  borderRadius: '12px',
                  background: '#141414',
                  border: '1px solid #2a2a2a',
                  transition: 'all 0.3s ease'
                }}
                styles={{
                  body: { padding: '30px 20px' }
                }}
              >
                <div style={{ marginBottom: 20 }}>
                  {feature.icon}
                </div>
                <Title level={4} style={{ marginBottom: 12, color: '#ffffff' }}>
                  {feature.title}
                </Title>
                <Paragraph style={{ color: '#b0b0b0', marginBottom: 0 }}>
                  {feature.description}
                </Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* How It Works */}
      <Card 
        style={{ 
          marginTop: 48,
          borderRadius: '12px',
          background: '#141414',
          border: '1px solid #2a2a2a',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}
        styles={{
          body: { padding: '40px' }
        }}
      >
        <Title level={2} style={{ textAlign: 'center', marginBottom: 40, color: '#ffffff' }}>
          Как это работает?
        </Title>
        <Row gutter={[32, 32]}>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div style={{ 
                fontSize: 48, 
                fontWeight: 'bold', 
                background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: 16 
              }}>
                1
              </div>
              <Title level={4} style={{ color: '#ffffff', marginBottom: 12 }}>
                Укажите параметры
              </Title>
              <Paragraph style={{ color: '#b0b0b0', fontSize: 15 }}>
                Выберите тему, целевую аудиторию и количество модулей для вашего курса
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div style={{ 
                fontSize: 48, 
                fontWeight: 'bold', 
                background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: 16 
              }}>
                2
              </div>
              <Title level={4} style={{ color: '#ffffff', marginBottom: 12 }}>
                AI создаёт структуру
              </Title>
              <Paragraph style={{ color: '#b0b0b0', fontSize: 15 }}>
                Нейросеть генерирует детальную программу курса с модулями и уроками
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div style={{ 
                fontSize: 48, 
                fontWeight: 'bold', 
                background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: 16 
              }}>
                3
              </div>
              <Title level={4} style={{ color: '#ffffff', marginBottom: 12 }}>
                Редактируйте и экспортируйте
              </Title>
              <Paragraph style={{ color: '#b0b0b0', fontSize: 15 }}>
                Дорабатывайте контент, генерируйте детали и экспортируйте в нужном формате
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default HomePage

