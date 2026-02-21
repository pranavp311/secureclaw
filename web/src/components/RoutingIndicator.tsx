interface Props {
  source: string
  timeMs?: number
  confidence?: number
}

export function RoutingIndicator({ source, timeMs, confidence }: Props) {
  const isLocal = source.includes('on-device') || source.includes('local')

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 11, color: 'var(--orange)', fontWeight: 600 }}>
        {source}
      </span>
      {timeMs !== undefined && (
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>{timeMs.toFixed(0)}ms</span>
      )}
      {confidence !== undefined && (
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>
          {(confidence * 100).toFixed(1)}% conf
        </span>
      )}
      <span style={{ fontSize: 11, color: 'var(--t3)' }}>
        {isLocal ? 'Private' : 'Cloud'}
      </span>
    </div>
  )
}
