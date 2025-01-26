// Import the functions you need from the SDKs you need
import { initializeApp, FirebaseApp } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';
import { getFirestore, Firestore } from 'firebase/firestore';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDrkg1EYBcWe-BEPceGu_J9lHjvcal99ac",
  authDomain: "batterup-mlb-hack.firebaseapp.com",
  projectId: "batterup-mlb-hack",
  storageBucket: "batterup-mlb-hack.firebasestorage.app",
  messagingSenderId: "682091179679",
  appId: "1:682091179679:web:04a553cbff70cf6c1bbcaa"
};

// Initialize Firebase
export const app: FirebaseApp = initializeApp(firebaseConfig);
export const auth: Auth = getAuth(app);
export const db: Firestore = getFirestore(app);