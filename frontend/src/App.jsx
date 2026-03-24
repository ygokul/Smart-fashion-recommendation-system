import { useState, useRef, useEffect, useCallback } from "react";
import { FiSend, FiCopy, FiCheck, FiEdit2, FiMaximize2, FiMinimize2, FiChevronRight, FiChevronLeft, FiDownload, FiEye, FiLogOut, FiUser, FiUsers, FiTrash2, FiRefreshCw, FiArchive, FiMessageSquare, FiSettings, FiHome, FiSave, FiX, FiCheckCircle } from "react-icons/fi";
import { BsRobot, BsLightning, BsTerminal } from "react-icons/bs";
import { FaUserCircle, FaGithub } from "react-icons/fa";
import { IoMdSettings } from "react-icons/io";
import { MdAutoFixHigh, MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";
import { TbBrain } from "react-icons/tb";
import { RiShieldCheckLine } from "react-icons/ri";
import { useNavigate } from "react-router-dom";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

import "./App.css";
import { getApiBaseUrl } from "./api";

// API Configuration
const BACKEND_URL = getApiBaseUrl();
const API_URLS = {
  chatStream: `${BACKEND_URL}/chat/stream`,
  chatAuthenticatedStream: `${BACKEND_URL}/chat/authenticated/stream`,
  logout: `${BACKEND_URL}/auth/logout`,
  verify: `${BACKEND_URL}/auth/verify`,
  profile: `${BACKEND_URL}/auth/profile`,
  profileGet: `${BACKEND_URL}/profile/get`,
  profileSave: `${BACKEND_URL}/profile/save`,
  profileStatus: `${BACKEND_URL}/profile/status`,
  sessions: `${BACKEND_URL}/chat/sessions`,
  newSession: `${BACKEND_URL}/chat/session/new`,
  chatHistory: (sessionId) => `${BACKEND_URL}/chat/history/${sessionId}`,
  clearChat: `${BACKEND_URL}/chat/clear`,
  clearSession: (sessionId) => `${BACKEND_URL}/chat/clear?session_id=${sessionId}`,
  adminCleanup: `${BACKEND_URL}/admin/cleanup`,
  imagesCheck: `${BACKEND_URL}/images-check`,
  health: `${BACKEND_URL}/health`
};

// Improved Image Display Component
const ImageDisplay = ({ imageData, isLoading = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imageSrc, setImageSrc] = useState("");

  useEffect(() => {
    if (isLoading) {
      setImageSrc("");
      setImageError(false);
      return;
    }

    if (!imageData) {
      setImageSrc("");
      return;
    }

    // Construct image URL
    let src = "";
    if (imageData.filename) {
      src = `${BACKEND_URL}/images/${imageData.filename}`;
    } else if (imageData.url) {
      src = imageData.url.startsWith('http')
        ? imageData.url
        : `${BACKEND_URL}${imageData.url}`;
    } else if (imageData.image_base64) {
      src = `data:image/png;base64,${imageData.image_base64}`;
    }

    console.log("🖼️ Image source:", src);
    setImageSrc(src);
    setImageError(false);
  }, [imageData, isLoading]);

  if (isLoading) {
    return (
      <div className="image-message loading">
        <div className="image-container">
          <div className="image-loading">
            <div className="loading-dots">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!imageData || !imageSrc) {
    return (
      <div className="image-message error">
        <div className="image-meta">
          <span className="image-prompt">{imageData?.prompt || "Image"}</span>
          <div className="image-tags">
            <span className="image-tag error">Failed to load</span>
          </div>
        </div>
        <div className="image-container">
          <div className="image-error">
            <div className="error-icon">⚠️</div>
            <div className="error-text">Image could not be loaded</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="image-message">
      <div className="image-meta">
        <span className="image-prompt">{imageData.prompt || "Generated Image"}</span>
        <div className="image-tags">
          <span className="image-tag">GENERATED</span>
          <span className="image-tag">FLUX.1-dev</span>
          <span className="image-tag">{imageData.size || "512x512"}</span>
        </div>
      </div>
      <div className={`image-container ${isExpanded ? 'expanded' : ''}`}>
        {imageError ? (
          <div className="image-error">
            <div className="error-icon">⚠️</div>
            <div className="error-text">Failed to load image</div>
            <button
              className="retry-btn"
              onClick={() => {
                setImageError(false);
                const newSrc = imageSrc.includes('?')
                  ? imageSrc.split('?')[0] + '?' + Date.now()
                  : imageSrc + '?' + Date.now();
                setImageSrc(newSrc);
              }}
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            <img
              src={imageSrc}
              alt={imageData.prompt || "Generated image"}
              className="generated-image"
              onClick={() => setIsExpanded(!isExpanded)}
              onLoad={() => console.log("✅ Image loaded successfully:", imageSrc)}
              onError={(e) => {
                console.error("❌ Image failed to load:", imageSrc);
                console.error("Image data:", imageData);
                setImageError(true);
              }}
            />
            <div className="image-actions">
              <button
                className="image-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(imageSrc, '_blank');
                }}
                title="View in new tab"
              >
                <FiEye />
              </button>
              <button
                className="image-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                title={isExpanded ? "Shrink" : "Expand"}
              >
                {isExpanded ? <FiMinimize2 /> : <FiMaximize2 />}
              </button>
              <button
                className="image-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  if (imageSrc.startsWith('data:image')) {
                    fetch(imageSrc)
                      .then(res => res.blob())
                      .then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `image-${Date.now()}.png`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                      });
                  } else {
                    const link = document.createElement('a');
                    link.href = imageSrc;
                    link.download = `image-${Date.now()}.png`;
                    link.click();
                  }
                }}
                title="Download"
              >
                <FiDownload />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// Session Management Component
