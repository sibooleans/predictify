import { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
import { useRouter } from 'expo-router';
import auth from '../../config/authentication'

export default function ProfileScreen() {
  const [email, setEmail] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user && user.email) {
        setEmail(user.email);
      } else {
        setEmail(null);
      }
    });
    return unsubscribe;
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      router.replace('/authent/login');
    } catch (error) {
      console.error('Sign out error:', error);
      alert('Failed to sign out');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>My Account</Text>
      {email ? (
        <>
          <Text style={styles.email}>Logged in as: {email}</Text>
          <Button title="Sign Out" onPress={handleSignOut} />
        </>
      ) : (
        <Text style={styles.email}>Loading user info...</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    textAlign: 'center',
    marginBottom: 24,
  },
  email: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 24,
  },
});
