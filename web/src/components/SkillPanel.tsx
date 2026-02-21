import { useState, useEffect } from 'react'

interface SkillInfo {
  name: string
  description: string
  parameters: Record<string, any>
}

interface Props {
  selected: Set<string>
  onToggle: (name: string) => void
}

export function SkillPanel({ selected, onToggle }: Props) {
  const [skills, setSkills] = useState<SkillInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/skills')
      .then((r) => r.json())
      .then((data: SkillInfo[]) => {
        setSkills(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ padding: 24, color: 'var(--t4)', fontSize: 12, textAlign: 'center' }}>
        Loading tools...
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {skills.map((skill) => {
        const isOn = selected.has(skill.name)
        return (
          <button
            key={skill.name}
            onClick={() => onToggle(skill.name)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 8,
              border: `1px solid ${isOn ? 'var(--orange)' : 'var(--b1)'}`,
              background: isOn ? 'var(--orange-10)' : 'transparent',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s',
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 7,
                border: `2px solid ${isOn ? 'var(--orange)' : 'var(--b1)'}`,
                background: isOn ? 'var(--orange)' : 'transparent',
                flexShrink: 0,
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: isOn ? 'var(--t1)' : 'var(--t3)',
                  fontFamily: 'Courier, monospace',
                }}
              >
                {skill.name}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: 'var(--t4)',
                  marginTop: 2,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {skill.description}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
