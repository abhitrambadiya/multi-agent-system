import { RoomDef } from '../types/office';

export const ROOMS: RoomDef[] = [
  {
    id: 'workstations',
    name: 'Workstations',
    x: 40,
    y: 40,
    w: 520,
    h: 270,
    floorPattern: 'url(#cp1)',
    hasGlassWalls: false,
  },
  {
    id: 'trading',
    name: 'Trading desk',
    x: 590,
    y: 40,
    w: 260,
    h: 270,
    floorPattern: 'url(#cp2)',
    hasGlassWalls: false,
  },
  {
    id: 'manager',
    name: "Manager's office",
    x: 880,
    y: 40,
    w: 280,
    h: 270,
    floorPattern: 'url(#wood)',
    hasGlassWalls: true,
  },
  {
    id: 'reception',
    name: 'Reception',
    x: 40,
    y: 470,
    w: 280,
    h: 250,
    floorPattern: 'url(#tile2)',
    hasGlassWalls: false,
  },
  {
    id: 'meeting',
    name: 'Meeting room',
    x: 470,
    y: 400,
    w: 330,
    h: 320,
    floorPattern: 'url(#cp1)',
    hasGlassWalls: true,
  },
  {
    id: 'lounge',
    name: 'Coffee lounge',
    x: 830,
    y: 400,
    w: 330,
    h: 320,
    floorPattern: 'url(#wood)',
    hasGlassWalls: false,
  },
];

export const DOORWAYS = [
  { x: 300, y: 302, w: 60, h: 16 },
  { x: 690, y: 302, w: 60, h: 16 },
  { x: 990, y: 302, w: 60, h: 16 },
  { x: 150, y: 462, w: 60, h: 16 },
  { x: 312, y: 560, w: 16, h: 60 },
  { x: 600, y: 392, w: 60, h: 16 },
  { x: 462, y: 540, w: 16, h: 60 },
  { x: 960, y: 392, w: 60, h: 16 },
  { x: 822, y: 540, w: 16, h: 60 },
];

export const COLUMNS: [number, number][] = [
  [565, 316],
  [865, 316],
  [465, 386],
  [825, 386],
  [326, 478],
  [160, 40],
];

export const SUNBEAMS = [160, 420, 690, 960];

export const TICKER_ITEMS = [
  { symbol: 'NVDA +2.4%', color: '#4cc38a' },
  { symbol: 'TSLA −1.1%', color: '#ef6b6b' },
  { symbol: 'AAPL +0.6%', color: '#4cc38a' },
  { symbol: 'MSFT +1.2%', color: '#4cc38a' },
  { symbol: 'AMZN −0.3%', color: '#ef6b6b' },
  { symbol: 'NVDA +2.4%', color: '#4cc38a' },
];

export const WAYPOINT_PATH_D =
  'M60 356H1140M395 356V700M815 356V700M330 310V356M720 310V356M1020 310V356M180 470V356M320 590H470M470 570H830M630 400V356M990 400V356';

// Common destination nodes in the office graph for autonomous waypoint routing
export const OFFICE_WAYPOINTS = {
  // Hallway central spine
  HALL_WEST: { x: 180, y: 356 },
  HALL_WORKSTATION: { x: 330, y: 356 },
  HALL_CROSS_WEST: { x: 395, y: 356 },
  HALL_MEETING_ENTRANCE: { x: 630, y: 356 },
  HALL_TRADING: { x: 720, y: 356 },
  HALL_CROSS_EAST: { x: 815, y: 356 },
  HALL_LOUNGE_ENTRANCE: { x: 990, y: 356 },
  HALL_MANAGER: { x: 1020, y: 356 },

  // Rooms
  DESK_ATLAS: { x: 125, y: 141 },
  DESK_NOVA: { x: 655, y: 171 },
  DESK_ECHO: { x: 330, y: 141 },
  DESK_SAGE: { x: 1015, y: 181 },
  MEETING_TABLE: { x: 630, y: 440 },
  COFFEE_BAR: { x: 1078, y: 464 },
  RECEPTION_COUCH: { x: 110, y: 660 },
};
