# Дизайн-система IT-ONE для AI Course Builder (Dark Theme)

## 🎨 Цветовая палитра

### Основные цвета
- **Primary Purple**: `#667eea` - Основной фиолетовый цвет IT-ONE
- **Primary Violet**: `#764ba2` - Дополнительный фиолетовый для градиентов
- **Gradient Primary**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`

### Дополнительные цвета
- **Secondary Blue**: `#4a90e2` - Информационный синий
- **Secondary Green**: `#4caf50` - Успех
- **Secondary Gold**: `#ffd700` - Внимание

### Темная тема
- **Dark BG Primary**: `#0a0a0a` - Основной фон
- **Dark BG Secondary**: `#141414` - Вторичный фон (карточки)
- **Dark BG Elevated**: `#1a1a1a` - Возвышенные элементы
- **Dark BG Hover**: `#202020` - Состояние наведения

### Цвета текста (Dark Theme)
- **Text Primary**: `#ffffff` - Основной текст
- **Text Secondary**: `#b0b0b0` - Вторичный текст
- **Text Muted**: `#808080` - Приглушенный текст

### Границы (Dark Theme)
- **Border Color**: `#2a2a2a` - Основные границы
- **Border Color Light**: `#333333` - Светлые границы

## 📝 Типографика

### Шрифты
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Заголовки
- **h1**: 2.5rem (40px), font-weight: 600
- **h2**: 2rem (32px), font-weight: 600
- **h3**: 1.5rem (24px), font-weight: 600

### Текст
- **Основной**: 14px, line-height: 1.6
- **Вторичный**: цвет #616161
- **Мелкий**: 12-13px

## 🎭 Компоненты

### Кнопки
- **Высота**: 40px (large: 50px)
- **Border Radius**: 8px
- **Primary**: Цвет `#667eea` с тенью
- **Hover**: Увеличенная тень

### Карточки
- **Border Radius**: 12px
- **Border**: 1px solid #e0e0e0
- **Shadow**: `0 4px 20px rgba(102, 126, 234, 0.1)`
- **Hover Shadow**: `0 8px 30px rgba(102, 126, 234, 0.2)`

### Inputs
- **Высота**: 40px
- **Border Radius**: 8px

## 🎨 Специальные эффекты

### Градиентный текст
```css
.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### Тени карточек
```css
.card-shadow {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
  transition: box-shadow 0.3s ease;
}

.card-shadow:hover {
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
}
```

## 🏷️ Брендинг IT-ONE

### Логотип
Текстовый логотип в белой плашке:
```jsx
<div style={{
  background: 'white',
  borderRadius: '8px',
  padding: '6px 12px',
  fontWeight: 700,
  fontSize: '18px',
  color: '#667eea',
  letterSpacing: '0.5px'
}}>
  IT_ONE
</div>
```

### Header
- **Фон**: Градиент IT-ONE
- **Высота**: 70px
- **Тень**: `0 2px 8px rgba(0,0,0,0.15)`

### Footer
- **Фон**: Градиент IT-ONE
- **Текст**: Белый
- **Padding**: 24px 50px

## 📱 Адаптивность

### Breakpoints
- **xs**: < 576px
- **sm**: 576px - 768px
- **md**: 768px - 992px
- **lg**: 992px - 1200px
- **xl**: 1200px - 1600px
- **xxl**: > 1600px

### Grid
- **Gutter**: 24px
- **Max Width**: 1200px (контентная область)

## ✨ Анимации

### Transitions
```css
transition: all 0.3s ease;
```

Применяется к:
- Карточкам (hover)
- Кнопкам
- Цветам
- Тенями

## 🎯 Использование

### Ant Design Dark Theme Config
```javascript
const theme = {
  token: {
    colorPrimary: '#667eea',
    colorSuccess: '#4caf50',
    colorWarning: '#ffd700',
    colorInfo: '#4a90e2',
    borderRadius: 8,
    fontSize: 14,
    
    // Dark Theme Colors
    colorBgBase: '#0a0a0a',
    colorBgContainer: '#141414',
    colorBgElevated: '#1a1a1a',
    colorBorder: '#2a2a2a',
    colorText: '#ffffff',
    colorTextSecondary: '#b0b0b0',
  },
  components: {
    Button: {
      controlHeight: 40,
      fontWeight: 500,
      primaryShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
    },
    Card: {
      borderRadiusLG: 12,
      boxShadowTertiary: '0 4px 20px rgba(0, 0, 0, 0.3)',
      colorBgContainer: '#141414',
    },
  },
  algorithm: 'dark',
}
```

## 📐 Spacing

- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px

## 🔗 Ссылки

- [IT-ONE Website](https://www.it-one.ru/)
- [Ant Design](https://ant.design/)

