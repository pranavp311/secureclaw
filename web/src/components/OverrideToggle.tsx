import type { RoutingOverride } from '../hooks/useChat'

interface Props {
  value: RoutingOverride
  onChange: (v: RoutingOverride) => void
}

const options: { value: RoutingOverride; label: string }[] = [
  { value: 'auto', label: 'Auto' },
  { value: 'local', label: 'Local' },
  { value: 'cloud', label: 'Cloud' },
]

export function OverrideToggle({ value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {options.map((opt) => {
        const active = value === opt.value
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--radius)',
              border: `1px solid ${active ? 'var(--orange)' : 'var(--b1)'}`,
              background: active ? 'var(--orange-10)' : 'transparent',
              color: active ? 'var(--orange)' : 'var(--t4)',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
              transition: 'all 0.15s',
            }}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
