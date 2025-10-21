import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  Button, 
  Space,
  message,
  Typography,
  Spin
} from 'antd'
import { RobotOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { coursesApi } from '../api/coursesApi'

const { Title, Paragraph } = Typography
const { TextArea } = Input

function CreateCoursePage() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      const response = await coursesApi.createCourse(values)
      
      message.success(`Курс "${response.course.course_title}" успешно создан!`)
      
      // Перенаправляем на страницу курса
      setTimeout(() => {
        navigate(`/courses/${response.id}`)
      }, 1000)
      
    } catch (error) {
      console.error('Error creating course:', error)
      message.error('Ошибка при создании курса. Проверьте настройки API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={() => navigate('/')}
        style={{ marginBottom: 16 }}
      >
        Назад
      </Button>

      <Card
        style={{
          borderRadius: '12px',
          background: '#141414',
          border: '1px solid #2a2a2a',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}
      >
        <div style={{ 
          textAlign: 'center', 
          marginBottom: 32,
          padding: '30px 20px 20px',
          background: 'linear-gradient(135deg, rgba(94, 138, 48, 0.2) 0%, rgba(45, 71, 25, 0.2) 100%)',
          borderRadius: '8px',
          marginTop: '-24px',
          marginLeft: '-24px',
          marginRight: '-24px'
        }}>
          <Title level={2} style={{ 
            background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: '12px'
          }}>
            <RobotOutlined style={{ color: '#5E8A30' }} /> Создать новый курс с помощью AI
          </Title>
          <Paragraph style={{ color: '#b0b0b0', fontSize: '15px' }}>
            Укажите параметры курса, и AI создаст для вас детальную структуру
          </Paragraph>
        </div>

        <Spin spinning={loading} tip="Генерируем курс... Это может занять 20-30 секунд">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              audience_level: 'junior',
              module_count: 4,
              duration_weeks: 8,
              hours_per_week: 5
            }}
          >
            <Form.Item
              label="Тема курса"
              name="topic"
              rules={[
                { required: true, message: 'Укажите тему курса' },
                { min: 3, message: 'Минимум 3 символа' }
              ]}
            >
              <Input 
                placeholder="Например: Python для начинающих, React.js, DevOps практики"
                size="large"
              />
            </Form.Item>

            <Form.Item
              label="Уровень аудитории"
              name="audience_level"
              rules={[{ required: true, message: 'Выберите уровень' }]}
            >
              <Select size="large">
                <Select.Option value="junior">Junior (начинающие)</Select.Option>
                <Select.Option value="middle">Middle (средний уровень)</Select.Option>
                <Select.Option value="senior">Senior (продвинутые)</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="Количество модулей"
              name="module_count"
              rules={[{ required: true, message: 'Укажите количество модулей' }]}
            >
              <InputNumber 
                min={2} 
                max={10} 
                style={{ width: '100%' }}
                size="large"
              />
            </Form.Item>

            <Space style={{ width: '100%' }} size="large">
              <Form.Item
                label="Длительность (недели)"
                name="duration_weeks"
                style={{ marginBottom: 0 }}
              >
                <InputNumber 
                  min={1} 
                  max={52}
                  size="large"
                />
              </Form.Item>

              <Form.Item
                label="Часов в неделю"
                name="hours_per_week"
                style={{ marginBottom: 0 }}
              >
                <InputNumber 
                  min={1} 
                  max={40}
                  size="large"
                />
              </Form.Item>
            </Space>

            <Form.Item style={{ marginTop: 24 }}>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  size="large"
                  loading={loading}
                  icon={<RobotOutlined style={{ color: '#5E8A30' }} />}
                >
                  Создать курс с помощью AI
                </Button>
                <Button 
                  size="large"
                  onClick={() => navigate('/')}
                  disabled={loading}
                >
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  )
}

export default CreateCoursePage

