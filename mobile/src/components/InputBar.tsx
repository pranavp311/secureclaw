import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { colors, radius } from '../theme';

interface Props {
  onSend: (text: string) => void;
  onToolsPress: () => void;
  disabled: boolean;
}

export default function InputBar({ onSend, onToolsPress, disabled }: Props) {
  const [text, setText] = useState('');

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  }

  return (
    <View style={styles.container}>
      <View style={styles.wrap}>
        <TouchableOpacity style={styles.toolsBtn} onPress={onToolsPress}>
          <Text style={styles.toolsBtnText}>Tools</Text>
        </TouchableOpacity>

        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          placeholder="Describe your task..."
          placeholderTextColor={colors.t4}
          multiline
          maxLength={2000}
          onSubmitEditing={handleSend}
          blurOnSubmit={false}
          returnKeyType="send"
          editable={!disabled}
        />

        <TouchableOpacity
          style={[styles.sendBtn, (!text.trim() || disabled) && styles.sendBtnDisabled]}
          onPress={handleSend}
          disabled={!text.trim() || disabled}
          activeOpacity={0.8}
        >
          {/* Up arrow */}
          <Text style={styles.arrow}>↑</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderTopWidth: 1,
    borderTopColor: colors.b1,
    backgroundColor: colors.bg,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 20,
  },
  wrap: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    maxWidth: 640,
    alignSelf: 'center',
    width: '100%',
  },
  toolsBtn: {
    height: 40,
    paddingHorizontal: 12,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.b1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  toolsBtnText: {
    fontSize: 12,
    color: colors.t3,
    fontWeight: '500',
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: colors.b1,
    borderRadius: radius,
    backgroundColor: colors.s1,
    color: colors.t1,
    fontSize: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    lineHeight: 20,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: radius,
    backgroundColor: colors.orange,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnDisabled: {
    opacity: 0.25,
  },
  arrow: {
    color: '#000',
    fontSize: 18,
    fontWeight: '700',
  },
});
