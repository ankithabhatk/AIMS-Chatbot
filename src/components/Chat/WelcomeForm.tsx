import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';

export const WelcomeForm: React.FC = () => {
  const { sendMessage, saveProfile } = useChat();
  const [formData, setFormData] = useState({
    name: '',
    mobile: '',
    email: '',
    course: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.mobile || !formData.email || !formData.course) return;

    // Save profile with automatic joinedAt timestamp via ChatContext
    saveProfile(formData);

    // Format message as requested
    const userMessage = `Name: ${formData.name}\nMobile: ${formData.mobile}\nEmail: ${formData.email}\nCourse: ${formData.course}`;

    // Trigger the flow with first name for personal greeting
    const firstName = formData.name.trim().split(' ')[0];
    sendMessage(userMessage, true, firstName);
  };

  return (
    <div className="message-row bot">
      <div className="message-container">
        <div className="message-info">
          <span className="sender-name">AIMS Assistant</span>
        </div>
        <div className="message-bubble bot-bubble">
          <div className="message-content">
            <p>Welcome! Please enter your details to proceed.</p>
            <form className="welcome-form-container" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="name">Full Name</label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="mobile">Mobile Number</label>
                <input
                  id="mobile"
                  name="mobile"
                  type="number"
                  className="form-input"
                  value={formData.mobile}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="email">Email ID</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="form-input"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="course">Course Interested</label>
                <select
                  id="course"
                  name="course"
                  className="form-input"
                  value={formData.course}
                  onChange={handleChange}
                  required
                >
                  <option value="" disabled>Select a course</option>
                  <option value="MBA">MBA</option>
                  <option value="MCA">MCA</option>
                  <option value="M.Com">M.Com</option>
                  <option value="BBA">BBA</option>
                  <option value="BCA">BCA</option>
                  <option value="B.Com">B.Com</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <button type="submit" className="form-submit-btn">Submit</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
