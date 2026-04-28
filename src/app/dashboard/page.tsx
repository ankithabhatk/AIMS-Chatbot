"use client";

import { useAuth } from '../../context/AuthContext';
import { ChatWindow } from '../../components/Chat/ChatWindow';
import { Sidebar } from '../../components/Sidebar/Sidebar';
import { FloatingRobot } from '../../components/Chat/FloatingRobot';
import { AnimatePresence } from 'framer-motion';
import { ChatProvider, useChat } from '../../context/ChatContext';

function DashboardContent() {
  const { user } = useAuth();
  const { isChatOpen, setIsChatOpen } = useChat();

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
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-4">
              Welcome, {user?.name || 'User'}!
            </h2>
            <p className="text-slate-400 mb-6">
              Role: {user?.role}
            </p>
            <button
              onClick={() => setIsChatOpen(true)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Start Chat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ChatProvider>
      <DashboardContent />
    </ChatProvider>
  );
}
