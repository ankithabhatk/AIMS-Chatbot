import React, { useState, useEffect } from 'react';
import { UserProfile as UserProfileType } from '../../services/storageService';
import { useChat } from '../../context/ChatContext';

interface UserProfileProps {
  profile: UserProfileType | null;
}

export const UserProfile: React.FC<UserProfileProps> = ({ profile }) => {
  const { restartSession } = useChat();
  const [showModal, setShowModal] = useState(false);
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!profile) return null;

  const joinedTime = profile.joinedAt || Date.now();
  const joinedDate = new Date(joinedTime);
  
  const formattedDate = mounted ? joinedDate.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) : "";
  
  const formattedTime = mounted ? joinedDate.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }) : "";

  // Get initials for avatar
  const userName = profile.name || "Student";
  const initials = userName
    .split(' ')
    .filter(Boolean)
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 1);

  return (
    <>
      <div className="profile-section" onClick={() => setShowModal(true)}>
        <div className="user-avatar-circle">{initials}</div>
        <div className="user-info-text">
          <div className="user-display-name">{userName}</div>
          <div className="user-joined-date">
            {formattedDate}, {formattedTime}
          </div>
        </div>
        <button 
          className="sidebar-logout-btn" 
          onClick={(e) => {
            e.stopPropagation();
            restartSession();
          }}
          title="Logout"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18.36 6.64A9 9 0 1 1 5.64 5.64"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
        </button>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setShowModal(false)}>&times;</button>
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <div className="user-avatar-circle" style={{ width: '80px', height: '80px', fontSize: '32px', margin: '0 auto 16px' }}>{initials}</div>
              <h2 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--aims-primary)' }}>{profile.name}</h2>
              <p style={{ color: 'var(--text-light)', fontSize: '14px' }}>Institutional Record</p>
            </div>
            
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ padding: '16px', background: 'var(--aims-bg)', borderRadius: '12px' }}>
                <p style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-light)', textTransform: 'uppercase', marginBottom: '4px' }}>Email ID</p>
                <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-dark)' }}>{profile.email}</p>
              </div>
              <div style={{ padding: '16px', background: 'var(--aims-bg)', borderRadius: '12px' }}>
                <p style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-light)', textTransform: 'uppercase', marginBottom: '4px' }}>Mobile Number</p>
                <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-dark)' }}>{profile.mobile || 'N/A'}</p>
              </div>
              <div style={{ padding: '16px', background: 'var(--aims-bg)', borderRadius: '12px' }}>
                <p style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-light)', textTransform: 'uppercase', marginBottom: '4px' }}>Interested Course</p>
                <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-dark)' }}>{profile.course}</p>
              </div>
              <div style={{ padding: '16px', background: 'var(--aims-bg)', borderRadius: '12px' }}>
                <p style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-light)', textTransform: 'uppercase', marginBottom: '4px' }}>Joined Date</p>
                <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-dark)' }}>{formattedDate} at {formattedTime}</p>
              </div>
            </div>

            <button 
              onClick={restartSession}
              style={{ 
                marginTop: '30px', 
                width: '100%', 
                padding: '14px', 
                background: '#FEE2E2', 
                color: '#DC2626', 
                border: 'none', 
                borderRadius: '12px', 
                fontWeight: '700', 
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px'
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18.36 6.64A9 9 0 1 1 5.64 5.64"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
              Logout / Restart Session
            </button>
          </div>
        </div>
      )}
    </>
  );
};
