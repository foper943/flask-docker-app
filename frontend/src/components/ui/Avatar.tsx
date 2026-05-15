interface AvatarProps {
  name: string
  src?: string | null
  size?: 'sm' | 'md' | 'lg'
}

const sizes = { sm: 'h-8 w-8 text-xs', md: 'h-10 w-10 text-sm', lg: 'h-16 w-16 text-xl' }

export default function Avatar({ name, src, size = 'md' }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={`${sizes[size]} rounded-full object-cover ring-2 ring-white`}
      />
    )
  }

  return (
    <div
      className={`${sizes[size]} flex items-center justify-center rounded-full
        bg-primary-100 font-semibold text-primary-700 ring-2 ring-white`}
    >
      {initials}
    </div>
  )
}
