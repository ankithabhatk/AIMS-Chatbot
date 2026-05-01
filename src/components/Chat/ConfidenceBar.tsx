"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface ConfidenceBarProps {
  confidence: number; // 0.0 – 1.0
}

function getLabel(confidence: number): string {
  if (confidence < 0.4) return 'Low · Exploring options';
  if (confidence < 0.7) return 'Building confidence';
  return 'High confidence';
}

function getTier(confidence: number): 'low' | 'medium' | 'high' {
  if (confidence < 0.4) return 'low';
  if (confidence < 0.7) return 'medium';
  return 'high';
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence }) => {
  const tier = getTier(confidence);
  const label = getLabel(confidence);
  const targetPct = Math.round(confidence * 100);

  return (
    <div className="confidence-bar-container" title={`Confidence: ${targetPct}%`}>
      <div className="confidence-bar-header">
        <span>{label}</span>
        <span style={{ opacity: 0.7 }}>{targetPct}%</span>
      </div>
      <div className="confidence-bar-track">
        <motion.div
          className={`confidence-bar-fill ${tier}`}
          initial={{ width: 0 }}
          animate={{ width: `${targetPct}%` }}
          transition={{ type: "spring", stiffness: 100, damping: 15 }}
          style={{ minWidth: "4px" }}
        />
      </div>
    </div>
  );
};
