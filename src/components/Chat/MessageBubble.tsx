import React, { useState, useEffect } from 'react';
import { ChatMessage, useChat } from '../../context/ChatContext';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { profile } = useChat();
  const [mounted, setMounted] = useState(false);
  const isUser = message.isUser;

  useEffect(() => {
    setMounted(true);
  }, []);
  
  const senderName = isUser ? (profile?.name || "Student") : "AIMS Assistant";
  
  // Try to parse timestamp from ID, or use current time if ID is not a timestamp
  let timestamp = "";
  if (mounted) {
    try {
      const idNum = parseInt(message.id);
      if (!isNaN(idNum) && idNum > 1000000000000) {
        timestamp = new Date(idNum).toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit', 
          hour12: true 
        });
      } else {
        timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
      }
    } catch (e) {
      timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    }
  }

  // Initials for User, "AI" for Bot
  const initials = isUser 
    ? (profile?.name || "Student").split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 1)
    : "AI";

  return (
    <div className={`message-row ${isUser ? 'user' : 'bot'}`}>
      <div className={`message-avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`}>
        {initials}
      </div>
      
      <div className="message-container">
        <div className="sender-info">{senderName}</div>
        <div className={`message-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
          <div className="message-content" dangerouslySetInnerHTML={{ __html: message.content.replace(/\n/g, '<br/>') }} />
        </div>
        <div className="message-timestamp">{timestamp}</div>
      </div>
    </div>
  );
};
