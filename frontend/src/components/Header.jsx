import { Layout, Menu } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeOutlined, 
  PlusOutlined, 
  BookOutlined,
  RobotOutlined 
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
    },
    {
      key: '/video-test',
      icon: <RobotOutlined />,
      label: <Link to="/video-test">Тест видео</Link>,
    },
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
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          {/* IT-ONE Logo */}
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
          
          {/* App Name */}
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
            <RobotOutlined style={{ fontSize: '26px' }} />
            AI Course Builder
          </div>
        </div>
      </Link>
      
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
        theme="dark"
      />
    </Header>
  )
}

export default AppHeader

