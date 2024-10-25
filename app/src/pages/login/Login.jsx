import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
 

function Login() {
  // var backend_url = "http://49.43.100.205:8000";
  // const backend_url = "http://0.0.0.0:8000";
  const backend_url =  "http://4.186.63.222:8000"

  // var backend_url = "http://127.0.0.1:8000";
  //  const backend_url =  "http://52.168.150.249:8000"
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const navigate = useNavigate(); // Create a navigate function

  useEffect(() => {
    // Check if login data is already stored in localStorage
    const storedUsername = localStorage.getItem('username');
    const loginTime = localStorage.getItem('loginTime');

    if (storedUsername && loginTime) {
      // Check if one hour has passed
      const now = new Date().getTime();
      const oneHour = 60 * 60 * 1000; // One hour in milliseconds
      if (now - loginTime > oneHour) {
        // If more than one hour has passed, remove the data
        localStorage.removeItem('username');
        localStorage.removeItem('loginTime');
      }
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      setError("Username and password are required");
      return;
    }

    try {
      const response = await axios.post(`${backend_url}/api/login`, {
        username: username,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Login successful!', response.data);
      setError(null);

      // Save the username and current time to localStorage
      localStorage.setItem('username', response.data.username);
      localStorage.setItem('loginTime', new Date().getTime());

      // Navigate to the home page after successful login
      navigate("/home");

    } catch (error) {
      if (error.response && error.response.data) {
        setError(error.response.data.detail || "Login failed");
      } else {
        setError("An error occurred. Please try again.");
      }
      console.error("Error:", error);
    }
  };

  return (
    <div className="login-container">
      <div className="card login-card">
        <div className="card-body">
          <h3 className="text-center mb-4">Welcome Back!</h3>

          {error && <div className="alert alert-danger fade show">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group mb-3">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                className="form-control"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </div>
            <div className="form-group mb-3">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                className="form-control"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-100">Login</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;
