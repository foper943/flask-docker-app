import { type ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  color?: 'indigo' | 'green' | 'yellow' | 'red' | 'gray'
}

const colors = {
  indigo: 'bg-indigo-100 text-indigo-700',
  green:  'bg-green-100 text-green-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  red:    'bg-red-100 text-red-700',
  gray:   'bg-gray-100 text-gray-700',
}

export default function Badge({ children, color = 'indigo' }: BadgeProps) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[color]}`}>
      {children}
    </span>
  )
}
