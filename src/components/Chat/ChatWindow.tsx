"use client";

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import { MessageBubble } from './MessageBubble';
import { RobotAvatar } from './RobotAvatar';
import { ChatHeader } from './ChatHeader';
import { ChatInput } from './ChatInput';
import { WelcomeMessage } from './WelcomeMessage';
import { AnnouncementBanner } from './AnnouncementBanner';
import { QuickReplies } from './QuickReplies';
import { FAQAccordion } from './FAQAccordion';
import { ImportantDates } from './ImportantDates';

export const ChatWindow: React.FC = () => {
  const { messages, isLoading, profile, sendMessage, isChatOpen } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (messages.length > 0 || isLoading) {
      scrollToBottom();
    }
  }, [messages, isLoading]);

  if (!isChatOpen) return null;

  return (
    <motion.section 
      className="chat-main"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <ChatHeader />

      <div className="chat-body" style={{ position: 'relative' }}>
        <div className="messages-container">
          <AnnouncementBanner />
          
          {!profile ? (
            <WelcomeMessage />
          ) : (
            <>
              {messages.length === 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <FAQAccordion />
                  <ImportantDates />
                </div>
              )}

              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              
              {isLoading && (
                <motion.div 
                  className="message-row bot"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="message-avatar bot-avatar-empty">
                    <RobotAvatar size={32} isAnimated={true} />
                  </div>
                  <div className="message-container">
                    <div className="sender-info">AIMS Assistant</div>
                    <div className="message-bubble bot-bubble" style={{ padding: '12px 20px' }}>
                      <div className="typing-indicator-bubble">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-section">
        {profile && !isLoading && (
          <QuickReplies onSelect={(query) => sendMessage(query)} />
        )}
        <ChatInput />
      </div>
    </motion.section>
  );
};
