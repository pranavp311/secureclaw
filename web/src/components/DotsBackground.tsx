import { useEffect, useRef } from 'react'

const SPACING = 44
const BASE_R = 2
const CURSOR_R = 130
const PUSH = 22

interface Dot {
  hx: number
  hy: number
  ox: number
  oy: number
  phase: number
}

interface Props {
  active: boolean
}

export function DotsBackground({ active }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: -9999, y: -9999 })
  const activeRef = useRef(active)
  const dotsRef = useRef<Dot[]>([])
  const pulsePhaseRef = useRef(0)
  const activeAmountRef = useRef(0)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    activeRef.current = active
  }, [active])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    function resize() {
      const dpr = window.devicePixelRatio || 1
      canvas!.width = window.innerWidth * dpr
      canvas!.height = window.innerHeight * dpr
      canvas!.style.width = window.innerWidth + 'px'
      canvas!.style.height = window.innerHeight + 'px'
      ctx!.scale(dpr, dpr)

      // Rebuild dot grid
      const W = window.innerWidth
      const H = window.innerHeight
      const cols = Math.ceil(W / SPACING) + 1
      const rows = Math.ceil(H / SPACING) + 1
      dotsRef.current = []
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          dotsRef.current.push({
            hx: c * SPACING,
            hy: r * SPACING,
            ox: 0,
            oy: 0,
            phase: Math.random() * Math.PI * 2,
          })
        }
      }
    }

    resize()
    window.addEventListener('resize', resize)

    function onMouseMove(e: MouseEvent) {
      mouseRef.current = { x: e.clientX, y: e.clientY }
    }
    function onMouseLeave() {
      mouseRef.current = { x: -9999, y: -9999 }
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)

    const W = () => window.innerWidth
    const H = () => window.innerHeight

    function frame() {
      const w = W()
      const h = H()
      const cx = w / 2
      const cy = h / 2
      const maxDist = Math.sqrt(cx * cx + cy * cy)

      ctx!.clearRect(0, 0, w, h)

      pulsePhaseRef.current += 0.03

      const target = activeRef.current ? 1 : 0
      activeAmountRef.current += (target - activeAmountRef.current) * 0.06
      const aa = activeAmountRef.current
      const breath = 0.6 + Math.sin(pulsePhaseRef.current * 1.8) * 0.4

      const mx = mouseRef.current.x
      const my = mouseRef.current.y

      for (const d of dotsRef.current) {
        d.phase += 0.008
        const fx = Math.sin(d.phase) * 1.5
        const fy = Math.cos(d.phase * 0.7) * 1.5

        const ddx = d.hx - mx
        const ddy = d.hy - my
        const dist = Math.sqrt(ddx * ddx + ddy * ddy)
        let bright = 0

        if (dist < CURSOR_R && dist > 0) {
          bright = 1 - dist / CURSOR_R
        }

        // No displacement — dots stay in place, only subtle float
        d.ox += (fx - d.ox) * 0.15
        d.oy += (fy - d.oy) * 0.15
        const x = d.hx + d.ox
        const y = d.hy + d.oy

        // Center-outward ripple for active (loading) state
        const distFromCenter = Math.sqrt((d.hx - cx) ** 2 + (d.hy - cy) ** 2)
        const rippleDelay = (distFromCenter / maxDist) * 2
        const rippleWave =
          Math.sin(pulsePhaseRef.current * 2 - rippleDelay * Math.PI) * 0.5 + 0.5
        const orangeAmt = aa * rippleWave

        // Cursor: grey (#333) → whiter (#aaa), no orange
        // Loading: grey (#333) → orange (#ff6600)
        const cursorWhite = bright * 0.5 // how much whiter from cursor
        const rc = Math.round(51 + (255 - 51) * orangeAmt + 120 * cursorWhite)
        const gc = Math.round(51 + (102 - 51) * orangeAmt + 120 * cursorWhite)
        const bc = Math.round(51 * (1 - orangeAmt) + 120 * cursorWhite)

        // Cursor: slightly enlarge. Loading: pulse size
        const r = BASE_R + bright * 1.2 + aa * breath * 0.8
        const alpha = Math.min(0.35 + bright * 0.35 + aa * breath * 0.25, 1)

        ctx!.beginPath()
        ctx!.arc(x, y, r, 0, Math.PI * 2)
        ctx!.fillStyle = `rgba(${rc},${gc},${bc},${alpha})`
        ctx!.fill()
      }

      rafRef.current = requestAnimationFrame(frame)
    }

    rafRef.current = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  )
}
