import React from 'react';
import { Agent } from '../../types/agent';
import { AgentSprite } from './AgentSprite';
import { useAgentStore } from '../../store/useAgentStore';

interface AgentRendererProps {
  agent: Agent;
}

export const AgentRenderer: React.FC<AgentRendererProps> = ({ agent }) => {
  const selectedAgentId = useAgentStore(state => state.selectedAgentId);
  const completedAgentId = useAgentStore(state => state.completedAgentId);
  const selectAgent = useAgentStore(state => state.selectAgent);

  const isSelected = selectedAgentId === agent.id;
  const isDone = completedAgentId === agent.id;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    selectAgent(agent.id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      e.stopPropagation();
      selectAgent(agent.id);
    }
  };

  const agentClasses = [
    'agent',
    isSelected ? 'sel' : '',
    isDone ? 'done' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <g
      id={`ag-${agent.id}`}
      data-id={agent.id}
      tabIndex={0}
      role="button"
      aria-label={`${agent.name}, ${agent.role}`}
      className={agentClasses}
      transform={`translate(${agent.x} ${agent.y})`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {/* Selection / Completion ring */}
      <circle
        className="ring"
        cy={4}
        r={21}
        fill="none"
        stroke={agent.color}
        strokeWidth={1.5}
      />

      {/* Character body (with horizontal flip when walking left) */}
      <g
        className="fl"
        transform={agent.flipped ? 'scale(-1 1)' : undefined}
      >
        <AgentSprite agent={agent} />
      </g>

      {/* Floating Status Badge Label */}
      <g className="lbl" transform="translate(0 27)">
        <rect
          x={-34}
          width={68}
          height={19}
          rx={6}
          fill="#0D0F12"
          fillOpacity={0.88}
          stroke="#343a47"
          strokeWidth={0.8}
        />
        <circle cx={-26} cy={9.5} r={2.6} fill={agent.color} />
        <text
          x={-20}
          y={8}
          fontSize={8.5}
          fontWeight={600}
          fill="#e6e8ee"
          fontFamily="Inter"
        >
          {agent.name}
        </text>
        <text
          id={`lt-${agent.id}`}
          x={-20}
          y={16}
          fontSize={7}
          fill="#8b93a3"
          fontFamily="Inter"
        >
          {agent.statusText}
        </text>
      </g>
    </g>
  );
};
