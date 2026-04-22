import React, { useState, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';

export const WelcomeMessage: React.FC = () => {
  const { sendMessage, saveProfile } = useChat();
  const [mounted, setMounted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    mobile: '',
    email: '',
    course: ''
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  const courses = [
    "MBA", "MCA", "M.Com", "BBA", "BCA", "B.Com", "BHM", "BBA Aviation"
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.course) return;

    // Save profile with automatic joinedAt timestamp via ChatContext
    saveProfile(formData);

    // Format user message for display in chat
    const userMessage = `Name: ${formData.name}\nEmail: ${formData.email}\nPhone: ${formData.mobile || 'N/A'}\nCourse: ${formData.course}`;

    // Trigger the flow with first name for personal greeting
    const firstName = formData.name.trim().split(' ')[0];
    sendMessage(userMessage, true, firstName);
  };

  const timestamp = mounted 
    ? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })
    : "";

  return (
    <div className="message-row bot">
      <div className="message-avatar bot-avatar">AI</div>
      <div className="message-container">
        <div className="sender-info">AIMS Assistant</div>
        <div className="message-bubble bot-bubble">
          <div className="message-content">
            <p style={{ marginBottom: '16px', fontWeight: '500' }}>Welcome to AIMS Institutes. Please provide your details to continue.</p>
            <form className="onboarding-form" onSubmit={handleSubmit}>
              <div className="onboarding-input-group">
                <label className="onboarding-label">Full Name:</label>
                <input
                  name="name"
                  type="text"
                  className="onboarding-input"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  required
                />
              </div>
              
              <div className="onboarding-input-group">
                <label className="onboarding-label">Email ID:</label>
                <input
                  name="email"
                  type="email"
                  className="onboarding-input"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div className="onboarding-input-group">
                <label className="onboarding-label">Phone:</label>
                <input
                  name="mobile"
                  type="number"
                  className="onboarding-input"
                  value={formData.mobile}
                  onChange={handleChange}
                  placeholder="Enter phone number"
                  required
                />
              </div>

              <div className="onboarding-input-group" style={{ alignItems: 'flex-start' }}>
                <label className="onboarding-label" style={{ marginTop: '8px' }}>Course:</label>
                <div className="onboarding-radio-group">
                  {courses.map(course => (
                    <label key={course} className={`onboarding-radio-option ${formData.course === course ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="course"
                        value={course}
                        checked={formData.course === course}
                        onChange={handleChange}
                        required
                      />
                      <div className="radio-custom-circle"></div>
                      <span className="onboarding-radio-label">{course}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '20px' }}>
                <button type="submit" className="onboarding-submit-btn" style={{ background: 'var(--aims-primary)', color: 'white', padding: '10px 24px', borderRadius: '8px', fontWeight: '700', border: 'none', cursor: 'pointer' }}>Submit</button>
              </div>
            </form>
          </div>
        </div>
        <div className="message-timestamp">
          {timestamp}
        </div>
      </div>
    </div>
  );
};
