import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { AnalysisData } from '../types';
import { colors, radius } from '../theme';

interface Props {
  data: AnalysisData;
  locked: boolean;
  openclawAvail: boolean;
  onExecute: (mode: string) => void;
}

export default function AnalysisCard({ data, locked, openclawAvail, onExecute }: Props) {
  const [selMode, setSelMode] = useState<'local' | 'cloud'>(data.recommendation);
  const [cloudProv, setCloudProv] = useState<'gemini' | 'openclaw'>('gemini');

  const pct = (data.confidence * 100).toFixed(1);
  const isLocal = data.recommendation === 'local';
  const rec = isLocal
    ? 'Confidence meets threshold. Recommended to run locally — data stays on your device.'
    : 'Confidence below threshold. Cloud execution recommended for higher accuracy.';

  function handlePick(mode: 'local' | 'cloud') {
    if (locked) return;
    setSelMode(mode);
  }

  function handleSetProv(prov: 'gemini' | 'openclaw') {
    if (locked) return;
    if (prov === 'openclaw' && !openclawAvail) return;
    setCloudProv(prov);
    setSelMode('cloud');
  }

  function handleExecute() {
    const mode = selMode === 'local' ? 'local' : cloudProv;
    onExecute(mode);
  }

  return (
    <View style={styles.bubble}>
      <Text style={styles.label}>Analysis</Text>

      <View style={styles.confRow}>
        <Text style={styles.confNum}>{pct}</Text>
        <Text style={styles.confPct}>% confidence</Text>
      </View>

      <View style={styles.track}>
        <View style={[styles.fill, { width: `${Math.max(data.confidence * 100, 1.5)}%` as any }]} />
      </View>

      <View style={styles.recBox}>
        <Text style={styles.recText}>{rec}</Text>
      </View>

      <View style={[styles.options, locked && styles.optionsLocked]}>
        {/* Local option */}
        <TouchableOpacity
          style={[styles.opt, selMode === 'local' && styles.optOn]}
          onPress={() => handlePick('local')}
          activeOpacity={locked ? 1 : 0.7}
        >
          <View style={styles.optHd}>
            <Text style={styles.optTitle}>Local</Text>
            <View style={[styles.optDot, selMode === 'local' && styles.optDotOn]} />
          </View>
          <Text style={styles.optMeta}>{data.local_time_ms.toFixed(0)}ms measured{'\n'}On-device inference</Text>
          <View style={styles.tagPriv}>
            <Text style={styles.tagPrivText}>Private</Text>
          </View>
        </TouchableOpacity>

        {/* Cloud option */}
        <TouchableOpacity
          style={[styles.opt, selMode === 'cloud' && styles.optOn]}
          onPress={() => handlePick('cloud')}
          activeOpacity={locked ? 1 : 0.7}
        >
          <View style={styles.optHd}>
            <Text style={styles.optTitle}>Cloud</Text>
            <View style={[styles.optDot, selMode === 'cloud' && styles.optDotOn]} />
          </View>
          <Text style={styles.optMeta}>~1–3s estimated{'\n'}Higher accuracy</Text>
          <View style={styles.tagApi}>
            <Text style={styles.tagApiText}>API</Text>
          </View>
          <View style={styles.provRow}>
            <TouchableOpacity
              style={[styles.provBtn, cloudProv === 'gemini' && styles.provBtnOn]}
              onPress={() => handleSetProv('gemini')}
              disabled={locked}
            >
              <Text style={[styles.provBtnText, cloudProv === 'gemini' && styles.provBtnTextOn]}>
                Gemini
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.provBtn, cloudProv === 'openclaw' && styles.provBtnOn, !openclawAvail && styles.provBtnDisabled]}
              onPress={() => handleSetProv('openclaw')}
              disabled={locked || !openclawAvail}
            >
              <Text style={[styles.provBtnText, cloudProv === 'openclaw' && styles.provBtnTextOn, !openclawAvail && styles.provBtnTextDisabled]}>
                OpenClaw
              </Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.execBtn, locked && styles.execBtnDisabled]}
        onPress={handleExecute}
        disabled={locked}
        activeOpacity={0.8}
      >
        <Text style={styles.execBtnText}>
          Execute {selMode === 'local' ? 'locally' : 'on cloud'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  bubble: {
    backgroundColor: colors.s1,
    borderWidth: 1,
    borderColor: colors.b1,
    borderRadius: radius,
    borderTopLeftRadius: 4,
    padding: 16,
    maxWidth: 540,
    width: '100%',
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    color: colors.orange,
    marginBottom: 16,
  },
  confRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    marginBottom: 8,
  },
  confNum: {
    fontSize: 28,
    fontWeight: '700',
    fontFamily: 'Courier',
    color: colors.t1,
  },
  confPct: {
    fontSize: 13,
    color: colors.t3,
    marginBottom: 4,
  },
  track: {
    height: 3,
    backgroundColor: colors.s3,
    borderRadius: 2,
    marginBottom: 20,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: colors.orange,
    borderRadius: 2,
  },
  recBox: {
    backgroundColor: colors.orange10,
    borderLeftWidth: 2,
    borderLeftColor: colors.orange,
    borderRadius: 8,
    padding: 10,
    marginBottom: 20,
  },
  recText: {
    fontSize: 12,
    lineHeight: 19,
    color: colors.t3,
  },
  options: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 14,
  },
  optionsLocked: {
    opacity: 0.6,
  },
  opt: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.b1,
    borderRadius: 8,
    padding: 14,
  },
  optOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange10,
  },
  optHd: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  optTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.t1,
  },
  optDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: colors.b1,
  },
  optDotOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange,
  },
  optMeta: {
    fontSize: 11,
    color: colors.t3,
    lineHeight: 18,
  },
  tagPriv: {
    alignSelf: 'flex-start',
    backgroundColor: colors.green10,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginTop: 6,
  },
  tagPrivText: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.green,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  tagApi: {
    alignSelf: 'flex-start',
    backgroundColor: colors.indigo10,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginTop: 6,
  },
  tagApiText: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.indigo,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  provRow: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 10,
  },
  provBtn: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: colors.b1,
  },
  provBtnOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange10,
  },
  provBtnDisabled: {
    opacity: 0.25,
  },
  provBtnText: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.t4,
    textTransform: 'uppercase',
  },
  provBtnTextOn: {
    color: colors.orange,
  },
  provBtnTextDisabled: {
    color: colors.t4,
  },
  execBtn: {
    backgroundColor: colors.orange,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  execBtnDisabled: {
    opacity: 0.35,
  },
  execBtnText: {
    color: '#000',
    fontSize: 13,
    fontWeight: '600',
  },
});
