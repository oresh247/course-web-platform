/**
 * IT-ONE Logo Component
 * Векторный логотип компании IT-ONE
 */

const ITOneLogo = ({ width = 100, height = 40, style = {} }) => {
  return (
    <div 
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'white',
        borderRadius: '8px',
        padding: '6px 12px',
        ...style
      }}
    >
      <svg 
        width={width} 
        height={height} 
        viewBox="0 0 100 40" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="it-one-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#5E8A30', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#2d4719', stopOpacity: 1 }} />
          </linearGradient>
        </defs>
        
        <text
          x="50"
          y="27"
          fontFamily="Arial, sans-serif"
          fontSize="18"
          fontWeight="700"
          letterSpacing="0.5"
          textAnchor="middle"
          fill="url(#it-one-gradient)"
        >
          IT_ONE
        </text>
      </svg>
    </div>
  )
}

export default ITOneLogo

