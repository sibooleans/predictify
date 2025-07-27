import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { createUserWithEmailAndPassword } from 'firebase/auth';
import auth from '../../config/authentication';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function SignupScreen() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    //make sure all 3 filled
    const createAccount = async () => {
        if (!username || !email || !password || !confirmPassword) {
            Alert.alert('Missing Fields', 'Please fill in all fields.');
            return;
        }
        //strong password. maybe can consider adding symbol and number also? seems unnecessary now tho
        if (password.length < 6) {
            Alert.alert('Weak password', 'Password must be at least 6 characters long.');
            return;
        }
        //check the string same.
        if (password !== confirmPassword) {
            Alert.alert('Error', 'Passwords do not match.');
            return;
        }
        //redirect from signup to login. only 4 first time.
        //flow is signup => login => home screen
        setLoading(true);
        try {
            await createUserWithEmailAndPassword(auth, email, password);
            try { //save it to the backend
                const response = await fetch('https://predictify-zcef.onrender.com/save-username', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username })
                });
        
                const result = await response.json();
                if (result.error) {
                    console.log('Username save failed:', result.error);
                }
            } catch (usernameError) {
                console.log('Username save failed:', usernameError);
        // if error caught means acct created but username not saved.
            }
            Alert.alert('Account Created', 'You can now log in with your new account.'); //again, alert for this?
            router.replace('/authent/login');
        } catch (err: any) {
            let errorMessage = 'Account creation failed. Please try again.';
            //throw error if probs.

            if (err.code === 'auth/email-already-in-use') {
                errorMessage = 'An account with this email already exists.';
            } else if (err.code === 'auth/invalid-email') {
                errorMessage = 'Please enter a valid email address.';
            } else if (err.code === 'auth/weak-password') {
                errorMessage = 'Password is too weak. Please choose a stronger password.';
            } else if (err.code === 'auth/network-request-failed') {
                errorMessage = 'Network error. Please check your connection.';
            }

            //consider adjusting abit so keyboard dont cover when typing itself. rn the keyboard covers some fields 
            //which could look a bit unprofesh?
      
            Alert.alert('Error', errorMessage);
        } finally {
            setLoading(false);
        }
    };
    return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Logo */}
      <View style={styles.header}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>📈</Text>
        </View>
        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Join Predictify today</Text>
      </View>

      {/* Form */}
      <View style={styles.form}>
        <View style={styles.inputContainer}>
          <Ionicons name="person-outline" size={20} color="#666" />
          <TextInput
            placeholder="Username"
            placeholderTextColor="#666"
            autoCapitalize="none"
            onChangeText={setUsername}
            style={styles.input}
          />
        </View>

        <View style={styles.inputContainer}>
          <Ionicons name="mail-outline" size={20} color="#666" />
          <TextInput
            placeholder="Email"
            placeholderTextColor="#666"
            autoCapitalize="none"
            keyboardType="email-address"
            onChangeText={setEmail}
            style={styles.input}
          />
        </View>

        <View style={styles.inputContainer}>
          <Ionicons name="lock-closed-outline" size={20} color="#666" />
          <TextInput
            placeholder="Password"
            placeholderTextColor="#666"
            secureTextEntry
            onChangeText={setPassword}
            style={styles.input}
          />
        </View>

        <View style={styles.inputContainer}>
          <Ionicons name="lock-closed-outline" size={20} color="#666" />
          <TextInput
            placeholder="Confirm Password"
            placeholderTextColor="#666"
            secureTextEntry
            onChangeText={setConfirmPassword}
            style={styles.input}
          />
        </View>

        <TouchableOpacity 
          style={styles.button}
          onPress={createAccount}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>Already have an account? </Text>
        <TouchableOpacity onPress={() => router.push('/authent/login')}>
          <Text style={styles.link}>Sign in here</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#111',
    borderWidth: 2,
    borderColor: '#00ccff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  logoText: {
    fontSize: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
  },
  form: {
    marginBottom: 32,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  input: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
    paddingVertical: 16,
    marginLeft: 12,
  },
  button: {
    backgroundColor: '#00ccff',
    borderRadius: 12,
    paddingVertical: 18,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerText: {
    color: '#aaa',
    fontSize: 16,
  },
  link: {
    color: '#00ccff',
    fontSize: 16,
    fontWeight: '600',
  },
});