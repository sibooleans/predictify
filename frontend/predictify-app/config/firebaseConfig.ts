import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyA11dIbKm8qOjoIriVTKfxt26wnzb1wD9s",
  authDomain: "predictify-612a6.firebaseapp.com",
  projectId: "predictify-612a6",
  storageBucket: "predictify-612a6.appspot.com",
  messagingSenderId: "964071857392",
  appId: "1:964071857392:web:7bd856fefff1633319f635"
};

const app = initializeApp(firebaseConfig);

export default app;



