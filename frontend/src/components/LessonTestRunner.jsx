import { Modal, Button, Card, Radio, Space, Progress, Result, message } from 'antd'
import { useState, useEffect } from 'react'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

const LessonTestRunner = ({
  visible,
  onCancel,
  test
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [isFinished, setIsFinished] = useState(false)
  const [results, setResults] = useState(null)

  useEffect(() => {
    if (visible && test) {
      // Сброс состояния при открытии
      setCurrentQuestionIndex(0)
      setAnswers({})
      setIsFinished(false)
      setResults(null)
    }
  }, [visible, test])

  if (!test || !test.questions) {
    return null
  }

  const questions = test.questions
  const currentQuestion = questions[currentQuestionIndex]
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100

  const handleAnswerSelect = (questionIndex, optionIndex) => {
    setAnswers({
      ...answers,
      [questionIndex]: optionIndex
    })
  }

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      finishTest()
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const finishTest = () => {
    let correctAnswers = 0
    const detailedResults = []

    questions.forEach((question, qIndex) => {
      const selectedOptionIndex = answers[qIndex]
      const correctOptionIndex = question.options.findIndex(opt => opt.is_correct)
      const isCorrect = selectedOptionIndex === correctOptionIndex

      if (isCorrect) {
        correctAnswers++
      }

      detailedResults.push({
        question: question.question_text,
        selectedOption: selectedOptionIndex !== undefined 
          ? question.options[selectedOptionIndex]?.option_text 
          : 'Не отвечено',
        correctOption: question.options[correctOptionIndex]?.option_text,
        isCorrect,
        explanation: question.explanation
      })
    })

    const score = Math.round((correctAnswers / questions.length) * 100)
    const passingScore = test.passing_score_percent || 70
    const passed = score >= passingScore

    setResults({
      score,
      correctAnswers,
      totalQuestions: questions.length,
      passed,
      detailedResults
    })
    setIsFinished(true)
  }

  const handleRestart = () => {
    setCurrentQuestionIndex(0)
    setAnswers({})
    setIsFinished(false)
    setResults(null)
  }

  if (isFinished && results) {
    return (
      <Modal
        title={`Результаты теста: ${test.lesson_title || 'Тест'}`}
        open={visible}
        onCancel={onCancel}
        width={800}
        footer={[
          <Button key="restart" onClick={handleRestart}>
            Пройти заново
          </Button>,
          <Button key="close" type="primary" onClick={onCancel}>
            Закрыть
          </Button>
        ]}
      >
        <Result
          status={results.passed ? 'success' : 'error'}
          title={results.passed ? 'Тест пройден!' : 'Тест не пройден'}
          subTitle={`Вы ответили правильно на ${results.correctAnswers} из ${results.totalQuestions} вопросов (${results.score}%)`}
        />

        <div style={{ marginTop: 24 }}>
          <Progress
            percent={results.score}
            status={results.passed ? 'success' : 'exception'}
            format={(percent) => `${percent}%`}
          />
        </div>

        <div style={{ marginTop: 24 }}>
          <h3>Детальные результаты:</h3>
          {results.detailedResults.map((result, index) => (
            <Card
              key={index}
              size="small"
              style={{ 
                marginBottom: 16,
                backgroundColor: '#141414',
                border: `1px solid ${result.isCorrect ? '#5E8A30' : '#ff4d4f'}`
              }}
              title={
                <Space>
                  {result.isCorrect ? (
                    <CheckCircleOutlined style={{ color: '#5E8A30' }} />
                  ) : (
                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                  )}
                  <span style={{ color: '#ffffff' }}>Вопрос {index + 1}</span>
                </Space>
              }
            >
              <p style={{ color: '#ffffff' }}><strong>Вопрос:</strong> {result.question}</p>
              <p style={{ 
                color: result.isCorrect ? '#5E8A30' : '#ff4d4f', 
                wordWrap: 'break-word', 
                whiteSpace: 'normal',
                backgroundColor: '#1a1a1a',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #2a2a2a'
              }}>
                <strong>Ваш ответ:</strong> <span style={{ display: 'block', marginTop: 4, color: '#ffffff' }}>{result.selectedOption}</span>
                {!result.isCorrect && (
                  <span style={{ display: 'block', marginTop: 8 }}>
                    <strong style={{ color: '#5E8A30' }}>Правильный ответ:</strong> 
                    <span style={{ display: 'block', marginTop: 4, color: '#ffffff' }}>{result.correctOption}</span>
                  </span>
                )}
              </p>
              {result.explanation && (
                <p style={{ 
                  marginTop: 8, 
                  fontStyle: 'italic', 
                  color: '#b0b0b0',
                  backgroundColor: '#1a1a1a',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #5E8A30'
                }}>
                  <strong>Объяснение:</strong> {result.explanation}
                </p>
              )}
            </Card>
          ))}
        </div>
      </Modal>
    )
  }

  return (
    <Modal
      title={`Прохождение теста: ${test.lesson_title || 'Тест'}`}
      open={visible}
      onCancel={onCancel}
      width={700}
      footer={[
        <Button key="prev" disabled={currentQuestionIndex === 0} onClick={handlePrevious}>
          Назад
        </Button>,
        <Button
          key="next"
          type="primary"
          onClick={handleNext}
          disabled={answers[currentQuestionIndex] === undefined}
        >
          {currentQuestionIndex === questions.length - 1 ? 'Завершить тест' : 'Далее'}
        </Button>
      ]}
    >
      <div style={{ marginBottom: 16 }}>
        <Progress percent={progress} />
        <div style={{ textAlign: 'center', marginTop: 8 }}>
          Вопрос {currentQuestionIndex + 1} из {questions.length}
        </div>
      </div>

      <Card style={{ backgroundColor: '#141414', border: '1px solid #2a2a2a' }}>
        <h3 style={{ marginBottom: 16, color: '#ffffff' }}>{currentQuestion.question_text}</h3>
        <Radio.Group
          value={answers[currentQuestionIndex]}
          onChange={(e) => handleAnswerSelect(currentQuestionIndex, e.target.value)}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {currentQuestion.options.map((option, optionIndex) => (
              <Radio 
                key={optionIndex} 
                value={optionIndex} 
                style={{ 
                  display: 'block', 
                  whiteSpace: 'normal', 
                  wordWrap: 'break-word',
                  padding: '12px',
                  lineHeight: '1.5',
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #2a2a2a',
                  borderRadius: '4px',
                  color: '#ffffff',
                  marginBottom: '8px'
                }}
              >
                <span style={{ display: 'inline-block', maxWidth: '100%', color: '#ffffff' }}>
                  {option.option_text}
                </span>
              </Radio>
            ))}
          </Space>
        </Radio.Group>
      </Card>
    </Modal>
  )
}

export default LessonTestRunner

