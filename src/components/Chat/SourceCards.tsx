"use client";

import React from 'react';

interface Source {
  url: string;
  title: string;
}

interface SourceCardsProps {
  sources: Source[];
}

function extractDomain(url: string): string {
  try {
    const { hostname } = new URL(url);
    return hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

function faviconUrl(url: string): string {
  try {
    const { origin } = new URL(url);
    return `${origin}/favicon.ico`;
  } catch {
    return '';
  }
}

export const SourceCards: React.FC<SourceCardsProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="source-cards-container" aria-label="Sources">
      {sources.map((source, i) => {
        const domain = extractDomain(source.url);
        const favicon = faviconUrl(source.url);
        return (
          <a
            key={i}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-card"
            title={source.title}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="source-card-icon"
              src={favicon}
              alt=""
              onError={(e) => {
                // Fallback to a generic link icon on favicon load failure
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
              {source.title}
            </span>
            <span className="source-card-domain">{domain}</span>
          </a>
        );
      })}
    </div>
  );
};
