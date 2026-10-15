import { useEffect, useRef } from 'react';
import { useSimulationStore } from '../store/useSimulationStore';
import { useAgentStore } from '../store/useAgentStore';
import { useCameraStore } from '../store/useCameraStore';

// Echo's route waypoints: Workstation corridor <-> Meeting Room table
const ECHO_ROUTE: [number, number][] = [
  [330, 330],
  [330, 356],
  [630, 356],
  [630, 440],
];

export const useSimulationLoop = () => {
  const animFrameIdRef = useRef<number | null>(null);

  // High-performance mutable simulation state (bypasses React state overhead)
  const simStateRef = useRef({
    echo: {
      x: 330,
      y: 330,
      flipped: false,
      facingUp: false,
      waypointIndex: 0,
      direction: 1,
      waitTime: 0,
      status: 'Walking',
    },
    pixel: {
      coffeeCycle: 0,
      isCoffee: true,
    },
    cam: {
      x: 600,
      y: 380,
      z: 1.0,
    },
    lastTime: performance.now(),
    progressAcc: 0,
    simMinutes: 642, // 10:42 AM
    lastZoomLabel: 100,
    lastTimeLabel: '',
  });

  useEffect(() => {
    const s = simStateRef.current;
    s.lastTime = performance.now();
    s.simMinutes = useSimulationStore.getState().simMinutes;

    const frame = (now: number) => {
      const rawDelta = Math.min(0.05, (now - s.lastTime) / 1000);
      s.lastTime = now;

      const simSpeed = useSimulationStore.getState().speed;
      const simDelta = rawDelta * simSpeed;

      // 1. Time advancement
      if (simDelta > 0) {
        s.simMinutes += simDelta * 0.4;
      }
      const totalM = s.simMinutes;
      const hours = Math.floor((totalM / 60) % 24);
      const mins = Math.floor(totalM % 60);
      const timeStr = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;

      // 2. Direct DOM update for analog clock hands & top clock text
      const hh = document.getElementById('hh');
      const hm = document.getElementById('hm');
      if (hh && hm) {
        hh.setAttribute('transform', `translate(470 56) rotate(${((totalM / 60) % 12) * 30})`);
        hm.setAttribute('transform', `translate(470 56) rotate(${(totalM % 60) * 6})`);
      }
      if (timeStr !== s.lastTimeLabel) {
        s.lastTimeLabel = timeStr;
        const clkEl = document.getElementById('clk');
        if (clkEl) clkEl.textContent = timeStr;
        useSimulationStore.getState().advanceMinutes(0.0001); // keep store loosely synced
      }

      // 3. Echo's navigation state machine
      const e = s.echo;
      const echoEl = document.getElementById('ag-echo');
      const echoFl = echoEl ? echoEl.querySelector('.fl') : null;
      const echoSpn = echoEl ? echoEl.querySelector('.sp') : null;
      const echoLt = document.getElementById('lt-echo');

      if (simDelta > 0) {
        if (e.waitTime > 0) {
          e.waitTime -= simDelta;
          if (e.waitTime <= 0) {
            e.status = 'Walking';
            if (echoLt) echoLt.textContent = 'Walking';
            if (echoSpn) echoSpn.setAttribute('class', 'sp walk');
            useAgentStore.getState().updateAgent('echo', {
              animation: 'walk',
              statusText: 'Walking',
              state: 'WALKING',
            });
          }
        } else {
          const target = ECHO_ROUTE[e.waypointIndex + e.direction];
          if (target) {
            const dx = target[0] - e.x;
            const dy = target[1] - e.y;
            const dist = Math.hypot(dx, dy);
            const speedPx = 46 * simDelta;

            if (dist <= speedPx) {
              e.x = target[0];
              e.y = target[1];
              e.waypointIndex += e.direction;
              const isEnd = e.waypointIndex === ECHO_ROUTE.length - 1 || e.waypointIndex === 0;

              if (isEnd) {
                e.direction *= -1;
                e.waitTime = e.waypointIndex !== 0 ? 5 : 4;
                const inMeeting = e.waypointIndex !== 0;
                e.status = inMeeting ? 'In meeting' : 'Writing';
                if (echoLt) echoLt.textContent = e.status;
                if (echoSpn) echoSpn.setAttribute('class', 'sp idle');

                useAgentStore.getState().updateAgent('echo', {
                  x: e.x,
                  y: e.y,
                  animation: 'idle',
                  statusText: e.status,
                  state: inMeeting ? 'MEETING' : 'WORKING',
                });
              }
            } else {
              e.x += (dx / dist) * speedPx;
              e.y += (dy / dist) * speedPx;

              const flipped = dx < -0.1;
              const facingUp = dy < -0.1;

              if (echoFl) {
                echoFl.setAttribute('transform', flipped ? 'scale(-1 1)' : '');
              }
              if (echoSpn && facingUp !== e.facingUp) {
                e.facingUp = facingUp;
                echoSpn.classList.toggle('u', facingUp);
              }
            }
          }
        }

        // Direct hardware-accelerated transform update for Echo
        if (echoEl) {
          echoEl.setAttribute('transform', `translate(${e.x.toFixed(1)} ${e.y.toFixed(1)})`);
        }
      }

      // 4. Pixel's coffee break cycle (when not busy)
      const pxStore = useAgentStore.getState().agents.pixel;
      if (simDelta > 0 && !pxStore.isBusy) {
        s.pixel.coffeeCycle += simDelta;
        if (s.pixel.coffeeCycle > 8) {
          s.pixel.coffeeCycle = 0;
          s.pixel.isCoffee = !s.pixel.isCoffee;
          const pxEl = document.getElementById('ag-pixel');
          const pxSpn = pxEl ? pxEl.querySelector('.sp') : null;
          const pxLt = document.getElementById('lt-pixel');
          const newStatus = s.pixel.isCoffee ? 'Coffee break' : 'Idle';
          const newAnim = s.pixel.isCoffee ? 'coffee' : 'idle';

          if (pxLt) pxLt.textContent = newStatus;
          if (pxSpn) pxSpn.setAttribute('class', `sp ${newAnim}`);

          useAgentStore.getState().updateAgent('pixel', {
            statusText: newStatus,
            animation: newAnim,
            state: s.pixel.isCoffee ? 'BREAK' : 'IDLE',
          });
        }
      }

      // 5. Task progress accumulation (every 1 second)
      if (simDelta > 0) {
        s.progressAcc += simDelta;
        if (s.progressAcc >= 1) {
          s.progressAcc = 0;
          const agents = useAgentStore.getState().agents;
          const onToast = (msg: string) => {
            useSimulationStore.getState().addToast(msg);
          };

          for (const key of Object.keys(agents) as (keyof typeof agents)[]) {
            const agent = agents[key];
            if (
              agent.statusText === 'Coffee break' ||
              (agent.statusText === 'Idle' && !agent.isBusy)
            ) {
              continue;
            }

            const deltaP = 2.2 + (agent.isBusy ? 1.5 : 0);
            useAgentStore.getState().advanceTaskProgress(agent.id, deltaP, timeStr, onToast);
          }

          // Update active count badge in top bar
          const actCount = Object.values(agents).filter(
            a => a.statusText !== 'Coffee break' && a.statusText !== 'Idle'
          ).length;
          const actEl = document.getElementById('act');
          if (actEl) actEl.textContent = String(actCount);

          // Update inspector progress bar width and task description live
          const selId = useAgentStore.getState().selectedAgentId;
          const selAgent = agents[selId];
          if (selAgent) {
            const ipg = document.getElementById('ipg');
            if (ipg) ipg.style.width = `${selAgent.progress}%`;
            const it2 = document.getElementById('it2');
            if (it2 && it2.textContent !== selAgent.task) it2.textContent = selAgent.task;
          }
        }
      }

      // 6. Camera Follow & Butter-Smooth Interpolation
      const camStore = useCameraStore.getState();
      const followId = camStore.followAgentId;
      let tgX = camStore.targetX;
      let tgY = camStore.targetY;
      let tgZ = camStore.targetZ;

      if (followId) {
        // Track following agent seamlessly
        if (followId === 'echo') {
          tgX = e.x;
          tgY = e.y;
        } else {
          const a = useAgentStore.getState().agents[followId];
          if (a) {
            tgX = a.x;
            tgY = a.y;
          }
        }
        tgZ = Math.max(1.9, tgZ);
      }

      // Exponential damping formula: cam += (target - cam) * (1 - 0.001^rd)
      const k = 1 - Math.pow(0.001, rawDelta);
      s.cam.x += (tgX - s.cam.x) * k;
      s.cam.y += (tgY - s.cam.y) * k;
      s.cam.z += (tgZ - s.cam.z) * k;

      // 7. Direct SVG ViewBox Rendering
      const svg = document.getElementById('world') as SVGSVGElement | null;
      const stage = document.getElementById('stage');
      if (svg && stage) {
        const r = stage.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
          const fit = Math.min(r.width / 1200, r.height / 760);
          const b = Math.max(0.001, fit * s.cam.z);
          const w = r.width / b;
          const h = r.height / b;
          const vx = s.cam.x - w / 2;
          const vy = s.cam.y - h / 2;

          svg.setAttribute('viewBox', `${vx.toFixed(1)} ${vy.toFixed(1)} ${w.toFixed(1)} ${h.toFixed(1)}`);
        }
      }

      // 8. Update zoom label
      const zoomPct = Math.round(s.cam.z * 100);
      if (zoomPct !== s.lastZoomLabel) {
        s.lastZoomLabel = zoomPct;
        const zl = document.getElementById('zl');
        if (zl) zl.textContent = `${zoomPct}%`;
      }

      animFrameIdRef.current = requestAnimationFrame(frame);
    };

    animFrameIdRef.current = requestAnimationFrame(frame);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, []);
};
