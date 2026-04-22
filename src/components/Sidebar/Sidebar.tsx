"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import { ChatItem } from './ChatItem';
import { UserProfile } from './UserProfile';
import { AdmissionContact } from './AdmissionContact';
import Image from 'next/image';
import { useIsMobile } from '../../hooks/useIsMobile';

export const Sidebar: React.FC = () => {
  const {
    conversations,
    currentConversationId,
    switchConversation,
    startNewConversation,
    renameConversation,
    deleteConversation,
    profile,
    isChatOpen,
    setIsChatOpen,
    isSidebarOpen,
    setIsSidebarOpen,
  } = useChat();

  const isMobile = useIsMobile();

  // ─── KEY LOGIC ────────────────────────────────────────────────────────────
  // Desktop: sidebar renders when chat is open (normal static flex item)
  // Mobile:  sidebar renders ONLY when hamburger is clicked (fixed overlay)
  //
  // This avoids the Framer Motion inline-style vs CSS transform conflict.
  // ──────────────────────────────────────────────────────────────────────────
  const shouldShowSidebar = isMobile ? isSidebarOpen : isChatOpen;

  // Close drawer after selecting a conversation on mobile
  const handleConversationClick = (id: string) => {
    switchConversation(id);
    if (isMobile) setIsSidebarOpen(false);
  };

  return (
    <>
      <AnimatePresence>
        {shouldShowSidebar && (
          <motion.aside
            // On mobile add 'sidebar-mobile' class → position: fixed overlay
            // On desktop no extra class → normal static sidebar (UNCHANGED)
            className={`sidebar${isMobile ? ' sidebar-mobile' : ''}`}
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 20, stiffness: 100 }}
          >
            <div className="sidebar-top">
              <div className="sidebar-logo-container" style={{ marginBottom: '20px', padding: '0 8px' }}>
                <Image
                  src="/aims logo.jpg"
                  alt="AIMS Logo"
                  width={32}
                  height={32}
                  style={{ objectFit: 'contain' }}
                />
              </div>
              <button
                onClick={startNewConversation}
                className="new-chat-btn"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                New Chat
              </button>
            </div>

            <div className="sidebar-history">
              <h3 className="history-title">RECENT HISTORY</h3>

              {conversations.length === 0 ? (
                <div style={{ padding: '0 12px', fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No previous conversations.
                </div>
              ) : (
                conversations.map(conv => (
                  <ChatItem
                    key={conv.id}
                    id={conv.id}
                    title={conv.title}
                    timestamp={conv.updatedAt}
                    isActive={conv.id === currentConversationId}
                    onClick={() => handleConversationClick(conv.id)}
                    onRename={renameConversation}
                    onDelete={deleteConversation}
                  />
                ))
              )}
            </div>

            <div className="sidebar-footer-container">
              <AdmissionContact />
              <UserProfile profile={profile} />

              <button
                onClick={() => {
                  setIsChatOpen(false);
                  setIsSidebarOpen(false);
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  borderTop: '1px solid var(--border-light)'
                }}
              >
                Close Chat
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Mobile backdrop — full screen dimmed overlay, closes drawer on tap */}
      <AnimatePresence>
        {isMobile && isSidebarOpen && (
          <motion.div
            className="sidebar-mobile-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
};
