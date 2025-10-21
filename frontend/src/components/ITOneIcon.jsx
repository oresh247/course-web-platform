/**
 * IT-ONE Icon Component
 * SVG иконка логотипа IT-ONE
 */

const ITOneIcon = ({ size = 24, color = '#5E8A30' }) => {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      {/* IT. */}
      <text 
        x="2" 
        y="8" 
        fontFamily="Arial, sans-serif" 
        fontSize="8" 
        fontWeight="bold" 
        fill={color}
      >
        IT.
      </text>
      
      {/* Green Diamond Symbol - стилизованный символ вместо O */}
      <g transform="translate(8, 4)">
        {/* Двойные шевроны, образующие ромб */}
        <path d="M1 0 L3 2 L1 4 L-1 2 Z" fill={color}/>
        <path d="M3 0 L5 2 L3 4 L1 2 Z" fill={color}/>
        <path d="M1 2 L3 4 L1 6 L-1 4 Z" fill={color}/>
        <path d="M3 2 L5 4 L3 6 L1 4 Z" fill={color}/>
      </g>
      
      {/* NE */}
      <text 
        x="14" 
        y="8" 
        fontFamily="Arial, sans-serif" 
        fontSize="8" 
        fontWeight="bold" 
        fill={color}
      >
        NE
      </text>
    </svg>
  )
}

export default ITOneIcon
