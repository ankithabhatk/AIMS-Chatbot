"use client";

import { ChatProvider } from '../context/ChatContext';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { Sidebar } from '../components/Sidebar/Sidebar';

export default function ChatbotPage() {
  return (
    <div className="app-container">
      <ChatProvider>
        <Sidebar />
        <ChatWindow />
      </ChatProvider>
    </div>
  );
}
