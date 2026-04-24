"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import { RobotAvatar } from './RobotAvatar';

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleCourseSelect = (course: string) => {
    setFormData(prev => ({ ...prev, course }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.course) return;

    saveProfile(formData);

    // Format for display
    const userMessage = `Name: ${formData.name}\nEmail: ${formData.email}\nPhone: ${formData.mobile || 'N/A'}\nCourse: ${formData.course}`;

    const firstName = formData.name.trim().split(' ')[0];
    sendMessage(userMessage, true, firstName);
  };

  const timestamp = mounted 
    ? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })
    : "";

  return (
    <motion.div 
      className="message-row bot"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="message-avatar bot-avatar-empty">
        <RobotAvatar size={32} isAnimated={true} />
      </div>
      <div className="message-container" style={{ maxWidth: '600px' }}>
        <div className="sender-info">AIMS Assistant</div>
        <div className="message-bubble bot-bubble" style={{ padding: '32px' }}>
          <div className="message-content">
            <h3 style={{ marginBottom: '24px', fontSize: '18px', fontWeight: '700' }}>
              Welcome to AIMS Institutes. Please provide your details to continue.
            </h3>
            
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <label style={{ width: '100px', fontSize: '12px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Full Name:</label>
                <input
                  name="name"
                  type="text"
                  className="onboarding-input"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  required
                  style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-light)', backgroundColor: 'var(--sidebar-bg)', color: 'var(--text-main)', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <label style={{ width: '100px', fontSize: '12px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Email ID:</label>
                <input
                  name="email"
                  type="email"
                  className="onboarding-input"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                  required
                  style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-light)', backgroundColor: 'var(--sidebar-bg)', color: 'var(--text-main)', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <label style={{ width: '100px', fontSize: '12px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Phone:</label>
                <input
                  name="mobile"
                  type="tel"
                  className="onboarding-input"
                  value={formData.mobile}
                  onChange={handleChange}
                  placeholder="Enter phone number"
                  required
                  style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-light)', backgroundColor: 'var(--sidebar-bg)', color: 'var(--text-main)', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div className="form-field" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Course Interested:</label>
                <div className="onboarding-radio-grid">
                  {courses.map(course => (
                    <div 
                      key={course}
                      className={`radio-card ${formData.course === course ? 'selected' : ''}`}
                      onClick={() => handleCourseSelect(course)}
                    >
                      <div className="radio-custom-circle"></div>
                      <span className="onboarding-radio-label">{course}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '12px' }}>
                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    backgroundColor: 'var(--aims-primary)',
                    color: 'white',
                    padding: '12px 32px',
                    borderRadius: '10px',
                    fontWeight: '700',
                    fontSize: '14px',
                    border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                >
                  Submit
                </motion.button>
              </div>
            </form>
          </div>
        </div>
        <div className="message-timestamp">{timestamp}</div>
      </div>
    </motion.div>
  );
};
