import { Modal, Form, InputNumber, Button, message } from 'antd'
import { useState } from 'react'
import { coursesApi } from '../api/coursesApi'

const LessonTestGenerator = ({
  visible,
  onCancel,
  onSuccess,
  courseId,
  moduleNumber,
  lessonIndex,
  lessonTitle
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleGenerate = async (values) => {
    setLoading(true)
    try {
      const testData = {
        num_questions: values.num_questions || 10
      }
      
      const result = await coursesApi.generateLessonTest(
        courseId,
        moduleNumber,
        lessonIndex,
        testData
      )
      
      message.success('Тест успешно сгенерирован!')
      onSuccess?.(result.test)
      form.resetFields()
      onCancel()
    } catch (error) {
      console.error('Ошибка генерации теста:', error)
      message.error(error.response?.data?.detail || 'Ошибка генерации теста')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={`Сгенерировать тест для урока: ${lessonTitle}`}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleGenerate}
        initialValues={{
          num_questions: 10
        }}
      >
        <Form.Item
          label="Количество вопросов"
          name="num_questions"
          rules={[
            { required: true, message: 'Укажите количество вопросов' },
            { type: 'number', min: 5, max: 20, message: 'От 5 до 20 вопросов' }
          ]}
        >
          <InputNumber
            min={5}
            max={20}
            style={{ width: '100%' }}
            placeholder="10"
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            Сгенерировать тест
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default LessonTestGenerator

