import React, { useState } from "react";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  UserCredential,
} from "firebase/auth";
import { auth } from "./firebase/config"; // Adjust the path as needed

const AuthForm: React.FC = () => {
  // Toggles between "Login" and "Register"
  const [isLoginMode, setIsLoginMode] = useState(true);

  // Email/password states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Loading + message states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Handle form submission for Email/Password
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      let userCredential: UserCredential;

      if (isLoginMode) {
        // LOGIN with email/password
        userCredential = await signInWithEmailAndPassword(
          auth,
          email,
          password
        );
        setSuccessMessage(`Welcome back, ${userCredential.user.email}!`);
      } else {
        // REGISTER with email/password
        userCredential = await createUserWithEmailAndPassword(
          auth,
          email,
          password
        );
        setSuccessMessage(`Account created for ${userCredential.user.email}!`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Google Sign-in
  const handleGoogleSignIn = async () => {
    setError(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      // You can access user info via result.user
      setSuccessMessage(`Welcome, ${result.user.displayName}!`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Switch between Login & Register mode
  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setError(null);
    setSuccessMessage(null);
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>{isLoginMode ? "Login" : "Register"}</h2>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label htmlFor="email" style={styles.label}>
              Email
            </label>
            <input
              id="email"
              type="email"
              style={styles.input}
              placeholder="Enter email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label htmlFor="password" style={styles.label}>
              Password
            </label>
            <input
              id="password"
              type="password"
              style={styles.input}
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <p style={styles.error}>{error}</p>}
          {successMessage && <p style={styles.success}>{successMessage}</p>}

          <button type="submit" style={styles.submitButton} disabled={loading}>
            {loading ? "Please wait..." : isLoginMode ? "Login" : "Register"}
          </button>
        </form>

        <div style={styles.divider}>
          <span style={styles.dividerLine} />
          <span style={styles.dividerText}>OR</span>
          <span style={styles.dividerLine} />
        </div>

        <button
          onClick={handleGoogleSignIn}
          style={styles.googleButton}
          disabled={loading}>
          {loading ? "Please wait..." : "Sign in with Google"}
        </button>

        <div style={styles.toggleContainer}>
          <p>
            {isLoginMode
              ? "Don't have an account?"
              : "Already have an account?"}
          </p>
          <button onClick={toggleMode} style={styles.toggleButton}>
            {isLoginMode ? "Register" : "Login"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthForm;

// Inline styles for demonstration; feel free to replace with your own
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f0f2f5",
    fontFamily: "Arial, sans-serif",
  },
  card: {
    width: "350px",
    background: "#fff",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    textAlign: "center",
  },
  title: {
    marginBottom: "1rem",
    fontWeight: 600,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    marginTop: "1rem",
  },
  formGroup: {
    marginBottom: "1rem",
    textAlign: "left",
  },
  label: {
    display: "block",
    marginBottom: "0.5rem",
  },
  input: {
    width: "100%",
    padding: "0.5rem",
    borderRadius: "4px",
    border: "1px solid #ccc",
    boxSizing: "border-box",
  },
  error: {
    color: "red",
    margin: "0.5rem 0",
  },
  success: {
    color: "green",
    margin: "0.5rem 0",
    fontWeight: 600,
  },
  submitButton: {
    backgroundColor: "#007bff",
    color: "#fff",
    padding: "0.75rem",
    fontSize: "1rem",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  divider: {
    display: "flex",
    alignItems: "center",
    margin: "1rem 0",
  },
  dividerLine: {
    flex: 1,
    height: "1px",
    backgroundColor: "#ccc",
  },
  dividerText: {
    margin: "0 0.5rem",
    color: "#999",
  },
  googleButton: {
    backgroundColor: "#4285F4",
    color: "#fff",
    padding: "0.75rem",
    fontSize: "1rem",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    width: "100%",
  },
  toggleContainer: {
    marginTop: "1rem",
  },
  toggleButton: {
    marginLeft: "0.5rem",
    backgroundColor: "transparent",
    color: "#007bff",
    border: "none",
    cursor: "pointer",
    textDecoration: "underline",
    padding: 0,
    fontSize: "1rem",
  },
};
