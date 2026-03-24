// import React, { useState } from "react";
// import { useNavigate, Link } from "react-router-dom";
// import { 
//   FiLogIn, 
//   FiUserPlus, 
//   FiLock, 
//   FiMail, 
//   FiUser, 
//   FiEye, 
//   FiEyeOff,
//   FiHome,
//   FiCheckCircle,
//   FiShield
// } from "react-icons/fi";
// import "./LoginPage.css";

// const API_URL = "http://127.0.0.1:8000";

// export default function LoginPage() {
//   const navigate = useNavigate();
//   const [isLogin, setIsLogin] = useState(true);
//   const [formData, setFormData] = useState({
//     username: "",
//     email: "",
//     password: "",
//     confirmPassword: ""
//   });
//   const [showPassword, setShowPassword] = useState(false);
//   const [showConfirmPassword, setShowConfirmPassword] = useState(false);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [success, setSuccess] = useState("");

//   const handleChange = (e) => {
//     setFormData({
//       ...formData,
//       [e.target.name]: e.target.value
//     });
//     setError("");
//     setSuccess("");
//   };

//   const validateForm = () => {
//     setError("");

//     if (!formData.username.trim()) {
//       setError("Username is required");
//       return false;
//     }

//     if (formData.username.length < 3) {
//       setError("Username must be at least 3 characters");
//       return false;
//     }

//     if (!isLogin) {
//       const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
//       if (!emailRegex.test(formData.email)) {
//         setError("Please enter a valid email address");
//         return false;
//       }
//     }

//     if (!formData.password) {
//       setError("Password is required");
//       return false;
//     }

//     if (formData.password.length < 6) {
//       setError("Password must be at least 6 characters");
//       return false;
//     }

//     if (!isLogin && formData.password !== formData.confirmPassword) {
//       setError("Passwords do not match");
//       return false;
//     }

//     return true;
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
    
//     if (!validateForm()) {
//       return;
//     }

//     setLoading(true);
//     setError("");
//     setSuccess("");

//     try {
//       const endpoint = isLogin ? "/auth/login" : "/auth/register";
//       const payload = isLogin 
//         ? { 
//             username: formData.username.trim(), 
//             password: formData.password 
//           }
//         : { 
//             username: formData.username.trim(), 
//             email: formData.email.trim(), 
//             password: formData.password 
//           };

//       console.log('Sending request to:', `${API_URL}${endpoint}`);

//       const response = await fetch(`${API_URL}${endpoint}`, {
//         method: "POST",
//         headers: { 
//           "Content-Type": "application/json",
//           "Accept": "application/json"
//         },
//         body: JSON.stringify(payload)
//       });

//       const responseText = await response.text();
//       console.log('Response status:', response.status);
//       console.log('Response text:', responseText);

//       let data;
//       try {
//         data = JSON.parse(responseText);
//       } catch (e) {
//         console.error('Failed to parse JSON response:', e);
//         throw new Error('Invalid response from server');
//       }

//       if (!response.ok) {
//         console.log('Error response data:', data);
//         throw new Error(data.detail || data.message || `Server returned ${response.status}`);
//       }

//       console.log('Authentication successful, data:', data);

//       if (isLogin) {
//         // Store authentication data
//         localStorage.setItem("access_token", data.access_token);
//         localStorage.setItem("user_id", data.user_id.toString());
//         localStorage.setItem("username", data.username);
//         localStorage.setItem("session_id", data.session_id);
        
//         console.log('Authentication data stored in localStorage');
        
//         // Check profile status after successful login
//         try {
//           const profileResponse = await fetch(`${API_URL}/profile/status`, {
//             headers: {
//               'Authorization': `Bearer ${data.access_token}`,
//               'Content-Type': 'application/json'
//             }
//           });
          
//           if (profileResponse.ok) {
//             const profileData = await profileResponse.json();
//             console.log('Profile status:', profileData);
            
