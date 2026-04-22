"use client";

import { ChatProvider, useChat } from '../context/ChatContext';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { FloatingRobot } from '../components/Chat/FloatingRobot';
import { AnimatePresence } from 'framer-motion';

function ChatAppContent() {
  const { isChatOpen } = useChat();

  return (
    <div className="app-container">
      <FloatingRobot />
      <AnimatePresence>
        {isChatOpen && (
          <>
            <Sidebar />
            <ChatWindow />
          </>
        )}
      </AnimatePresence>
      
      {!isChatOpen && (
        <div style={{ 
          position: 'fixed', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          pointerEvents: 'none'
        }}>
          <h1 style={{ 
            fontSize: '32px', 
            fontWeight: '800', 
            color: 'var(--aims-primary)', 
            marginBottom: '12px',
            opacity: 0.1
          }}>
            AIMS Academic Assistant
          </h1>
          <p style={{ 
            fontSize: '16px', 
            color: 'var(--text-muted)',
            opacity: 0.2
          }}>
            Click the robot to start a conversation
          </p>
        </div>
      )}
    </div>
  );
}

export default function ChatbotPage() {
  return (
    <ChatProvider>
      <ChatAppContent />
    </ChatProvider>
  );
}
