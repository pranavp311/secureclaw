import { useState, useRef, useEffect } from 'react'
import { PrivacyBadge } from './PrivacyBadge'
import { RoutingIndicator } from './RoutingIndicator'
import type { ChatMessage } from '../hooks/useChat'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (msg: string) => void
  onToolsPress: () => void
  disabled: boolean
}

export function ChatPanel({ messages, isLoading, onSend, onToolsPress, disabled }: Props) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', zIndex: 1 }}>
      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 16px',
        }}
      >
        <div style={{ maxWidth: 640, margin: '0 auto', width: '100%' }}>
          {messages.length === 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '60vh',
                textAlign: 'center',
                padding: '0 32px',
              }}
            >
              <p style={{ fontSize: 15, lineHeight: '25px', color: 'var(--t3)' }}>
                Every task is analysed on-device for confidentiality and efficiency.
                You choose whether it runs locally or in the cloud.
              </p>
              <p style={{ marginTop: 24, fontSize: 12, color: 'var(--t4)', letterSpacing: '0.3px' }}>
                Type a task below to get started
              </p>
            </div>
          )}

          {messages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 14 }}>
                  <div
                    style={{
                      background: 'var(--s3)',
                      borderRadius: 'var(--radius)',
                      borderBottomRightRadius: 4,
                      padding: '10px 16px',
                      maxWidth: '80%',
                    }}
                  >
                    <p style={{ fontSize: 14, lineHeight: '22px', color: 'var(--t1)', margin: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </p>
                  </div>
                </div>
              )
            }

            // Assistant message — styled like mobile AnalysisCard + ResultCard
            return (
              <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 14, width: '100%' }}>
                <div
                  style={{
                    background: 'var(--s1)',
                    border: '1px solid var(--b1)',
                    borderRadius: 'var(--radius)',
                    borderTopLeftRadius: 4,
                    padding: 16,
                    maxWidth: 540,
                    width: '100%',
                  }}
                >
                  {/* Label */}
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.6px',
                      color: 'var(--orange)',
                      marginBottom: 12,
                    }}
                  >
                    Result
                  </div>

                  {/* Meta row */}
                  {msg.routing && (
                    <div style={{ marginBottom: 14 }}>
                      <RoutingIndicator
                        source={msg.routing.source}
                        timeMs={msg.total_time_ms}
                        confidence={msg.routing.confidence}
                      />
                    </div>
                  )}

                  {/* Privacy badge */}
                  {msg.privacy && (
                    <div style={{ marginBottom: 14 }}>
                      <PrivacyBadge
                        riskLevel={msg.privacy.risk_level}
                        piiTypes={msg.privacy.pii_types}
                      />
                    </div>
                  )}

                  {/* Function calls */}
                  {msg.function_calls && msg.function_calls.length > 0 ? (
                    msg.function_calls.map((fc, i) => (
                      <div
                        key={i}
                        style={{
                          background: 'var(--s3)',
                          borderRadius: 8,
                          padding: 12,
                          marginBottom: 6,
                        }}
                      >
                        <div
                          style={{
                            fontFamily: 'Courier, monospace',
                            fontSize: 12,
                            color: 'var(--orange)',
                            fontWeight: 600,
                            marginBottom: 4,
                          }}
                        >
                          {fc.name}
                        </div>
                        {fc.arguments && Object.entries(fc.arguments).map(([k, v]) => (
                          <div key={k} style={{ fontFamily: 'Courier, monospace', fontSize: 12 }}>
                            <span style={{ color: 'var(--t3)' }}>{k}: </span>
                            <span style={{ color: 'var(--t1)' }}>{JSON.stringify(v)}</span>
                          </div>
                        ))}
                      </div>
                    ))
                  ) : null}

                  {/* Skill results */}
                  {msg.skill_results && msg.skill_results.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {msg.skill_results.map((sr, i) => (
                        <div
                          key={i}
                          style={{
                            background: sr.success ? 'var(--s3)' : 'var(--red-10)',
                            border: sr.success ? 'none' : '1px solid var(--red-border)',
                            borderRadius: 8,
                            padding: 12,
                            marginBottom: 6,
                          }}
                        >
                          <p
                            style={{
                              fontSize: 13,
                              lineHeight: '20px',
                              color: sr.success ? 'var(--t2)' : 'var(--red)',
                              margin: 0,
                              whiteSpace: 'pre-wrap',
                            }}
                          >
                            {sr.output}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Fallback text if no function calls */}
                  {(!msg.function_calls || msg.function_calls.length === 0) &&
                   (!msg.skill_results || msg.skill_results.length === 0) && (
                    <p style={{ fontSize: 13, lineHeight: '20px', color: 'var(--t2)', margin: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </p>
                  )}
                </div>
              </div>
            )
          })}

          {/* Loading indicator */}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 14 }}>
              <div
                style={{
                  background: 'var(--s1)',
                  border: '1px solid var(--b1)',
                  borderRadius: 'var(--radius)',
                  borderTopLeftRadius: 4,
                  padding: 16,
                }}
              >
                <div style={{ display: 'flex', gap: 5, paddingTop: 4, paddingBottom: 4 }}>
                  <div className="loading-dot" />
                  <div className="loading-dot" />
                  <div className="loading-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area — matches mobile InputBar */}
      <div
        style={{
          borderTop: '1px solid var(--b1)',
          background: 'var(--bg)',
          padding: '12px 16px 20px',
          position: 'relative',
          zIndex: 2,
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: 8,
            maxWidth: 640,
            margin: '0 auto',
            width: '100%',
          }}
        >
          <button
            type="button"
            onClick={onToolsPress}
            style={{
              height: 40,
              padding: '0 12px',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--b1)',
              background: 'transparent',
              color: 'var(--t3)',
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Tools
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your task..."
            disabled={disabled}
            rows={1}
            style={{
              flex: 1,
              minHeight: 40,
              maxHeight: 120,
              border: '1px solid var(--b1)',
              borderRadius: 'var(--radius)',
              background: 'var(--s1)',
              color: 'var(--t1)',
              fontSize: 14,
              padding: '10px 14px',
              lineHeight: '20px',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              opacity: disabled ? 0.5 : 1,
            }}
          />

          <button
            type="submit"
            disabled={!input.trim() || disabled}
            style={{
              width: 40,
              height: 40,
              borderRadius: 'var(--radius)',
              background: 'var(--orange)',
              border: 'none',
              cursor: !input.trim() || disabled ? 'not-allowed' : 'pointer',
              opacity: !input.trim() || disabled ? 0.25 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'opacity 0.15s',
            }}
          >
            <span style={{ color: '#000', fontSize: 18, fontWeight: 700 }}>↑</span>
          </button>
        </form>
      </div>
    </div>
  )
}