//             if (profileData.is_complete) {
//               // User has complete profile, redirect to chat
//               setSuccess("Login successful! Redirecting to chat...");
//               setTimeout(() => navigate("/chat"), 1500);
//             } else {
//               // New user or incomplete profile, redirect to setup
//               setSuccess("Login successful! Setting up your profile...");
//               setTimeout(() => navigate("/profile-setup"), 1500);
//             }
//           } else {
//             // If profile check fails, assume new user
//             console.log('Profile check failed, assuming new user');
//             setSuccess("Login successful! Setting up your profile...");
//             setTimeout(() => navigate("/profile-setup"), 1500);
//           }
//         } catch (profileError) {
//           console.log('Profile check error, assuming new user:', profileError);
//           setSuccess("Login successful! Setting up your profile...");
//           setTimeout(() => navigate("/profile-setup"), 1500);
//         }
//       } else {
//         // Registration successful
//         setSuccess("Registration successful! Please login.");
//         setIsLogin(true);
//         setFormData({
//           username: "",
//           email: "",
//           password: "",
//           confirmPassword: ""
//         });
//       }
//     } catch (err) {
//       console.error('Authentication error:', err);
//       setError(err.message || "An error occurred. Please try again.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleDemoLogin = async () => {
//     setLoading(true);
//     setError("");
//     setSuccess("");
    
//     try {
//       const response = await fetch(`${API_URL}/auth/login`, {
//         method: "POST",
//         headers: { 
//           "Content-Type": "application/json",
//           "Accept": "application/json"
//         },
//         body: JSON.stringify({
//           username: "demo",
//           password: "demo123"
//         })
//       });

//       const responseText = await response.text();
//       console.log('Demo login response:', response.status, responseText);

//       let data;
//       try {
//         data = JSON.parse(responseText);
//       } catch (e) {
//         throw new Error('Invalid response from server');
//       }

//       if (!response.ok) {
//         throw new Error(data.detail || "Demo login failed. Please register first.");
//       }

//       // Store authentication data
//       localStorage.setItem("access_token", data.access_token);
//       localStorage.setItem("user_id", data.user_id.toString());
//       localStorage.setItem("username", data.username);
//       localStorage.setItem("session_id", data.session_id);
      
//       console.log('Demo login successful, data stored');
      
//       // Check profile status
//       try {
//         const profileResponse = await fetch(`${API_URL}/profile/status`, {
//           headers: {
//             'Authorization': `Bearer ${data.access_token}`,
//             'Content-Type': 'application/json'
//           }
//         });
        
//         if (profileResponse.ok) {
//           const profileData = await profileResponse.json();
//           console.log('Demo profile status:', profileData);
          
//           if (profileData.is_complete) {
//             setSuccess("Demo login successful! Redirecting to chat...");
//             setTimeout(() => navigate("/chat"), 1500);
//           } else {
//             setSuccess("Demo login successful! Setting up your profile...");
//             setTimeout(() => navigate("/profile-setup"), 1500);
//           }
//         } else {
//           setSuccess("Demo login successful! Setting up your profile...");
//           setTimeout(() => navigate("/profile-setup"), 1500);
//         }
//       } catch (profileError) {
//         console.log('Profile check error:', profileError);
//         setSuccess("Demo login successful! Setting up your profile...");
//         setTimeout(() => navigate("/profile-setup"), 1500);
//       }
//     } catch (err) {
//       console.error('Demo login error:', err);
//       setError(err.message || "Demo login failed. Please try regular login or register.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleForgotPassword = () => {
//     setError("Password reset feature coming soon!");
//   };

//   return (
//     <div className="login-container">
//       {/* Background Pattern */}
//       <div className="background-pattern"></div>
      
//       {/* Main Content */}
//       <div className="login-content">
//         {/* Left Panel - Brand Info */}
//         <div className="brand-panel">
//           <div className="brand-header">
//             <div className="logo">
//               <div className="logo-icon">SF</div>
//               <h1 className="logo-text">SmartFit</h1>
//             </div>
//             <h2 className="brand-title">
//               Welcome to <span className="highlight">SmartFit AI</span>
//             </h2>
//             <p className="brand-description">
//               Your personal AI fashion stylist. Get personalized clothing recommendations, 
//               style advice, and virtual try-ons powered by advanced AI.
//             </p>
//           </div>

//           <div className="features">
//             <div className="feature">
//               <div className="feature-icon">
//                 <FiCheckCircle />
//               </div>
//               <div className="feature-content">
//                 <h4>AI-Powered Styling</h4>
//                 <p>Personalized fashion recommendations</p>
//               </div>
//             </div>
            
//             <div className="feature">
//               <div className="feature-icon">
//                 <FiShield />
//               </div>
//               <div className="feature-content">
//                 <h4>Secure & Private</h4>
//                 <p>Your data is always protected</p>
//               </div>
//             </div>
//           </div>

//           <div className="demo-section">
//             <p className="demo-text">Ready to transform your style?</p>
//             <button 
//               className="demo-button"
//               onClick={handleDemoLogin}
//               disabled={loading}
//             >
//               Try Demo Account
//               <span className="arrow">→</span>
//             </button>
//           </div>
//         </div>

