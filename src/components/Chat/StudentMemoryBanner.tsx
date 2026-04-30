"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface StudentMemoryBannerProps {
  /** Topics/interests detected by the backend counselor (e.g. ["coding", "business"]) */
  interests: string[];
  /** Confidence score (0–1) as reported by profile_confidence_score in meta */
  confidenceScore: number | null;
  /** Previous confidence score for showing delta */
  prevConfidenceScore: number | null;
  /** Whether to show at all */
  visible: boolean;
}

const INTEREST_LABELS: Record<string, string> = {
  coding: '💻 Coding / Tech',
  business: '📈 Business',
  management: '🏢 Management / MBA',
  hospitality: '🏨 Hospitality',
  commerce: '💼 Commerce',
  design: '🎨 Design',
};

function formatInterest(interest: string): string {
  return INTEREST_LABELS[interest.toLowerCase()] ?? `📌 ${interest}`;
}

function getConfidenceLabel(score: number): string {
  if (score < 0.4) return 'Still exploring options';
  if (score < 0.7) return 'Building direction';
  return 'Clear direction identified';
}

export const StudentMemoryBanner: React.FC<StudentMemoryBannerProps> = ({
  interests,
  confidenceScore,
  prevConfidenceScore,
  visible,
}) => {
  if (!visible || interests.length === 0) return null;

  let deltaIcon = '→';
  let deltaClass = 'confidence-delta-same';
  if (
    confidenceScore !== null &&
    prevConfidenceScore !== null &&
    Math.abs(confidenceScore - prevConfidenceScore) >= 0.02
  ) {
    if (confidenceScore > prevConfidenceScore) {
      deltaIcon = '↑';
      deltaClass = 'confidence-delta-up';
    } else {
      deltaIcon = '↓';
      deltaClass = 'confidence-delta-down';
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        className="memory-banner"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.35 }}
        role="status"
        aria-label="Student profile snapshot"
      >
        <div className="memory-banner-icon">🧠</div>
        <div className="memory-banner-content">
          <div className="memory-banner-title">Session Memory</div>

          {interests.length > 0 && (
            <div className="memory-banner-items">
              {interests.map((interest) => (
                <span key={interest} className="memory-tag">
                  {formatInterest(interest)}
                </span>
              ))}
            </div>
          )}

          {confidenceScore !== null && (
            <div className="memory-confidence-change">
              <span>Confidence:</span>
              <span className={deltaClass}>{deltaIcon}</span>
              <strong>{getConfidenceLabel(confidenceScore)}</strong>
              <span style={{ opacity: 0.6 }}>({Math.round(confidenceScore * 100)}%)</span>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
