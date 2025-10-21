import { Routes, Route } from 'react-router-dom'
import { Layout, ConfigProvider, theme as antdTheme } from 'antd'
import AppHeader from './components/Header'
import HomePage from './pages/HomePage'
import CreateCoursePage from './pages/CreateCoursePage'
import CourseViewPage from './pages/CourseViewPage'
import CoursesListPage from './pages/CoursesListPage'
import './styles/App.css'

const { Content, Footer } = Layout

// IT-ONE Dark Theme Configuration
const theme = {
  token: {
    colorPrimary: '#5E8A30',
    colorSuccess: '#4caf50',
    colorWarning: '#ffd700',
    colorError: '#ff4d4f',
    colorInfo: '#5E8A30',
    borderRadius: 8,
    fontSize: 14,
    fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif`,
    
    // Dark Theme Colors
    colorBgBase: '#0a0a0a',
    colorBgContainer: '#141414',
    colorBgElevated: '#1a1a1a',
    colorBorder: '#2a2a2a',
    colorBorderSecondary: '#333333',
    colorText: '#ffffff',
    colorTextSecondary: '#b0b0b0',
    colorTextTertiary: '#808080',
    colorTextQuaternary: '#505050',
  },
  components: {
    Button: {
      controlHeight: 40,
      fontWeight: 500,
      primaryShadow: '0 2px 8px rgba(94, 138, 48, 0.3)',
      defaultBorderColor: '#2a2a2a',
      defaultBg: '#1a1a1a',
      defaultColor: '#ffffff',
    },
    Card: {
      borderRadiusLG: 12,
      boxShadowTertiary: '0 4px 20px rgba(0, 0, 0, 0.3)',
      colorBgContainer: '#141414',
      colorBorderSecondary: '#2a2a2a',
    },
    Input: {
      controlHeight: 40,
      borderRadius: 8,
      colorBgContainer: '#1a1a1a',
      colorBorder: '#2a2a2a',
      colorText: '#ffffff',
    },
    Select: {
      controlHeight: 40,
      colorBgContainer: '#1a1a1a',
      colorBorder: '#2a2a2a',
    },
    Layout: {
      bodyBg: '#0a0a0a',
      headerBg: 'transparent',
      footerBg: 'transparent',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemSelectedBg: 'rgba(255, 255, 255, 0.1)',
    },
    Empty: {
      colorText: '#b0b0b0',
    },
    Typography: {
      colorText: '#ffffff',
      colorTextSecondary: '#b0b0b0',
    },
    Modal: {
      contentBg: '#141414',
      headerBg: '#141414',
    },
    Dropdown: {
      colorBgElevated: '#1a1a1a',
    },
  },
  algorithm: antdTheme.darkAlgorithm,
}

function App() {
  return (
    <ConfigProvider theme={theme}>
      <Layout style={{ minHeight: '100vh', background: '#0a0a0a' }}>
        <AppHeader />
        <Content style={{ padding: '24px 50px', marginTop: 70, background: '#0a0a0a' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/create" element={<CreateCoursePage />} />
            <Route path="/courses" element={<CoursesListPage />} />
            <Route path="/courses/:id" element={<CourseViewPage />} />
          </Routes>
        </Content>
        <Footer style={{ 
          textAlign: 'center',
          background: '#0a0a0a',
          color: '#808080',
          padding: '24px 50px',
          borderTop: '1px solid #2a2a2a'
        }}>
          <div>
            <strong style={{ color: '#b0b0b0' }}>AI Course Builder</strong> ©2025
          </div>
        </Footer>
      </Layout>
    </ConfigProvider>
  )
}

export default App

