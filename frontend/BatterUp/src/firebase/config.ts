import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCnKcvyn3lVIrWuo6J6wgTjCIEZwGgvdoY",
  authDomain: "batterup-mlb-hack.firebaseapp.com",
  projectId: "batterup-mlb-hack",
  storageBucket: "batterup-mlb-hack.firebasestorage.app",
  messagingSenderId: "682091179679",
  appId: "1:682091179679:web:04a553cbff70cf6c1bbcaa"
};


// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);