import { Modal, Form, Input, Button, Space, Card, Radio, message, InputNumber } from 'antd'
import { useState, useEffect } from 'react'
import { coursesApi } from '../api/coursesApi'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'

const LessonTestEditor = ({
  visible,
  onCancel,
  onSuccess,
  courseId,
  moduleNumber,
  lessonIndex,
  test: initialTest
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [test, setTest] = useState(initialTest)

  useEffect(() => {
    if (initialTest) {
      setTest(initialTest)
      form.setFieldsValue({ test: initialTest })
    }
  }, [initialTest, form])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      // Валидация: в каждом вопросе должен быть ровно один правильный ответ
      const testData = values.test
      if (testData && testData.questions) {
        for (let i = 0; i < testData.questions.length; i++) {
          const question = testData.questions[i]
          if (!question.options || question.options.length < 2) {
            message.error(`Вопрос ${i + 1}: должно быть минимум 2 варианта ответа`)
            return
          }
          const correctCount = question.options.filter(opt => opt.is_correct).length
          if (correctCount !== 1) {
            message.error(`Вопрос ${i + 1}: должен быть ровно один правильный ответ (найдено: ${correctCount})`)
            return
          }
        }
        
        // Обновляем total_questions
        testData.total_questions = testData.questions.length
      }
      
      setLoading(true)
      
      await coursesApi.updateLessonTest(
        courseId,
        moduleNumber,
        lessonIndex,
        testData
      )
      
      message.success('Тест успешно обновлен!')
      onSuccess?.(testData)
      onCancel()
    } catch (error) {
      if (error.errorFields) {
        // Ошибки валидации формы
        return
      }
      console.error('Ошибка обновления теста:', error)
      message.error(error.response?.data?.detail || 'Ошибка обновления теста')
    } finally {
      setLoading(false)
    }
  }


  if (!test) {
    return null
  }

  return (
    <Modal
      title={`Редактирование теста: ${test.lesson_title || 'Тест'}`}
      open={visible}
      onCancel={onCancel}
      width={900}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Отмена
        </Button>,
        <Button key="save" type="primary" onClick={handleSave} loading={loading}>
          Сохранить
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ test }}
      >
        <Form.Item name={['test', 'lesson_title']} hidden>
          <Input />
        </Form.Item>
        <Form.Item name={['test', 'lesson_goal']} hidden>
          <Input />
        </Form.Item>
        <Form.Item name={['test', 'total_questions']} hidden>
          <Input />
        </Form.Item>
        <Form.Item name={['test', 'passing_score_percent']} label="Процент для прохождения">
          <InputNumber min={0} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.List name={['test', 'questions']}>
          {(fields, { add, remove }) => (
            <>
              {fields.map((field, questionIndex) => (
                <Card
                  key={field.key}
                  title={`Вопрос ${questionIndex + 1}`}
                  extra={
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => remove(field.name)}
                    >
                      Удалить вопрос
                    </Button>
                  }
                  style={{ marginBottom: 16 }}
                >
                  <Form.Item
                    name={[field.name, 'question_text']}
                    label="Текст вопроса"
                    rules={[{ required: true, message: 'Введите текст вопроса' }]}
                  >
                    <Input.TextArea rows={3} placeholder="Введите текст вопроса" />
                  </Form.Item>

                  <Form.Item label="Варианты ответов">
                    <Form.List name={[field.name, 'options']}>
                      {(optionFields, { add: addOption, remove: removeOption }) => (
                        <>
                          {optionFields.map((optionField, optionIndex) => (
                            <div key={optionField.key} style={{ 
                              marginBottom: 12, 
                              padding: 12, 
                              border: '1px solid #2a2a2a', 
                              borderRadius: 4, 
                              backgroundColor: '#141414'
                            }}>
                              <Space direction="vertical" style={{ width: '100%' }} size="small">
                                <Form.Item
                                  name={[optionField.name, 'is_correct']}
                                  style={{ margin: 0 }}
                                >
                                  <Radio.Group>
                                    <Radio value={true} style={{ color: '#ffffff' }}>Правильный</Radio>
                                    <Radio value={false} style={{ color: '#ffffff' }}>Неправильный</Radio>
                                  </Radio.Group>
                                </Form.Item>
                                <Form.Item
                                  name={[optionField.name, 'option_text']}
                                  rules={[{ required: true, message: 'Введите вариант ответа' }]}
                                  style={{ margin: 0, width: '100%' }}
                                >
                                  <Input.TextArea 
                                    placeholder="Вариант ответа" 
                                    rows={2}
                                    style={{ 
                                      width: '100%',
                                      backgroundColor: '#1a1a1a',
                                      color: '#ffffff',
                                      border: '1px solid #2a2a2a'
                                    }}
                                    autoSize={{ minRows: 2, maxRows: 6 }}
                                  />
                                </Form.Item>
                                {optionFields.length > 2 && (
                                  <div style={{ textAlign: 'right' }}>
                                    <Button
                                      type="text"
                                      danger
                                      size="small"
                                      icon={<DeleteOutlined />}
                                      onClick={() => removeOption(optionField.name)}
                                    >
                                      Удалить вариант
                                    </Button>
                                  </div>
                                )}
                              </Space>
                            </div>
                          ))}
                          {optionFields.length < 6 && (
                            <Button
                              type="dashed"
                              onClick={() => {
                                addOption({
                                  option_text: '',
                                  is_correct: false
                                })
                              }}
                              block
                              icon={<PlusOutlined />}
                            >
                              Добавить вариант ответа
                            </Button>
                          )}
                        </>
                      )}
                    </Form.List>
                  </Form.Item>

                  <Form.Item
                    name={[field.name, 'explanation']}
                    label="Объяснение правильного ответа"
                  >
                    <Input.TextArea 
                      rows={5} 
                      placeholder="Объяснение (опционально)" 
                      autoSize={{ minRows: 5, maxRows: 10 }}
                      style={{
                        backgroundColor: '#1a1a1a',
                        color: '#ffffff',
                        border: '1px solid #2a2a2a'
                      }}
                    />
                  </Form.Item>
                </Card>
              ))}
              <Button
                type="dashed"
                onClick={() => {
                  add({
                    question_text: '',
                    options: [
                      { option_text: '', is_correct: true },
                      { option_text: '', is_correct: false }
                    ],
                    explanation: ''
                  })
                }}
                block
                icon={<PlusOutlined />}
              >
                Добавить вопрос
              </Button>
            </>
          )}
        </Form.List>
      </Form>
    </Modal>
  )
}

export default LessonTestEditor

