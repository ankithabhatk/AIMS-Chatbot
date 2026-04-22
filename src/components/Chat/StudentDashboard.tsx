import React from 'react';
import { useChat } from '../../context/ChatContext';

export const StudentDashboard: React.FC = () => {
  const { profile, startNewConversation } = useChat();

  if (!profile) return null;

  const joinedTime = profile.joinedAt || Date.now();
  const joinedDate = new Date(joinedTime);
  const formattedJoined = joinedDate.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="student-dashboard">
      <div className="dashboard-card">
        <div className="dashboard-header">
          <div className="dashboard-avatar">
            {(profile.name || "Student").split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 2)}
          </div>
          <div className="dashboard-title">
            <h3>Student Information</h3>
            <p>Institutional Record</p>
          </div>
        </div>
        
        <div className="dashboard-grid">
          <div className="dashboard-item">
            <label>Full Name</label>
            <span>{profile.name}</span>
          </div>
          <div className="dashboard-item">
            <label>Interested Course</label>
            <span>{profile.course}</span>
          </div>
          <div className="dashboard-item">
            <label>Email ID</label>
            <span>{profile.email}</span>
          </div>
          <div className="dashboard-item">
            <label>Mobile Number</label>
            <span>{profile.mobile}</span>
          </div>
          <div className="dashboard-item full">
            <label>Academic Joined Date</label>
            <span>{formattedJoined}</span>
          </div>
        </div>

        <p className="dashboard-hint" style={{ marginTop: '24px', textAlign: 'center' }}>Select a previous conversation from the sidebar to continue.</p>
      </div>
    </div>
  );
};
