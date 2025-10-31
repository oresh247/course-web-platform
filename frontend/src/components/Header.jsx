import { Layout, Menu } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeOutlined, 
  PlusOutlined, 
  BookOutlined,
  QuestionCircleOutlined
  // RobotOutlined исключаем из использованных
} from '@ant-design/icons'

const { Header } = Layout

function AppHeader() {
  const location = useLocation()
  const currentPath = location.pathname

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">Главная</Link>,
    },
    {
      key: '/create',
      icon: <PlusOutlined />,
      label: <Link to="/create">Создать курс</Link>,
    },
    {
      key: '/courses',
      icon: <BookOutlined />,
      label: <Link to="/courses">Мои курсы</Link>,
    }
    // Пункт '/video-test' больше не нужен
  ]

  return (
    <Header 
      style={{ 
        position: 'fixed', 
        zIndex: 1000, 
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        gap: '30px',
        padding: '0 50px',
        background: 'linear-gradient(135deg, #5E8A30 0%, #2d4719 100%)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        height: '70px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* IT-ONE Logo (external link) */}
        <a href="https://www.it-one.ru/" target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '6px 12px',
            fontWeight: 700,
            fontSize: '18px',
            color: '#5E8A30',
            letterSpacing: '0.5px'
          }}>
            IT_ONE
          </div>
        </a>
        {/* App Name (link to home) */}
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div style={{ 
            color: 'white', 
            fontSize: '22px', 
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            borderLeft: '2px solid rgba(255,255,255,0.3)',
            paddingLeft: '15px'
          }}>
            AI Course Builder
          </div>
        </Link>
      </div>
      <Menu
        mode="horizontal"
        selectedKeys={[currentPath]}
        items={menuItems}
        style={{ 
          flex: 1, 
          minWidth: 0,
          background: 'transparent',
          borderBottom: 'none',
          fontSize: '16px'
        }}
      />
      <a
        href="/user-guide.html"
        target="_blank"
        rel="noreferrer"
        title="Инструкция для пользователя"
        style={{
          marginLeft: 'auto',
          color: 'white',
          display: 'flex',
          alignItems: 'center'
        }}
      >
        <QuestionCircleOutlined style={{ fontSize: 22 }} />
      </a>
    </Header>
  )
}

export default AppHeader

