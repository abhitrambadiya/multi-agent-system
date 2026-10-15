import React from 'react';
import { ROOMS, DOORWAYS, COLUMNS, SUNBEAMS, WAYPOINT_PATH_D } from '../../constants/officeData';
import { Plant, Chair, Sofa, Desk } from './OfficeFurniture';
import { StockTicker } from './StockTicker';
import { useSimulationStore } from '../../store/useSimulationStore';

export const WallClock: React.FC = () => {
  // Only re-renders when the simulated minute integer changes
  const simMinuteInt = useSimulationStore(state => Math.floor(state.simMinutes));
  const hourAngle = ((simMinuteInt / 60) % 12) * 30;
  const minuteAngle = (simMinuteInt % 60) * 6;

  return (
    <g>
      <circle cx={470} cy={56} r={10} fill="#f4efe6" stroke="#2b303b" strokeWidth={2} />
      <line
        id="hh"
        x1={0}
        y1={0}
        x2={0}
        y2={-5}
        stroke="#222"
        strokeWidth={1.6}
        transform={`translate(470 56) rotate(${hourAngle})`}
      />
      <line
        id="hm"
        x1={0}
        y1={0}
        x2={0}
        y2={-7.5}
        stroke="#222"
        strokeWidth={1}
        transform={`translate(470 56) rotate(${minuteAngle})`}
      />
    </g>
  );
};