const SessionManager = ({ sessions, activeSession, onSelectSession, onCreateSession, onDeleteSession, onClose }) => {
  const [newSessionName, setNewSessionName] = useState("");

  const handleCreateSession = () => {
    if (newSessionName.trim()) {
      onCreateSession(newSessionName);
      setNewSessionName("");
    }
  };

  return (
    <div className="session-manager">
      <div className="session-header">
        <h3>Chat Sessions</h3>
        <button className="close-sessions" onClick={onClose}>×</button>
      </div>

      <div className="create-session">
        <input
          type="text"
          value={newSessionName}
          onChange={(e) => setNewSessionName(e.target.value)}
          placeholder="Enter session name"
          onKeyPress={(e) => e.key === 'Enter' && handleCreateSession()}
        />
        <button
          onClick={handleCreateSession}
          disabled={!newSessionName.trim()}
        >
          <FiEdit2 /> New
        </button>
      </div>

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="no-sessions">
            <FiArchive />
            <p>No saved sessions</p>
          </div>
        ) : (
          sessions.map(session => (
            <div
              key={session.id}
              className={`session-item ${activeSession === session.id ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
            >
              <div className="session-info">
                <div className="session-icon">
                  <BsRobot />
                </div>
                <div className="session-details">
                  <h4>{session.title || "Untitled Session"}</h4>
                  <p>{session.message_count || 0} messages</p>
                  {session.last_activity && (
                    <small>Last active: {new Date(session.last_activity).toLocaleDateString()}</small>
                  )}
                </div>
              </div>
              <div className="session-actions">
                <button
                  className="delete-session-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  title="Delete session"
                >
                  <FiTrash2 />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Profile Edit Modal Component
const ProfileEditModal = ({
  profileData,
  onSave,
  onCancel,
  onInputChange,
  onMeasurementChange,
  onStylePreferenceToggle
}) => {
  const [localData, setLocalData] = useState(profileData);
  const [saving, setSaving] = useState(false);

  const styleOptions = [
    "Casual", "Formal", "Business", "Sporty", "Bohemian",
    "Vintage", "Minimalist", "Streetwear", "Elegant", "Edgy",
    "Romantic", "Preppy", "Artsy", "Classic", "Trendy"
  ];

  const genderOptions = [
    "Male", "Female", "Non-binary", "Prefer not to say"
  ];

  const bodyTypeOptions = [
    "Rectangle", "Hourglass", "Pear", "Apple", "Inverted Triangle"
  ];

  const skinToneOptions = [
    "Fair", "Light", "Medium", "Olive", "Tan", "Dark"
  ];

  const faceShapeOptions = [
    "Oval", "Round", "Square", "Heart", "Diamond", "Oblong"
  ];

  const hairTypeOptions = [
    "Straight", "Wavy", "Curly", "Coily", "Bald", "Short", "Long"
  ];

  const handleLocalInputChange = (field, value) => {
    setLocalData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleLocalMeasurementChange = (field, value) => {
    setLocalData(prev => ({
      ...prev,
      measurements: {
        ...prev.measurements,
        [field]: value
      },
      [field]: value
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(localData);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-edit-modal-overlay">
      <div className="profile-edit-modal">
        <div className="modal-header">
          <h2>Edit Profile</h2>
          <button className="close-modal" onClick={onCancel}>
            <FiX />
          </button>
        </div>

        <div className="modal-content">
          {/* Gender */}
          <div className="form-group">
            <label>Gender</label>
            <select
              value={localData.gender || ''}
              onChange={(e) => handleLocalInputChange('gender', e.target.value)}
            >
              <option value="">Select Gender</option>
              {genderOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          {/* Body Type */}
          <div className="form-group">
            <label>Body Type</label>
            <select
              value={localData.body_type || ''}
              onChange={(e) => handleLocalInputChange('body_type', e.target.value)}
            >
              <option value="">Select Body Type</option>
              {bodyTypeOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          {/* Skin Tone */}
          <div className="form-group">
            <label>Skin Tone</label>
            <select
              value={localData.skin_tone || ''}
              onChange={(e) => handleLocalInputChange('skin_tone', e.target.value)}
            >
              <option value="">Select Skin Tone</option>
              {skinToneOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          {/* Face Shape */}
          <div className="form-group">
            <label>Face Shape</label>
            <select
              value={localData.face_shape || ''}
              onChange={(e) => handleLocalInputChange('face_shape', e.target.value)}
            >
              <option value="">Select Face Shape</option>
              {faceShapeOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          {/* Hair Type as Multi-Select */}
          <div className="form-section">
            <h3>Hair Type</h3>
            <p className="section-description">Select all that apply to your hair type</p>
            <div className="style-preferences-grid">
              {hairTypeOptions.map((hairType, index) => (
                <button
                  key={index}
                  className={`style-option ${
                    (localData.hair_type || []).includes(hairType) ? 'selected' : ''
                  }`}
                  onClick={() => {
                    const currentHairTypes = Array.isArray(localData.hair_type) 
                      ? localData.hair_type 
                      : localData.hair_type 
                        ? [localData.hair_type] 
                        : [];
                    
                    const newHairTypes = currentHairTypes.includes(hairType)
                      ? currentHairTypes.filter(h => h !== hairType)
                      : [...currentHairTypes, hairType];
                    
                    handleLocalInputChange('hair_type', newHairTypes);
                  }}
                  type="button"
                >
                  {hairType}
                  {(localData.hair_type || []).includes(hairType) && <FiCheck className="check-icon" />}
                </button>
              ))}
            </div>
          </div>

          {/* Measurements Section */}
          <div className="form-section">
            <h3>Measurements (Optional)</h3>
            <div className="measurements-grid">
              <div className="measurement-input">
                <label>Height (cm)</label>
                <input
                  type="number"
                  value={localData.measurements?.height || ''}
                  onChange={(e) => handleLocalMeasurementChange('height', e.target.value)}
                  placeholder="e.g., 170"
                  min="50"
                  max="250"
                />
              </div>

              <div className="measurement-input">
                <label>Weight (kg)</label>
                <input
                  type="number"
                  value={localData.measurements?.weight || ''}
                  onChange={(e) => handleLocalMeasurementChange('weight', e.target.value)}
                  placeholder="e.g., 65"
                  min="20"
                  max="200"
                  step="0.1"
                />
              </div>

              <div className="measurement-input">
                <label>Bust (inches)</label>
                <input
                  type="number"
                  value={localData.measurements?.bust || ''}
                  onChange={(e) => handleLocalMeasurementChange('bust', e.target.value)}
                  placeholder="e.g., 34"
                  min="20"
                  max="60"
                  step="0.5"
                />
              </div>

              <div className="measurement-input">
                <label>Waist (inches)</label>
                <input
                  type="number"
                  value={localData.measurements?.waist || ''}
                  onChange={(e) => handleLocalMeasurementChange('waist', e.target.value)}
                  placeholder="e.g., 28"
                  min="20"
                  max="60"
                  step="0.5"
                />
              </div>

              <div className="measurement-input">
                <label>Hips (inches)</label>
                <input
                  type="number"
                  value={localData.measurements?.hips || ''}
                  onChange={(e) => handleLocalMeasurementChange('hips', e.target.value)}
                  placeholder="e.g., 36"
                  min="20"
                  max="60"
                  step="0.5"
                />
              </div>
            </div>
          </div>

          {/* Style Preferences */}
          <div className="form-section">
            <h3>Style Preferences</h3>
            <p className="section-description">Select all that apply to your personal style</p>
            <div className="style-preferences-grid">
              {styleOptions.map((style, index) => (
                <button
                  key={index}
                  className={`style-option ${(localData.style_preferences || []).includes(style) ? 'selected' : ''}`}
                  onClick={() => {
                    const newPreferences = (localData.style_preferences || []).includes(style)
                      ? (localData.style_preferences || []).filter(p => p !== style)
                      : [...(localData.style_preferences || []), style];
                    handleLocalInputChange('style_preferences', newPreferences);
                  }}
                  type="button"
                >
                  {style}
                  {(localData.style_preferences || []).includes(style) && <FiCheck className="check-icon" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button
            className="cancel-btn"
            onClick={onCancel}
            disabled={saving}
          >
            <FiX /> Cancel
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>Saving...</>
            ) : (
              <>
                <FiSave /> Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Profile Details Component (For View Profile Page)
const ProfileDetails = ({ user, profileData, onSaveProfile }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState(profileData);
  const [saveStatus, setSaveStatus] = useState({ type: '', message: '' });

  const getProfileCompletion = () => {
    if (!profileData) return 0;

    let completed = 0;
    const totalSections = 7;

    if (profileData.gender) completed++;
    if (profileData.body_type) completed++;
    if (profileData.skin_tone) completed++;
    if (profileData.face_shape) completed++;
    // Check if hair_type has at least one selection
    if (profileData.hair_type && profileData.hair_type.length > 0) completed++;
    if (profileData.style_preferences && profileData.style_preferences.length > 0) completed++;
    if (profileData.measurements && Object.values(profileData.measurements).some(v => v)) completed++;

    return Math.round((completed / totalSections) * 100);
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

  const handleSave = async (updatedData) => {
    try {
      await onSaveProfile(updatedData);
      setSaveStatus({ type: 'success', message: 'Profile updated successfully!' });
      setIsEditing(false);

      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveStatus({ type: '', message: '' });
      }, 3000);
    } catch (error) {
      setSaveStatus({ type: 'error', message: error.message });
    }
  };

  const handleEditClick = () => {
    setEditData(profileData);
    setIsEditing(true);
    setSaveStatus({ type: '', message: '' });
  };

  return (
    <div className="profile-details-container">
      {saveStatus.message && (
        <div className={`save-status ${saveStatus.type}`}>
          {saveStatus.type === 'success' ? <FiCheckCircle /> : '⚠️'}
          <span>{saveStatus.message}</span>
        </div>
      )}

      <div className="profile-details-header">
        <h2>Profile Details</h2>
        <button
          className="edit-profile-btn-large"
          onClick={handleEditClick}
          title="Edit profile setup"
        >
          <FiEdit2 /> Edit Profile
        </button>
      </div>

      <div className="profile-details-content">
        <div className="profile-overview">
          <div className="profile-avatar-large">
            <FaUserCircle />
          </div>

          <div className="profile-basic-info">
            <h3>{user?.username || "User"}</h3>
            <p className="profile-email">{user?.email || "No email"}</p>
            <p className="profile-tier">{user?.subscription_tier || "Free Tier"}</p>
            <p className="profile-joined">
              Joined {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Recently"}
            </p>
          </div>
        </div>

        {/* Profile Completion Progress */}
        <div className="completion-section">
          <div className="completion-header">
            <h4>Profile Completion</h4>
            <span className="completion-percentage">{getProfileCompletion()}%</span>
          </div>
          <div className="progress-bar-large">
            <div
              className="progress-fill-large"
              style={{ width: `${getProfileCompletion()}%` }}
            ></div>
          </div>
          <p className="completion-note">
            {getProfileCompletion() >= 80
              ? "Great! Your profile is almost complete."
              : getProfileCompletion() >= 50
                ? "Good progress! Complete more sections for better recommendations."
                : "Please complete more sections for personalized recommendations."}
          </p>
        </div>

        {/* Profile Setup Details */}
        <div className="profile-sections">
          <h3>Profile Setup Details</h3>

          {profileData ? (
            <div className="sections-grid">
              {/* Gender Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('gender') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('gender') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Gender</h4>
                  <p className="section-value">{profileData.gender || "Not set"}</p>
                  <span className="section-status">
                    {profileData.gender ? "✓ Completed" : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Body Type Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('body_type') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('body_type') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Body Type</h4>
                  <p className="section-value">{profileData.body_type || "Not set"}</p>
                  <span className="section-status">
                    {profileData.body_type ? "✓ Completed" : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Skin Tone Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('skin_tone') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('skin_tone') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Skin Tone</h4>
                  <p className="section-value">{profileData.skin_tone || "Not set"}</p>
                  <span className="section-status">
                    {profileData.skin_tone ? "✓ Completed" : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Face Shape Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('face_shape') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('face_shape') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Face Shape</h4>
                  <p className="section-value">{profileData.face_shape || "Not set"}</p>
                  <span className="section-status">
                    {profileData.face_shape ? "✓ Completed" : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Hair Type Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('hair_type') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('hair_type') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Hair Type</h4>
                  <div className="style-tags-list">
                    {profileData.hair_type && profileData.hair_type.length > 0 ? (
                      profileData.hair_type.map((hairType, index) => (
                        <span key={index} className="style-tag-item">{hairType}</span>
                      ))
                    ) : (
                      <p className="no-data">No hair types selected</p>
                    )}
                  </div>
                  <span className="section-status">
                    {profileData.hair_type && profileData.hair_type.length > 0
                      ? `✓ ${profileData.hair_type.length} selected`
                      : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Style Preferences Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('style_preferences') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('style_preferences') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Style Preferences</h4>
                  <div className="style-tags-list">
                    {profileData.style_preferences && profileData.style_preferences.length > 0 ? (
                      profileData.style_preferences.map((pref, index) => (
                        <span key={index} className="style-tag-item">{pref}</span>
                      ))
                    ) : (
                      <p className="no-data">No preferences selected</p>
                    )}
                  </div>
                  <span className="section-status">
                    {profileData.style_preferences && profileData.style_preferences.length > 0
                      ? `✓ ${profileData.style_preferences.length} selected`
                      : "Not completed"}
                  </span>
                </div>
              </div>

              {/* Measurements Section */}
              <div className="profile-section-card" style={{ borderLeftColor: getSectionColor('measurements') }}>
                <div className="section-icon" style={{ backgroundColor: getSectionColor('measurements') }}>
                  <FiUser />
                </div>
                <div className="section-content">
                  <h4>Measurements</h4>
                  <div className="measurements-list">
                    {profileData.measurements ? (
                      <div className="measurements-details">
                        {profileData.measurements.height && (
                          <div className="measurement-item">
                            <span>Height:</span>
                            <strong>{profileData.measurements.height} cm</strong>
                          </div>
                        )}
                        {profileData.measurements.weight && (
                          <div className="measurement-item">
                            <span>Weight:</span>
                            <strong>{profileData.measurements.weight} kg</strong>
                          </div>
                        )}
                        {profileData.measurements.bust && (
                          <div className="measurement-item">
                            <span>Bust:</span>
                            <strong>{profileData.measurements.bust} in</strong>
                          </div>
                        )}
                        {profileData.measurements.waist && (
                          <div className="measurement-item">
                            <span>Waist:</span>
                            <strong>{profileData.measurements.waist} in</strong>
                          </div>
                        )}
                        {profileData.measurements.hips && (
                          <div className="measurement-item">
                            <span>Hips:</span>
                            <strong>{profileData.measurements.hips} in</strong>
                          </div>
                        )}
                        {!profileData.measurements.height && !profileData.measurements.weight &&
                          !profileData.measurements.bust && !profileData.measurements.waist &&
                          !profileData.measurements.hips && (
                            <p className="no-data">No measurements provided</p>
                          )}
                      </div>
                    ) : (
                      <p className="no-data">No measurements provided</p>
                    )}
                  </div>
                  <span className="section-status">
                    {profileData.measurements && Object.values(profileData.measurements).some(v => v)
                      ? "✓ Provided"
                      : "Not completed"}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="no-profile-data">
              <div className="no-data-icon">📝</div>
              <h4>No Profile Data Found</h4>
              <p>You haven't set up your profile yet. Click "Edit Profile" to get started.</p>
              <button
                className="setup-profile-btn"
                onClick={handleEditClick}
              >
                <FiEdit2 /> Setup Profile Now
              </button>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="profile-actions-section">
          <button
            className="action-btn primary"
            onClick={handleEditClick}
          >
            <FiEdit2 /> Edit Profile
          </button>
          <button
            className="action-btn secondary"
            onClick={() => window.location.reload()}
          >
            <FiRefreshCw /> Refresh Data
          </button>
        </div>
      </div>

      {/* Edit Modal */}
      {isEditing && (
        <ProfileEditModal
          profileData={editData}
          onSave={handleSave}
          onCancel={() => setIsEditing(false)}
        />
      )}
    </div>
  );
};

export default function App() {
  const navigate = useNavigate();

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!localStorage.getItem("access_token");
  });
  const [user, setUser] = useState(() => {
    const userData = localStorage.getItem("user_data");
    return userData ? JSON.parse(userData) : null;
  });
  const [token, setToken] = useState(() => {
    return localStorage.getItem("access_token") || null;
  });

  // Profile state
  const [userProfile, setUserProfile] = useState(() => {
    const profileData = localStorage.getItem("user_profile");
    return profileData ? JSON.parse(profileData) : null;
  });
  const [profileLoading, setProfileLoading] = useState(false);

  // Session state
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem("session_id") || crypto.randomUUID();
  });
  const [userSessions, setUserSessions] = useState([]);
  const [showSessionManager, setShowSessionManager] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isDarkTheme, setIsDarkTheme] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);
  const [activePage, setActivePage] = useState("chat"); // "chat" or "profile"
  const [modelVersion] = useState("SmartFit");
  const [thinkingTime, setThinkingTime] = useState(0);

  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const thinkingTimerRef = useRef(null);

  // Check authentication on mount
  useEffect(() => {
    checkAuthentication();
    if (isAuthenticated) {
      loadUserSessions();
      loadUserProfileData();
    }
  }, [isAuthenticated]);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input, adjustTextareaHeight]);

  useEffect(() => {
    if (activePage === "chat") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading, activePage]);

  // Theme effect
  useEffect(() => {
    if (isDarkTheme) {
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
    }
  }, [isDarkTheme]);

  // Start/stop thinking timer
  useEffect(() => {
    if (loading) {
      setThinkingTime(0);
      thinkingTimerRef.current = setInterval(() => {
        setThinkingTime(prev => prev + 100);
      }, 100);
    } else {
      if (thinkingTimerRef.current) {
        clearInterval(thinkingTimerRef.current);
        thinkingTimerRef.current = null;
      }
    }

    return () => {
      if (thinkingTimerRef.current) {
        clearInterval(thinkingTimerRef.current);
      }
    };
  }, [loading]);

  // Authentication functions
  const checkAuthentication = async () => {
    const savedToken = localStorage.getItem("access_token");
    if (savedToken) {
      try {
        const response = await fetch(API_URLS.verify, {
          headers: {
            'Authorization': `Bearer ${savedToken}`
          }
        });

        if (response.ok) {
          setToken(savedToken);
          setIsAuthenticated(true);

          // Load user profile
          await loadUserProfile(savedToken);
        } else {
          handleLogout();
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
        handleLogout();
      }
    } else {
      setIsAuthenticated(false);
    }
  };

  const loadUserProfile = async (userToken) => {
    try {
      const response = await fetch(API_URLS.profile, {
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem("user_data", JSON.stringify(userData));
      }
    } catch (error) {
      console.error("Failed to load user profile:", error);
    }
  };

  const loadUserProfileData = async () => {
    if (!isAuthenticated || !token) return;

    try {
      setProfileLoading(true);
      const response = await fetch(API_URLS.profileGet, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.profile_data) {
          // Transform the data to match our frontend structure
          const transformedProfile = {
            gender: data.profile_data.gender,
            body_type: data.profile_data.body_type,
            skin_tone: data.profile_data.skin_tone,
            face_shape: data.profile_data.face_shape,
            hair_type: Array.isArray(data.profile_data.hair_type) 
              ? data.profile_data.hair_type 
              : data.profile_data.hair_type 
                ? [data.profile_data.hair_type] 
                : [],
            style_preferences: data.profile_data.style_preferences || [],
            measurements: data.profile_data.measurements || {
              height: data.profile_data.height,
              weight: data.profile_data.weight,
              bust: data.profile_data.bust,
              waist: data.profile_data.waist,
              hips: data.profile_data.hips
            }
          };

          setUserProfile(transformedProfile);
          localStorage.setItem('user_profile', JSON.stringify(transformedProfile));
          console.log("Loaded user profile:", transformedProfile);
        }
      } else if (response.status === 404) {
        // No profile exists yet, that's okay
        console.log("No profile found - new user");
      }
    } catch (error) {
      console.error("Failed to load user profile data:", error);
    } finally {
      setProfileLoading(false);
    }
  };

  const loadUserSessions = async () => {
    if (!isAuthenticated || !token) return;

    try {
      const response = await fetch(API_URLS.sessions, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserSessions(data.sessions || []);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const handleLogout = async () => {
    try {
      if (token && sessionId) {
        await fetch(API_URLS.logout, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ session_id: sessionId })
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear all authentication data
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_data");
      localStorage.removeItem("user_id");
      localStorage.removeItem("username");
      localStorage.removeItem("session_id");
      localStorage.removeItem("user_profile");
      localStorage.removeItem("profile_complete");

      setToken(null);
      setUser(null);
      setUserProfile(null);
      setIsAuthenticated(false);
      setSessionId(crypto.randomUUID());
      setMessages([]);
      setUserSessions([]);
      setActivePage("chat");

      // Redirect to login page
      navigate("/login");
    }
  };

  const handleSaveProfile = async (profileData) => {
    try {
      const token = localStorage.getItem('access_token');
      const sessionId = localStorage.getItem('session_id') || 'default';

      if (!token) {
        throw new Error('Please login first');
      }

      const saveData = {
        session_id: sessionId,
        profile_data: {
          gender: profileData.gender,
          body_type: profileData.body_type,
          skin_tone: profileData.skin_tone,
          face_shape: profileData.face_shape,
          hair_type: profileData.hair_type || [],
          style_preferences: profileData.style_preferences || [],
          measurements: profileData.measurements || {},
          height: profileData.measurements?.height || '',
          weight: profileData.measurements?.weight || '',
          bust: profileData.measurements?.bust || '',
          waist: profileData.measurements?.waist || '',
          hips: profileData.measurements?.hips || ''
        }
      };

      const response = await fetch(API_URLS.profileSave, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(saveData)
      });

      if (response.ok) {
        const result = await response.json();

        // Update local state
        setUserProfile(profileData);
        localStorage.setItem('user_profile', JSON.stringify(profileData));
        localStorage.setItem('profile_complete', result.is_complete.toString());

        // Reload profile data to get updated completion status
        await loadUserProfileData();

        return result;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      throw error;
    }
  };

  const handleCreateNewSession = async (sessionName) => {
    if (!isAuthenticated || !token) {
      // For non-authenticated users, just create a local session
      const newSessionId = crypto.randomUUID();
      setActiveSessionId(newSessionId);
      setSessionId(newSessionId);
      setMessages([]);
      return;
    }

    try {
      const response = await fetch(API_URLS.newSession, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: crypto.randomUUID(),
          session_name: sessionName
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newSession = {
          id: data.session_id,
          title: sessionName,
          message_count: 0,
          last_activity: new Date().toISOString()
        };

        setUserSessions(prev => [newSession, ...prev]);
        setActiveSessionId(data.session_id);
        setSessionId(data.session_id);
        setMessages([]);

        return newSession;
      }
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleSelectSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    setSessionId(sessionId);
    setShowSessionManager(false);

    // Load session history if authenticated
    if (isAuthenticated && token) {
      await loadSessionHistory(sessionId);
    }
  };

  const loadSessionHistory = async (sessionId) => {
    if (!isAuthenticated || !token) return;

    try {
      const response = await fetch(API_URLS.chatHistory(sessionId), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();

        // Convert API messages to app format
        const formattedMessages = data.messages.map(msg => ({
          role: msg.role,
          text: msg.text,
          timestamp: new Date(msg.timestamp),
          id: Date.now() + Math.random(),
          tokens: msg.tokens || 0,
          imageData: msg.imageData,
          isSystem: false
        }));

        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error("Failed to load session history:", error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this session? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(API_URLS.clearSession(sessionId), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setUserSessions(prev => prev.filter(s => s.id !== sessionId));

        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setSessionId(crypto.randomUUID());
          setMessages([]);
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
      alert("Failed to delete session. Please try again.");
    }
  };

  // Language detection function
  const detectLanguage = (code) => {
    const normalizedCode = code.toLowerCase().trim();
    const lines = normalizedCode.split('\n').slice(0, 3);
    const firstLines = lines.join(' ');

    // Check for bash/shell patterns
    const bashPatterns = [
      /^#!/,
      /\$\([^)]+\)/,
      /\$\{[^}]+\}/,
      /(apt-get|apt|yum|brew|npm|pip|git) (install|update|upgrade|remove)/,
      /(sudo|chmod|chown|mkdir|rm|cp|mv|ls|cd|pwd|echo|cat|grep|find|awk|sed) /,
      /(curl|wget) (http|https):\/\//,
      /export [A-Z_]+=/,
      /source |\. /,
      /&&|\|\|/,
      /> |>> |< |2>/,
      /alias [a-zA-Z_]+=/,
      /function [a-zA-Z_]+\(\)/
    ];

    const hasBashPattern = bashPatterns.some(pattern => pattern.test(firstLines));

    if (firstLines.includes('#!')) {
      if (firstLines.includes('bash') || firstLines.includes('sh')) {
        return 'bash';
      }
    }

    if (hasBashPattern) {
      return 'bash';
    }

    // Check for Python patterns
    const pythonPatterns = [
      /^import |^from [a-zA-Z_]+ import/,
      /def [a-zA-Z_]+\(/,
      /class [A-Za-z_]+/,
      /print\([^)]*\)/,
      /if __name__ == "__main__"/,
      /(True|False|None)\b/,
      /(async|await)\b/,
      /(yield|raise)\b/,
      /(try:|except |finally:)/,
      /(with |as )/,
      /(lambda |:)/,
      /\.(append|remove|pop|insert|split|join|format)\(/,
      /\[.*for .* in .*\]/,
      /@[a-zA-Z_]+/,
      /self\./
    ];

    const hasPythonPattern = pythonPatterns.some(pattern => pattern.test(firstLines));
    const hasPythonKeywords = firstLines.includes('def ') || firstLines.includes('class ') ||
      firstLines.includes('import ') || firstLines.includes('print(');

    if (hasPythonPattern || hasPythonKeywords) {
      return 'python';
    }

    // Check for other languages
    if (firstLines.includes('console.log') || firstLines.includes('function') ||
      firstLines.includes('const ') || firstLines.includes('let ') || firstLines.includes('=>')) {
      return 'javascript';
    }

    if (firstLines.includes('public class') || firstLines.includes('System.out.') ||
      firstLines.includes('void main')) {
      return 'java';
    }

    if (firstLines.includes('#include') || firstLines.includes('using namespace') ||
      firstLines.includes('std::')) {
      return 'cpp';
    }

    if (firstLines.includes('fn ') || firstLines.includes('impl ') || firstLines.includes('unwrap()')) {
      return 'rust';
    }

    if (firstLines.includes('func ') && firstLines.includes('package ')) {
      return 'go';
    }

    if (firstLines.includes('<?php') || firstLines.includes('echo ')) {
      return 'php';
    }

    if (firstLines.includes('SELECT ') || firstLines.includes('FROM ') || firstLines.includes('WHERE ')) {
      return 'sql';
    }

    if (firstLines.includes('<html') || firstLines.includes('<!DOCTYPE')) {
      return 'html';
    }

    if (firstLines.includes('{') && firstLines.includes('}') &&
      (firstLines.includes(':') || firstLines.includes(';'))) {
      return 'css';
    }

    return 'python';
  };

  // Language display name
  const getDisplayLanguage = (language) => {
    const languageMap = {
      'bash': 'Terminal',
      'sh': 'Shell',
      'python': 'Python',
      'py': 'Python',
      'javascript': 'JavaScript',
      'js': 'JavaScript',
      'typescript': 'TypeScript',
      'ts': 'TypeScript',
      'java': 'Java',
      'cpp': 'C++',
      'c++': 'C++',
      'c': 'C',
      'rust': 'Rust',
      'go': 'Go',
      'ruby': 'Ruby',
      'rb': 'Ruby',
      'php': 'PHP',
      'swift': 'Swift',
      'kotlin': 'Kotlin',
      'html': 'HTML',
      'css': 'CSS',
      'sql': 'SQL',
      'json': 'JSON',
      'yaml': 'YAML',
      'yml': 'YAML',
      'dockerfile': 'Dockerfile',
      'markdown': 'Markdown',
      'md': 'Markdown'
    };

    return languageMap[language] || language.charAt(0).toUpperCase() + language.slice(1);
  };

  // Language color
  const getLanguageColor = (language) => {
    const colors = {
      'bash': '#4EAA25',
      'sh': '#4EAA25',
      'python': '#3572A5',
      'javascript': '#F1E05A',
      'typescript': '#2B7489',
      'java': '#B07219',
      'cpp': '#F34B7D',
      'c': '#555555',
      'rust': '#DEA584',
      'go': '#00ADD8',
      'ruby': '#701516',
      'php': '#4F5D95',
      'swift': '#FFAC45',
      'kotlin': '#A97BFF',
      'html': '#E34C26',
      'css': '#563D7C',
      'sql': '#E38C00',
      'json': '#292929',
      'yaml': '#CB171E',
      'dockerfile': '#2496ED',
      'markdown': '#083FA1'
    };

    return colors[language] || '#6B7280';
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input;
    setInput("");

    // Create user message
    const userMessageId = Date.now();
    const userMessage = {
      role: "user",
      text: userText,
      timestamp: new Date(),
      id: userMessageId,
      tokens: Math.ceil(userText.length / 4)
    };

    setMessages((p) => [...p, userMessage]);

    // Create a unique ID for the assistant response
    const assistantId = Date.now() + 1;

    // Create assistant message with loading state
    const assistantMessage = {
      role: "assistant",
      text: "",
      timestamp: new Date(),
      id: assistantId,
      tokens: 0,
      thinkingTime: 0,
      prompt: userText,
      isLoading: true
    };

    setMessages((p) => [...p, assistantMessage]);

    setLoading(true);
    setIsTyping(true);

    try {
      // Choose the appropriate API endpoint based on authentication
      const apiUrl = isAuthenticated
        ? API_URLS.chatAuthenticatedStream
        : API_URLS.chatStream;

      const headers = {
        "Content-Type": "application/json"
      };

      // Add authentication header if logged in
      if (isAuthenticated && token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(apiUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: sessionId,
          query: userText
        }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error("❌ API Error:", errorText);
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const contentType = res.headers.get("content-type");

      if (contentType && contentType.includes("text/event-stream")) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let assistantText = "";
        let imageDataReceived = null;
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();

            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.slice(6);
                if (dataStr === '') continue;

                const data = JSON.parse(dataStr);
                console.log("📥 Received data:", data);

                if (data.type === "text") {
                  assistantText += data.content;
                  setIsTyping(true);
                  setMessages((p) => {
                    const updated = [...p];
                    const targetMessage = updated.find(msg => msg.id === assistantId);
                    if (targetMessage && !targetMessage.imageData) {
                      targetMessage.text = assistantText;
                      targetMessage.tokens = Math.ceil(assistantText.length / 4);
                      targetMessage.timestamp = new Date();
                      targetMessage.thinkingTime = thinkingTime;
                      targetMessage.isLoading = false;
                    }
                    return updated;
                  });
                } else if (data.type === "image") {
                  imageDataReceived = {
                    type: "image",
                    image_id: data.image_id || `img_${Date.now()}`,
                    prompt: data.prompt || userText,
                    filename: data.filename,
                    url: data.url,
                    image_base64: data.image_base64,
                    model: data.model || "FLUX.1-dev",
                    size: data.size || "512x512",
                    format: data.format || "PNG"
                  };

                  console.log("🖼️ Image data received:", imageDataReceived);

                  setMessages((p) => {
                    const updated = [...p];
                    const targetMessage = updated.find(msg => msg.id === assistantId);
                    if (targetMessage) {
                      targetMessage.imageData = imageDataReceived;
                      targetMessage.timestamp = new Date();
                      targetMessage.thinkingTime = thinkingTime;
                      targetMessage.isLoading = false;

                      if (!targetMessage.text) {
                        targetMessage.text = "Here's the image you requested:";
                      }
                    } else {
                      updated.push({
                        role: "assistant",
                        text: "Here's the image you requested:",
                        timestamp: new Date(),
                        id: assistantId,
                        imageData: imageDataReceived,
                        thinkingTime: thinkingTime,
                        isLoading: false
                      });
                    }
                    return updated;
                  });
                } else if (data.type === "error") {
                  console.error("❌ Error from server:", data.content);
                  setMessages((p) => {
                    const updated = [...p];
                    const targetMessage = updated.find(msg => msg.id === assistantId);
                    if (targetMessage) {
                      targetMessage.text = `Error: ${data.content}`;
                      targetMessage.isError = true;
                      targetMessage.isLoading = false;
                    }
                    return updated;
                  });
                }
              } catch (e) {
                console.error("❌ Error parsing SSE data:", e);
              }
            }
          }

          buffer = lines[lines.length - 1];
        }
      } else {
        const data = await res.json();
        console.log("📥 Non-stream response:", data);

        setMessages((p) => {
          const updated = [...p];
          const targetMessage = updated.find(msg => msg.id === assistantId);

          if (!targetMessage) {
            const newAssistantMessage = {
              role: "assistant",
              text: "",
              timestamp: new Date(),
              id: assistantId,
              thinkingTime: thinkingTime,
              isLoading: false
            };

            if (data.type === "image") {
              newAssistantMessage.imageData = data;
              newAssistantMessage.text = "Here's the image you requested:";
            } else if (data.type === "text") {
              newAssistantMessage.text = data.content;
              newAssistantMessage.tokens = Math.ceil(data.content.length / 4);
            } else if (data.type === "error") {
              newAssistantMessage.text = data.content;
              newAssistantMessage.isError = true;
            }

            updated.push(newAssistantMessage);
          } else {
            targetMessage.isLoading = false;

            if (data.type === "image") {
              targetMessage.imageData = data;
              targetMessage.timestamp = new Date();
              targetMessage.thinkingTime = thinkingTime;
              if (!targetMessage.text) {
                targetMessage.text = "Here's the image you requested:";
              }
            } else if (data.type === "text") {
              targetMessage.text = data.content;
              targetMessage.tokens = Math.ceil(data.content.length / 4);
              targetMessage.timestamp = new Date();
              targetMessage.thinkingTime = thinkingTime;
            } else if (data.type === "error") {
              targetMessage.text = data.content;
              targetMessage.isError = true;
            }
          }

          return updated;
        });
      }
    } catch (error) {
      console.error("❌ Error sending message:", error);
      setMessages((p) => {
        const updated = [...p];
        const targetMessage = updated.find(msg => msg.id === assistantId);
        if (targetMessage) {
          targetMessage.text = `Sorry, I encountered an error: ${error.message}. Please try again.`;
          targetMessage.isError = true;
          targetMessage.isLoading = false;
        }
        return updated;
      });
    } finally {
      setLoading(false);
      setIsTyping(false);
      setThinkingTime(0);
    }
  };

  const copyCode = (code, index) => {
    navigator.clipboard.writeText(code);
    setCopied(index);
    setTimeout(() => setCopied(null), 1500);
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const formatDate = (date) => {
    const now = new Date();
    const msgDate = new Date(date);
    const diffMs = now - msgDate;
    const diffHours = diffMs / (1000 * 60 * 60);

    if (diffHours < 24) {
      return "Today";
    } else if (diffHours < 48) {
      return "Yesterday";
    } else {
      return msgDate.toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        year: msgDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    }
  };

  const formatThinkingTime = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleRegenerate = () => {
    if (messages.length > 0) {
      const lastUserMessage = messages.filter(m => m.role === "user").pop();
      if (lastUserMessage) {
        setInput(lastUserMessage.text);
        setTimeout(() => {
          sendMessage();
        }, 100);
      }
    }
  };

  // Clear conversation history function
  const handleClearHistory = async () => {
    if (messages.length === 0) {
      alert("No conversation history to clear.");
      return;
    }

    if (window.confirm("Are you sure you want to clear all conversation history? This action cannot be undone.")) {
      try {
        const headers = {
          'Content-Type': 'application/json'
        };

        if (isAuthenticated && token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(API_URLS.clearChat, {
          method: 'POST',
          headers,
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (response.ok) {
          const result = await response.json();
          console.log("Clear history result:", result);
          setMessages([]);
          setInput("");
          alert("Conversation history cleared successfully!");
        } else {
          throw new Error('Failed to clear history');
        }
      } catch (error) {
        console.error("Error clearing history:", error);
        alert("Failed to clear history. Please try again.");
      }
    }
  };

  // Clear chat (just local messages) function
  const handleClearChat = () => {
    if (messages.length > 0 && window.confirm("Are you sure you want to clear the current chat? This will only clear the display, not the server history.")) {
      setMessages([]);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme);
  };

  const toggleSidebar = () => {
    setShowSidebar(!showSidebar);
  };

  const handleNewChat = () => {
    if (messages.length > 0) {
      if (window.confirm("Start a new chat? Current conversation will be saved to your history.")) {
        setMessages([]);
        setInput("");

        // Create a new session
        handleCreateNewSession(`Chat ${new Date().toLocaleDateString()}`);
      }
    }
  };

  const totalTokens = messages.reduce((sum, msg) => sum + (msg.tokens || 0), 0);
  const userMessagesCount = messages.filter(m => m.role === 'user').length;
  const imageMessagesCount = messages.filter(m => m.imageData).length;

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    navigate("/login");
    return null;
  }

  return (
    <div className="app-container">
      {/* Neural Network Background */}
      <svg className="neural-background" viewBox="0 0 800 600">
        <path
          className="neural-path"
          d="M50,100 C150,50 250,150 350,100 C450,50 550,150 650,100 
              M50,300 C150,250 250,350 350,300 C450,250 550,350 650,300 
              M50,500 C150,450 250,550 350,500 C450,450 550,550 650,500"
          style={{ animationDelay: '0s' }}
        />
        <path
          className="neural-path"
          d="M100,50 C200,100 300,0 400,50 C500,100 600,0 700,50 
              M100,250 C200,300 300,200 400,250 C500,300 600,200 700,250 
              M100,450 C200,500 300,400 400,450 C500,500 600,400 700,450"
          style={{ animationDelay: '2.5s' }}
        />
        <path
          className="neural-path"
          d="M150,150 C250,200 350,100 450,150 C550,200 650,100 750,150 
              M150,350 C250,400 350,300 450,350 C550,400 650,300 750,350 
              M150,550 C250,600 350,500 450,550 C550,600 650,500 750,550"
          style={{ animationDelay: '5s' }}
        />
      </svg>

      {/* Session Manager */}
      {showSessionManager && (
        <SessionManager
          sessions={userSessions}
          activeSession={activeSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateNewSession}
          onDeleteSession={handleDeleteSession}
          onClose={() => setShowSessionManager(false)}
        />
      )}

      {/* Sidebar Panel */}
      <div className={`sidebar ${!showSidebar ? 'sidebar-collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="logo" onClick={toggleSidebar} style={{ cursor: 'pointer' }}>
            <div className="logo-icon-wrapper">
              <TbBrain className="logo-icon" />
            </div>
            {showSidebar && (
              <div className="logo-text">
                <span className="logo-main">SmartFit</span>
                {/* <span className="logo-sub">xxx</span> */}
              </div>
            )}
          </div>

          <button
            className="new-chat-btn"
            onClick={handleNewChat}
            title="Start new chat"
            style={{ display: activePage === "chat" ? 'flex' : 'none' }}
          >
            <div className="btn-icon">
              <FiEdit2 />
            </div>
            {showSidebar && <span>New Chat</span>}
          </button>
        </div>

        {/* Navigation Menu */}
        <div className="sidebar-navigation">
          <nav className="nav-menu">
            <button
              className={`nav-item ${activePage === "chat" ? 'active' : ''}`}
              onClick={() => setActivePage("chat")}
            >
              <div className="nav-icon">
                <FiMessageSquare />
              </div>
              {showSidebar && <span className="nav-label">Chat</span>}
            </button>

            <button
              className={`nav-item ${activePage === "profile" ? 'active' : ''}`}
              onClick={() => setActivePage("profile")}
            >
              <div className="nav-icon">
                <FiUser />
              </div>
              {showSidebar && <span className="nav-label">Profile</span>}
            </button>

            {showSidebar && isAuthenticated && (
              <button
                className="nav-item"
                onClick={() => setShowSessionManager(true)}
              >
                <div className="nav-icon">
                  <FiUsers />
                </div>
                {showSidebar && <span className="nav-label">Sessions</span>}
              </button>
            )}
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div
              className="user-avatar"
              onClick={() => setActivePage("profile")}
              style={{ cursor: 'pointer' }}
            >
              {user ? (
                <div className="authenticated-avatar">
                  <FaUserCircle />
                  <div className="online-dot"></div>
                </div>
              ) : (
                <div className="guest-avatar">
                  <FaUserCircle />
                </div>
              )}
            </div>
            {showSidebar && (
              <div className="user-info">
                <span>{user ? user.username : "User"}</span>
                <small>{user ? (user.subscription_tier || "Free Tier") : "Loading..."}</small>
              </div>
            )}
            <button
              className="auth-btn"
              onClick={handleLogout}
              title="Logout"
            >
              <FiLogOut />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        <div className="chat-header">
          <div className="header-left">
            <button
              className="sidebar-toggle"
              onClick={toggleSidebar}
              aria-label={showSidebar ? "Collapse sidebar" : "Expand sidebar"}
            >
              {showSidebar ? <FiChevronLeft /> : <FiChevronRight />}
            </button>
            <div className="model-indicator">
              <div className="model-dot"></div>
              <span>{modelVersion}</span>
              <RiShieldCheckLine className="shield-icon" title="Secure & Private" />
            </div>
            {activePage === "chat" && (
              <div className="header-stats">
                <div className="stat-item">
                  <span className="stat-label">Tokens</span>
                  <span className="stat-value">• {totalTokens.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Messages</span>
                  <span className="stat-value">• {userMessagesCount}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Images</span>
                  <span className="stat-value">• {imageMessagesCount}</span>
                </div>
              </div>
            )}
          </div>

          <div className="header-actions">
            {activePage === "chat" && (
              <>
                {isAuthenticated && (
                  <button
                    className="action-btn"
                    onClick={() => setShowSessionManager(true)}
                    title="View sessions"
                  >
                    <FiUsers /> Sessions
                  </button>
                )}
                <button
                  className="action-btn"
                  onClick={handleClearChat}
                  disabled={messages.length === 0}
                  title="Clear current chat (local only)"
                >
                  Clear Chat
                </button>
                <button
                  className="action-btn"
                  onClick={handleClearHistory}
                  disabled={messages.length === 0}
                  title="Clear conversation history from server"
                  style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', color: 'white' }}
                >
                  Clear History
                </button>
                <button
                  className="action-btn regenerate-btn"
                  onClick={handleRegenerate}
                  disabled={messages.length === 0 || loading}
                  title="Regenerate last response"
                >
                  <MdAutoFixHigh />
                  Regenerate
                </button>
                <button
                  className="action-btn fullscreen-btn"
                  onClick={toggleFullscreen}
                  title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                >
                  {isFullscreen ? <FiMinimize2 /> : <FiMaximize2 />}
                </button>
              </>
            )}

            {activePage === "profile" && (
              <button
                className="action-btn"
                onClick={() => setActivePage("chat")}
                title="Go to Chat"
              >
                <FiMessageSquare /> Chat
              </button>
            )}

            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              title={isDarkTheme ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDarkTheme ? <MdOutlineLightMode /> : <MdOutlineDarkMode />}
            </button>
          </div>
        </div>

        {/* Render Chat or Profile based on active page */}
        {activePage === "chat" ? (
          <>
            <div className="messages-container">
              <div className="messages">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon-wrapper">
                      <TbBrain className="empty-icon" />
                    </div>
                    <h3>Welcome to SmartFit</h3>
                    <p className="empty-subtitle">
                      Your intelligent AI assistant with image generation capabilities
                    </p>

                    {/* Profile Completion Prompt */}
                    {isAuthenticated && (!userProfile || Object.keys(userProfile).length === 0) && (
                      <div className="profile-prompt">
                        <div className="prompt-card profile-card">
                          <div className="prompt-icon" style={{ backgroundColor: "#3b82f6" }}>
                            <FiUser />
                          </div>
                          <div className="prompt-content">
                            <span className="prompt-title">Complete Your Profile</span>
                            <span className="prompt-category">Get personalized recommendations</span>
                            <button
                              className="profile-action-btn"
                              onClick={() => setActivePage("profile")}
                            >
                              Go to Profile
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="example-prompts">
                      <div className="prompt-section">
                        <h4>Try asking me:</h4>
                        <div className="prompt-grid">
                          {[
                            {
                              title: "Suggest outfits for the occasion",
                              prompt: "Recommend a complete outfit based on the user's occasion, weather, and style preference",
                              icon: "👗",
                              color: "#ec4899",
                              category: "Outfit Recommendation"
                            },
                            {
                              title: "Explain outfit matching logic",
                              prompt: "Explain how the system selects matching tops, bottoms, and accessories for a balanced outfit",
                              icon: "🧠",
                              color: "#8b5cf6",
                              category: "Fashion Intelligence"
                            },
                            {
                              title: "Generate wardrobe-based suggestions",
                              prompt: "Generate clothing recommendations using the user's existing wardrobe and current fashion trends",
                              icon: "👕",
                              color: "#3572A5",
                              category: "Personal Styling"
                            }
                          ].map((example, index) => (
                            <button
                              key={index}
                              className="prompt-card"
                              onClick={() => setInput(example.prompt)}
                              style={{ '--card-color': example.color }}
                            >
                              <div className="prompt-icon" style={{ backgroundColor: example.color }}>
                                {example.icon}
                              </div>
                              <div className="prompt-content">
                                <span className="prompt-title">{example.title}</span>
                                <span className="prompt-category">{example.category}</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((m, i) => (
                      <div key={m.id || i} className={`message-wrapper ${m.role} ${m.isSystem ? 'system' : ''}`}>
                        <div className="message-container">
                          <div className="message-avatar">
                            {m.role === "user" ? (
                              <div className="user-avatar-circle">
                                <FaUserCircle />
                              </div>
                            ) : m.role === "system" ? (
                              <div className="system-avatar">
                                <div className="system-avatar-bg">
                                  <FiRefreshCw />
                                </div>
                              </div>
                            ) : (
                              <div className="ai-avatar">
                                <div className="ai-avatar-bg">
                                  <BsRobot />
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="message-content">
                            <div className="message-header">
                              <div className="message-sender-info">
                                <span className={`message-sender ${m.role}`}>
                                  {m.role === "user" ? "You" : m.role === "system" ? "System" : "UAI Assistant"}
                                </span>
                                {m.role === "assistant" && (
                                  <span className="model-tag">SmartFit</span>
                                )}
                              </div>
                              <div className="message-meta">
                                <span className="message-time">
                                  {formatTime(m.timestamp)}
                                </span>
                                {m.role === "assistant" && m.thinkingTime > 0 && (
                                  <span className="thinking-badge">
                                    {formatThinkingTime(m.thinkingTime)}
                                  </span>
                                )}
                                {m.role === "assistant" && m.isLoading && (
                                  <span className="thinking-badge generating">
                                    <span style={{ marginRight: '6px' }}>Generating</span>
                                    <div className="generating-dots">
                                      <span></span>
                                      <span></span>
                                      <span></span>
                                    </div>
                                  </span>
                                )}
                                <span className="token-badge">
                                  ~{m.tokens ? m.tokens.toLocaleString() : '0'} tokens
                                </span>
                              </div>
                            </div>

                            <div className={`message-body ${m.isError ? 'error' : ''}`}>
                              {m.imageData || m.isLoading ? (
                                // Show image display with proper loading state
                                <ImageDisplay
                                  imageData={m.imageData || { prompt: m.prompt }}
                                  isLoading={m.isLoading || false}
                                />
                              ) : m.isSystem ? (
                                // System messages
                                <div className="system-message">
                                  <span className="system-icon">⚙️</span>
                                  <span>{m.text}</span>
                                </div>
                              ) : (
                                // Regular text messages
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={{
                                    code({ inline, className, children, ...props }) {
                                      const match = /language-(\w+)/.exec(className || "");
                                      const codeText = String(children).replace(/\n$/, "");
                                      const language = match?.[1] || detectLanguage(codeText);
                                      const displayLanguage = getDisplayLanguage(language);
                                      const languageColor = getLanguageColor(language);

                                      if (!inline) {
                                        return (
                                          <div className="code-block-wrapper" data-language={language}>
                                            <div className="code-block-header">
                                              <div className="code-language">
                                                <div
                                                  className="language-dot"
                                                  style={{ backgroundColor: languageColor }}
                                                ></div>
                                                <span className="language-name">{displayLanguage}</span>
                                                {language === 'bash' && (
                                                  <span className="terminal-badge">
                                                    <BsTerminal />
                                                    Terminal
                                                  </span>
                                                )}
                                              </div>
                                              <div className="code-actions">
                                                <button
                                                  className="copy-btn"
                                                  onClick={() => copyCode(codeText, i)}
                                                  aria-label="Copy code"
                                                >
                                                  {copied === i ? (
                                                    <>
                                                      <FiCheck className="copied-icon" />
                                                      <span className="copied-text">Copied</span>
                                                    </>
                                                  ) : (
                                                    <>
                                                      <FiCopy />
                                                      <span className="copy-text">Copy</span>
                                                    </>
                                                  )}
                                                </button>
                                              </div>
                                            </div>
                                            <div className="code-content" data-language={language}>
                                              <SyntaxHighlighter
                                                language={language === 'bash' ? 'bash' : language}
                                                style={vscDarkPlus}
                                                customStyle={{
                                                  background: "transparent",
                                                  margin: 0,
                                                  padding: language === 'bash' ? "12px 16px" : "16px",
                                                  fontSize: "13px",
                                                  borderRadius: "0 0 8px 8px",
                                                  fontFamily: "'SF Mono', 'Cascadia Code', 'Monaco', 'Consolas', monospace",
                                                }}
                                                showLineNumbers={language !== 'bash'}
                                                wrapLines
                                                lineNumberStyle={{
                                                  color: "#6b7280",
                                                  minWidth: "3em",
                                                  userSelect: "none",
                                                  textAlign: "right",
                                                  paddingRight: "1em",
                                                  marginRight: "1em",
                                                  borderRight: "1px solid #374151"
                                                }}
                                                PreTag="div"
                                              >
                                                {codeText}
                                              </SyntaxHighlighter>
                                            </div>
                                            {language === 'bash' && (
                                              <div className="terminal-prompt">
                                                <span className="prompt-symbol">$</span>
                                                <span className="prompt-text">Run this command in your terminal</span>
                                              </div>
                                            )}
                                          </div>
                                        );
                                      }

                                      return (
                                        <code
                                          className="inline-code"
                                          style={{
                                            backgroundColor: `${languageColor}15`,
                                            borderColor: `${languageColor}30`,
                                            color: languageColor
                                          }}
                                        >
                                          {children}
                                        </code>
                                      );
                                    },
                                    pre({ children }) {
                                      return <>{children}</>;
                                    },
                                    table({ children }) {
                                      return (
                                        <div className="table-container">
                                          <table>{children}</table>
                                        </div>
                                      );
                                    },
                                    a({ href, children }) {
                                      return (
                                        <a
                                          href={href}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="markdown-link"
                                        >
                                          {children}
                                        </a>
                                      );
                                    },
                                    blockquote({ children }) {
                                      return (
                                        <blockquote className="markdown-blockquote">
                                          {children}
                                        </blockquote>
                                      );
                                    }
                                  }}
                                >
                                  {m.text}
                                </ReactMarkdown>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {loading && messages[messages.length - 1]?.role !== "assistant" && (
                      <div className="ai-thinking-indicator">
                        {/* Neural background */}
                        <div className="thinking-neural-bg">
                          {[...Array(12)].map((_, i) => (
                            <div
                              key={`node-${i}`}
                              className="neural-node"
                              style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 2}s`
                              }}
                            />
                          ))}
                          {[...Array(8)].map((_, i) => (
                            <div
                              key={`conn-${i}`}
                              className="neural-connection"
                              style={{
                                left: `${Math.random() * 50}%`,
                                top: `${Math.random() * 100}%`,
                                width: `${20 + Math.random() * 100}px`,
                                transform: `rotate(${Math.random() * 360}deg)`,
                                animationDelay: `${Math.random() * 4}s`
                              }}
                            />
                          ))}
                        </div>

                        {/* Floating elements */}
                        <div className="floating-element" />
                        <div className="floating-element" />
                        <div className="floating-element" />

                        {/* Thinking header */}
                        <div className="thinking-header">
                          <div className="thinking-avatar">
                            <BsRobot />
                          </div>
                          <div className="thinking-text-content">
                            <div className="thinking-title">
                              SmartFit is thinking
                              <div className="generating-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                              </div>
                            </div>
                            <div className="thinking-subtitle">
                              Processing your query with advanced neural networks
                            </div>
                          </div>
                        </div>

                        {/* Enhanced thinking process */}
                        <div className="thinking-process">
                          <div className="progress-label">
                            <span className="progress-text">Reasoning process</span>
                            <span className="progress-percentage">
                              {Math.min(Math.floor((thinkingTime / 6000) * 100), 100)}%
                            </span>
                          </div>

                          <div className="process-steps">
                            {[
                              { id: 1, text: "Analyzing query", detail: "Understanding context and intent" },
                              { id: 2, text: "Processing logic", detail: "Applying reasoning models" },
                              { id: 3, text: "Generating response", detail: "Creating optimized output" },
                              { id: 4, text: "Quality assurance", detail: "Ensuring accuracy and relevance" }
                            ].map((step, index) => (
                              <div
                                key={step.id}
                                className={`process-step ${index < Math.floor(thinkingTime / 1500) ? 'completed' : ''
                                  } ${index === Math.floor(thinkingTime / 1500) ? 'active' : ''}`}
                              >
                                <div className="step-icon">
                                  <div className="step-check">✓</div>
                                  {step.id}
                                </div>
                                <div className="step-text">
                                  <div>{step.text}</div>
                                  <div className="step-detail">{step.detail}</div>
                                </div>
                              </div>
                            ))}
                          </div>

                          <div className="process-progress">
                            <div
                              className="process-progress-bar"
                              style={{ width: `${Math.min((thinkingTime / 6000) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </>
                )}
              </div>
            </div>

            {/* Input Area */}
            <div className="input-container">
              <div className="input-wrapper">
                <div className="textarea-container">
                  <textarea
                    ref={textareaRef}
                    placeholder="Message SmartFit... (Ask anything or generate images)"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    className="message-textarea"
                    aria-label="Message input"
                  />

                  <div className="input-actions">
                    <button
                      className="send-btn"
                      onClick={sendMessage}
                      disabled={!input.trim() || loading}
                      aria-label="Send message"
                      title="Send message (Ctrl + Enter)"
                    >
                      <div className="send-btn-content">
                        <FiSend className="send-icon" />
                        <span className="send-text">Send</span>
                      </div>
                    </button>
                  </div>
                </div>

                <div className="input-footer">
                  <div className="footer-left">
                    {/* <a
                      href="https://github.com/SDineshKumar1304/UAI_GPT"
                      className="github-link"
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="GitHub repository"
                      title="View on GitHub"
                    >
                      <FaGithub />
                    </a> */}
                  </div>
                  <div className="footer-right">
                    <small className="hint-text">
                      <kbd>Enter</kbd> to send • <kbd>Shift</kbd> + <kbd>Enter</kbd> for new line
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          // Profile Page
          <div className="profile-page-container">
            <ProfileDetails
              user={user}
              profileData={userProfile}
              onSaveProfile={handleSaveProfile}
            />
          </div>
        )}
      </div>
    </div>
  );
}