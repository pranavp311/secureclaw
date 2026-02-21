import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme';

export default function Header() {
  return (
    <View style={styles.container}>
      <Text style={styles.logo}>
        Secure<Text style={styles.accent}>Claw</Text>
      </Text>
      <Text style={styles.tagline}>Private AI inference, by default</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 12,
  },
  logo: {
    fontSize: 36,
    fontWeight: '700',
    color: colors.t1,
    letterSpacing: -0.5,
  },
  accent: {
    color: colors.orange,
  },
  tagline: {
    fontSize: 12,
    color: colors.t4,
    marginTop: 6,
    letterSpacing: 0.2,
  },
});
