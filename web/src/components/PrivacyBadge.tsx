interface Props {
  riskLevel: string
  piiTypes?: string[]
}

export function PrivacyBadge({ riskLevel, piiTypes = [] }: Props) {
  const config: Record<string, { cls: string; label: string }> = {
    low: { cls: 'badge-green', label: 'Private' },
    medium: { cls: 'badge-orange', label: 'Caution' },
    high: { cls: 'badge-red', label: 'Sensitive' },
  }

  const c = config[riskLevel] || config.low

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span className={`badge ${c.cls}`}>{c.label}</span>
      {piiTypes.length > 0 && (
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>
          {piiTypes.join(', ')}
        </span>
      )}
    </div>
  )
}
