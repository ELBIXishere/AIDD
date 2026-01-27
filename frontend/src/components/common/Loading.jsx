/**
 * 로딩 스피너 컴포넌트
 */
export default function Loading({ size = 'md', message = '' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }
  
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className={`${sizes[size]} border-2 border-accent border-t-transparent rounded-full animate-spin`} />
      {message && (
        <p className="text-sm text-slate-400">{message}</p>
      )}
    </div>
  )
}
