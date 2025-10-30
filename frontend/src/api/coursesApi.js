import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Диагностика: смотрим, что попало в сборку
// Внимание: видно в консоли браузера
try {
  // eslint-disable-next-line no-console
  console.log('VITE_API_URL =', import.meta.env.VITE_API_URL)
  // eslint-disable-next-line no-console
  console.log('API_BASE_URL =', API_BASE_URL)
} catch (_) {}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const coursesApi = {
  // Создать курс
  createCourse: async (data) => {
    const response = await api.post('/api/courses/', data)
    return response.data
  },

  // Получить все курсы
  getCourses: async (limit = 50, offset = 0) => {
    const response = await api.get('/api/courses/', {
      params: { limit, offset }
    })
    return response.data
  },

  // Получить курс по ID
  getCourse: async (id) => {
    const response = await api.get(`/api/courses/${id}`)
    return response.data
  },

  // Обновить курс
  updateCourse: async (id, data) => {
    const response = await api.put(`/api/courses/${id}`, data)
    return response.data
  },

  // Удалить курс
  deleteCourse: async (id) => {
    const response = await api.delete(`/api/courses/${id}`)
    return response.data
  },

  // Сгенерировать контент модуля
  generateModuleContent: async (courseId, moduleNumber) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/generate`
    )
    return response.data
  },

  // Получить контент модуля
  getModuleContent: async (courseId, moduleNumber) => {
    const response = await api.get(
      `/api/courses/${courseId}/modules/${moduleNumber}/content`
    )
    return response.data
  },

  // Регенерировать цель модуля с помощью AI
  regenerateModuleGoal: async (courseId, moduleNumber) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/regenerate-goal`
    )
    return response.data
  },

  // Регенерировать план контента урока с помощью AI
  regenerateLessonContent: async (courseId, moduleNumber, lessonIndex) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/regenerate-content`
    )
    return response.data
  },

  // Сгенерировать детальный контент урока (лекцию со слайдами)
  generateLessonDetailedContent: async (courseId, moduleNumber, lessonIndex) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/generate`
    )
    return response.data
  },

  // Получить детальный контент урока
  getLessonContent: async (courseId, moduleNumber, lessonIndex) => {
    const response = await api.get(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/content`
    )
    return response.data
  },

  // Проверка здоровья API
  healthCheck: async () => {
    const response = await api.get('/api/health')
    return response.data
  },
}

export default api

