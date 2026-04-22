"use client";

import React, { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { WelcomeMessage } from './WelcomeMessage';
import { ChatHeader } from './ChatHeader';

export const ChatWindow: React.FC = () => {
  const { messages, isLoading, profile, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <section className="chat-container">
      <ChatHeader />

      <div className="chat-body">
        <div className="messages-wrapper">
          {!profile ? (
            <WelcomeMessage />
          ) : (
            <>
              {messages.length === 0 ? (
                <div className="message-row bot">
                  <div className="message-avatar bot-avatar">AI</div>
                  <div className="message-container">
                    <div className="sender-info">AIMS Assistant</div>
                    <div className="message-bubble bot-bubble">
                      <div className="message-content">
                        Welcome back, {profile.name.split(' ')[0]}. How can I assist you today?
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))
              )}
              
              {messages.length > 0 && 
               !messages[messages.length - 1].isUser && 
               messages[messages.length - 1].metadata?.suggestions && 
               !isLoading && (
                <div className="suggestions-container">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxWidth: '85%' }}>
                    {messages[messages.length - 1].metadata!.suggestions!.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => sendMessage(sug)}
                        className="suggestion-btn"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {isLoading && (
                <div className="message-row bot">
                  <div className="message-avatar bot-avatar">AI</div>
                  <div className="message-container">
                    <div className="sender-info">AIMS Assistant</div>
                    <div className="typing-indicator-bubble">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <ChatInput />
    </section>
  );
};
