# Исправление ошибки "You cannot render a <Router> inside another <Router>"

## Проблема
При обновлении структуры приложения возникла ошибка:
```
Uncaught Error: You cannot render a <Router> inside another <Router>. 
You should never have more than one in your app.
```

## Причина
В приложении было **два** компонента `BrowserRouter`:
1. В `frontend/src/main.jsx` (оригинальный)
2. В `frontend/src/App.jsx` (добавленный при обновлении)

React Router не позволяет иметь вложенные роутеры в одном приложении.

## Решение ✅

### 1. Оставили BrowserRouter только в main.jsx
**frontend/src/main.jsx:**
```javascript
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <ConfigProvider locale={ruRU}>
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
```

### 2. Убрали BrowserRouter из App.jsx
**frontend/src/App.jsx:**
```javascript
function App() {
  return (
    <ConfigProvider theme={theme}>
      <AntdApp>
        <Layout style={{ minHeight: '100vh', background: '#0a0a0a' }}>
          <AppHeader />
          <Content style={{ padding: '24px 50px', marginTop: 70, background: '#0a0a0a' }}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/create" element={<CreateCoursePage />} />
              <Route path="/courses" element={<CoursesListPage />} />
              <Route path="/courses/:id" element={<CourseViewPage />} />
              <Route path="/video-test" element={<VideoTestPage />} />
            </Routes>
          </Content>
          <Footer>...</Footer>
        </Layout>
      </AntdApp>
    </ConfigProvider>
  )
}
```

## Результат

### Структура приложения:
```
main.jsx
├── BrowserRouter (с future flags)
    └── ConfigProvider (русская локализация)
        └── App.jsx
            └── ConfigProvider (темная тема)
                └── AntdApp (для message API)
                    └── Layout
                        ├── AppHeader
                        ├── Routes
                        └── Footer
```

### Преимущества:
- ✅ **Один роутер** - нет конфликтов
- ✅ **Future flags** - готовность к React Router v7
- ✅ **AntdApp** - правильная работа с message API
- ✅ **Двойная тема** - русская локализация + темная тема
- ✅ **Чистая архитектура** - разделение ответственности

## Проверка

1. **Откройте** `http://localhost:3000`
2. **Проверьте консоль** - ошибок быть не должно
3. **Проверьте навигацию** - все ссылки должны работать
4. **Проверьте предупреждения** - их не должно быть

## Заключение

Ошибка успешно исправлена! Теперь приложение имеет правильную структуру роутинга:
- 🎯 **Один BrowserRouter** в корне приложения
- 🎯 **Future flags** для совместимости с v7
- 🎯 **AntdApp** для корректной работы с уведомлениями
- 🎯 **Чистая консоль** без ошибок и предупреждений
