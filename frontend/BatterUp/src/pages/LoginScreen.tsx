import React, { useState } from "react";
import {
  getAuth,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../api"; // Import updated apiRequest
import firebase from "firebase/compat/app";

const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState(false); // Toggle Login/Register
  const navigate = useNavigate();
  const auth = getAuth();
  const provider = new GoogleAuthProvider();

  // Handle Email/Password Authentication
  const handleAuth = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    try {
      let userCredential;
      if (isRegistering) {
        // Register New User
        userCredential = await createUserWithEmailAndPassword(
          auth,
          email,
          password
        );
      } else {
        // Login Existing User
        userCredential = await signInWithEmailAndPassword(
          auth,
          email,
          password
        );
      }

      const user = userCredential.user;
      const token = await user.getIdToken(true); // Get Firebase token

      if (isRegistering) {
        // Send user registration data to backend with the token
        await apiRequest(
          "/auth/register",
          "POST",
          {
            email: user.email,
            username: email.split("@")[0], // Use email prefix as username
            role: "user", // Default role
            firebase_uid: user.uid,
          },
          token
        ); // Pass token here
      }

      navigate("/"); // ✅ Redirect to dashboard after successful login/signup
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Google Sign-In
  const handleGoogleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      const token = await user.getIdToken(true); // Get Firebase token

      console.log("Google User:", user);
      console.log("email", user.email);
      console.log("username", user.displayName || email.split("@")[0]);
      console.log("token", user.uid);
      console.log("token", token);

      // Send user registration to backend with token
      await apiRequest(
        "/auth/register",
        "POST",
        {
          email: user.email,
          username: user.displayName || email.split("@")[0], // Use Google name or email prefix
          role: "user",
          firebase_uid: user.uid,
        },
        token
      ); // Pass token here

      navigate("/"); // ✅ Redirect on success
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg w-96">
        <h2 className="text-2xl font-bold text-center mb-6">
          {isRegistering ? "Sign Up" : "Login"}
        </h2>

        {/* Error Message */}
        {error && (
          <p className="text-red-500 text-sm text-center mb-4">{error}</p>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          <div>
            <label className="block text-gray-700 font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">
              Password
            </label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white font-bold py-2 rounded-lg hover:bg-blue-700 transition duration-200">
            {isRegistering ? "Sign Up" : "Login"}
          </button>
        </form>

        {/* Google Sign-In Button */}
        <button
          onClick={handleGoogleSignIn}
          className="w-full bg-red-500 text-white font-bold py-2 rounded-lg mt-4 hover:bg-red-600 transition duration-200 flex items-center justify-center space-x-2">
          <img
            src="https://www.svgrepo.com/show/355037/google.svg"
            className="w-5 h-5"
            alt="Google logo"
          />
          <span>Sign in with Google</span>
        </button>

        {/* Toggle Between Login & Sign Up */}
        <p className="text-sm text-gray-600 text-center mt-4">
          {isRegistering
            ? "Already have an account?"
            : "Don't have an account?"}{" "}
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-blue-500 hover:underline">
            {isRegistering ? "Login" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
