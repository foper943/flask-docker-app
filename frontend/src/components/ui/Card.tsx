import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

export default function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`rounded-xl border border-gray-200 bg-white p-5 shadow-sm
        ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}
        ${className}`}
    >
      {children}
    </div>
  )
}
