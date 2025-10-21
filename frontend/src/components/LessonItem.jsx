import { Space, Tag, Button, Dropdown } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons'

const LessonItem = ({ 
  lesson, 
  index, 
  moduleNumber,
  onGenerateContent,
  onViewContent,
  onExportContent,
  onEdit,
  isGenerating
}) => {
  const exportMenuItems = [
    {
      key: 'pptx',
      label: '📊 PowerPoint',
      onClick: () => onExportContent('pptx')
    },
    {
      key: 'html',
      label: '📄 HTML',
      onClick: () => onExportContent('html')
    },
    {
      key: 'markdown',
      label: '📝 Markdown',
      onClick: () => onExportContent('markdown')
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: '16px', fontWeight: 500 }}>
          {index + 1}. {lesson.lesson_title}
        </span>
        <Space size="small">
          <Button 
            type="primary"
            size="small" 
            icon={<ThunderboltOutlined />}
            loading={isGenerating}
            onClick={onGenerateContent}
            title="Сгенерировать слайды"
          />
          <Button 
            size="small" 
            icon={<BookOutlined />}
            onClick={onViewContent}
            title="Просмотр детального контента"
          />
          <Dropdown menu={{ items: exportMenuItems }}>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              title="Экспортировать контент урока"
            />
          </Dropdown>
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={onEdit}
            title="Редактировать урок"
          />
        </Space>
      </div>
      
      <Space direction="vertical" style={{ width: '100%', paddingLeft: 20 }}>
        <div><strong>Цель:</strong> {lesson.lesson_goal}</div>
        <div>
          <Tag color="green">{lesson.format}</Tag>
          <Tag icon={<ClockCircleOutlined />}>
            {lesson.estimated_time_minutes} мин
          </Tag>
        </div>
        <div>
          <strong>План контента:</strong>
          <ul style={{ marginTop: 8, marginBottom: 0, marginLeft: 20, paddingLeft: 20 }}>
            {lesson.content_outline.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Оценка:</strong> {lesson.assessment}
        </div>
      </Space>
    </div>
  )
}

export default LessonItem

