// Конфигурация API endpoints
const API_CONFIG = {
  // Определяем базовый URL API в зависимости от окружения
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? process.env.REACT_APP_API_URL || 'https://course-builder-api.onrender.com'
    : 'http://localhost:8000',
  
  // Endpoints для видео
  VIDEO: {
    AVATARS: '/api/video/avatars',
    VOICES: '/api/video/voices',
    GENERATE_LESSON: '/api/video/generate-lesson',
    GENERATE_SLIDES: '/api/video/generate-lesson-slides',
    STATUS: '/api/video/status',
    DOWNLOAD: '/api/video/download'
  },
  
  // Endpoints для курсов
  COURSES: {
    LIST: '/api/courses',
    CREATE: '/api/courses',
    GET: '/api/courses',
    UPDATE: '/api/courses',
    DELETE: '/api/courses'
  }
};

// Функция для получения полного URL
export const getApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Функция для получения URL видео API
export const getVideoApiUrl = (endpoint) => {
  return getApiUrl(API_CONFIG.VIDEO[endpoint]);
};

// Функция для получения URL курсов API
export const getCoursesApiUrl = (endpoint) => {
  return getApiUrl(API_CONFIG.COURSES[endpoint]);
};

export default API_CONFIG;
