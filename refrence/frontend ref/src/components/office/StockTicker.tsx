import React from 'react';
import { TICKER_ITEMS } from '../../constants/officeData';

export const StockTicker: React.FC = () => {
  const isReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  return (
    <g>
      <rect x={600} y={48} width={240} height={28} fill="#0a0d13" rx={4} />
      <g clipPath="url(#tk)">
        <g>
          {TICKER_ITEMS.map((item, idx) => (
            <text
              key={idx}
              x={608 + idx * 92}
              y={66}
              fontSize="10.5"
              fontWeight="600"
              fontFamily="Inter"
              fill={item.color}
            >
              {item.symbol}
            </text>
          ))}
          {!isReducedMotion && (
            <animateTransform
              attributeName="transform"
              type="translate"
              from="0"
              to="-276"
              dur="9s"
              repeatCount="indefinite"
            />
          )}
        </g>
      </g>
    </g>
  );
};