//         {/* Right Panel - Login Form */}
//         <div className="form-panel">
//           <div className="form-container">
//             <div className="form-header">
//               <h2>{isLogin ? "Welcome Back" : "Create Account"}</h2>
//               <p>{isLogin ? "Sign in to your SmartFit AI account" : "Join SmartFit AI for personalized fashion styling"}</p>
//             </div>

//             {/* Error/Success Messages */}
//             {error && (
//               <div className="message error">
//                 <div className="message-icon">!</div>
//                 <div className="message-content">{error}</div>
//                 <button className="message-close" onClick={() => setError("")}>×</button>
//               </div>
//             )}

//             {success && (
//               <div className="message success">
//                 <div className="message-icon">✓</div>
//                 <div className="message-content">{success}</div>
//                 <button className="message-close" onClick={() => setSuccess("")}>×</button>
//               </div>
//             )}

//             {/* Form */}
//             <form onSubmit={handleSubmit} className="auth-form">
//               <div className="form-group">
//                 <div className="input-container">
//                   <div className="icon-container">
//                     <FiUser className="input-icon" />
//                   </div>
//                   <input
//                     type="text"
//                     name="username"
//                     value={formData.username}
//                     onChange={handleChange}
//                     placeholder="Username"
//                     required
//                     minLength="3"
//                     disabled={loading}
//                     className="form-input"
//                   />
//                 </div>
//               </div>

//               {!isLogin && (
//                 <div className="form-group">
//                   <div className="input-container">
//                     <div className="icon-container">
//                       <FiMail className="input-icon" />
//                     </div>
//                     <input
//                       type="email"
//                       name="email"
//                       value={formData.email}
//                       onChange={handleChange}
//                       placeholder="Email Address"
//                       required
//                       disabled={loading}
//                       className="form-input"
//                     />
//                   </div>
//                 </div>
//               )}

//               <div className="form-group">
//                 <div className="input-container">
//                   <div className="icon-container">
//                     <FiLock className="input-icon" />
//                   </div>
//                   <input
//                     type={showPassword ? "text" : "password"}
//                     name="password"
//                     value={formData.password}
//                     onChange={handleChange}
//                     placeholder="Password"
//                     required
//                     minLength="6"
//                     disabled={loading}
//                     className="form-input"
//                   />
//                   <button
//                     type="button"
//                     className="password-toggle"
//                     onClick={() => setShowPassword(!showPassword)}
//                     disabled={loading}
//                   >
//                     {showPassword ? <FiEyeOff /> : <FiEye />}
//                   </button>
//                 </div>
//               </div>

//               {!isLogin && (
//                 <div className="form-group">
//                   <div className="input-container">
//                     <div className="icon-container">
//                       <FiLock className="input-icon" />
//                     </div>
//                     <input
//                       type={showConfirmPassword ? "text" : "password"}
//                       name="confirmPassword"
//                       value={formData.confirmPassword}
//                       onChange={handleChange}
//                       placeholder="Confirm Password"
//                       required
//                       minLength="6"
//                       disabled={loading}
//                       className="form-input"
//                     />
//                     <button
//                       type="button"
//                       className="password-toggle"
//                       onClick={() => setShowConfirmPassword(!showConfirmPassword)}
//                       disabled={loading}
//                     >
//                       {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
//                     </button>
//                   </div>
//                 </div>
//               )}

//               <button
//                 type="submit"
//                 className="submit-button"
//                 disabled={loading}
//               >
//                 {loading ? (
//                   <span className="loading"></span>
//                 ) : (
//                   <>
//                     {isLogin ? (
//                       <>
//                         <FiLogIn className="button-icon" />
//                         Sign In
//                       </>
//                     ) : (
//                       <>
//                         <FiUserPlus className="button-icon" />
//                         Create Account
//                       </>
//                     )}
//                   </>
//                 )}
//               </button>
//             </form>

//             {/* Form Footer */}
//             <div className="form-footer">
//               <div className="toggle-section">
//                 <span className="toggle-text">
//                   {isLogin ? "Don't have an account?" : "Already have an account?"}
//                 </span>
//                 <button
//                   type="button"
//                   className="toggle-button"
//                   onClick={() => {
//                     setIsLogin(!isLogin);
//                     setError("");
//                     setSuccess("");
//                     setFormData({
//                       username: formData.username,
//                       email: "",
//                       password: "",
//                       confirmPassword: ""
//                     });
//                   }}
//                   disabled={loading}
//                 >
//                   {isLogin ? "Sign Up" : "Sign In"}
//                 </button>
//               </div>

