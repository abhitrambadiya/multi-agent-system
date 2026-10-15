# Agent HQ — Frontend-Only AI Office Simulator

A modular, production-grade 2D AI office simulation built with **React**, **TypeScript**, **Vite**, **Tailwind CSS**, and **Zustand**.

This project transforms the original monolithic `Agent HQ.html` prototype into a clean, maintainable, component-driven frontend architecture while preserving 100% of the original visual aesthetic, interactive camera controls, character animations, and agent simulations.

---

## 🏗️ Architecture Overview

```
MultiAgent/
├── Agent HQ.html                  # Original reference prototype (preserved)
├── index.html                     # Vite entry template with Google Fonts Inter
├── package.json                   # Dependencies (React 18, Vite 6, Zustand, Lucide, Tailwind)
├── tsconfig.json                  # Strict TypeScript configuration
├── vite.config.ts                 # Fast Vite dev server & bundler configuration
├── tailwind.config.js             # Agent HQ custom dark palette & tokens
├── postcss.config.js              # PostCSS plugins
├── src/
│   ├── main.tsx                   # React root entry point
│   ├── App.tsx                    # Top-level application component
│   ├── index.css                  # Design tokens, variables & SVG character animations
│   ├── types/
│   │   ├── agent.ts               # Agent, AgentState, TaskDefinition, Waypoint models
│   │   └── office.ts              # RoomDef, FurnitureDef, CameraState
│   ├── constants/
│   │   ├── initialAgents.ts       # Atlas, Nova, Echo, Sage, Pixel initial datasets
│   │   └── officeData.ts          # Office rooms, columns, doorways, ticker, waypoints
│   ├── store/
│   │   ├── useAgentStore.ts       # Agent state, task assignment, progress, logs & queue
│   │   ├── useCameraStore.ts      # Viewport zoom, pan, exponential smoothing & follow agent
│   │   ├── useSimulationStore.ts  # Simulation clock (day/time), speed presets, toast banners
│   │   └── useUIStore.ts          # Nav rail collapse, inspector drawer, modal navigation
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx       # Main grid/flex layout coordinator
│   │   │   ├── NavRail.tsx        # Collapsible left sidebar with Lucide navigation icons
│   │   │   └── TopBar.tsx         # Breadcrumbs, active agent counter, clock & inspector toggle
│   │   ├── office/
│   │   │   ├── OfficeViewport.tsx # Responsive SVG stage with camera pan/wheel zoom engine
│   │   │   ├── OfficeDefs.tsx     # SVG filters, wood/tile/carpet patterns & gradients
│   │   │   ├── OfficeRooms.tsx    # 6 functional rooms, furniture, animated wall clock
│   │   │   ├── OfficeFurniture.tsx# Reusable Plant, Chair, Sofa, Desk SVG components
│   │   │   └── StockTicker.tsx    # Animated market ticker with pause/reduced-motion support
│   │   ├── agent/
│   │   │   ├── AgentRenderer.tsx  # Character transform, selection ring, badges & click handlers
│   │   │   └── AgentSprite.tsx    # Vector character body, legs, torso, eyes & accessories
│   │   ├── inspector/
│   │   │   └── AgentInspector.tsx # Selected agent dossier, task picker, progress bar & timeline
│   │   ├── controls/
│   │   │   ├── BottomDock.tsx     # Zoom (-/+/reset), speed (pause/0.5x/1x/2x), overlay toggles
│   │   │   └── Toast.tsx          # Real-time task completion toast notifications
│   │   └── modals/
│   │       └── NavModals.tsx      # Interactive drawers for Roster, Tasks, Markets, Meetings
│   └── simulation/
│       └── useSimulationLoop.ts   # requestAnimationFrame coordinator for agent routines & camera
```

---

## 🤖 The Five Agents

1. **Atlas (Research Agent)**
   - **Station**: Workstations (Top-Left, Desk 1)
   - **Accent Color**: `#6ea8ff` (Soft Blue)
   - **Accessory**: Spectacles / Wire-frame Glasses
   - **Initial Task**: *Summarize EV supply-chain sources*
   - **Behavior**: Concentrated research, live task progression with source review logs.

2. **Nova (Market Analyst)**
   - **Station**: Trading Desk (Center-Top)
   - **Accent Color**: `#4cc38a` (Emerald Green)
   - **Accessory**: Magenta Hair Flower
   - **Initial Task**: *Track spreads on the watchlist*
   - **Behavior**: Scans trading desk ticker spreads, updates risk models, volume anomaly detection.

