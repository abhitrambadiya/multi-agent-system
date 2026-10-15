import React from 'react';

interface PlantProps {
  x: number;
  y: number;
  scale?: number;
}

export const Plant: React.FC<PlantProps> = ({ x, y, scale = 1 }) => {
  const angles = [0, 60, 120, 180, 240, 300];
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} filter="url(#sh)">
      <circle r={11} fill="#e7ddcc" />
      <circle r={9} fill="#5a3f2b" />
      {angles.map(a => (
        <ellipse
          key={a}
          cy={-8}
          rx={4.6}
          ry={10}
          fill={a % 120 ? '#35874b' : '#4aa660'}
          transform={`rotate(${a})`}
        />
      ))}
      <circle r={3} fill="#6cc27c" />
    </g>
  );
};

interface ChairProps {
  x: number;
  y: number;
  color?: string;
}

export const Chair: React.FC<ChairProps> = ({ x, y, color = '#3d4764' }) => {
  return (
    <g transform={`translate(${x} ${y})`} filter="url(#sh)">
      <rect x={-15} y={-4} width={5} height={12} rx={2} fill="#262c3e" />
      <rect x={10} y={-4} width={5} height={12} rx={2} fill="#262c3e" />
      <circle r={12} fill={color} />
      <circle r={8} fill="#fff" opacity={0.09} />
      <path
        d="M-12 7Q0 21 12 7"
        stroke="#252b3d"
        strokeWidth={5}
        fill="none"
        strokeLinecap="round"
      />
    </g>
  );
};

interface SofaProps {
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  up?: boolean;
}

export const Sofa: React.FC<SofaProps> = ({ x, y, w, h, color, up = true }) => {
  return (
    <g filter="url(#sh)">
      <rect x={x} y={y} width={w} height={h} fill={color} rx={9} />
      <rect
        x={x + 5}
        y={up ? y + 3 : y + h - 13}
        width={w - 10}
        height={10}
        fill="#000"
        rx={5}
        opacity={0.2}
      />
      <rect
        x={x + 6}
        y={up ? y + 14 : y + 5}
        width={w - 12}
        height={h - 21}
        fill="#fff"
        rx={6}
        opacity={0.13}
      />
      <rect
        x={x + w / 2 - 0.5}
        y={up ? y + 14 : y + 5}
        width={1}
        height={h - 21}
        fill="#000"
        opacity={0.15}
      />
    </g>
  );
};

interface DeskProps {
  x: number;
  y: number;
  w: number;
  numMonitors?: number;
  glowColor?: string;
  seed?: number;
}

export const Desk: React.FC<DeskProps> = ({
  x,
  y,
  w,
  numMonitors = 1,
  glowColor = '#5b8cff',
  seed = 0,
}) => {
  const mw = Math.min(34, (w - 26) / numMonitors);

  const monitors = Array.from({ length: numMonitors }, (_, i) => {
    const cx = x + w / 2 + (i - (numMonitors - 1) / 2) * (mw + 5);
    return (
      <React.Fragment key={i}>
        {/* Screen glare */}
        <rect
          x={cx - mw / 2 - 3}
          y={y + 15}
          width={mw + 6}
          height={14}
          fill="url(#gl)"
          opacity={0.55}
        />
        {/* Monitor bezel */}
        <rect x={cx - mw / 2} y={y + 5} width={mw} height={10} fill="#0a0d13" rx={2} />
        {/* Screen glass */}
        <rect
          x={cx - mw / 2 + 1.5}
          y={y + 6.5}
          width={mw - 3}
          height={6.5}
          fill="#0f1a30"
        />
        {/* Animated code/chart lines */}
        {[0, 1].map(j => (
          <rect
            key={j}
            className="ln"
            x={cx - mw / 2 + 3}
            y={y + 7.4 + j * 2.6}
            width={mw - 9}
            height={1.3}
            fill={glowColor}
            style={{ animationDelay: `${((seed + i * 2 + j) % 7) * 0.45}s` }}
          />
        ))}
        {/* Monitor stand */}
        <rect x={cx - 3} y={y + 14.5} width={6} height={2} fill="#222" />
      </React.Fragment>
    );
  });

  return (
    <g filter="url(#sh)">
      {/* Desk top */}
      <rect
        x={x}
        y={y}
        width={w}
        height={50}
        fill="url(#wd)"
        rx={5}
        stroke="#8a6842"
        strokeWidth={1.2}
      />
      {/* Cable wire */}
      <path
        d={`M${x + w - 34} ${y + 14}q8 20 22 12`}
        stroke="#16181d"
        strokeWidth={1}
        fill="none"
      />
      {/* Monitors */}
      {monitors}
      {/* Keyboard */}
      <rect
        x={x + w / 2 - 12}
        y={y + 27}
        width={24}
        height={8}
        fill="url(#ky)"
        rx={1.5}
        stroke="#b9b5aa"
        strokeWidth={0.5}
      />
      {/* Mouse */}
      <ellipse
        cx={x + w / 2 + 22}
        cy={y + 31}
        rx={3.4}
        ry={4.4}
        fill="#e5e2da"
      />
      {/* Desk lamp base & arm & head */}
      <circle cx={x + 10} cy={y + 13} r={4.4} fill="#2b303b" />
      <path d={`M${x + 10} ${y + 13}l9 14`} stroke="#2b303b" strokeWidth={1.6} />
      <circle cx={x + 19} cy={y + 27} r={2.2} fill="#f2d06b" />
      {/* Coffee mug */}
      <circle cx={x + w - 10} cy={y + 40} r={4.2} fill="#f4f1ea" />
      <circle cx={x + w - 10} cy={y + 40} r={2.5} fill="#6b4a33" />
      {/* Sticky note */}
      <rect
        x={x + 8}
        y={y + 34}
        width={12}
        height={10}
        fill="#fff"
        rx={1}
        opacity={0.85}
        transform={`rotate(-8 ${x + 14} ${y + 39})`}
      />
    </g>
  );
};