//               <div className="divider">
//                 <span className="divider-text">or</span>
//               </div>

//               <div className="actions">
//                 <Link to="/" className="home-link">
//                   <FiHome className="link-icon" />
//                   Back to Home
//                 </Link>
//                 {isLogin && (
//                   <button 
//                     className="forgot-link"
//                     onClick={handleForgotPassword}
//                     disabled={loading}
//                   >
//                     Forgot Password?
//                   </button>
//                 )}
//               </div>

//               <div className="terms">
//                 <p>
//                   By continuing, you agree to our{" "}
//                   <a href="#" className="terms-link">Terms of Service</a> and{" "}
//                   <a href="#" className="terms-link">Privacy Policy</a>
//                 </p>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { 
  FiLogIn, 
  FiUserPlus, 
  FiLock, 
  FiMail, 
  FiUser, 
  FiEye, 
  FiEyeOff,
  FiHome,
  FiCheckCircle,
  FiShield
} from "react-icons/fi";
import "./LoginPage.css";
import { getApiBaseUrl } from "./api";

const API_URL = getApiBaseUrl();

export default function LoginPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError("");
    setSuccess("");
  };

  const validateForm = () => {
    setError("");

    if (!formData.username.trim()) {
      setError("Username is required");
      return false;
    }

    if (formData.username.length < 3) {
      setError("Username must be at least 3 characters");
      return false;
    }

    if (!isLogin) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        setError("Please enter a valid email address");
        return false;
      }
    }

    if (!formData.password) {
      setError("Password is required");
      return false;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }

    if (!isLogin && formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const endpoint = isLogin ? "/auth/login" : "/auth/register";
      const payload = isLogin 
        ? { 
            username: formData.username.trim(), 
            password: formData.password 
          }
        : { 
            username: formData.username.trim(), 
            email: formData.email.trim(), 
            password: formData.password 
          };

      console.log('Sending request to:', `${API_URL}${endpoint}`);

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const responseText = await response.text();
      console.log('Response status:', response.status);
      console.log('Response text:', responseText);

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        console.error('Failed to parse JSON response:', e);
        throw new Error('Invalid response from server');
      }

      if (!response.ok) {
        console.log('Error response data:', data);
        throw new Error(data.detail || data.message || `Server returned ${response.status}`);
      }

      console.log('Authentication successful, data:', data);

      if (isLogin) {
        // Store authentication data
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_id", data.user_id.toString());
        localStorage.setItem("username", data.username);
        localStorage.setItem("session_id", data.session_id);
        
        console.log('✅ Login successful! Redirecting to profile setup...');
        
        // Show success message
        setSuccess("Login successful! Redirecting to profile setup...");
        
        // Redirect to profile setup after short delay
        setTimeout(() => {
          console.log('Navigating to /profile-setup');
          navigate("/profile-setup");
        }, 1000);
        
      } else {
        // Registration successful
        setSuccess("Registration successful! Please login.");
        setIsLogin(true);
        setFormData({
          username: "",
          email: "",
          password: "",
          confirmPassword: ""
        });
      }
    } catch (err) {
      console.error('Authentication error:', err);
      setError(err.message || "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({
          username: "demo",
          password: "demo123"
        })
      });

      const responseText = await response.text();
      console.log('Demo login response:', response.status, responseText);

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        throw new Error('Invalid response from server');
      }

      if (!response.ok) {
        throw new Error(data.detail || "Demo login failed. Please register first.");
      }

      // Store authentication data
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", data.user_id.toString());
      localStorage.setItem("username", data.username);
      localStorage.setItem("session_id", data.session_id);
      
      console.log('✅ Demo login successful! Redirecting to profile setup...');
      
      // Show success message
      setSuccess("Demo login successful! Redirecting to profile setup...");
      
      // Redirect to profile setup
      setTimeout(() => {
        console.log('Navigating to /profile-setup');
        navigate("/profile-setup");
      }, 1000);
      
    } catch (err) {
      console.error('Demo login error:', err);
      setError(err.message || "Demo login failed. Please try regular login or register.");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = () => {
    setError("Password reset feature coming soon!");
  };

  return (
    <div className="login-container">
      {/* Background Pattern */}
      <div className="background-pattern"></div>
      
      {/* Main Content */}
      <div className="login-content">
        {/* Left Panel - Brand Info */}
        <div className="brand-panel">
          <div className="brand-header">
            <div className="logo">
              <div className="logo-icon">SF</div>
              <h1 className="logo-text">SmartFit</h1>
            </div>
            <h2 className="brand-title">
              Welcome to <span className="highlight">SmartFit AI</span>
            </h2>
            <p className="brand-description">
              Your personal AI fashion stylist. Get personalized clothing recommendations, 
              style advice, and virtual try-ons powered by advanced AI.
            </p>
          </div>

          <div className="features">
            <div className="feature">
              <div className="feature-icon">
                <FiCheckCircle />
              </div>
              <div className="feature-content">
                <h4>AI-Powered Styling</h4>
                <p>Personalized fashion recommendations</p>
              </div>
            </div>
            
            <div className="feature">
              <div className="feature-icon">
                <FiShield />
              </div>
              <div className="feature-content">
                <h4>Secure & Private</h4>
                <p>Your data is always protected</p>
              </div>
            </div>
          </div>

          <div className="demo-section">
            <p className="demo-text">Ready to transform your style?</p>
            <button 
              className="demo-button"
              onClick={handleDemoLogin}
              disabled={loading}
            >
              Try Demo Account
              <span className="arrow">→</span>
            </button>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className="form-panel">
          <div className="form-container">
            <div className="form-header">
              <h2>{isLogin ? "Welcome Back" : "Create Account"}</h2>
              <p>{isLogin ? "Sign in to your SmartFit AI account" : "Join SmartFit AI for personalized fashion styling"}</p>
            </div>

            {/* Error/Success Messages */}
            {error && (
              <div className="message error">
                <div className="message-icon">!</div>
                <div className="message-content">{error}</div>
                <button className="message-close" onClick={() => setError("")}>×</button>
              </div>
            )}

            {success && (
              <div className="message success">
                <div className="message-icon">✓</div>
                <div className="message-content">{success}</div>
                <button className="message-close" onClick={() => setSuccess("")}>×</button>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <div className="input-container">
                  <div className="icon-container">
                    <FiUser className="input-icon" />
                  </div>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="Username"
                    required
                    minLength="3"
                    disabled={loading}
                    className="form-input"
                  />
                </div>
              </div>

              {!isLogin && (
                <div className="form-group">
                  <div className="input-container">
                    <div className="icon-container">
                      <FiMail className="input-icon" />
                    </div>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Email Address"
                      required
                      disabled={loading}
                      className="form-input"
                    />
                  </div>
                </div>
              )}

              <div className="form-group">
                <div className="input-container">
                  <div className="icon-container">
                    <FiLock className="input-icon" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Password"
                    required
                    minLength="6"
                    disabled={loading}
                    className="form-input"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? <FiEyeOff /> : <FiEye />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <div className="form-group">
                  <div className="input-container">
                    <div className="icon-container">
                      <FiLock className="input-icon" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Confirm Password"
                      required
                      minLength="6"
                      disabled={loading}
                      className="form-input"
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={loading}
                    >
                      {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="submit-button"
                disabled={loading}
              >
                {loading ? (
                  <span className="loading"></span>
                ) : (
                  <>
                    {isLogin ? (
                      <>
                        <FiLogIn className="button-icon" />
                        Sign In
                      </>
                    ) : (
                      <>
                        <FiUserPlus className="button-icon" />
                        Create Account
                      </>
                    )}
                  </>
                )}
              </button>
            </form>

            {/* Form Footer */}
            <div className="form-footer">
              <div className="toggle-section">
                <span className="toggle-text">
                  {isLogin ? "Don't have an account?" : "Already have an account?"}
                </span>
                <button
                  type="button"
                  className="toggle-button"
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError("");
                    setSuccess("");
                    setFormData({
                      username: formData.username,
                      email: "",
                      password: "",
                      confirmPassword: ""
                    });
                  }}
                  disabled={loading}
                >
                  {isLogin ? "Sign Up" : "Sign In"}
                </button>
              </div>

              <div className="divider">
                <span className="divider-text">or</span>
              </div>

              <div className="actions">
                <Link to="/" className="home-link">
                  <FiHome className="link-icon" />
                  Back to Home
                </Link>
                {isLogin && (
                  <button 
                    className="forgot-link"
                    onClick={handleForgotPassword}
                    disabled={loading}
                  >
                    Forgot Password?
                  </button>
                )}
              </div>

              <div className="terms">
                <p>
                  By continuing, you agree to our{" "}
                  <a href="#" className="terms-link">Terms of Service</a> and{" "}
                  <a href="#" className="terms-link">Privacy Policy</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}