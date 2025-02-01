import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, onIdTokenChanged, User } from "firebase/auth";
import { auth } from "./firebase/config";
import { getFirestore, doc, getDoc } from "firebase/firestore";

// Initialize Firestore
const db = getFirestore();

interface AuthContextType {
  user: User | null;
  token: string | null;
  role: string | null;
  loading: boolean;
  logout: () => void;
}

// Create context
const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  role: null,
  loading: true,
  logout: () => {},
});

// AuthProvider Component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Monitor Authentication State
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setLoading(false);

      if (currentUser) {
        const idToken = await currentUser.getIdToken();
        setToken(idToken);
        localStorage.setItem("authToken", idToken);

        // Fetch role from Firestore
        const userDoc = await getDoc(doc(db, "users", currentUser.uid));
        if (userDoc.exists()) {
          setRole(userDoc.data().role);
        } else {
          setRole(null);
        }

        console.log("🔥 Access Token:", idToken); // ✅ Log Token in Console
      } else {
        setToken(null);
        setRole(null);
        localStorage.removeItem("authToken");
        console.log("⚠️ No user logged in.");
      }
    });

    return () => unsubscribe();
  }, []);

  // Automatic Token Refresh
  useEffect(() => {
    const storedToken = localStorage.getItem("authToken");
    if (storedToken) {
      setToken(storedToken);
    }

    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setLoading(false);

      if (currentUser) {
        const idToken = await currentUser.getIdToken();
        setToken(idToken);
        localStorage.setItem("authToken", idToken);
      } else {
        setToken(null);
        localStorage.removeItem("authToken");
      }
    });

    return () => unsubscribe();
  }, []);

  // Logout function
  const logout = async () => {
    await auth.signOut();
    setUser(null);
    setToken(null);
    setRole(null);
    localStorage.removeItem("authToken");
    console.log("🚪 User Logged Out.");
  };

  return (
    <AuthContext.Provider value={{ user, token, role, loading, logout }}>
      {loading ? <div>Loading...</div> : children}
    </AuthContext.Provider>
  );
};

// Hook for easy access to AuthContext
export const useAuth = () => useContext(AuthContext);