3. **Echo (Writing Agent)**
   - **Station**: Hallway Corridor & Meeting Room Board Table
   - **Accent Color**: `#e5a64f` (Warm Amber)
   - **Accessory**: Gold Knitted Scarf
   - **Initial Task**: *Heading to the 11:00 sync*
   - **Behavior**: Autonomous navigation loop between workstations and the meeting room table with sprite flipping, directional facing, and timed pauses.

4. **Sage (Office Manager)**
   - **Station**: Manager's Executive Office (Top-Right)
   - **Accent Color**: `#a995ff` (Lavender)
   - **Accessory**: Lavender Necktie
   - **Initial Task**: *Approve this week's plan*
   - **Behavior**: Oversees office operations, approves briefs, coordinates weekly schedules.

5. **Pixel (Engineering Agent)**
   - **Station**: Coffee Lounge & Snack Counter
   - **Accent Color**: `#ef7f93` (Coral Pink)
   - **Accessory**: DJ Headphones & Coffee Mug
   - **Initial Task**: *Wait for the next build*
   - **Behavior**: Cycles between sipping coffee in the lounge and idle reflection; switches into active build execution when assigned a task.

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18.0.0 or later, v24 recommended)
- npm (v9.0.0 or later)

### Installation
```bash
# Clone or navigate to the repository
cd MultiAgent

# Install dependencies
npm install
```

### Running Locally
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Building for Production
```bash
npm run build
```
Generates an optimized bundle in `dist/` with full TypeScript type checking.

---

## 🎮 Controls & Layout

- **Fullscreen Immersive View**: The office view covers 100% of the screen and stays stably fixed. Opening/closing the inspector or expanding the navigation rail will never resize, squeeze, or jerk the office view.
- **Overlapping Glassmorphism Panels**: The left navigation rail, top status bar, and right agent inspector float smoothly over the office canvas with modern backdrop-blur glassmorphism.
- **Pan the Office**: Click and drag anywhere on the office floor.
- **Zoom**: Scroll your mouse wheel, or use the `+` / `−` buttons in the bottom dock (70% to 350%).
- **Reset View**: Click the crosshair button in the bottom dock to center the camera at 100%.
- **Select Agent**: Click any agent on the office floor or click their avatar badge in the inspector roster.
- **Follow Agent**: Select an agent and click **Follow agent** in the inspector. The camera smoothly tracks the moving agent across the office with zero lag or stutter.
- **Assign Task**: Click **Assign task** in the inspector to open the task picker popover and assign a new job.
- **Simulation Speed**: Toggle between `Pause`, `0.5×`, `1×`, and `2×` in the dock.
- **View Overlays**:
  - `Paths`: Toggles visibility of the dotted office waypoint walkways.
  - `Labels`: Toggles floating character badges above agents.
- **Sidebar & Inspector Toggles**:
  - Collapse / Expand the left navigation rail via the bottom chevron button.
  - Hide / Reveal the right inspector panel via the top-bar button (slides in/out smoothly without resizing the office).
- **Interactive Navigation Modals**:
  - Clicking **Agents**, **Tasks**, **Markets**, or **Meetings** in the navigation rail opens dedicated detail modals with tracking shortcuts.

---

## 📋 Status & Future Enhancements

### Fully Implemented in this Migration:
- [x] 100% faithful port of the SVG office (rooms, glass walls, furniture, plants, shadows, sunbeams, animated steam, animated clock hands).
- [x] All 5 agents with custom outfits, accessories, and keyframe animations (`walk`, `type`, `coffee`, breathing, directional flips).
- [x] Zustand state stores for Agents, Camera, Simulation, and UI shell.
- [x] Interactive camera engine with exponential damping, smooth panning, wheel zooming, and agent tracking.
- [x] Live simulation clock with auto-updating analog clock hands and digital timestamps.
- [x] Task progression accumulator, completion triggers, green ring burst animation, toast notifications, and queue rotation.
- [x] Working navigation rail with expandable width and interactive views for Agents, Tasks, Markets, and Meetings.
- [x] Strict TypeScript types and zero production build warnings.

### Simulated / Roadmap for Future Phases:
- [ ] **A* Pathfinding**: Currently Echo follows a deterministic corridor route and other agents have assigned desks/break points. A future update will introduce dynamic multi-agent collision-avoiding A* pathfinding.
- [ ] **Phaser 2D Engine Integration**: Can optionally replace the pure SVG stage with a WebGL/Canvas Phaser 3 renderer for large-scale multi-agent performance (50+ agents).
- [ ] **Backend / LLM Integration**: Can connect agent state machines to real LLM inference engines (Gemini API, WebSockets, or local agents) to drive real autonomous decision-making.
