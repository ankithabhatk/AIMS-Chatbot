"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ChatMessage, useChat } from '../../context/ChatContext';
import { FeedbackButtons } from './FeedbackButtons';
import { UserSummaryCard } from './UserSummaryCard';
import { RobotAvatar } from './RobotAvatar';
import { ConfidenceBar } from './ConfidenceBar';
import { SourceCards } from './SourceCards';

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Lightweight markdown renderer for bot responses.
 * Handles: **bold**, • bullets, --- dividers, and newlines.
 * Returns an array of React nodes.
 */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Horizontal rule
    if (line.trim() === '---') {
      nodes.push(<hr key={`hr-${i}`} />);
      i++;
      continue;
    }

    // Bullet line (starts with • or -)
    if (/^[•\-]\s/.test(line.trim())) {
      // Collect consecutive bullet lines
      const bulletLines: string[] = [];
      while (i < lines.length && /^[•\-]\s/.test(lines[i].trim())) {
        bulletLines.push(lines[i].trim().replace(/^[•\-]\s/, ''));
        i++;
      }
      nodes.push(
        <div key={`bullets-${i}`} className="md-bullet-list">
          {bulletLines.map((b, bi) => (
            <div key={bi} className="md-bullet-item">
              <span>{renderInline(b)}</span>
            </div>
          ))}
        </div>
      );
      continue;
    }

    // Regular line (may contain inline formatting)
    if (line.trim() !== '') {
      nodes.push(
        <p key={`p-${i}`} style={{ margin: '3px 0' }}>
          {renderInline(line)}
        </p>
      );
    }

    i++;
  }

  return <>{nodes}</>;
}

/**
 * Render inline markdown: **bold** and `code`.
 */
function renderInline(text: string): React.ReactNode {
  // Split on **bold** and `code`
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="md-strong">{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code key={i} style={{
              fontFamily: 'monospace',
              fontSize: '0.9em',
              background: 'rgba(0,0,0,0.07)',
              padding: '1px 5px',
              borderRadius: '4px',
            }}>
              {part.slice(1, -1)}
            </code>
          );
        }
        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </>
  );
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { profile } = useChat();
  const isUser = message.isUser;

  const senderName = isUser ? (profile?.name || 'Student') : 'AIMS Assistant';

  const timestamp = new Date(
    parseInt(message.id) > 1_000_000_000 ? parseInt(message.id) : Date.now()
  ).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });

  const initials = isUser
    ? (profile?.name || 'S')
        .split(' ')
        .filter(Boolean)
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 1)
    : '';

  const isOnboardingSummary =
    isUser &&
    message.content.startsWith('Name: ') &&
    message.content.includes('Course: ');

  const confidence = message.metadata?.confidence;
  const sources = message.metadata?.sources ?? [];
  const hasSources = sources.length > 0;

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
        <div
          className="sender-info"
          style={{
            fontSize: '12px',
            fontWeight: '700',
            color: 'var(--text-main)',
            marginBottom: '4px',
            textAlign: isUser ? 'right' : 'left',
          }}
        >
          {senderName}
        </div>

        {isOnboardingSummary ? (
          <UserSummaryCard profile={profile!} />
        ) : (
          <div className={`message-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
            {isUser ? (
              // User messages: plain text
              <div className="message-content">{message.content}</div>
            ) : (
              // Bot messages: rendered markdown
              <div className="message-content">
                {renderMarkdown(message.content)}
              </div>
            )}
          </div>
        )}

        {/* Confidence bar — bot messages only, when confidence is available */}
        {!isUser && !isOnboardingSummary && typeof confidence === 'number' && (
          <ConfidenceBar confidence={confidence} />
        )}

        {/* Source cards — bot messages only */}
        {!isUser && !isOnboardingSummary && hasSources && (
          <SourceCards sources={sources} />
        )}

        <div
          className="message-footer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            gap: '12px',
            marginTop: '6px',
          }}
        >
          <div className="message-timestamp">{timestamp}</div>
          {!isUser && !isOnboardingSummary && <FeedbackButtons />}
        </div>
      </div>
    </motion.div>
  );
};
