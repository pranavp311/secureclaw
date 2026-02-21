import React from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { colors, radius } from '../theme';

const ALL_TOOLS = [
  { key: 'get_weather', label: 'Get Weather' },
  { key: 'set_alarm', label: 'Set Alarm' },
  { key: 'send_message', label: 'Send Message' },
  { key: 'create_reminder', label: 'Create Reminder' },
  { key: 'search_contacts', label: 'Search Contacts' },
  { key: 'play_music', label: 'Play Music' },
  { key: 'set_timer', label: 'Set Timer' },
];

interface Props {
  visible: boolean;
  selected: Set<string>;
  threshold: number;
  onToggleTool: (key: string) => void;
  onThresholdChange: (value: number) => void;
  onClose: () => void;
}

const THRESHOLD_PRESETS = [0.7, 0.8, 0.9, 0.95, 0.99];

export default function ToolsModal({
  visible,
  selected,
  threshold,
  onToggleTool,
  onThresholdChange,
  onClose,
}: Props) {
  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Settings</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Text style={styles.closeBtnText}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.section}>Active Tools</Text>
          {ALL_TOOLS.map((tool) => {
            const isOn = selected.has(tool.key);
            return (
              <TouchableOpacity
                key={tool.key}
                style={[styles.toolRow, isOn && styles.toolRowOn]}
                onPress={() => onToggleTool(tool.key)}
                activeOpacity={0.7}
              >
                <Text style={[styles.toolLabel, isOn && styles.toolLabelOn]}>
                  {tool.label}
                </Text>
                <View style={[styles.check, isOn && styles.checkOn]}>
                  {isOn && <Text style={styles.checkMark}>✓</Text>}
                </View>
              </TouchableOpacity>
            );
          })}

          <Text style={[styles.section, { marginTop: 28 }]}>
            Confidence Threshold
          </Text>
          <Text style={styles.thresholdNote}>
            Requests at or above this confidence run locally.
          </Text>
          <View style={styles.presets}>
            {THRESHOLD_PRESETS.map((p) => (
              <TouchableOpacity
                key={p}
                style={[styles.preset, threshold === p && styles.presetOn]}
                onPress={() => onThresholdChange(p)}
              >
                <Text style={[styles.presetText, threshold === p && styles.presetTextOn]}>
                  {(p * 100).toFixed(0)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.b1,
  },
  title: {
    fontSize: 17,
    fontWeight: '600',
    color: colors.t1,
  },
  closeBtn: {
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  closeBtnText: {
    fontSize: 15,
    color: colors.orange,
    fontWeight: '500',
  },
  content: {
    padding: 20,
  },
  section: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    color: colors.t3,
    marginBottom: 12,
  },
  toolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.b1,
    marginBottom: 8,
  },
  toolRowOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange10,
  },
  toolLabel: {
    fontSize: 14,
    color: colors.t2,
  },
  toolLabelOn: {
    color: colors.t1,
    fontWeight: '500',
  },
  check: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: colors.b2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange,
  },
  checkMark: {
    color: '#000',
    fontSize: 12,
    fontWeight: '700',
  },
  thresholdNote: {
    fontSize: 12,
    color: colors.t3,
    marginBottom: 14,
    lineHeight: 18,
  },
  presets: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  preset: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.b1,
  },
  presetOn: {
    borderColor: colors.orange,
    backgroundColor: colors.orange10,
  },
  presetText: {
    fontSize: 13,
    color: colors.t3,
    fontWeight: '500',
  },
  presetTextOn: {
    color: colors.orange,
  },
});
