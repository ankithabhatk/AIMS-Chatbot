"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ChatMessage, useChat } from '../../context/ChatContext';
import { FeedbackButtons } from './FeedbackButtons';
import { UserSummaryCard } from './UserSummaryCard';
import { RobotAvatar } from './RobotAvatar';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { profile } = useChat();
  const isUser = message.isUser;
  
  const senderName = isUser ? (profile?.name || "Student") : "AIMS Assistant";
  
  // Format timestamp
  const timestamp = new Date(parseInt(message.id) > 1000000000 ? parseInt(message.id) : Date.now())
    .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });

  const initials = isUser 
    ? (profile?.name || "S").split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 1)
    : "";

  // Check if this is an onboarding summary message
  const isOnboardingSummary = isUser && message.content.startsWith("Name: ") && message.content.includes("Course: ");

  return (
    <motion.div 
      className={`message-row ${isUser ? 'user' : 'bot'}`}
      initial={{ opacity: 0, x: isUser ? 20 : -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className={`message-avatar ${isUser ? 'user-avatar' : 'bot-avatar-empty'}`}>
        {isUser ? initials : <RobotAvatar size={32} isAnimated={true} />}
      </div>
      
      <div className="message-content-wrapper">
        <div className="sender-info" style={{ 
          fontSize: '12px', 
          fontWeight: '700', 
          color: 'var(--text-main)', 
          marginBottom: '4px',
          textAlign: isUser ? 'right' : 'left'
        }}>
          {senderName}
        </div>

        {isOnboardingSummary ? (
          <UserSummaryCard profile={profile!} />
        ) : (
          <div className={`message-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
            <div 
              className="message-content" 
              dangerouslySetInnerHTML={{ __html: message.content.replace(/\n/g, '<br/>') }} 
            />
          </div>
        )}

        <div className="message-footer" style={{ display: 'flex', alignItems: 'center', justifyContent: isUser ? 'flex-end' : 'flex-start', gap: '12px' }}>
          <div className="message-timestamp">{timestamp}</div>
          {!isUser && !isOnboardingSummary && <FeedbackButtons />}
        </div>
      </div>
    </motion.div>
  );
};
