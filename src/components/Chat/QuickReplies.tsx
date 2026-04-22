"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface QuickRepliesProps {
  onSelect: (query: string) => void;
}

export const QuickReplies: React.FC<QuickRepliesProps> = ({ onSelect }) => {
  const suggestions = [
    "Courses offered?",
    "Admission process",
    "Fees structure",
    "Campus facilities",
    "Scholarship info",
    "Important dates",
    "Contact admissions"
  ];

  return (
    <motion.div 
      className="quick-replies-container"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      {suggestions.map((sug, index) => (
        <motion.button
          key={index}
          className="quick-reply-chip"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onSelect(sug)}
        >
          {sug}
        </motion.button>
      ))}
    </motion.div>
  );
};
