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

  // Дублировать модуль (серверная копия с детальным контентом)
  duplicateModule: async (courseId, moduleNumber, payload, options = {}) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/duplicate`,
      payload,
      { signal: options.signal }
    )
    return response.data
  },

  // Удалить модуль
  deleteModule: async (courseId, moduleNumber) => {
    const response = await api.delete(
      `/api/courses/${courseId}/modules/${moduleNumber}`
    )
    return response.data
  },

  // Регенерировать план контента урока с помощью AI
  // ============================================================================
  // API МЕТОДЫ ДЛЯ РАБОТЫ С ТЕСТАМИ
  // ============================================================================
  
  // Сгенерировать тест для урока
  generateLessonTest: async (courseId, moduleNumber, lessonIndex, testData = {}) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/generate-test`,
      testData
    )
    return response.data
  },

  // Получить тест для урока
  getLessonTest: async (courseId, moduleNumber, lessonIndex) => {
    const response = await api.get(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/test`
    )
    return response.data
  },

  // Обновить тест для урока
  updateLessonTest: async (courseId, moduleNumber, lessonIndex, test) => {
    const response = await api.put(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/test`,
      { test }
    )
    return response.data
  },

  // Перегенерировать тест для урока
  regenerateLessonTest: async (courseId, moduleNumber, lessonIndex, testData = {}) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/regenerate-test`,
      testData
    )
    return response.data
  },

  regenerateLessonContent: async (courseId, moduleNumber, lessonIndex, body = null) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/regenerate-content`,
      body
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

  // Дублировать урок
  duplicateLesson: async (courseId, moduleNumber, lessonIndex, payload) => {
    const response = await api.post(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}/duplicate`,
      payload
    )
    return response.data
  },

  // Удалить урок
  deleteLesson: async (courseId, moduleNumber, lessonIndex) => {
    const response = await api.delete(
      `/api/courses/${courseId}/modules/${moduleNumber}/lessons/${lessonIndex}`
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

