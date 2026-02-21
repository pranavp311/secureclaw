import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { analyze, checkOpenClawStatus, execute } from './src/api';
import AnalysisCard from './src/components/AnalysisCard';
import DotsBackground from './src/components/DotsBackground';
import Header from './src/components/Header';
import InputBar from './src/components/InputBar';
import LoadingDots from './src/components/LoadingDots';
import ResultCard from './src/components/ResultCard';
import ToolsModal from './src/components/ToolsModal';
import { colors, radius } from './src/theme';
import { AnalysisData, Message } from './src/types';

const DEFAULT_TOOLS = new Set([
  'get_weather',
  'set_alarm',
  'send_message',
  'create_reminder',
  'search_contacts',
  'play_music',
  'set_timer',
]);

let msgIdCounter = 0;
function nextId() {
  return String(++msgIdCounter);
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set(DEFAULT_TOOLS));
  const [threshold, setThreshold] = useState(0.99);
  const [openclawAvail, setOpenclawAvail] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const listRef = useRef<FlatList>(null);
  const touchX = useRef(-9999);
  const touchY = useRef(-9999);

  // Track the current pending analysis so Execute can reference it
  const pendingAnalysis = useRef<{ id: string; data: AnalysisData; msg: string } | null>(null);

  useEffect(() => {
    checkOpenClawStatus()
      .then((s) => setOpenclawAvail(s.available))
      .catch(() => {});
  }, []);

  function scrollToBottom() {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  }

  function addMessage(msg: Message) {
    setMessages((prev) => [...prev, msg]);
    scrollToBottom();
  }

  function removeMessage(id: string) {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }

  function lockAllAnalysisCards() {
    setMessages((prev) =>
      prev.map((m) => (m.type === 'analysis' ? { ...m, locked: true } : m)),
    );
  }

  const handleSend = useCallback(
    async (text: string) => {
      if (busy) return;
      if (!selectedTools.size) {
        Alert.alert('No tools selected', 'Select at least one tool in Settings.');
        return;
      }

      setBusy(true);
      const loadingId = nextId();

      addMessage({ id: nextId(), type: 'user', text });
      addMessage({ id: loadingId, type: 'loading' });

      try {
        const data = await analyze(text, Array.from(selectedTools), threshold);
        removeMessage(loadingId);

        if (data.error) {
          addMessage({ id: nextId(), type: 'error', text: data.error });
        } else {
          const analysisId = nextId();
          pendingAnalysis.current = { id: analysisId, data, msg: text };
          addMessage({
            id: analysisId,
            type: 'analysis',
            data,
            originalMsg: text,
            locked: false,
          });
        }
      } catch (e: unknown) {
        removeMessage(loadingId);
        const msg = e instanceof Error ? e.message : 'Network error';
        addMessage({ id: nextId(), type: 'error', text: msg });
      }

      setBusy(false);
    },
    [busy, selectedTools, threshold],
  );

  const handleExecute = useCallback(
    async (mode: string) => {
      if (busy || !pendingAnalysis.current) return;
      setBusy(true);

      const { data: analysisData, msg } = pendingAnalysis.current;
      pendingAnalysis.current = null;
      lockAllAnalysisCards();

      const execLoadingId = nextId();
      addMessage({ id: execLoadingId, type: 'loading' });

      const cachedResult =
        mode === 'local'
          ? {
              function_calls: analysisData.function_calls,
              total_time_ms: analysisData.local_time_ms,
              confidence: analysisData.confidence,
            }
          : undefined;

      try {
        const result = await execute(msg, Array.from(selectedTools), mode, cachedResult);
        removeMessage(execLoadingId);
        addMessage({ id: nextId(), type: 'result', data: result, originalMsg: msg });
      } catch (e: unknown) {
        removeMessage(execLoadingId);
        const errMsg = e instanceof Error ? e.message : 'Network error';
        addMessage({
          id: nextId(),
          type: 'result',
          data: { source: 'error', error: errMsg },
          originalMsg: msg,
        });
      }

      setBusy(false);
    },
    [busy, selectedTools],
  );

  function toggleTool(key: string) {
    setSelectedTools((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  function renderItem({ item }: { item: Message }) {
    switch (item.type) {
      case 'user':
        return (
          <View style={styles.msgUser}>
            <View style={styles.userBubble}>
              <Text style={styles.userText}>{item.text}</Text>
            </View>
          </View>
        );

      case 'loading':
        return (
          <View style={styles.msgSys}>
            <View style={styles.sysBubble}>
              <LoadingDots />
            </View>
          </View>
        );

      case 'error':
        return (
          <View style={styles.msgSys}>
            <View style={styles.sysBubble}>
              <View style={styles.errBox}>
                <Text style={styles.errText}>{item.text}</Text>
              </View>
            </View>
          </View>
        );

      case 'analysis':
        return (
          <View style={styles.msgSys}>
            <AnalysisCard
              data={item.data}
              locked={item.locked}
              openclawAvail={openclawAvail}
              onExecute={handleExecute}
            />
          </View>
        );

      case 'result':
        return (
          <View style={styles.msgSys}>
            <ResultCard data={item.data} originalMsg={item.originalMsg} />
          </View>
        );
    }
  }

  return (
    <SafeAreaView
      style={styles.container}
      onTouchStart={(e) => {
        touchX.current = e.nativeEvent.pageX;
        touchY.current = e.nativeEvent.pageY;
      }}
      onTouchMove={(e) => {
        touchX.current = e.nativeEvent.pageX;
        touchY.current = e.nativeEvent.pageY;
      }}
      onTouchEnd={() => {
        touchX.current = -9999;
        touchY.current = -9999;
      }}
    >
      <DotsBackground touchX={touchX} touchY={touchY} active={busy} />
      <StatusBar style="light" />
      <Header />

      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        {messages.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>
              Every task is analysed on-device for confidentiality and efficiency.
              You choose whether it runs locally or in the cloud.
            </Text>
            <Text style={styles.emptyHint}>Type a task below to get started</Text>
          </View>
        ) : (
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderItem}
            contentContainerStyle={styles.messageList}
            onContentSizeChange={scrollToBottom}
          />
        )}

        <InputBar
          onSend={handleSend}
          onToolsPress={() => setShowTools(true)}
          disabled={busy}
        />
      </KeyboardAvoidingView>

      <ToolsModal
        visible={showTools}
        selected={selectedTools}
        threshold={threshold}
        onToggleTool={toggleTool}
        onThresholdChange={setThreshold}
        onClose={() => setShowTools(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  keyboardView: {
    flex: 1,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyText: {
    fontSize: 15,
    lineHeight: 25,
    color: colors.t3,
    textAlign: 'center',
  },
  emptyHint: {
    marginTop: 24,
    fontSize: 12,
    color: colors.t4,
    letterSpacing: 0.3,
  },
  messageList: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    maxWidth: 640,
    alignSelf: 'center',
    width: '100%',
  },
  msgUser: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 14,
  },
  userBubble: {
    backgroundColor: colors.s3,
    borderRadius: radius,
    borderBottomRightRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxWidth: '80%',
  },
  userText: {
    fontSize: 14,
    lineHeight: 22,
    color: colors.t1,
  },
  msgSys: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    marginBottom: 14,
    width: '100%',
  },
  sysBubble: {
    backgroundColor: colors.s1,
    borderWidth: 1,
    borderColor: colors.b1,
    borderRadius: radius,
    borderTopLeftRadius: 4,
    padding: 16,
    maxWidth: 540,
    width: '100%',
  },
  errBox: {
    backgroundColor: 'rgba(239,68,68,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: 10,
  },
  errText: {
    color: '#f87171',
    fontSize: 12,
  },
});
