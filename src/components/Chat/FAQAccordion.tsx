"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '../../context/ChatContext';

interface FAQItem {
  question: string;
  answer: string;
}

export const FAQAccordion: React.FC = () => {
  const { profile } = useChat();
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const course = profile?.course || 'MBA';
  const isUG = ['BCA', 'BBA', 'B.Com', 'BHM', 'BBA Aviation'].includes(course);

  const faqs: FAQItem[] = [
    {
      question: `What are the eligibility criteria for ${course}?`,
      answer: course === 'MCA' 
        ? "Candidates must have a Bachelor's degree (BCA/B.Sc/B.Com/B.A) with Mathematics at 10+2 level or at Graduate level with minimum 50% marks. A valid KMAT/PGCET score is required."
        : course === 'MBA'
          ? "Candidates must have a Bachelor's degree with a minimum of 50% aggregate marks (45% for SC/ST). A valid score in CAT/MAT/XAT/CMAT/KMAT is also required."
          : isUG
            ? `Candidates for ${course} must have completed 10+2 (PUC) or equivalent from a recognized board with a minimum of 45-50% aggregate marks.`
            : `Candidates for ${course} must have a Bachelor's degree with a minimum of 50% aggregate marks. Please check the official brochure for specific entrance exam requirements.`
    },
    {
      question: "How can I apply for scholarships?",
      answer: "Scholarships are merit-based and need-based. You can apply through the student portal after admission. Documentation of previous academic records and income proof will be required."
    },
    {
      question: "Are there hostel facilities for outstation students?",
      answer: "Yes, AIMS provides separate hostel facilities for boys and girls with 24/7 security, Wi-Fi, and nutritious mess facilities."
    },
    {
      question: "Does the college provide placement assistance?",
      answer: "AIMS has a dedicated Corporate Relations team that provides 100% placement assistance. Top recruiters include Amazon, Deloitte, ICICI Bank, and many more."
    }
  ];

  return (
    <div className="faq-container" style={{ width: '100%', maxWidth: '600px', marginTop: '20px' }}>
      <h4 style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase' }}>Frequently Asked Questions</h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {faqs.map((faq, index) => (
          <div key={index} style={{ border: '1px solid var(--border-light)', borderRadius: '12px', overflow: 'hidden' }}>
            <button
              onClick={() => setActiveIndex(activeIndex === index ? null : index)}
              style={{
                width: '100%',
                padding: '16px',
                textAlign: 'left',
                background: 'var(--card-bg)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: 'var(--text-main)',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              {faq.question}
              <motion.span
                animate={{ rotate: activeIndex === index ? 180 : 0 }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </motion.span>
            </button>
            <AnimatePresence>
              {activeIndex === index && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{ padding: '0 16px 16px', fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                    {faq.answer}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
};
