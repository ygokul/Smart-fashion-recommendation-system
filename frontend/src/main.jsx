import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import LandingPage from './LandingPage'
import LoginPage from './LoginPage'
import ProfileSetupPage from './ProfileSetupPage'
import ChatPage from './App'
import './index.css'
import { getApiBaseUrl } from './api'

const API_URL = getApiBaseUrl()

// Loading component
const LoadingScreen = () => (
  <div className="loading-screen">
    <div className="spinner"></div>
    <p>Loading UAI...</p>
  </div>
)

// Simple auth check function
const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [isAuth, setIsAuth] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        navigate('/login');
        setLoading(false);
        return;
      }

      // Verify token with backend
      try {
        const response = await fetch(`${API_URL}/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          setIsAuth(true);
        } else {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
          localStorage.removeItem('session_id');
          localStorage.removeItem('user_profile');
          navigate('/login');
        }
      } catch (error) {
        console.error('Token verification failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('session_id');
        localStorage.removeItem('user_profile');
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [navigate]);

  if (loading) {
    return <LoadingScreen />;
  }

  return isAuth ? children : null;
};

// Profile Protected Route
const ProfileProtectedRoute = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [needsProfile, setNeedsProfile] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkProfile = async () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        navigate('/login');
        setLoading(false);
        return;
      }

      try {
        // Check profile status
        const response = await fetch(`${API_URL}/profile/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.is_complete) {
            // Profile is complete, go to chat
            navigate('/chat');
          } else {
            // Profile incomplete, stay on profile setup
            setNeedsProfile(true);
          }
        } else {
          // If can't check profile, assume needs setup
          setNeedsProfile(true);
        }
      } catch (error) {
        console.error('Profile check error:', error);
        setNeedsProfile(true);
      } finally {
        setLoading(false);
      }
    };

    checkProfile();
  }, [navigate]);

  if (loading) {
    return <LoadingScreen />;
  }

  return needsProfile ? children : null;
};

// App wrapper with navigation control
function AppWrapper() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    
    // If user is on landing page and already logged in, redirect to chat
    if (token && location.pathname === '/') {
      navigate('/chat');
    }
    
    // If user tries to access login page while logged in, redirect based on profile status
    if (token && location.pathname === '/login') {
      // Check profile status and redirect accordingly
      const checkAndRedirect = async () => {
        try {
          const response = await fetch(`${API_URL}/profile/status`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.is_complete) {
              navigate('/chat');
            } else {
              navigate('/profile-setup');
            }
          }
        } catch (error) {
          console.error('Profile status check failed:', error);
          navigate('/profile-setup');
        }
      };
      
      checkAndRedirect();
    }
  }, [location.pathname, navigate]);

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route 
        path="/profile-setup" 
        element={
          <ProtectedRoute>
            <ProfileProtectedRoute>
              <ProfileSetupPage />
            </ProfileProtectedRoute>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/chat" 
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } 
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function MainApp() {
  return (
    <Router>
      <AppWrapper />
    </Router>
  )
}

// Add loading screen styles
const style = document.createElement('style')
style.textContent = `
  .loading-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .spinner {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .loading-screen p {
    color: white;
    margin-top: 20px;
    font-size: 1.2rem;
  }
`
document.head.appendChild(style)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MainApp />
  </React.StrictMode>
)