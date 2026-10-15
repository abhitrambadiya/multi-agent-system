import React from 'react';

export const OfficeDefs: React.FC = () => {
  return (
    <defs>
      {/* Drop shadow filter */}
      <filter id="sh" x="-30%" y="-30%" width="170%" height="190%">
        <feDropShadow dx="3" dy="5" stdDeviation="2.6" floodColor="#0a0806" floodOpacity="0.4" />
      </filter>

      {/* Background grid pattern */}
      <pattern id="bg" width="40" height="40" patternUnits="userSpaceOnUse">
        <rect width="40" height="40" fill="#0D0F12" />
        <path d="M40 0H0V40" fill="none" stroke="#171A20" />
      </pattern>

      {/* Wood plank floor pattern */}
      <pattern id="wood" width="80" height="20" patternUnits="userSpaceOnUse">
        <rect width="80" height="20" fill="#c79d73" />
        <path
          d="M0 0H80M0 10H80M0 20H80M25 0V10M65 10V20"
          stroke="#97704a"
          strokeOpacity="0.55"
        />
        <path
          d="M3 3.5H60M8 7H40M0 14H70M20 17H75"
          stroke="#a97f55"
          strokeOpacity="0.35"
          strokeWidth="0.8"
        />
      </pattern>

      {/* Carpet 1 (slate-blue pattern) */}
      <pattern id="cp1" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" fill="#5e7897" />
        <circle cx="1.5" cy="1.5" r="0.7" fill="#7790ae" />
        <circle cx="4.5" cy="4.5" r="0.7" fill="#4e6785" />
      </pattern>

      {/* Carpet 2 (teal pattern) */}
      <pattern id="cp2" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" fill="#3d6b6f" />
        <circle cx="1.5" cy="1.5" r="0.7" fill="#558589" />
        <circle cx="4.5" cy="4.5" r="0.7" fill="#315659" />
      </pattern>

      {/* Floor tiles pattern (office hall) */}
      <pattern id="tile" width="60" height="60" patternUnits="userSpaceOnUse">
        <rect width="60" height="60" fill="#d8d2c5" />
        <path d="M0 0H60V60" fill="none" stroke="#bdb6a5" strokeWidth="1.5" />
        <rect width="30" height="30" fill="#fff" opacity="0.14" />
        <rect x="30" y="30" width="30" height="30" fill="#fff" opacity="0.14" />
      </pattern>

      {/* Reception floor tile pattern */}
      <pattern id="tile2" width="40" height="40" patternUnits="userSpaceOnUse">
        <rect width="40" height="40" fill="#e6dfd0" />
        <rect width="20" height="20" fill="#cdc4b0" />
        <rect x="20" y="20" width="20" height="20" fill="#cdc4b0" />
      </pattern>

      {/* Keyboard texture pattern */}
      <pattern id="ky" width="4" height="3" patternUnits="userSpaceOnUse">
        <rect width="4" height="3" fill="#d6d2c8" />
        <rect width="3" height="2" fill="#f7f5ef" />
      </pattern>

      {/* Wood surface gradient */}
      <linearGradient id="wd" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#d4ac7d" />
        <stop offset="1" stopColor="#b98d5b" />
      </linearGradient>

      {/* Architectural column gradient */}
      <linearGradient id="col" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#f1ede4" />
        <stop offset="1" stopColor="#b9b2a4" />
      </linearGradient>

      {/* Screen glare gradient */}
      <linearGradient id="gl" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#7aa7ff" stopOpacity="0.6" />
        <stop offset="1" stopColor="#7aa7ff" stopOpacity="0" />
      </linearGradient>

      {/* Room ambient warm radial light */}
      <radialGradient id="lamp">
        <stop offset="0" stopColor="#fff0c0" stopOpacity="0.4" />
        <stop offset="1" stopColor="#fff0c0" stopOpacity="0" />
      </radialGradient>

      {/* Sunlight beam gradient */}
      <linearGradient id="ray" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#fff" stopOpacity="0.2" />
        <stop offset="1" stopColor="#fff" stopOpacity="0" />
      </linearGradient>

      {/* Dark vignette backdrop gradient */}
      <radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">
        <stop offset="0.62" stopColor="#05070b" stopOpacity="0" />
        <stop offset="1" stopColor="#05070b" stopOpacity="0.5" />
      </radialGradient>

      {/* Ticker marquee clip path */}
      <clipPath id="tk">
        <rect x="600" y="48" width="240" height="28" rx="4" />
      </clipPath>
    </defs>
  );
};