export const OfficeRoomsComponent: React.FC = () => {
  return (
    <g>
      {/* 1. Backdrop Grid & Outer Floor Border */}
      <rect x={-400} y={-300} width={2000} height={1400} fill="url(#bg)" />
      <rect
        x={14}
        y={14}
        width={1172}
        height={732}
        fill="url(#tile)"
        rx={8}
        stroke="#2a2f3a"
        strokeWidth={16}
      />
      <rect
        x={14}
        y={14}
        width={1172}
        height={732}
        fill="none"
        rx={8}
        stroke="#555d6e"
        strokeWidth={1}
      />

      {/* 2. Walkway Path Overlay Network */}
      <g
        id="paths"
        fill="none"
        stroke="#fff"
        strokeOpacity={0.8}
        strokeWidth={3}
        strokeDasharray="2 9"
        strokeLinecap="round"
      >
        <path d={WAYPOINT_PATH_D} />
      </g>

      {/* 3. Rooms Structure, Floors & Walls */}
      {ROOMS.map(room => (
        <g key={room.id}>
          {/* Drop shadow underneath room */}
          <rect
            x={room.x + 5}
            y={room.y + 8}
            width={room.w}
            height={room.h}
            fill="#000"
            rx={4}
            opacity={0.28}
          />
          {/* Room flooring */}
          <rect
            x={room.x}
            y={room.y}
            width={room.w}
            height={room.h}
            fill={room.floorPattern}
          />
          {/* Room ambient warm lighting */}
          <ellipse
            cx={room.x + room.w / 2}
            cy={room.y + room.h / 2}
            rx={room.w * 0.52}
            ry={room.h * 0.47}
            fill="url(#lamp)"
          />

          {/* Wall styling: Glass vs Solid */}
          {room.hasGlassWalls ? (
            <>
              <rect
                x={room.x}
                y={room.y + 6}
                width={room.w}
                height={room.h}
                fill="none"
                rx={3}
                stroke="#6f9db3"
                strokeWidth={5}
                strokeOpacity={0.55}
              />
              <rect
                x={room.x}
                y={room.y}
                width={room.w}
                height={room.h}
                fill="#bfeaff"
                rx={3}
                fillOpacity={0.1}
                stroke="#b6e4f7"
                strokeWidth={4}
                strokeOpacity={0.85}
              />
              <path
                d={`M${room.x + room.w / 2} ${room.y}V${room.y + room.h}M${room.x} ${room.y + room.h / 2}H${room.x + room.w}`}
                stroke="#fff"
                strokeOpacity={0.35}
              />
              <polygon
                points={`${room.x + 20},${room.y + room.h} ${room.x + 90},${room.y + room.h} ${room.x + 190},${room.y} ${room.x + 120},${room.y}`}
                fill="#fff"
                opacity={0.06}
              />
            </>
          ) : (
            <>
              <rect
                x={room.x}
                y={room.y + 7}
                width={room.w}
                height={room.h}
                fill="none"
                rx={3}
                stroke="#8f877a"
                strokeWidth={10}
              />
              <rect
                x={room.x}
                y={room.y}
                width={room.w}
                height={room.h}
                fill="none"
                rx={3}
                stroke="#f1ede4"
                strokeWidth={7}
              />
              <rect
                x={room.x + 4.5}
                y={room.y + 4.5}
                width={room.w - 9}
                height={room.h - 9}
                fill="none"
                rx={2}
                stroke="#c9c2b4"
                strokeWidth={1}
              />
            </>
          )}

          {/* Room Name Tag */}
          <text
            x={room.x + 14}
            y={room.y + room.h - 12}
            fontSize={11}
            fontWeight={600}
            fill="#1c2433"
            opacity={0.4}
            fontFamily="Inter"
          >
            {room.name}
          </text>
        </g>
      ))}

      {/* 4. Doorway Cutouts */}
      {DOORWAYS.map((d, i) => (
        <g key={i}>
          <rect x={d.x} y={d.y} width={d.w} height={d.h} fill="url(#tile)" />
          {d.w > d.h ? (
            <>
              <rect x={d.x - 2} y={d.y + 3} width={5} height={10} fill="#5b5448" />
              <rect x={d.x + d.w - 3} y={d.y + 3} width={5} height={10} fill="#5b5448" />
            </>
          ) : (
            <>
              <rect x={d.x + 3} y={d.y - 2} width={10} height={5} fill="#5b5448" />
              <rect x={d.x + 3} y={d.y + d.h - 3} width={10} height={5} fill="#5b5448" />
            </>
          )}
        </g>
      ))}

      {/* 5. Structural Columns */}
      {COLUMNS.map(([cx, cy], i) => (
        <g key={i} filter="url(#sh)">
          <rect
            x={cx - 8}
            y={cy - 8}
            width={16}
            height={16}
            fill="url(#col)"
            rx={2}
            stroke="#9a9488"
            strokeWidth={0.8}
          />
        </g>
      ))}

      {/* 6. Exterior Windows & Glass Highlights */}
      {Array.from({ length: 6 }, (_, i) => 90 + i * 190).map(x => (
        <g key={`win-top-${x}`}>
          <rect x={x} y={9} width={100} height={10} fill="#bfe6fb" rx={2} />
          <rect x={x + 49} y={9} width={2} height={10} fill="#fff" opacity={0.8} />
        </g>
      ))}
      {Array.from({ length: 3 }, (_, i) => 110 + i * 220).map(y => (
        <g key={`win-side-${y}`}>
          <rect x={9} y={y} width={10} height={100} fill="#bfe6fb" rx={2} />
          <rect x={1181} y={y} width={10} height={100} fill="#bfe6fb" rx={2} />
        </g>
      ))}

      {/* 7. Workstations Interior */}
      {/* Filing cabinets */}
      {Array.from({ length: 4 }, (_, i) => (
        <g key={`cab-${i}`} filter="url(#sh)">
          <rect x={66 + i * 34} y={50} width={30} height={18} fill="#aab3c4" rx={2} />
          <rect x={70 + i * 34} y={54} width={22} height={4} fill="#8f99ac" rx={1} />
          <rect x={70 + i * 34} y={61} width={22} height={4} fill="#8f99ac" rx={1} />
        </g>
      ))}
      {/* Bookshelf with books */}
      <rect x={300} y={48} width={120} height={14} fill="#7a5a3a" rx={2} />
      {Array.from({ length: 8 }, (_, i) => (
        <rect
          key={`bk-${i}`}
          x={303 + i * 14}
          y={50}
          width={10}
          height={10}
          fill={['#d9786a', '#6aa3d9', '#e2c15f', '#7bbf8a'][i % 4]}
          rx={1}
        />
      ))}

      {/* Dynamic Wall Analog Clock Hand */}
      <WallClock />

      {/* 6 Workstation Desks and Chairs (2 rows of 3) */}
      {[80, 205].map((rowY, rIdx) =>
        [60, 235, 410].map((colX, cIdx) => (
          <g key={`desk-${rIdx}-${cIdx}`}>
            <rect
              x={colX - 4}
              y={rowY - 4}
              width={138}
              height={70}
              fill="#000"
              rx={3}
              opacity={0.07}
            />
            <Desk x={colX} y={rowY} w={130} seed={rIdx * 3 + cIdx} />
            <Chair x={colX + 65} y={rowY + 64} />
          </g>
        ))
      )}
      <Plant x={52} y={292} />
      <Plant x={546} y={62} />
      <Plant x={300} y={290} scale={0.8} />

      {/* 8. Trading Desk Interior */}
      <StockTicker />
      {[
        [600, 110],
        [730, 110],
        [600, 215],
        [730, 215],
      ].map(([dx, dy], i) => (
        <g key={`td-${i}`}>
          <Desk
            x={dx}
            y={dy}
            w={110}
            numMonitors={3}
            glowColor={i % 2 ? '#ef8a97' : '#5ee0a0'}
            seed={i + 10}
          />
          <Chair x={dx + 55} y={dy + 64} color="#2f4f60" />
        </g>
      ))}
      <Plant x={842} y={290} scale={0.9} />

      {/* 9. Manager's Office Interior */}
      <rect x={900} y={48} width={240} height={18} fill="#6b4a33" rx={3} />
      {Array.from({ length: 18 }, (_, i) => (
        <rect
          key={`mbk-${i}`}
          x={904 + i * 13}
          y={51}
          width={9}
          height={12}
          fill={['#d9786a', '#7fa6a0', '#e2c15f', '#6d83c9', '#b784c9'][i % 5]}
          rx={1}
        />
      ))}
      {/* Executive Rug */}
      <rect
        x={955}
        y={168}
        width={120}
        height={70}
        fill="#7f6585"
        rx={12}
        opacity={0.5}
      />
      <Desk x={930} y={110} w={170} numMonitors={2} glowColor="#a995ff" seed={20} />
      <Chair x={1015} y={183} color="#5f4d96" />
      <Sofa x={900} y={246} w={110} h={34} color="#566f92" up={false} />
      <rect x={1030} y={252} width={40} height={22} fill="#cdb591" rx={6} />
      <Plant x={1135} y={68} />
      <Plant x={1135} y={282} scale={0.9} />

      {/* 10. Meeting Room Interior */}
      <rect x={580} y={408} width={110} height={9} fill="#0a0d13" rx={2} />
      <rect x={584} y={411} width={102} height={3} fill="#6aa8ff" />
      <rect
        x={505}
        y={490}
        width={260}
        height={140}
        fill="#6f5a82"
        rx={10}
        opacity={0.35}
      />
      <g filter="url(#sh)">
        <rect x={520} y={500} width={230} height={110} fill="#6e4d36" rx={26} />
        <rect x={526} y={506} width={218} height={98} fill="url(#wd)" rx={22} />
        <rect x={560} y={520} width={50} height={32} fill="#d9d4ca" rx={3} />
        <rect x={660} y={556} width={50} height={32} fill="#d9d4ca" rx={3} />
        <circle cx={635} cy={555} r={8} fill="#2b303b" />
      </g>
      {[550, 635, 720].map(mx => (
        <React.Fragment key={`mc-${mx}`}>
          <Chair x={mx} y={482} color="#6a5a98" />
          <Chair x={mx} y={628} color="#6a5a98" />
        </React.Fragment>
      ))}
      <Chair x={502} y={555} color="#6a5a98" />
      <Chair x={768} y={555} color="#6a5a98" />
      <Plant x={492} y={434} />
      <Plant x={782} y={434} />
      <Plant x={782} y={702} />
      <Plant x={492} y={702} />

      {/* 11. Coffee Lounge Interior */}
      <circle cx={990} cy={568} r={92} fill="#b8806a" opacity={0.5} />
      <circle
        cx={990}
        cy={568}
        r={70}
        fill="none"
        stroke="#fff"
        strokeOpacity={0.4}
        strokeWidth={3}
      />
      <Sofa x={930} y={486} w={120} h={40} color="#c98f4d" up={true} />
      <Sofa x={930} y={610} w={120} h={40} color="#c98f4d" up={false} />
      <g filter="url(#sh)">
        <circle cx={990} cy={568} r={26} fill="#ecdfca" />
        <circle cx={990} cy={568} r={19} fill="#d3bd9b" />
      </g>
      <g filter="url(#sh)">
        <rect x={862} y={540} width={40} height={40} fill="#4f8d8f" rx={14} />
        <rect x={1076} y={540} width={40} height={40} fill="#4f8d8f" rx={14} />
        <rect x={1030} y={410} width={120} height={34} fill="#ece7dd" rx={5} />
        <rect x={1036} y={414} width={110} height={10} fill="#6f7e99" rx={3} />
        <rect x={1044} y={425} width={24} height={14} fill="#20252f" rx={3} />
        <circle cx={1056} cy={426} r={2} fill="#4cc38a" />
        <circle cx={1096} cy={435} r={4} fill="#fff" />
        <circle cx={1112} cy={435} r={4} fill="#fff" />
        <rect x={844} y={430} width={28} height={60} fill="#d65a50" rx={4} />
        <rect x={848} y={436} width={20} height={24} fill="#fff" rx={2} opacity={0.45} />
      </g>
      {/* Steam floating from espresso machine */}
      <path
        className="stm"
        d="M1054 420q3-4 0-8"
        stroke="#fff"
        strokeWidth={1.4}
        fill="none"
        opacity={0.7}
      />
      <rect x={884} y={408} width={44} height={26} fill="#2b303b" rx={2} />
      <rect x={888} y={412} width={36} height={18} fill="#d9a05b" />
      <circle cx={906} cy={421} r={6} fill="#7b5ea7" />
      <Plant x={860} y={702} />
      <Plant x={1138} y={702} />
      <Plant x={1138} y={486} scale={0.9} />
      <Plant x={1138} y={430} scale={0.8} />

      {/* 12. Reception Interior */}
      <ellipse
        cx={180}
        cy={610}
        rx={110}
        ry={56}
        fill="#dcd5c5"
        stroke="#c4bba6"
        strokeWidth={3}
      />
      <rect x={90} y={482} width={140} height={22} fill="#12151c" rx={4} />
      <text
        x={160}
        y={497}
        textAnchor="middle"
        fontSize={11}
        fontWeight={600}
        fill="#9d8fff"
        fontFamily="Inter"
        letterSpacing={1.5}
      >
        AGENT HQ
      </text>
      <g filter="url(#sh)">
        <rect x={80} y={540} width={190} height={40} fill="#f1ece2" rx={20} />
        <rect x={80} y={540} width={190} height={12} fill="#4e5d7c" rx={8} />
        <rect x={150} y={556} width={50} height={16} fill="#12151c" rx={3} />
      </g>
      <Sofa x={54} y={664} w={120} h={38} color="#6f84a6" up={false} />
      <rect x={190} y={672} width={34} height={22} fill="#cdb591" rx={6} />
      <rect x={246} y={476} width={36} height={24} fill="#2b303b" rx={2} />
      <rect x={250} y={480} width={28} height={16} fill="#d9a05b" />
      <Plant x={60} y={502} />
      <Plant x={298} y={704} scale={0.9} />

      {/* 13. Print Corner */}
      <g filter="url(#sh)">
        <rect x={60} y={386} width={52} height={34} fill="#e2e2e9" rx={4} />
        <rect x={66} y={392} width={40} height={12} fill="#8c96ac" rx={2} />
        <circle cx={146} cy={404} r={14} fill="#cfeaf7" />
        <circle cx={146} cy={404} r={9} fill="#7fc4ee" />
        <rect x={210} y={392} width={90} height={22} fill="#a98160" rx={5} />
      </g>
      <Plant x={300} y={440} scale={0.9} />

      {/* 14. Sunlight Ray Beams */}
      {SUNBEAMS.map(sx => (
        <polygon
          key={`sun-${sx}`}
          points={`${sx},16 ${sx + 70},16 ${sx + 210},300 ${sx + 130},300`}
          fill="url(#ray)"
        />
      ))}

      {/* 15. Vignette Overlay */}
      <rect
        x={-400}
        y={-300}
        width={2000}
        height={1400}
        fill="url(#vig)"
        pointerEvents="none"
      />
    </g>
  );
};

// React.memo ensures the office room geometry is rendered ONCE and never re-diffed!
export const OfficeRooms = React.memo(OfficeRoomsComponent);
