import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  FiCheck, 
  FiChevronRight, 
  FiUser, 
  FiDroplet,
  FiSmile,
  FiStar,
  FiSave,
  FiArrowLeft,
  FiHelpCircle,
  FiX
} from "react-icons/fi";
import { 
  BsPersonFill,
  BsRulers,
  BsPlayCircle
} from "react-icons/bs";
import "./ProfileSetupPage.css";
import { getApiBaseUrl } from "./api";

const API_URL = getApiBaseUrl();

// YouTube embed component
const YouTubeEmbed = ({ videoId, title, width = "100%", height = "400" }) => {
  return (
    <div className="youtube-embed-container">
      <iframe
        width={width}
        height={height}
        src={`https://www.youtube.com/embed/${videoId}`}
        title={title}
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        loading="lazy"
      ></iframe>
    </div>
  );
};

// Help Modal Component
const HelpModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="help-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>
            <FiX />
          </button>
        </div>
        <div className="modal-content">
          {children}
        </div>
      </div>
    </div>
  );
};

export default function ProfileSetupPage() {
  const navigate = useNavigate();
  const [profileData, setProfileData] = useState({
    gender: "",
    body_type: "",
    skin_tone: "",
    face_shape: "",
    hair_type: [], // Changed from string to array
    style_preferences: [],
    measurements: {
      height: "",
      weight: "",
      bust: "",
      waist: "",
      hips: ""
    }
  });
  const [completedSections, setCompletedSections] = useState([]);
  const [activeSection, setActiveSection] = useState("gender");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  // Help modal states
  const [showBodyTypeHelp, setShowBodyTypeHelp] = useState(false);
  const [showFaceShapeHelp, setShowFaceShapeHelp] = useState(false);
  const [showHairTypeHelp, setShowHairTypeHelp] = useState(false);
  const [showMeasurementsHelp, setShowMeasurementsHelp] = useState(false);

  // Get authentication token
  const token = localStorage.getItem("access_token");
  const sessionId = localStorage.getItem("session_id");

  // Available options
  const genders = ["Male", "Female", "Non-binary", "Prefer not to say"];
  const bodyTypes = ["Rectangle", "Hourglass", "Pear", "Apple", "Inverted Triangle"];
  const skinTones = ["Fair", "Light", "Medium", "Olive", "Tan", "Dark"];
  const faceShapes = ["Oval", "Round", "Square", "Heart", "Diamond", "Oblong"];
  const hairTypes = ["Straight", "Wavy", "Curly", "Coily", "Bald", "Short", "Long"];
  const stylePreferencesList = [
    "Casual", "Formal", "Business", "Bohemian", "Streetwear", 
    "Classic", "Trendy", "Minimalist", "Vintage", "Sporty"
  ];

  // YouTube video IDs - Add hairType video ID
  const youtubeVideos = {
    bodyType: "SHVSa5imqmA",
    faceShape: "CvHYaoOW_-c",
    hairType: "Ngz8HI7bBm0"
  };

  useEffect(() => {
    // Check if user is authenticated
    if (!token) {
      console.log("No authentication token found, redirecting to login");
      navigate("/login");
      return;
    }

    console.log("Profile setup page loaded for user:", localStorage.getItem("username"));
    console.log("Token exists:", !!token);
    
    // Load existing profile data
    loadProfileData();
  }, [navigate, token]);

  const loadProfileData = async () => {
    try {
      console.log("Loading profile data from API...");
      
      // Try to get profile from API
      const response = await fetch(`${API_URL}/profile/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log("Profile status response status:", response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Loaded profile data from API:', data);

        if (data.is_complete) {
          // Profile is already complete, redirect to chat
          console.log("Profile is already complete, redirecting to chat");
          navigate("/chat");
          return;
        }

        // Load data from API response
        if (data.profile_data) {
          const apiData = data.profile_data;
          console.log("Setting profile data from API:", apiData);
          
          // Handle hair_type conversion from string to array for backward compatibility
          let hairTypeData = [];
          if (apiData.hair_type) {
            if (Array.isArray(apiData.hair_type)) {
              hairTypeData = apiData.hair_type;
            } else if (typeof apiData.hair_type === 'string' && apiData.hair_type.trim() !== '') {
              hairTypeData = [apiData.hair_type];
            }
          }
          
          setProfileData({
            gender: apiData.gender || "",
            body_type: apiData.body_type || "",
            skin_tone: apiData.skin_tone || "",
            face_shape: apiData.face_shape || "",
            hair_type: hairTypeData, // Use array format
            style_preferences: apiData.style_preferences || [],
            measurements: apiData.measurements || {
              height: "", weight: "", bust: "", waist: "", hips: ""
            }
          });

          // Mark completed sections
          const completed = [];
          if (apiData.gender) completed.push("gender");
          if (apiData.body_type) completed.push("body_type");
          if (apiData.skin_tone) completed.push("skin_tone");
          if (apiData.face_shape) completed.push("face_shape");
          if (hairTypeData.length > 0) completed.push("hair_type"); // Check array length
          if (apiData.style_preferences && apiData.style_preferences.length > 0) completed.push("style_preferences");
          if (apiData.measurements && Object.values(apiData.measurements).some(v => v)) completed.push("measurements");
          
          console.log("Completed sections from API:", completed);
          setCompletedSections(completed);
          
          // Set active section to first incomplete section
          const sections = ["gender", "body_type", "skin_tone", "face_shape", "hair_type", "style_preferences", "measurements"];
          const firstIncomplete = sections.find(section => !completed.includes(section));
          if (firstIncomplete) {
            setActiveSection(firstIncomplete);
          }
        }
      } else if (response.status === 404) {
        // No profile exists yet - that's fine for new users
        console.log('No profile found - new user');
      } else {
        console.log('Profile API returned error status:', response.status);
        // Continue with empty profile if API fails
      }
    } catch (error) {
      console.error('Error loading profile:', error);
      // Continue with empty profile if API fails
    } finally {
      setLoading(false);
    }
  };

  const handleSectionComplete = (section) => {
    if (!completedSections.includes(section)) {
      const newCompleted = [...completedSections, section];
      setCompletedSections(newCompleted);
      console.log(`Section ${section} marked as complete. Completed:`, newCompleted);
    }
    
    // Move to next section
    const sections = ["gender", "body_type", "skin_tone", "face_shape", "hair_type", "style_preferences", "measurements"];
    const currentIndex = sections.indexOf(section);
    if (currentIndex < sections.length - 1) {
      const nextSection = sections[currentIndex + 1];
      console.log(`Moving from ${section} to ${nextSection}`);
      setActiveSection(nextSection);
    }
  };

  const handleGenderSelect = (gender) => {
    console.log("Selected gender:", gender);
    setProfileData({...profileData, gender: gender});
    handleSectionComplete("gender");
  };

  const handleBodyTypeSelect = (type) => {
    console.log("Selected body type:", type);
    setProfileData({...profileData, body_type: type});
    handleSectionComplete("body_type");
  };

  const handleSkinToneSelect = (tone) => {
    console.log("Selected skin tone:", tone);
    setProfileData({...profileData, skin_tone: tone});
    handleSectionComplete("skin_tone");
  };

  const handleFaceShapeSelect = (shape) => {
    console.log("Selected face shape:", shape);
    setProfileData({...profileData, face_shape: shape});
    handleSectionComplete("face_shape");
  };

  const toggleHairType = (type) => {
    const current = [...profileData.hair_type];
    if (current.includes(type)) {
      const index = current.indexOf(type);
      current.splice(index, 1);
      console.log("Removed hair type:", type);
    } else {
      current.push(type);
      console.log("Added hair type:", type);
    }
    setProfileData({...profileData, hair_type: current});
    console.log("Current hair types:", current);
  };

  const removeHairType = (type) => {
    const current = [...profileData.hair_type];
    const index = current.indexOf(type);
    if (index !== -1) {
      current.splice(index, 1);
      setProfileData({...profileData, hair_type: current});
      console.log("Removed hair type:", type);
    }
  };

  const toggleStylePreference = (preference) => {
    const current = [...profileData.style_preferences];
    if (current.includes(preference)) {
      const index = current.indexOf(preference);
      current.splice(index, 1);
      console.log("Removed preference:", preference);
    } else {
      current.push(preference);
      console.log("Added preference:", preference);
    }
    setProfileData({...profileData, style_preferences: current});
    console.log("Current preferences:", current);
  };

  const handleMeasurementChange = (field, value) => {
    console.log(`Measurement ${field} changed to:`, value);
    setProfileData({
      ...profileData,
      measurements: {
        ...profileData.measurements,
        [field.toLowerCase()]: value
      }
    });
  };

  const saveProfileToAPI = async () => {
    if (!token) {
      throw new Error("Authentication token missing. Please login again.");
    }

    console.log("Saving profile to API...");
    console.log("Profile data to save:", profileData);

    // Prepare the request payload
    const payload = {
      session_id: sessionId,
      profile_data: {
        gender: profileData.gender || null,
        body_type: profileData.body_type || null,
        skin_tone: profileData.skin_tone || null,
        face_shape: profileData.face_shape || null,
        hair_type: profileData.hair_type || [], // Send as array
        style_preferences: profileData.style_preferences || [],
        measurements: profileData.measurements || {},
        height: profileData.measurements.height || null,
        weight: profileData.measurements.weight || null,
        bust: profileData.measurements.bust || null,
        waist: profileData.measurements.waist || null,
        hips: profileData.measurements.hips || null
      }
    };

    console.log("Sending payload:", JSON.stringify(payload, null, 2));

    try {
      const response = await fetch(`${API_URL}/profile/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      console.log("Save profile response status:", response.status);
      console.log("Save profile response headers:", response.headers);

      const responseText = await response.text();
      console.log("Save profile response text:", responseText);

      if (!response.ok) {
        console.error("Save profile error response:", responseText);
        
        // Try to parse error message
        let errorMessage = "Failed to save profile";
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          errorMessage = responseText || errorMessage;
        }
        
        throw new Error(errorMessage);
      }

      // Try to parse response
      let result;
      try {
        result = JSON.parse(responseText);
      } catch (e) {
        console.error("Failed to parse JSON response:", e);
        // Create a mock response if parsing fails
        result = {
          profile_id: Date.now(),
          completed_sections: completedSections.length,
          is_complete: completedSections.length >= 4,
          message: "Profile saved (response parse failed)"
        };
      }
      
      console.log("Save profile success:", result);
      return result;
      
    } catch (err) {
      console.error("Network or API error:", err);
      throw err;
    }
  };

  const handleSubmit = async () => {
    console.log("Submit clicked. Completed sections:", completedSections.length);
    
    if (completedSections.length < 4) {
      setError(`Please complete at least 4 sections before continuing. You have completed ${completedSections.length} sections.`);
      return;
    }

    setSaving(true);
    setError("");
    
    try {
      // Save to API
      console.log("Attempting to save profile to API...");
      const result = await saveProfileToAPI();
      
      // Also save to localStorage for quick access
      const profileToSave = {
        gender: profileData.gender,
        bodyType: profileData.body_type,
        skinTone: profileData.skin_tone,
        faceShape: profileData.face_shape,
        hairType: profileData.hair_type, // Save as array
        stylePreferences: profileData.style_preferences,
        measurements: profileData.measurements
      };
      
      localStorage.setItem('user_profile', JSON.stringify(profileToSave));
      localStorage.setItem('profile_complete', 'true');
      console.log("Profile saved to localStorage");
      
      setSuccess("Profile saved successfully! Redirecting to chat...");
      setTimeout(() => {
        console.log("Redirecting to chat...");
        navigate("/chat");
      }, 1500);
      
    } catch (err) {
      console.error("Profile save error:", err);
      
      // If API save fails, still save to localStorage and continue
      if (completedSections.length >= 4) {
        console.log("API save failed, but saving to localStorage and continuing...");
        
        const profileToSave = {
          gender: profileData.gender,
          bodyType: profileData.body_type,
          skinTone: profileData.skin_tone,
          faceShape: profileData.face_shape,
          hairType: profileData.hair_type,
          stylePreferences: profileData.style_preferences,
          measurements: profileData.measurements
        };
        
        localStorage.setItem('user_profile', JSON.stringify(profileToSave));
        localStorage.setItem('profile_complete', 'true');
        
        setSuccess("Profile saved locally! API may have issues, but you can continue to chat. Redirecting...");
        setTimeout(() => {
          navigate("/chat");
        }, 1500);
      } else {
        setError(err.message || "Failed to save profile. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  };

  const getSectionIcon = (section) => {
    switch(section) {
      case "gender": return <FiUser />;
      case "body_type": return <BsPersonFill />;
      case "skin_tone": return <FiDroplet />;
      case "face_shape": return <FiSmile />;
      case "hair_type": return <FiUser />;
      case "style_preferences": return <FiStar />;
      case "measurements": return <BsRulers />;
      default: return <FiUser />;
    }
  };

  const getSectionColor = (section) => {
    const colors = {
      gender: "#3b82f6",
      body_type: "#6366f1",
      skin_tone: "#f59e0b",
      face_shape: "#10b981",
      hair_type: "#8b5cf6",
      style_preferences: "#ec4899",
      measurements: "#3b82f6"
    };
    return colors[section] || "#6366f1";
  };

  const SectionProgress = ({ section, title, description }) => {
    const isCompleted = completedSections.includes(section);
    const isActive = activeSection === section;

    return (
      <div 
        className={`progress-card ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}
        onClick={() => {
          console.log(`Clicked on ${section} section`);
          setActiveSection(section);
        }}
      >
        <div className="progress-icon" style={{ backgroundColor: getSectionColor(section) }}>
          {getSectionIcon(section)}
          {isCompleted && <FiCheck className="check-icon" />}
        </div>
        <div className="progress-content">
          <h4>{title}</h4>
          <p>{description}</p>
          <div className="progress-status">
            <span className="status-indicator">
              {isCompleted ? "Completed" : "Not Started"}
            </span>
            <FiChevronRight className="chevron-icon" />
          </div>
        </div>
      </div>
    );
  };

  // Calculate completion percentage
  const completionPercentage = Math.round((completedSections.length / 7) * 100);

  // Show loading while checking profile
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading your profile...</p>
      </div>
    );
  }

  return (
    <div className="profile-setup-container">
      {/* Help Modals */}
      <HelpModal
        isOpen={showBodyTypeHelp}
        onClose={() => setShowBodyTypeHelp(false)}
        title="How to Identify Your Body Type"
      >
        <div className="help-content">
          <p>Identifying your body type helps us recommend clothes that fit and flatter your silhouette.</p>
          <YouTubeEmbed 
            videoId={youtubeVideos.bodyType}
            title="How To Measure for Your Body Type"
            width="100%"
            height="315"
          />
          <div className="help-tips">
            <h4>Quick Tips:</h4>
            <ul>
              <li><strong>Rectangle:</strong> Shoulders, waist, and hips are similar widths</li>
              <li><strong>Hourglass:</strong> Well-defined waist with balanced shoulders and hips</li>
              <li><strong>Pear:</strong> Hips wider than shoulders with a defined waist</li>
              <li><strong>Apple:</strong> Shoulders and hips similar, waist less defined</li>
              <li><strong>Inverted Triangle:</strong> Shoulders wider than hips</li>
            </ul>
          </div>
        </div>
      </HelpModal>

      <HelpModal
        isOpen={showFaceShapeHelp}
        onClose={() => setShowFaceShapeHelp(false)}
        title="How to Identify Your Face Shape"
      >
        <div className="help-content">
          <p>Knowing your face shape helps us recommend glasses, hairstyles, and accessories that complement you.</p>
          <YouTubeEmbed 
            videoId={youtubeVideos.faceShape}
            title="7 Common Face Shapes - How to Find Out in 1 Minute!"
            width="100%"
            height="315"
          />
          <div className="help-tips">
            <h4>Quick Reference:</h4>
            <ul>
              <li><strong>Oval:</strong> Balanced, slightly longer than wide</li>
              <li><strong>Round:</strong> Cheeks widest part, soft angles</li>
              <li><strong>Square:</strong> Strong jawline, forehead and jaw similar width</li>
              <li><strong>Heart:</strong> Wider forehead, narrow chin</li>
              <li><strong>Diamond:</strong> Narrow forehead and chin, wide cheekbones</li>
              <li><strong>Oblong:</strong> Longer than wide, straight sides</li>
            </ul>
          </div>
        </div>
      </HelpModal>

      <HelpModal
        isOpen={showHairTypeHelp}
        onClose={() => setShowHairTypeHelp(false)}
        title="Hair Type Guide"
      >
        <div className="help-content">
          <p>Understanding your hair type helps us recommend hairstyles, hair accessories, and products that work best for your hair texture.</p>
          <YouTubeEmbed 
            videoId={youtubeVideos.hairType}
            title="How to Get PERFECT Hair in 4 Easy Steps | Style Theory"
            width="100%"
            height="315"
          />
          <div className="help-tips">
            <h4>Hair Type Categories:</h4>
            <ul>
              <li><strong>Straight:</strong> Hair falls flat from roots to ends, no curl pattern</li>
              <li><strong>Wavy:</strong> Hair has gentle 'S' shaped waves</li>
              <li><strong>Curly:</strong> Well-defined spiral curls (loose to tight)</li>
              <li><strong>Coily:</strong> Tight curls or zig-zag pattern, very springy</li>
              <li><strong>Bald:</strong> No hair or shaved head - we'll focus on accessories</li>
              <li><strong>Short:</strong> Hair length above shoulders</li>
              <li><strong>Long:</strong> Hair length below shoulders</li>
            </ul>
            <div className="hair-care-tips">
              <h4>Quick Hair Care Tips:</h4>
              <ul>
                <li><strong>Straight:</strong> Can become oily quickly, use lightweight products</li>
                <li><strong>Wavy:</strong> Enhance waves with sea salt sprays</li>
                <li><strong>Curly:</strong> Needs moisture, avoid sulfates</li>
                <li><strong>Coily:</strong> Requires deep conditioning, protective styles</li>
              </ul>
            </div>
          </div>
        </div>
      </HelpModal>

      <HelpModal
        isOpen={showMeasurementsHelp}
        onClose={() => setShowMeasurementsHelp(false)}
        title="How to Take Your Measurements"
      >
        <div className="help-content">
          <p>Accurate measurements ensure perfect fit recommendations. Here's how to measure correctly:</p>
          <div className="measurement-instructions">
            <div className="instruction-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h5>Height</h5>
                <p>Stand straight against a wall without shoes. Use a measuring tape from top of head to floor.</p>
              </div>
            </div>
            <div className="instruction-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h5>Bust/Chest</h5>
                <p>Measure around the fullest part of your chest, keeping tape parallel to the floor.</p>
              </div>
            </div>
            <div className="instruction-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h5>Waist</h5>
                <p>Measure around the narrowest part of your waist (usually above belly button).</p>
              </div>
            </div>
            <div className="instruction-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h5>Hips</h5>
                <p>Measure around the fullest part of your hips, keeping tape parallel to the floor.</p>
              </div>
            </div>
          </div>
          <div className="measurement-tips">
            <h4>Tips for Accurate Measurements:</h4>
            <ul>
              <li>Use a soft measuring tape</li>
              <li>Stand naturally, don't suck in your stomach</li>
              <li>Measure over lightweight clothing or underwear</li>
              <li>Keep tape snug but not tight</li>
              <li>Record measurements in inches or centimeters</li>
            </ul>
          </div>
        </div>
      </HelpModal>

      {/* Header */}
      <div className="profile-header">
        <button className="back-button" onClick={() => navigate("/login")}>
          <FiArrowLeft /> Back to Login
        </button>
        <div className="header-content">
          <h1>Complete Your Profile</h1>
          <p className="subtitle">Set up your profile to get personalized fashion recommendations</p>
        </div>
      </div>

      {/* Background */}
      <div className="setup-bg">
        <div className="bg-shape shape-1"></div>
        <div className="bg-shape shape-2"></div>
        <div className="bg-shape shape-3"></div>
      </div>

      <div className="setup-wrapper">
        {/* Error/Success Messages */}
        {error && (
          <div className="setup-message error">
            <div className="message-icon">!</div>
            <div className="message-content">{error}</div>
            <button className="message-close" onClick={() => setError("")}>×</button>
          </div>
        )}

        {success && (
          <div className="setup-message success">
            <div className="message-icon">✓</div>
            <div className="message-content">{success}</div>
            <button className="message-close" onClick={() => setSuccess("")}>×</button>
          </div>
        )}

        <div className="setup-content">
          {/* Left Panel - Progress Overview */}
          <div className="progress-sidebar">
            <h3>Setup Progress</h3>
            
            <div className="progress-summary">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${completionPercentage}%` }}
                ></div>
              </div>
              <p className="progress-text">
                {completedSections.length} of 7 sections completed • {completionPercentage}%
              </p>
            </div>
            
            <SectionProgress 
              section="gender"
              title="Gender"
              description="For personalized recommendations"
            />
            
            <SectionProgress 
              section="body_type"
              title="Body Type"
              description="Help us understand your silhouette"
            />
            
            <SectionProgress 
              section="skin_tone"
              title="Skin Tone"
              description="For color recommendations"
            />
            
            <SectionProgress 
              section="face_shape"
              title="Face Shape"
              description="For accessory suggestions"
            />
            
            <SectionProgress 
              section="hair_type"
              title="Hair Type"
              description="For hairstyle recommendations"
            />
            
            <SectionProgress 
              section="style_preferences"
              title="Style Preferences"
              description="Your fashion preferences"
            />
            
            <SectionProgress 
              section="measurements"
              title="Measurements"
              description="For perfect fit suggestions"
            />

            <div className="complete-action">
              <button 
                className="complete-btn"
                onClick={handleSubmit}
                disabled={saving || completedSections.length < 4}
              >
                {saving ? (
                  <span className="loading"></span>
                ) : (
                  <>
                    <FiSave className="btn-icon" />
                    {completedSections.length >= 7 ? "Complete & Continue" : "Save & Continue"}
                    <span className="btn-badge">{completedSections.length}/7</span>
                  </>
                )}
              </button>
              <p className="action-note">
                {completedSections.length >= 4 
                  ? "Ready to continue! Click Save & Continue"
                  : `Complete at least 4 sections to continue (${completedSections.length}/4)`}
              </p>
            </div>
          </div>

          {/* Right Panel - Active Section */}
          <div className="active-section-panel">
            <div className="section-header">
              <div className="section-icon" style={{ backgroundColor: getSectionColor(activeSection) }}>
                {getSectionIcon(activeSection)}
              </div>
              <div className="section-header-content">
                <h2>
                  {activeSection === "gender" && "Gender"}
                  {activeSection === "body_type" && "Body Type"}
                  {activeSection === "skin_tone" && "Skin Tone"}
                  {activeSection === "face_shape" && "Face Shape"}
                  {activeSection === "hair_type" && "Hair Type"}
                  {activeSection === "style_preferences" && "Style Preferences"}
                  {activeSection === "measurements" && "Measurements"}
                </h2>
                <p className="section-description">
                  {activeSection === "gender" && "Select your gender for personalized fashion recommendations"}
                  {activeSection === "body_type" && "Select your body type for personalized clothing suggestions"}
                  {activeSection === "skin_tone" && "Choose your skin tone for color palette recommendations"}
                  {activeSection === "face_shape" && "Select your face shape for accessory recommendations"}
                  {activeSection === "hair_type" && "Select your hair type(s) for hairstyle suggestions"}
                  {activeSection === "style_preferences" && "Select your preferred fashion styles"}
                  {activeSection === "measurements" && "Enter your measurements for perfect fit"}
                </p>
                {activeSection === "body_type" && (
                  <button 
                    className="help-button"
                    onClick={() => setShowBodyTypeHelp(true)}
                  >
                    <FiHelpCircle /> How to identify your body type?
                  </button>
                )}
                {activeSection === "face_shape" && (
                  <button 
                    className="help-button"
                    onClick={() => setShowFaceShapeHelp(true)}
                  >
                    <FiHelpCircle /> How to identify your face shape?
                  </button>
                )}
                {activeSection === "hair_type" && (
                  <button 
                    className="help-button"
                    onClick={() => setShowHairTypeHelp(true)}
                  >
                    <FiHelpCircle /> Learn about hair types
                  </button>
                )}
                {activeSection === "measurements" && (
                  <button 
                    className="help-button"
                    onClick={() => setShowMeasurementsHelp(true)}
                  >
                    <FiHelpCircle /> How to take measurements?
                  </button>
                )}
              </div>
            </div>

            <div className="section-content">
              {activeSection === "gender" && (
                <div className="gender-section">
                  <div className="options-grid">
                    {genders.map((gender) => (
                      <button
                        key={gender}
                        className={`option-card ${profileData.gender === gender ? 'selected' : ''}`}
                        onClick={() => handleGenderSelect(gender)}
                      >
                        <div className="option-icon">
                          <FiUser />
                        </div>
                        <span className="option-label">{gender}</span>
                      </button>
                    ))}
                  </div>
                  <div className="gender-info">
                    <h4>Why we ask for gender?</h4>
                    <p>Knowing your gender helps us provide more accurate fashion recommendations tailored to your preferences and body type.</p>
                    <ul>
                      <li><strong>Male/Female:</strong> For traditional sizing and style recommendations</li>
                      <li><strong>Non-binary:</strong> For inclusive fashion suggestions</li>
                      <li><strong>Prefer not to say:</strong> We'll use neutral recommendations</li>
                    </ul>
                  </div>
                </div>
              )}

              {activeSection === "body_type" && (
                <div className="body-type-section">
                  <div className="options-grid">
                    {bodyTypes.map((type) => (
                      <button
                        key={type}
                        className={`option-card ${profileData.body_type === type ? 'selected' : ''}`}
                        onClick={() => handleBodyTypeSelect(type)}
                      >
                        <div className="option-icon">
                          <BsPersonFill />
                        </div>
                        <span className="option-label">{type}</span>
                      </button>
                    ))}
                  </div>
                  <div className="video-guide">
                    <div className="video-header">
                      <BsPlayCircle className="video-icon" />
                      <h4>Need Help Identifying?</h4>
                    </div>
                    <p>Watch this quick guide to identify your body type:</p>
                    <div className="video-container">
                      <YouTubeEmbed 
                        videoId={youtubeVideos.bodyType}
                        title="How To Measure for Your Body Type"
                        width="100%"
                        height="200"
                      />
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "skin_tone" && (
                <div className="skin-tone-selector">
                  <div className="skin-tone-options">
                    {skinTones.map((tone) => (
                      <div
                        key={tone}
                        className={`tone-option ${profileData.skin_tone === tone ? 'selected' : ''}`}
                        onClick={() => handleSkinToneSelect(tone)}
                      >
                        <div className="tone-color" style={{
                          backgroundColor: 
                            tone === "Fair" ? "#ffdbac" :
                            tone === "Light" ? "#f1c27d" :
                            tone === "Medium" ? "#e0ac69" :
                            tone === "Olive" ? "#c68642" :
                            tone === "Tan" ? "#8d5524" :
                            "#3d0c02"
                        }}></div>
                        <span className="tone-label">{tone}</span>
                      </div>
                    ))}
                  </div>
                  <div className="skin-tone-info">
                    <h4>Color Palette Recommendations</h4>
                    <p>Based on your skin tone, we'll recommend colors that complement you best.</p>
                    <ul>
                      <li><strong>Fair:</strong> Soft pastels, jewel tones</li>
                      <li><strong>Medium:</strong> Earth tones, warm colors</li>
                      <li><strong>Dark:</strong> Bright colors, pastels, metallics</li>
                    </ul>
                  </div>
                </div>
              )}

              {activeSection === "face_shape" && (
                <div className="face-shape-section">
                  <div className="options-grid">
                    {faceShapes.map((shape) => (
                      <button
                        key={shape}
                        className={`option-card ${profileData.face_shape === shape ? 'selected' : ''}`}
                        onClick={() => handleFaceShapeSelect(shape)}
                      >
                        <div className="option-icon">
                          <FiSmile />
                        </div>
                        <span className="option-label">{shape}</span>
                      </button>
                    ))}
                  </div>
                  <div className="video-guide">
                    <div className="video-header">
                      <BsPlayCircle className="video-icon" />
                      <h4>Quick Identification Guide</h4>
                    </div>
                    <p>Watch this 1-minute guide to identify your face shape:</p>
                    <div className="video-container">
                      <YouTubeEmbed 
                        videoId={youtubeVideos.faceShape}
                        title="7 Common Face Shapes - How to Find Out in 1 Minute!"
                        width="100%"
                        height="200"
                      />
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "hair_type" && (
                <div className="hair-type-section">
                  {/* Selected Hair Types Display */}
                  <div className="selected-preferences">
                    <h4>Selected Hair Types ({profileData.hair_type.length})</h4>
                    {profileData.hair_type.length > 0 ? (
                      <div className="preference-tags">
                        {profileData.hair_type.map((type) => (
                          <span key={type} className="preference-tag">
                            {type}
                            <button onClick={() => removeHairType(type)}>×</button>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="no-selection">No hair types selected yet</p>
                    )}
                  </div>
                  
                  {/* Hair Type Selection Grid */}
                  <div className="options-grid">
                    {hairTypes.map((type) => (
                      <button
                        key={type}
                        className={`option-card ${profileData.hair_type.includes(type) ? 'selected' : ''}`}
                        onClick={() => toggleHairType(type)}
                      >
                        <div className="option-icon">
                          {type === "Straight" ? "S" : 
                           type === "Wavy" ? "W" : 
                           type === "Curly" ? "C" : 
                           type === "Coily" ? "Z" : 
                           type === "Bald" ? "B" : 
                           type === "Short" ? "S" : "L"}
                        </div>
                        <span className="option-label">{type}</span>
                      </button>
                    ))}
                  </div>
                  
                  {/* Video Guide */}
                  <div className="video-guide">
                    <div className="video-header">
                      <BsPlayCircle className="video-icon" />
                      <h4>Hair Type & Styling Guide</h4>
                    </div>
                    <p>Watch this guide to understand hair types and how to style them:</p>
                    <div className="video-container">
                      <YouTubeEmbed 
                        videoId={youtubeVideos.hairType}
                        title="How to Get PERFECT Hair in 4 Easy Steps | Style Theory"
                        width="100%"
                        height="250"
                      />
                    </div>
                    <button 
                      className="help-button"
                      onClick={() => setShowHairTypeHelp(true)}
                      style={{ marginTop: '15px', width: '100%' }}
                    >
                      <FiHelpCircle /> Learn more about hair types and care
                    </button>
                  </div>
                  
                  {/* Information Section */}
                  <div className="hair-type-info">
                    <h4>Why Hair Type Matters for Fashion</h4>
                    <p>Your hair type influences:</p>
                    <ul>
                      <li><strong>Accessories:</strong> Hairpins, headbands, hats that work with your hair</li>
                      <li><strong>Hairstyles:</strong> Recommended styles for your hair texture</li>
                      <li><strong>Necklines:</strong> Clothing necklines that complement your hairstyle</li>
                      <li><strong>Colors:</strong> Hair colors that suit your skin tone</li>
                    </ul>
                    <div className="selection-hint">
                      <p><strong>Tip:</strong> You can select multiple hair types if you have different textures or want to try different styles.</p>
                    </div>
                  </div>
                  
                  {/* Complete Button */}
                  <button 
                    className="complete-section-btn"
                    onClick={() => {
                      if (profileData.hair_type.length > 0) {
                        handleSectionComplete("hair_type");
                      }
                    }}
                    disabled={profileData.hair_type.length === 0}
                    style={{ marginTop: '30px' }}
                  >
                    {profileData.hair_type.length > 0 
                      ? `Save ${profileData.hair_type.length} Hair Type${profileData.hair_type.length > 1 ? 's' : ''}`
                      : "Select at least one hair type"}
                  </button>
                </div>
              )}

              {activeSection === "style_preferences" && (
                <div className="style-preferences">
                  <div className="selected-preferences">
                    <h4>Selected Preferences ({profileData.style_preferences.length})</h4>
                    {profileData.style_preferences.length > 0 ? (
                      <div className="preference-tags">
                        {profileData.style_preferences.map((pref) => (
                          <span key={pref} className="preference-tag">
                            {pref}
                            <button onClick={() => toggleStylePreference(pref)}>×</button>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="no-selection">No preferences selected yet</p>
                    )}
                  </div>
                  
                  <div className="preferences-grid">
                    {stylePreferencesList.map((preference) => (
                      <button
                        key={preference}
                        className={`preference-card ${profileData.style_preferences.includes(preference) ? 'selected' : ''}`}
                        onClick={() => toggleStylePreference(preference)}
                      >
                        <div className="preference-icon">
                          <FiStar />
                        </div>
                        <span className="preference-label">{preference}</span>
                      </button>
                    ))}
                  </div>
                  
                  <button 
                    className="complete-section-btn"
                    onClick={() => {
                      if (profileData.style_preferences.length > 0) {
                        handleSectionComplete("style_preferences");
                      }
                    }}
                    disabled={profileData.style_preferences.length === 0}
                  >
                    {profileData.style_preferences.length > 0 
                      ? `Save ${profileData.style_preferences.length} Preferences`
                      : "Select at least one preference"}
                  </button>
                </div>
              )}

              {activeSection === "measurements" && (
                <div className="measurements-section">
                  <div className="measurements-form">
                    <div className="measurements-grid">
                      {['height', 'weight', 'bust', 'waist', 'hips'].map((measurement) => (
                        <div key={measurement} className="measurement-input">
                          <label htmlFor={measurement}>
                            <BsRulers className="input-icon" />
                            {measurement.charAt(0).toUpperCase() + measurement.slice(1)}
                          </label>
                          <input
                            type="text"
                            id={measurement}
                            placeholder={`Enter ${measurement}`}
                            value={profileData.measurements[measurement] || ""}
                            onChange={(e) => handleMeasurementChange(measurement, e.target.value)}
                            className="form-input"
                          />
                          <span className="measurement-unit">
                            {measurement === "height" ? "cm" : 
                             measurement === "weight" ? "kg" : "in"}
                          </span>
                        </div>
                      ))}
                    </div>
                    
                    <div className="measurements-actions">
                      <button 
                        className="skip-btn"
                        onClick={() => {
                          console.log("Skipping measurements");
                          handleSectionComplete("measurements");
                        }}
                      >
                        Skip for now
                      </button>
                      <button 
                        className="save-btn"
                        onClick={() => {
                          // Check if any measurement is filled
                          const hasMeasurements = Object.values(profileData.measurements).some(v => v);
                          if (hasMeasurements) {
                            handleSectionComplete("measurements");
                          } else {
                            setError("Please enter at least one measurement or skip this section");
                          }
                        }}
                      >
                        Save Measurements
                      </button>
                    </div>
                  </div>
                  
                  <div className="measurements-help">
                    <div className="help-prompt">
                      <FiHelpCircle className="help-icon" />
                      <div>
                        <h4>Need help with measurements?</h4>
                        <p>Watch our guide on how to accurately take your body measurements.</p>
                        <button 
                          className="watch-guide-btn"
                          onClick={() => setShowMeasurementsHelp(true)}
                        >
                          <BsPlayCircle /> Watch Measurement Guide
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="section-navigation">
              <button 
                className="nav-btn prev-btn"
                onClick={() => {
                  const sections = ["gender", "body_type", "skin_tone", "face_shape", "hair_type", "style_preferences", "measurements"];
                  const currentIndex = sections.indexOf(activeSection);
                  if (currentIndex > 0) {
                    const prevSection = sections[currentIndex - 1];
                    console.log(`Navigating from ${activeSection} to ${prevSection}`);
                    setActiveSection(prevSection);
                  }
                }}
                disabled={activeSection === "gender"}
              >
                ← Previous
              </button>
              
              <div className="section-indicators">
                {["gender", "body_type", "skin_tone", "face_shape", "hair_type", "style_preferences", "measurements"].map((section, index) => (
                  <span
                    key={section}
                    className={`section-dot ${activeSection === section ? 'active' : ''} ${completedSections.includes(section) ? 'completed' : ''}`}
                    onClick={() => {
                      console.log(`Clicked dot for ${section}`);
                      setActiveSection(section);
                    }}
                  ></span>
                ))}
              </div>
              
              <button 
                className="nav-btn next-btn"
                onClick={() => {
                  const sections = ["gender", "body_type", "skin_tone", "face_shape", "hair_type", "style_preferences", "measurements"];
                  const currentIndex = sections.indexOf(activeSection);
                  if (currentIndex < sections.length - 1) {
                    const nextSection = sections[currentIndex + 1];
                    console.log(`Navigating from ${activeSection} to ${nextSection}`);
                    setActiveSection(nextSection);
                  }
                }}
                disabled={activeSection === "measurements"}
              >
                Next →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}