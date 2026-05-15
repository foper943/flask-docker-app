interface StarRatingProps {
  value: number
  max?: number
  onChange?: (v: number) => void
  size?: 'sm' | 'md'
}

export default function StarRating({ value, max = 5, onChange, size = 'md' }: StarRatingProps) {
  const starSize = size === 'sm' ? 'text-base' : 'text-2xl'

  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange?.(star)}
          className={`${starSize} leading-none ${onChange ? 'cursor-pointer' : 'cursor-default'}
            ${star <= value ? 'text-yellow-400' : 'text-gray-300'}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}
