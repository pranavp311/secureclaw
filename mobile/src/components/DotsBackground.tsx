import React, { useEffect, useRef } from 'react';
import { Dimensions, StyleSheet, View } from 'react-native';

const SPACING = 44;
const BASE_R = 2;
const TOUCH_R = 130;
const PUSH = 22;

type Dot = {
  hx: number;
  hy: number;
  ox: number;
  oy: number;
  phase: number;
  vref: React.RefObject<View | null>;
};

interface Props {
  touchX: React.MutableRefObject<number>;
  touchY: React.MutableRefObject<number>;
  active?: boolean;
}

export default function DotsBackground({ touchX, touchY, active }: Props) {
  const { width: W, height: H } = Dimensions.get('screen');

  const dots = useRef<Dot[]>([]);
  const pulsePhase = useRef(0);
  const activeAmount = useRef(0);
  const activeRef = useRef(active ?? false);

  // Build grid once (synchronously before first render)
  if (dots.current.length === 0) {
    const cols = Math.ceil(W / SPACING) + 1;
    const rows = Math.ceil(H / SPACING) + 1;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        dots.current.push({
          hx: c * SPACING,
          hy: r * SPACING,
          ox: 0,
          oy: 0,
          phase: Math.random() * Math.PI * 2,
          vref: React.createRef<View | null>(),
        });
      }
    }
  }

  useEffect(() => {
    activeRef.current = active ?? false;
  }, [active]);

  useEffect(() => {
    const cx = W / 2;
    const cy = H / 2;
    const maxDist = Math.sqrt(cx * cx + cy * cy);

    let raf: ReturnType<typeof requestAnimationFrame>;

    function frame() {
      pulsePhase.current += 0.03;

      const target = activeRef.current ? 1 : 0;
      activeAmount.current += (target - activeAmount.current) * 0.06;
      const aa = activeAmount.current;
      const breath = 0.6 + Math.sin(pulsePhase.current * 1.8) * 0.4;

      const mx = touchX.current;
      const my = touchY.current;

      for (const d of dots.current) {
        d.phase += 0.008;
        const fx = Math.sin(d.phase) * 1.5;
        const fy = Math.cos(d.phase * 0.7) * 1.5;

        const dx = d.hx - mx;
        const dy = d.hy - my;
        const dist = Math.sqrt(dx * dx + dy * dy);
        let px = 0;
        let py = 0;
        let bright = 0;

        if (dist < TOUCH_R && dist > 0) {
          const force = (1 - dist / TOUCH_R) * PUSH;
          px = (dx / dist) * force;
          py = (dy / dist) * force;
          bright = 1 - dist / TOUCH_R;
        }

        d.ox += (px + fx - d.ox) * 0.15;
        d.oy += (py + fy - d.oy) * 0.15;
        const x = d.hx + d.ox;
        const y = d.hy + d.oy;

        // Center-outward ripple for active state
        const distFromCenter = Math.sqrt((d.hx - cx) ** 2 + (d.hy - cy) ** 2);
        const rippleDelay = (distFromCenter / maxDist) * 2;
        const rippleWave = Math.sin(pulsePhase.current * 2 - rippleDelay * Math.PI) * 0.5 + 0.5;
        const orangeAmt = aa * rippleWave;

        const colorFactor = Math.max(bright, orangeAmt);
        const rc = Math.round(51 + (255 - 51) * colorFactor);
        const gc = Math.round(51 + (102 - 51) * colorFactor);
        const bc = Math.round(51 * (1 - colorFactor));

        const r = BASE_R + bright * 2 + aa * breath * 0.8;
        const alpha = Math.min(0.35 + bright * 0.5 + aa * breath * 0.25, 1);
        const diameter = r * 2;

        if (d.vref.current) {
          (d.vref.current as any).setNativeProps({
            style: {
              left: x - r,
              top: y - r,
              width: diameter,
              height: diameter,
              borderRadius: r,
              opacity: alpha,
              backgroundColor: `rgb(${rc},${gc},${bc})`,
            },
          });
        }
      }

      raf = requestAnimationFrame(frame);
    }

    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {dots.current.map((d, i) => (
        <View
          key={i}
          ref={d.vref as React.RefObject<View>}
          style={{
            position: 'absolute',
            left: d.hx - BASE_R,
            top: d.hy - BASE_R,
            width: BASE_R * 2,
            height: BASE_R * 2,
            borderRadius: BASE_R,
            backgroundColor: '#333',
            opacity: 0.35,
          }}
        />
      ))}
    </View>
  );
}
