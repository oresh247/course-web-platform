import { Card, Col, Row, Typography, Button, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  FormOutlined,
  CommentOutlined,
  ArrowLeftOutlined,
  ThunderboltOutlined,
  MessageOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

/**
 * Выбор способа создания курса: быстрая форма или уточнение в чате.
 */
function CreateCourseChoicePage() {
  const navigate = useNavigate()

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/')}
        style={{ marginBottom: 16 }}
      >
        Назад
      </Button>

      <div style={{ marginBottom: 32, textAlign: 'center' }}>
        <Title level={2} style={{ color: '#ffffff', marginBottom: 8 }}>
          Как создать курс?
        </Title>
        <Paragraph style={{ color: '#b0b0b0', fontSize: 16, marginBottom: 0 }}>
          Выберите быстрый вариант без уточнений или диалог с ботом для персонализации структуры.
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card
            hoverable
            onClick={() => navigate('/create/form')}
            style={{
              height: '100%',
              background: '#141414',
              border: '1px solid #2a2a2a',
              borderRadius: 12,
              cursor: 'pointer',
            }}
            styles={{ body: { padding: 28 } }}
          >
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <ThunderboltOutlined style={{ fontSize: 40, color: '#5E8A30' }} />
              <div>
                <Title level={4} style={{ color: '#ffffff', marginBottom: 8 }}>
                  <FormOutlined style={{ marginRight: 8 }} />
                  Быстро, без уточнения
                </Title>
                <Paragraph style={{ color: '#b0b0b0', marginBottom: 12 }}>
                  Укажите тему, аудиторию и число модулей — AI сразу сгенерирует структуру
                  и добавит курс в «Мои курсы».
                </Paragraph>
                <Text type="secondary">Подходит, когда параметры уже ясны.</Text>
              </div>
              <Button type="primary" block onClick={() => navigate('/create/form')}>
                Создать по форме
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            hoverable
            onClick={() => navigate('/create/chat')}
            style={{
              height: '100%',
              background: '#141414',
              border: '1px solid #2a2a2a',
              borderRadius: 12,
              cursor: 'pointer',
            }}
            styles={{ body: { padding: 28 } }}
          >
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <MessageOutlined style={{ fontSize: 40, color: '#6fa03c' }} />
              <div>
                <Title level={4} style={{ color: '#ffffff', marginBottom: 8 }}>
                  <CommentOutlined style={{ marginRight: 8 }} />
                  С уточнением в чате
                </Title>
                <Paragraph style={{ color: '#b0b0b0', marginBottom: 12 }}>
                  Бот уточнит цель, разделы и уроки. После диалога структура сохранится
                  в «Мои курсы» с карточками как обычно.
                </Paragraph>
                <Text type="secondary">Подходит для персонализации программы.</Text>
              </div>
              <Button type="primary" block onClick={() => navigate('/create/chat')}>
                Начать диалог
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default CreateCourseChoicePage
