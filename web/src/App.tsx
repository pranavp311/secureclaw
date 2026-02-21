import { useState, useCallback } from 'react'
import { DotsBackground } from './components/DotsBackground'
import { ChatPanel } from './components/ChatPanel'
import { OverrideToggle } from './components/OverrideToggle'
import { SkillPanel } from './components/SkillPanel'
import { useChat } from './hooks/useChat'

const DEFAULT_TOOLS = new Set([
  'get_weather', 'set_alarm', 'send_message', 'create_reminder',
  'search_contacts', 'play_music', 'set_timer', 'web_browse',
  'file_read', 'file_write', 'file_list', 'calendar_add',
  'calendar_list', 'calendar_delete',
])

export default function App() {
  const {
    messages,
    isLoading,
    routingOverride,
    setRoutingOverride,
    sendMessage,
    clearMessages,
  } = useChat()

  const [showTools, setShowTools] = useState(false)
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set(DEFAULT_TOOLS))

  const toggleTool = useCallback((name: string) => {
    setSelectedTools((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  return (
    <div style={{ height: '100vh', width: '100vw', background: 'var(--bg)', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Interactive dots background */}
      <DotsBackground active={isLoading} />

      {/* Header — matches mobile Header */}
      <header
        style={{
          textAlign: 'center',
          paddingTop: 16,
          paddingBottom: 12,
          position: 'relative',
          zIndex: 1,
          flexShrink: 0,
        }}
      >
        <h1
          style={{
            fontSize: 36,
            fontWeight: 700,
            color: 'var(--t1)',
            letterSpacing: '-0.5px',
            margin: 0,
          }}
        >
          Secure<span style={{ color: 'var(--orange)' }}>Claw</span>
        </h1>
        <p
          style={{
            fontSize: 12,
            color: 'var(--t4)',
            marginTop: 6,
            letterSpacing: '0.2px',
          }}
        >
          Private AI inference, by default
        </p>

        {/* Routing override + clear */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            marginTop: 12,
          }}
        >
          <OverrideToggle value={routingOverride} onChange={setRoutingOverride} />
          <button
            onClick={clearMessages}
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--b1)',
              background: 'transparent',
              color: 'var(--t4)',
              fontSize: 11,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            Clear
          </button>
        </div>
      </header>

      {/* Main chat area */}
      <div style={{ flex: 1, minHeight: 0, position: 'relative', zIndex: 1 }}>
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          onToolsPress={() => setShowTools(true)}
          disabled={isLoading}
        />
      </div>

      {/* Tools modal overlay — matches mobile ToolsModal */}
      {showTools && (
        <>
          <div
            onClick={() => setShowTools(false)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              zIndex: 50,
            }}
          />
          <div
            style={{
              position: 'fixed',
              bottom: 0,
              left: 0,
              right: 0,
              zIndex: 51,
              background: 'var(--s1)',
              borderTop: '1px solid var(--b1)',
              borderRadius: '16px 16px 0 0',
              maxHeight: '70vh',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px 12px',
                borderBottom: '1px solid var(--b1)',
              }}
            >
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--t1)', margin: 0 }}>
                  Tools
                </h2>
                <p style={{ fontSize: 11, color: 'var(--t4)', marginTop: 4 }}>
                  {selectedTools.size} selected
                </p>
              </div>
              <button
                onClick={() => setShowTools(false)}
                style={{
                  padding: '8px 16px',
                  borderRadius: 'var(--radius)',
                  background: 'var(--orange)',
                  border: 'none',
                  color: '#000',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Done
              </button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 20px 20px' }}>
              <SkillPanel selected={selectedTools} onToggle={toggleTool} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
