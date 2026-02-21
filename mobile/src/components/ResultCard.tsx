import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ResultData } from '../types';
import { colors, radius, fontMono } from '../theme';

interface Props {
  data: ResultData;
  originalMsg: string;
}

export default function ResultCard({ data, originalMsg }: Props) {
  const isLocal = (data.source ?? '').includes('on-device');

  return (
    <View style={styles.bubble}>
      <Text style={styles.label}>Result</Text>

      <View style={styles.meta}>
        <Text style={styles.metaSrc}>{data.source}</Text>
        {!!data.total_time_ms && (
          <Text style={styles.metaItem}>{data.total_time_ms.toFixed(0)}ms</Text>
        )}
        {data.confidence !== undefined && (
          <Text style={styles.metaItem}>{(data.confidence * 100).toFixed(1)}% conf</Text>
        )}
        <Text style={styles.metaItem}>{isLocal ? 'Private' : 'Cloud'}</Text>
      </View>

      {data.error ? (
        <View style={styles.fnCard}>
          <Text style={styles.fnNameFail}>{originalMsg} unsuccessful</Text>
          <View style={styles.errBox}>
            <Text style={styles.errText}>{data.error}</Text>
          </View>
        </View>
      ) : data.function_calls && data.function_calls.length > 0 ? (
        data.function_calls.map((fn, i) => (
          <View key={i} style={styles.fnCard}>
            <Text style={styles.fnName}>{originalMsg} successful!</Text>
            {Object.entries(fn.arguments ?? {}).map(([k, v]) => (
              <Text key={k} style={styles.fnRow}>
                <Text style={styles.fnKey}>{k}: </Text>
                <Text style={styles.fnVal}>{JSON.stringify(v)}</Text>
              </Text>
            ))}
          </View>
        ))
      ) : (
        <Text style={styles.noCalls}>No function calls generated.</Text>
      )}
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
    marginBottom: 12,
  },
  meta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 14,
    marginBottom: 14,
  },
  metaSrc: {
    fontSize: 11,
    color: colors.orange,
    fontWeight: '600',
  },
  metaItem: {
    fontSize: 11,
    color: colors.t3,
  },
  fnCard: {
    backgroundColor: colors.s3,
    borderRadius: 8,
    padding: 12,
    marginBottom: 6,
  },
  fnName: {
    fontFamily: fontMono,
    fontSize: 12,
    color: colors.orange,
    fontWeight: '600',
    marginBottom: 4,
  },
  fnNameFail: {
    fontFamily: fontMono,
    fontSize: 12,
    color: colors.red,
    fontWeight: '600',
    marginBottom: 4,
  },
  fnRow: {
    fontFamily: fontMono,
    fontSize: 12,
  },
  fnKey: {
    color: colors.t3,
  },
  fnVal: {
    color: colors.t1,
  },
  errBox: {
    backgroundColor: colors.red10,
    borderWidth: 1,
    borderColor: colors.redBorder,
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
  },
  errText: {
    color: colors.red,
    fontSize: 12,
  },
  noCalls: {
    color: colors.t4,
    fontSize: 12,
    marginTop: 8,
  },
});
