import { useState, useRef, useCallback, useEffect } from 'react'

export type RoutingOverride = 'auto' | 'local' | 'cloud'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  privacy?: {
    risk_level: string
    pii_types: string[]
    recommendation: string
    summary: string
  }
  routing?: {
    source: string
    override: string
    confidence: number
  }
  function_calls?: Array<{ name: string; arguments: Record<string, any> }>
  skill_results?: Array<{
    skill: string
    success: boolean
    output: string
    data: any
  }>
  total_time_ms?: number
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [routingOverride, setRoutingOverride] = useState<RoutingOverride>('auto')
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const idCounter = useRef(0)

  const genId = () => `msg-${++idCounter.current}-${Date.now()}`

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    function connect() {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        wsRef.current = ws
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        // Reconnect after 2s
        setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        ws.close()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'typing') {
            setIsLoading(data.status)
            return
          }

          if (data.type === 'response') {
            setIsLoading(false)
            const assistantMsg: ChatMessage = {
              id: genId(),
              role: 'assistant',
              content: data.message || 'No response.',
              timestamp: Date.now(),
              privacy: data.privacy,
              routing: data.routing,
              function_calls: data.function_calls,
              skill_results: data.skill_results,
              total_time_ms: data.total_time_ms,
            }
            setMessages((prev) => [...prev, assistantMsg])
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    connect()

    return () => {
      wsRef.current?.close()
    }
  }, [])

  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim()) return

      const userMsg: ChatMessage = {
        id: genId(),
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      // Try WebSocket first, fall back to REST
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            message: content.trim(),
            routing_override: routingOverride,
          })
        )
      } else {
        // REST fallback
        fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content.trim(),
            routing_override: routingOverride,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            setIsLoading(false)
            const assistantMsg: ChatMessage = {
              id: genId(),
              role: 'assistant',
              content: data.message || 'No response.',
              timestamp: Date.now(),
              privacy: data.privacy,
              routing: data.routing,
              function_calls: data.function_calls,
              skill_results: data.skill_results,
              total_time_ms: data.total_time_ms,
            }
            setMessages((prev) => [...prev, assistantMsg])
          })
          .catch(() => {
            setIsLoading(false)
            const errorMsg: ChatMessage = {
              id: genId(),
              role: 'assistant',
              content: 'Failed to connect to the agent server.',
              timestamp: Date.now(),
            }
            setMessages((prev) => [...prev, errorMsg])
          })
      }
    },
    [routingOverride]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isLoading,
    isConnected,
    routingOverride,
    setRoutingOverride,
    sendMessage,
    clearMessages,
  }
}
