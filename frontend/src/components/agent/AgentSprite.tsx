import React from 'react';
import { Agent } from '../../types/agent';

interface AgentSpriteProps {
  agent: Agent;
}

export const AgentSprite: React.FC<AgentSpriteProps> = ({ agent }) => {
  const [shirtColor, pantsColor, hairColor] = agent.outfit;

  // Accessories on Torso vs Head
  const renderTorsoAccessory = () => {
    switch (agent.accessoryType) {
      case 'scarf':
        return (
          <path
            d="M-8 3h16"
            stroke="#f4e3c2"
            strokeWidth={2.4}
            strokeLinecap="round"
          />
        );
      case 'tie':
        return <path d="M0 -2l2 4-2 5-2-5z" fill="#e8e6f2" />;
      default:
        return null;
    }
  };

  const renderHeadAccessory = () => {
    switch (agent.accessoryType) {
      case 'glasses':
        return (
          <g fill="none" stroke="#12151c" strokeWidth={1}>
            <circle cx={-3.2} cy={-9} r={2.3} />
            <circle cx={3.2} cy={-9} r={2.3} />
            <path d="M-.9-9h1.8" />
          </g>
        );
      case 'flower':
        return <circle cx={0} cy={-19} r={3.4} fill="#c4527a" />;
      case 'headphones':
        return (
          <>
            <path
              d="M-8.6-10a8.6 8.6 0 0 1 17.2 0"
              fill="none"
              stroke="#11141a"
              strokeWidth={1.6}
            />
            <rect x={-10} y={-11} width={3} height={5} rx={1.4} fill="#11141a" />
            <rect x={7} y={-11} width={3} height={5} rx={1.4} fill="#11141a" />
          </>
        );
      default:
        return null;
    }
  };

  const classes = [
    'sp',
    agent.animation,
    agent.seated ? 'seat' : '',
    agent.facingUp ? 'u' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <g className={classes} data-sp>
      {/* Ground drop shadow */}
      <ellipse cy={19} rx={11} ry={3.2} fill="#000" opacity={0.3} />

      {/* Legs (hidden when seated) */}
      <g className="lg">
        <rect className="lL" x={-6} y={9} width={5} height={10} rx={2} fill={pantsColor} />
        <rect className="lR" x={1} y={9} width={5} height={10} rx={2} fill={pantsColor} />
      </g>

      {/* Torso */}
      <g className="tor">
        <rect x={-9} y={-3} width={18} height={15} rx={6} fill={shirtColor} />
        {renderTorsoAccessory()}
        {/* Left Arm */}
        <rect
          className="aL"
          x={-12.5}
          y={-2}
          width={4.5}
          height={12}
          rx={2.2}
          fill={shirtColor}
        />
        {/* Right Arm */}
        <g className="aR">
          <rect x={8} y={-2} width={4.5} height={12} rx={2.2} fill={shirtColor} />
          {agent.hasMug && (
            <rect x={8.6} y={8} width={5} height={5} rx={1.2} fill="#f4f1ea" />
          )}
        </g>
      </g>

      {/* Head */}
      <g className="hd">
        {/* Face skin */}
        <circle cy={-10} r={8} fill="#f1c8a4" />
        {/* Front hair */}
        <path
          d="M-8.6-10a8.6 8.6 0 0 1 17.2 0q-8.6-5-17.2 0z"
          fill={hairColor}
        />
        {/* Back hair (shown when facing up) */}
        <circle className="hb" cy={-10} r={8.2} fill={hairColor} />
        {/* Eyes (hidden when facing up) */}
        <g className="eyes">
          <circle cx={-3} cy={-9} r={1.1} fill="#2a2230" />
          <circle cx={3} cy={-9} r={1.1} fill="#2a2230" />
        </g>
        {/* Head accessories */}
        {renderHeadAccessory()}
      </g>
    </g>
  );
};
