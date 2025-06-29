import { getAuth } from 'firebase/auth';
import app from './firebaseConfig';

const auth = getAuth(app);
export default auth;

/*import { 
    initializeAuth, 
    // @ts-ignore
    getReactNativePersistence,
} from 'firebase/auth';
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';
import app from './firebaseConfig';

const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(ReactNativeAsyncStorage),
});

export default auth;

import { initializeAuth } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { app } from './firebaseConfig';

// SOLUTION: Import from react-native submodule
import { getReactNativePersistence } from 'firebase/auth/react-native';

const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage) // Now works
});

export default auth;*/