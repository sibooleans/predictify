import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import { Stack, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useColorScheme } from '@/hooks/useColorScheme';
import { onAuthStateChanged } from 'firebase/auth';
import auth from '../config/authentication';

export default function GlobalLayout() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const [isFontsLoaded] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
  });

  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        router.navigate('/(tabs)');
      } else {
        router.navigate('/authent/login');
      }
      setAuthChecked(true);
    });

    return unsubscribe;
  }, []);

  if (!isFontsLoaded || !authChecked) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    //<ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
    //for now, attempting to do a dark mode globally.
    //in the future, can provide options to choose light or dark mode under settings?
    <ThemeProvider value={DarkTheme}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="authent/login" />
        <Stack.Screen name="authent/signup" />
        <Stack.Screen name="+not-found" />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}
