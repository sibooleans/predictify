import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { signInWithEmailAndPassword } from 'firebase/auth';
import auth from '../../config/authentication';
import { Link } from 'expo-router';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function Login() {

    const [loginField, setLoginField] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter(); 

    const login = async () => {
        if (!loginField || !password) {
            Alert.alert('Missing info', 'Please enter both email and password.');
            return;
        }

        setLoading(true);
        //shud this be Alert.alert? seems a bit weird but it works. maybe the msg itself not needed.
        try {
            let emailToUse = loginField;
        
        // check for @ if not username - resolve it by match w email.
            if (!loginField.includes('@')) {
                try {
                    const response = await fetch('https://predictify-zcef.onrender.com/resolve-login', { //maybe can import api?
                        method: 'POST',
                        headers: {
                        'Content-Type': 'application/json',
                        },
                    body: JSON.stringify({ login_input: loginField })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    Alert.alert('Login Failed', 'Username not found.');
                    return;
                }
                
                emailToUse = result.email;
            } catch (resolveError) {
                console.log('Username resolution failed:', resolveError);
                // If username resolution fails, try original input as email
            }
        }
        await signInWithEmailAndPassword(auth, emailToUse, password);
        Alert.alert("Welcome back!', 'Login successful.");
        router.replace('/(tabs)');

            // still needa redirect to main screen
        } catch (error: any) {
            let errorMessage = "Login failed. Please try again.";

            if (error.code === 'auth/user-not-found') {
                errorMessage = 'No account found with this email.';
            } else if (error.code === 'auth/wrong-password') {
                errorMessage = 'Incorrect password.';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'Please enter a valid email address.';
            } else if (error.code === 'auth/too-many-requests') {
                errorMessage = 'Too many failed attempts. Please try again later.';
            } else if (error.code === 'auth/network-request-failed') {
                errorMessage = 'Network error. Please check your connection.';
            }
      
            Alert.alert('Login Failed', errorMessage);
        } finally {
        setLoading(false);
        }
    };
     //in the future shud implement a username system maybe.implemented. can use either username or email.
    return (
    <View style={styles.container}>
      {/* App header */}
      <View style={styles.header}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>📈</Text>
        </View>
        <Text style={styles.title}>Welcome Back</Text>
        <Text style={styles.subtitle}>Sign in to Predictify</Text>
      </View>

      {/* Form */}
      <View style={styles.form}>
        <View style={styles.inputContainer}>
          <Ionicons name="mail-outline" size={20} color="#666" />
          <TextInput
            placeholder="Email or Username"
            placeholderTextColor="#666"
            autoCapitalize="none"
            onChangeText={setLoginField}
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

        <TouchableOpacity 
          style={styles.button}
          onPress={login}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>Don't have an account? </Text>
        <Link href="/authent/signup" asChild>
          <TouchableOpacity>
            <Text style={styles.link}>Sign up here</Text>
          </TouchableOpacity>
        </Link>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    paddingHorizontal: 24,
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
    marginBottom: 40,
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