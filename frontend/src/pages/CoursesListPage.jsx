import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Card, 
  List, 
  Button, 
  Space, 
  Tag, 
  Empty,
  Spin,
  App,
  Popconfirm,
  Typography,
  Input,
  Select,
  Table
} from 'antd'
import { 
  EyeOutlined, 
  DeleteOutlined, 
  PlusOutlined,
  BookOutlined,
  ClockCircleOutlined,
  UserOutlined
} from '@ant-design/icons'
import { SmileOutlined, TeamOutlined, CrownOutlined } from '@ant-design/icons'
import { coursesApi } from '../api/coursesApi'

const { Title, Paragraph, Text } = Typography

function CoursesListPage() {
  const { message } = App.useApp();
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('cards') // 'cards' | 'table'
  const [searchQuery, setSearchQuery] = useState('')
  const [audienceFilter, setAudienceFilter] = useState('all')

  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    setLoading(true)
    try {
      const data = await coursesApi.getCourses()
      setCourses(data)
    } catch (error) {
      console.error('Error loading courses:', error)
      message.error('Ошибка загрузки курсов')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await coursesApi.deleteCourse(id)
      message.success('Курс удален')
      loadCourses()
    } catch (error) {
      console.error('Error deleting course:', error)
      message.error('Ошибка удаления курса')
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="Загрузка курсов..." />
      </div>
    )
  }

  // Применяем фильтры к списку
  const filteredCourses = courses.filter(c => {
    const q = searchQuery.trim().toLowerCase()
    const okSearch = !q || String(c.course_title || '').toLowerCase().includes(q)
    const aud = String(c.target_audience || '').toLowerCase()
    const okAudience = audienceFilter === 'all' || aud.includes(audienceFilter)
    return okSearch && okAudience
  })

  // Колонки таблицы
  const columns = [
    { title: 'Название', dataIndex: 'course_title', key: 'title', render: (text, record) => (
      <a onClick={() => navigate(`/courses/${record.id}`)}>{text}</a>
    ) },
    { title: 'Аудитория', dataIndex: 'target_audience', key: 'aud' },
    { title: 'Недель', dataIndex: 'duration_weeks', key: 'weeks', width: 100 },
    { title: 'Часов', dataIndex: 'duration_hours', key: 'hours', width: 100,
      render: (v) => v ?? '-' },
    { title: 'Создан', dataIndex: 'created_at', key: 'created', width: 140,
      render: (v) => new Date(v).toLocaleDateString('ru-RU') },
    { title: 'Действия', key: 'actions', width: 220, render: (_, record) => (
      <Space>
        <Button type="link" icon={<EyeOutlined />} onClick={() => navigate(`/courses/${record.id}`)} style={{ color: '#5E8A30', fontWeight: 500 }}>Открыть</Button>
        <Popconfirm title="Удалить курс?" description="Это действие нельзя отменить" onConfirm={() => handleDelete(record.id)} okText="Да" cancelText="Нет">
          <Button type="link" danger icon={<DeleteOutlined />} style={{ fontWeight: 500 }}>Удалить</Button>
        </Popconfirm>
      </Space>
    )}
  ]

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 32,
        padding: '30px',
        background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
        borderRadius: '12px',
        color: 'white',
        boxShadow: '0 4px 20px rgba(94, 138, 48, 0.4)'
      }}>
        <Title level={2} style={{ color: 'white', margin: 0 }}>
          <BookOutlined /> Мои курсы
        </Title>
        <Space>
          <Input.Search
            allowClear
            placeholder="Поиск по названию"
            onSearch={setSearchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: 260 }}
          />
          <Select
            value={audienceFilter}
            onChange={setAudienceFilter}
            style={{ width: 180 }}
            options={[
              { value: 'all', label: 'Все уровни' },
              { value: 'junior', label: 'Junior' },
              { value: 'middle', label: 'Middle' },
              { value: 'senior', label: 'Senior' }
            ]}
          />
          <Button onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}>
            {viewMode === 'cards' ? 'Таблица' : 'Карточки'}
          </Button>
          <Button 
            size="large"
            icon={<PlusOutlined />}
            onClick={() => navigate('/create')}
            style={{
              background: 'white',
              color: '#5E8A30',
              border: 'none',
              fontWeight: 600
            }}
          >
            Создать курс
          </Button>
        </Space>
      </div>

      {filteredCourses.length === 0 ? (
        <Card style={{
          borderRadius: '12px',
          background: '#141414',
          border: '1px solid #2a2a2a',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}>
          <Empty
            description={
              <span style={{ fontSize: '15px', color: '#b0b0b0' }}>
                У вас пока нет курсов.<br />
                Создайте первый курс с помощью AI!
              </span>
            }
          >
            <Button 
              type="primary" 
              size="large"
              icon={<PlusOutlined />}
              onClick={() => navigate('/create')}
            >
              Создать курс
            </Button>
          </Empty>
        </Card>
      ) : viewMode === 'cards' ? (
        <List
          grid={{ 
            gutter: 24, 
            xs: 1, 
            sm: 1, 
            md: 2, 
            lg: 2, 
            xl: 3, 
            xxl: 3 
          }}
          dataSource={filteredCourses}
          renderItem={(course) => (
            <List.Item>
              <Card
                hoverable
                style={{
                  borderRadius: '12px',
                  background: '#141414',
                  border: '1px solid #2a2a2a',
                  transition: 'all 0.3s ease',
                  height: '100%'
                }}
                styles={{
                  body: {
                    paddingBottom: '80px',
                    position: 'relative',
                    minHeight: '200px'
                  }
                }}
                actions={[
                  <Button 
                    type="link" 
                    icon={<EyeOutlined />}
                    onClick={() => navigate(`/courses/${course.id}`)}
                    style={{ color: '#5E8A30', fontWeight: 500 }}
                  >
                    Открыть
                  </Button>,
                  <Popconfirm
                    title="Удалить курс?"
                    description="Это действие нельзя отменить"
                    onConfirm={() => handleDelete(course.id)}
                    okText="Да"
                    cancelText="Нет"
                  >
                    <Button 
                      type="link" 
                      danger
                      icon={<DeleteOutlined />}
                      style={{ fontWeight: 500 }}
                    >
                      Удалить
                    </Button>
                  </Popconfirm>
                ]}
              >
                <Card.Meta
                  title={
                    <div style={{ 
                      marginBottom: 16,
                      fontSize: '18px',
                      fontWeight: 600,
                      color: '#ffffff',
                      lineHeight: 1.4
                    }}>
                      {(() => {
                        const lvl = String(course.target_audience || '').toLowerCase()
                        const color = '#5E8A30'
                        const size = 18
                        let icon = <SmileOutlined style={{ color, fontSize: size, marginRight: 8 }} />
                        if (lvl.includes('middle')) icon = <TeamOutlined style={{ color, fontSize: size, marginRight: 8 }} />
                        if (lvl.includes('senior')) icon = <CrownOutlined style={{ color, fontSize: size, marginRight: 8 }} />
                        return (
                          <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                            {icon}
                            {course.course_title}
                          </span>
                        )
                      })()}
                    </div>
                  }
                  description={
                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      <div style={{ color: '#b0b0b0', fontSize: '14px' }}>
                        <UserOutlined style={{ marginRight: '8px', color: '#5E8A30' }} />
                        {course.target_audience}
                      </div>
                      {course.duration_weeks && (
                        <div style={{ color: '#b0b0b0', fontSize: '14px' }}>
                          <ClockCircleOutlined style={{ marginRight: '8px', color: '#5E8A30' }} />
                          {course.duration_weeks} недель
                          {course.duration_hours && ` (${course.duration_hours} часов)`}
                        </div>
                      )}
                      <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid #2a2a2a' }}>
                        <Text type="secondary" style={{ fontSize: 12, color: '#808080' }}>
                          Создан: {new Date(course.created_at).toLocaleDateString('ru-RU')}
                        </Text>
                      </div>
                    </Space>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      ) : (
        <Card style={{ borderRadius: '12px', background: '#141414', border: '1px solid #2a2a2a' }}>
          <Table
            rowKey="id"
            dataSource={filteredCourses}
            columns={columns}
            pagination={{ pageSize: 9 }}
          />
        </Card>
      )}
    </div>
  )
}

export default CoursesListPage

