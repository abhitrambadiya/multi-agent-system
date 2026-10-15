import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// ─── Icons (inline SVGs) ──────────────────────────────────────────────────────
const Icon = ({ path, size = 16, color = 'currentColor', className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={{ flexShrink: 0 }}
  >
    <path d={path} />
  </svg>
);

const ICONS = {
  check: 'M20 6L9 17l-5-5',
  x: 'M18 6L6 18M6 6l12 12',
  alert: 'M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
  loader: 'M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83',
  cpu: 'M4 4h16v16H4zM9 9h6v6H9zM9 1v3m6-3v3M9 20v3m6-3v3M1 9h3m-3 6h3M20 9h3m-3 6h3',
  play: 'M5 3l14 9-14 9V3z',
  bot: 'M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4zM4 14h16M4 18h16M7 10v4M17 10v4',
  wrench: 'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z',
  package: 'M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
  dollar: 'M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  user: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6',
  sparkle: 'M12 3L9.5 9.5 3 12l6.5 2.5L12 21l2.5-6.5L21 12l-6.5-2.5z',
  info: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 16v-4M12 8h.01',
  building: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z',
  database: 'M4 6c0 1.66 3.58 3 8 3s8-1.34 8-3-3.58-3-8-3-8 1.34-8 3zm0 6c0 1.66 3.58 3 8 3s8-1.34 8-3m-16 6c0 1.66 3.58 3 8 3s8-1.34 8-3',
  globe: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z',
  externalLink: 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3',
};

const SUGGESTED_PROMPTS = [
  "How many laptops will we need to reach the safety threshold?",
  "We have only 2 laptops left, but the IT department needs 12 by next week.",
  "How many laptops are there in the inventory?",
  "Who are the suppliers for Laptop Stand?",
  "How much budget is left?",
  "Emergency purchase: 150 enterprise laptops required immediately.",
];

const INTENT_LABELS = {
  inventory_query: { label: 'Inventory Query', color: '#0284c7', bg: '#e0f2fe', icon: 'package' },
  supplier_query: { label: 'Supplier Query', color: '#0d9488', bg: '#ccfbf1', icon: 'building' },
  budget_query: { label: 'Budget Query', color: '#16a34a', bg: '#dcfce7', icon: 'dollar' },
  procurement_request: { label: 'Procurement Request', color: '#6366f1', bg: '#ede9fe', icon: 'send' },
  purchase_order_query: { label: 'Purchase Order Query', color: '#d97706', bg: '#fef3c7', icon: 'file' },
  risk_query: { label: 'Risk & Policy Query', color: '#ea580c', bg: '#ffedd5', icon: 'shield' },
  clarification_required: { label: 'Clarification Needed', color: '#7c3aed', bg: '#f5f3ff', icon: 'info' },
  out_of_scope: { label: 'Out of Scope', color: '#dc2626', bg: '#fee2e2', icon: 'x' },
};

export const getSupplierName = (supplier) => {
  if (!supplier) return '—';
  if (typeof supplier === 'string') return supplier;
  if (typeof supplier === 'object') {
    return supplier.name || supplier.supplier || '—';
  }
  return String(supplier);
};

// ─── UI Components ────────────────────────────────────────────────────────────

const Badge = ({ label, status }) => {
  const styles = {
    SUCCESS: { bg: '#dcfce7', border: '#86efac', text: '#15803d' },
    QUERY_ANSWERED: { bg: '#e0f2fe', border: '#7dd3fc', text: '#0369a1' },
    PAUSED: { bg: '#fef3c7', border: '#fcd34d', text: '#b45309' },
    PAUSED_FOR_APPROVAL: { bg: '#fef3c7', border: '#fcd34d', text: '#b45309' },
    BLOCKED: { bg: '#fee2e2', border: '#fca5a5', text: '#b91c1c' },
    REJECTED: { bg: '#ffedd5', border: '#fdba74', text: '#c2410c' },
    NEEDS_CLARIFICATION: { bg: '#ede9fe', border: '#c4b5fd', text: '#6d28d9' },
    FAILED: { bg: '#ffe4e6', border: '#fda4af', text: '#be123c' },
    RUNNING: { bg: '#eff6ff', border: '#93c5fd', text: '#1d4ed8' },
  };
  const s = styles[status] || { bg: '#f1f5f9', border: '#cbd5e1', text: '#475569' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px',
      borderRadius: 999, fontSize: 10, fontWeight: 700, letterSpacing: '0.04em',
      background: s.bg, border: `1px solid ${s.border}`, color: s.text,
      textTransform: 'uppercase'
    }}>
      {label}
    </span>
  );
};

const LLMPill = ({ mode }) => {
  const isLive = mode === 'LIVE_LLM';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 7px',
      borderRadius: 999, fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
      background: isLive ? '#eff6ff' : '#f8fafc',
      border: `1px solid ${isLive ? '#93c5fd' : '#cbd5e1'}`,
      color: isLive ? '#1d4ed8' : '#475569'
    }}>
      {isLive ? '⚡ LIVE GEMINI' : '⚙ DETERMINISTIC'}
    </span>
  );
};

const Card = ({ children, style = {} }) => (
  <div style={{
    background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)', ...style
  }}>
    {children}
  </div>
);

const SectionTitle = ({ children, icon }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
    <span style={{ color: '#6366f1', display: 'flex' }}>
      <Icon path={ICONS[icon]} size={16} />
    </span>
    <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', color: '#475569', textTransform: 'uppercase' }}>
      {children}
    </span>
  </div>
);

// ─── Main Application ─────────────────────────────────────────────────────────

export default function App() {
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState('');
  const [state, setState] = useState(null);
  const [overallStatus, setOverallStatus] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const [needsClarification, setNeedsClarification] = useState(false);
  const [clarificationQ, setClarificationQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState({ online: false, liveLLM: false, provider: null, model: null });
  const [auditOpen, setAuditOpen] = useState(false);
  const [customQtyInput, setCustomQtyInput] = useState('');
  const [customMode, setCustomMode] = useState('PURCHASE_QUANTITY');
  const textareaRef = useRef(null);

  useEffect(() => {
    const check = async () => {
      try {
        const r = await axios.get(`${API_URL}/api/health`);
        setHealth({
          online: true,
          liveLLM: r.data.live_llm_configured,
          provider: r.data.llm_provider,
          model: r.data.llm_model,
        });
      } catch {
        setHealth({ online: false, liveLLM: false, provider: null, model: null });
      }
    };
    check();
    const iv = setInterval(check, 15000);
    return () => clearInterval(iv);
  }, []);

  const reset = () => {
    setState(null);
    setOverallStatus('');
    setIsPaused(false);
    setNeedsClarification(false);
    setClarificationQ('');
    setError('');
    setThreadId('');
    setCustomQtyInput('');
  };

  const runWorkflow = async (overridePrompt = null) => {
    const textToRun = overridePrompt || input;
    if (!textToRun.trim()) return;
    setLoading(true);
    reset();
    try {
      const res = await axios.post(`${API_URL}/api/workflow/run`, { business_event: textToRun.trim() });
      setThreadId(res.data.thread_id);
      setOverallStatus(res.data.status);
      setIsPaused(res.data.is_paused);
      setNeedsClarification(res.data.needs_clarification || false);
      setClarificationQ(res.data.clarification_question || '');
      setState(res.data.state);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error executing request');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigure = async ({ strategy, quantity, supplierName, customTargetType }) => {
    if (!threadId) return;
    setLoading(true);
    setError('');
    try {
      const payload = {
        thread_id: threadId,
        selected_strategy: strategy !== undefined ? strategy : state?.selected_strategy,
        final_order_quantity: quantity !== undefined ? Number(quantity) : state?.final_order_quantity,
        selected_supplier_name: supplierName !== undefined ? supplierName : state?.selected_supplier_name,
        custom_target_type: customTargetType || (strategy === 'custom' ? customMode : undefined),
      };
      const res = await axios.post(`${API_URL}/api/workflow/configure`, payload);
      setOverallStatus(res.data.status);
      setIsPaused(res.data.is_paused);
      setState(res.data.state);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error updating configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (action) => {
    if (!threadId) return;
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_URL}/api/workflow/approve`, { thread_id: threadId, action });
      setOverallStatus(res.data.status);
      setIsPaused(false);
      setState(res.data.state);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || `Error processing ${action}`);
    } finally {
      setLoading(false);
    }
  };

  const traces = state?.agent_traces || [];
  const proc = state?.procurement_result || {};
  const finance = state?.finance_result || {};
  const risk = state?.risk_result || {};
  const exec = state?.execution_result;
  const queryResult = state?.query_result;
  const intentKey = state?.intent;
  const intentMeta = INTENT_LABELS[intentKey] || { label: intentKey || 'Processing', color: '#6366f1', bg: '#ede9fe', icon: 'cpu' };
  const isProcurementFlow = intentKey === 'procurement_request';

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: "'Inter', system-ui, -apple-system, sans-serif" }}>

      {/* ─── Header ─────────────────────────────────────────────────────── */}
      <div style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '0 32px' }}>
        <div style={{ maxWidth: 1160, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon path={ICONS.cpu} size={18} color="#fff" />
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
                AI-EOS
              </div>
              <div style={{ fontSize: 11, color: '#64748b', fontWeight: 500, marginTop: -2 }}>
                Autonomous Enterprise Operating System
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Database pill */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 11px', borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <Icon path={ICONS.database} size={12} color="#0284c7" />
              <span style={{ fontSize: 11, fontWeight: 600, color: '#0369a1' }}>PostgreSQL</span>
            </div>

            {/* Backend status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 8, background: health.online ? '#f0fdf4' : '#fef2f2', border: `1px solid ${health.online ? '#bbf7d0' : '#fecaca'}` }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: health.online ? '#22c55e' : '#ef4444', display: 'inline-block' }} />
              <span style={{ fontSize: 11, fontWeight: 600, color: health.online ? '#15803d' : '#dc2626' }}>
                {health.online ? 'Online' : 'Offline'}
              </span>
            </div>

            {/* LLM status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 8, background: health.liveLLM ? '#eff6ff' : '#f8fafc', border: `1px solid ${health.liveLLM ? '#bfdbfe' : '#e2e8f0'}` }}>
              <Icon path={health.liveLLM ? ICONS.sparkle : ICONS.cpu} size={13} color={health.liveLLM ? '#3b82f6' : '#94a3b8'} />
              <span style={{ fontSize: 11, fontWeight: 600, color: health.liveLLM ? '#1d4ed8' : '#64748b' }}>
                {health.liveLLM ? `${health.provider || 'Gemini'} · ${health.model || 'gemini-3.5-flash'}` : 'Deterministic Fallback'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Main Layout ────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 1160, margin: '0 auto', padding: '24px', display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24 }}>

        {/* ─── LEFT COLUMN ─────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Natural Language Command Bar */}
          <Card style={{ padding: 22 }}>
            <SectionTitle icon="send">Natural Language Intent Router</SectionTitle>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) runWorkflow(); }}
              placeholder="Ask a question or enter a procurement instruction in natural language…&#10;• 'How many laptops will we need to reach the safety threshold?'&#10;• 'We have only 2 laptops left, but the IT department needs 12 by next week.'&#10;• 'Who are the suppliers for Laptop Stand?'"
              style={{
                width: '100%', minHeight: 90, padding: '12px 14px', borderRadius: 8,
                border: '1.5px solid #e2e8f0', fontSize: 14, fontFamily: 'inherit',
                color: '#0f172a', resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box',
                outline: 'none', transition: 'border-color .2s',
                background: '#fafbfc',
              }}
              onFocus={e => { e.target.style.borderColor = '#6366f1'; }}
              onBlur={e => { e.target.style.borderColor = '#e2e8f0'; }}
            />

            {/* Quick Suggestions Chips */}
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
                Prompt Suggestions:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {SUGGESTED_PROMPTS.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(p); runWorkflow(p); }}
                    style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 500,
                      background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#475569',
                      cursor: 'pointer', transition: 'all .15s', textAlign: 'left',
                    }}
                    onMouseEnter={e => { e.target.style.background = '#e8f0fe'; e.target.style.borderColor = '#a5b4fc'; e.target.style.color = '#4338ca'; }}
                    onMouseLeave={e => { e.target.style.background = '#f1f5f9'; e.target.style.borderColor = '#e2e8f0'; e.target.style.color = '#475569'; }}
                  >
                    {p.length > 55 ? p.slice(0, 52) + '…' : p}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
              {state && (
                <button
                  onClick={reset}
                  style={{ padding: '8px 16px', borderRadius: 8, fontSize: 12, fontWeight: 600, background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#64748b', cursor: 'pointer' }}
                >
                  Clear Screen
                </button>
              )}
              <button
                onClick={() => runWorkflow()}
                disabled={loading || !input.trim()}
                style={{
                  marginLeft: 'auto', padding: '10px 24px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                  background: loading || !input.trim() ? '#c7d2fe' : 'linear-gradient(135deg,#6366f1,#4f46e5)',
                  border: 'none', color: '#fff', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8, boxShadow: '0 2px 8px rgba(99,102,241,.25)',
                  transition: 'all .2s',
                }}
              >
                {loading ? (
                  <><Icon path={ICONS.loader} size={15} color="#fff" className="spin" />Routing Intent…</>
                ) : (
                  <><Icon path={ICONS.play} size={14} color="#fff" />Submit Request</>
                )}
              </button>
            </div>
          </Card>

          {/* Error Banner */}
          {error && (
            <div style={{ padding: '12px 16px', borderRadius: 8, background: '#fff1f2', border: '1px solid #fecdd3', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <Icon path={ICONS.x} size={16} color="#e11d48" />
              <span style={{ fontSize: 13, color: '#9f1239', fontWeight: 500 }}>{error}</span>
            </div>
          )}

          {/* Clarification Needed Card */}
          {needsClarification && clarificationQ && (
            <div style={{ padding: 20, borderRadius: 10, background: '#faf5ff', border: '1.5px solid #c4b5fd' }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 10 }}>
                <Icon path={ICONS.info} size={18} color="#7c3aed" />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#5b21b6', marginBottom: 4 }}>Clarification Required</div>
                  <div style={{ fontSize: 13, color: '#4c1d95', lineHeight: 1.5 }}>{clarificationQ}</div>
                </div>
              </div>
              <div style={{ fontSize: 11, color: '#7c3aed', fontStyle: 'italic' }}>
                Please provide the specific product and quantity in the prompt above.
              </div>
            </div>
          )}

          {/* ─── Inventory / Query Result Card (Section A) ───────────────── */}
          {queryResult && !isProcurementFlow && (
            <Card style={{ padding: 22, border: '1.5px solid #bae6fd', background: '#f0f9ff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon path={ICONS.database} size={18} color="#0284c7" />
                  <span style={{ fontSize: 13, fontWeight: 800, color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Database Query Result ({intentMeta.label})
                  </span>
                </div>
                <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 6, background: '#e0f2fe', color: '#0284c7', border: '1px solid #7dd3fc' }}>
                  {queryResult.data_source || 'PostgreSQL'}
                </span>
              </div>

              <div style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', marginBottom: 14, lineHeight: 1.5 }}>
                {queryResult.summary}
              </div>

              {/* Safety Threshold Replenishment breakdown (Section A requirement) */}
              {queryResult.units_needed_for_safety !== undefined && (
                <div style={{ background: '#fff', padding: 16, borderRadius: 10, border: '1.5px solid #0284c7', marginTop: 10, marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <Icon path={ICONS.shield} size={16} color="#0284c7" />
                    <span style={{ fontSize: 12, fontWeight: 800, color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Safety Threshold Shortfall Analysis
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                    <div style={{ padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: 10, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Current Usable Stock</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#334155', marginTop: 4 }}>{queryResult.current_stock} <span style={{ fontSize: 12, fontWeight: 600 }}>units</span></div>
                      <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>In-stock usable inventory</div>
                    </div>
                    <div style={{ padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: 10, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Safety Threshold</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#334155', marginTop: 4 }}>{queryResult.minimum_stock} <span style={{ fontSize: 12, fontWeight: 600 }}>units</span></div>
                      <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>Configured minimum stock buffer</div>
                    </div>
                    <div style={{ padding: 12, borderRadius: 8, background: '#eff6ff', border: '1.5px solid #3b82f6' }}>
                      <div style={{ fontSize: 10, color: '#1d4ed8', fontWeight: 700, textTransform: 'uppercase' }}>Additional Units Needed</div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: '#1d4ed8', marginTop: 2 }}>{queryResult.units_needed_for_safety} <span style={{ fontSize: 13, fontWeight: 600 }}>units</span></div>
                      <div style={{ fontSize: 10, color: '#2563eb', fontWeight: 600, marginTop: 2 }}>max(0, {queryResult.minimum_stock} - {queryResult.current_stock})</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Standard Inventory Count Grid */}
              {queryResult.current_stock !== undefined && queryResult.units_needed_for_safety === undefined && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, background: '#fff', padding: 12, borderRadius: 8, border: '1px solid #e0f2fe' }}>
                  <div>
                    <div style={{ fontSize: 9, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Product</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a' }}>{queryResult.product}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Current Stock</div>
                    <div style={{ fontSize: 14, fontWeight: 800, color: '#0284c7' }}>{queryResult.current_stock} units</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Safety Threshold</div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#334155' }}>{queryResult.minimum_stock} units</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Location</div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#334155' }}>{queryResult.location}</div>
                  </div>
                </div>
              )}

              {/* Supplier query table */}
              {queryResult.quotes && (
                <div style={{ background: '#fff', borderRadius: 8, overflow: 'hidden', border: '1px solid #e0f2fe', marginTop: 10 }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                    <thead>
                      <tr style={{ background: '#f8fafc' }}>
                        <th style={{ padding: '6px 10px', textAlign: 'left', color: '#64748b' }}>Supplier</th>
                        <th style={{ padding: '6px 10px', textAlign: 'left', color: '#64748b' }}>Unit Price</th>
                        <th style={{ padding: '6px 10px', textAlign: 'left', color: '#64748b' }}>Lead Time</th>
                        <th style={{ padding: '6px 10px', textAlign: 'left', color: '#64748b' }}>Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {queryResult.quotes.map((q, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '6px 10px', fontWeight: 600 }}>{q.name}</td>
                          <td style={{ padding: '6px 10px', color: '#0f172a', fontWeight: 700 }}>₹{q.unit_price?.toLocaleString()}</td>
                          <td style={{ padding: '6px 10px', color: '#64748b' }}>{q.delivery_days} days</td>
                          <td style={{ padding: '6px 10px', color: '#64748b' }}>★ {q.rating}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* ─── Buyer Decision Center: Purchasing Strategies (Section B) ─── */}
          {isProcurementFlow && state?.available_strategies && (
            <Card style={{ padding: 22, border: '1.5px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <SectionTitle icon="package">Select Purchasing Strategy</SectionTitle>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>
                  Active Strategy: <strong style={{ color: '#4f46e5' }}>{state?.selected_strategy?.replace(/_/g, ' ').toUpperCase()}</strong> ({state?.final_order_quantity} units)
                </span>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                {state.available_strategies.map((strat) => {
                  const isSelected = state.selected_strategy === strat.strategy;
                  return (
                    <div
                      key={strat.strategy}
                      style={{
                        padding: 14, borderRadius: 10,
                        background: isSelected ? '#f5f3ff' : '#fff',
                        border: `2px solid ${isSelected ? '#6366f1' : '#e2e8f0'}`,
                        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                        boxShadow: isSelected ? '0 4px 12px rgba(99,102,241,0.12)' : 'none',
                        transition: 'all .2s'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <span style={{ fontSize: 12, fontWeight: 800, color: isSelected ? '#4338ca' : '#0f172a' }}>
                            {strat.name}
                          </span>
                          {isSelected && (
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#6366f1', color: '#fff' }}>
                              ACTIVE
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 20, fontWeight: 800, color: isSelected ? '#4f46e5' : '#1e293b', marginBottom: 6 }}>
                          {strat.strategy === 'custom' && isSelected ? state.final_order_quantity : strat.quantity} <span style={{ fontSize: 12, fontWeight: 600 }}>units</span>
                        </div>
                        <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.4, marginBottom: 8 }}>
                          {strat.description}
                        </div>
                        <div style={{ fontSize: 10, color: '#64748b', background: '#f8fafc', padding: '6px 8px', borderRadius: 6, border: '1px solid #f1f5f9', lineHeight: 1.4 }}>
                          <strong>Consequence:</strong> {strat.consequences}
                        </div>
                      </div>

                      <div style={{ marginTop: 12 }}>
                        {strat.strategy === 'custom' && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 8 }}>
                            <div style={{ display: 'flex', gap: 4, background: '#f1f5f9', padding: 2, borderRadius: 6 }}>
                              <button
                                type="button"
                                onClick={() => setCustomMode('PURCHASE_QUANTITY')}
                                style={{
                                  flex: 1, padding: '4px 6px', fontSize: 10, fontWeight: 700, borderRadius: 4, border: 'none',
                                  background: customMode === 'PURCHASE_QUANTITY' ? '#fff' : 'transparent',
                                  color: customMode === 'PURCHASE_QUANTITY' ? '#4f46e5' : '#64748b',
                                  boxShadow: customMode === 'PURCHASE_QUANTITY' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                                  cursor: 'pointer'
                                }}
                              >
                                Purchase Qty
                              </button>
                              <button
                                type="button"
                                onClick={() => setCustomMode('TARGET_TOTAL_STOCK')}
                                style={{
                                  flex: 1, padding: '4px 6px', fontSize: 10, fontWeight: 700, borderRadius: 4, border: 'none',
                                  background: customMode === 'TARGET_TOTAL_STOCK' ? '#fff' : 'transparent',
                                  color: customMode === 'TARGET_TOTAL_STOCK' ? '#4f46e5' : '#64748b',
                                  boxShadow: customMode === 'TARGET_TOTAL_STOCK' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                                  cursor: 'pointer'
                                }}
                              >
                                Target Total Stock
                              </button>
                            </div>
                            <div style={{ display: 'flex', gap: 6 }}>
                              <input
                                type="number"
                                min="1"
                                placeholder={customMode === 'PURCHASE_QUANTITY' ? 'Units to order' : 'Desired total stock'}
                                value={customQtyInput}
                                onChange={(e) => setCustomQtyInput(e.target.value)}
                                style={{
                                  width: '60%', padding: '5px 8px', borderRadius: 6, border: '1px solid #cbd5e1',
                                  fontSize: 12, outline: 'none'
                                }}
                              />
                              <button
                                onClick={() => {
                                  const q = parseInt(customQtyInput, 10);
                                  if (q > 0) handleConfigure({ strategy: 'custom', quantity: q, customTargetType: customMode });
                                }}
                                style={{
                                  flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                                  background: '#4f46e5', color: '#fff', border: 'none', cursor: 'pointer'
                                }}
                              >
                                Set
                              </button>
                            </div>
                            <div style={{ fontSize: 9, color: '#64748b' }}>
                              {customMode === 'PURCHASE_QUANTITY' 
                                ? 'Direct purchase quantity.' 
                                : `Target inventory level in warehouse (usable stock: ${state?.current_stock ?? '—'}).`}
                            </div>
                          </div>
                        )}
                        <button
                          onClick={() => handleConfigure({ strategy: strat.strategy, quantity: strat.quantity, customTargetType: customMode })}
                          disabled={loading || (isSelected && strat.strategy !== 'custom')}
                          style={{
                            width: '100%', padding: '7px 0', borderRadius: 6, fontSize: 11, fontWeight: 700,
                            background: isSelected ? '#e0e7ff' : '#f8fafc',
                            border: `1px solid ${isSelected ? '#a5b4fc' : '#cbd5e1'}`,
                            color: isSelected ? '#4338ca' : '#475569',
                            cursor: loading || isSelected ? 'default' : 'pointer'
                          }}
                        >
                          {isSelected ? '✓ Strategy Selected' : 'Select Strategy'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* ─── Buyer Decision Center: Multi-Vendor Evaluation (Section C) ── */}
          {isProcurementFlow && state?.eligible_quotes && state.eligible_quotes.length > 0 && (
            <Card style={{ padding: 22, border: '1.5px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <SectionTitle icon="building">Eligible Supplier Quotes ({state.eligible_quotes.length} from PostgreSQL)</SectionTitle>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: -10 }}>
                    {state.eligible_quotes.length < 3 ? (
                      <span style={{ color: '#d97706', fontWeight: 600 }}>
                        ⚠️ Only {state.eligible_quotes.length} eligible suppliers found in database (target: 3 options).
                      </span>
                    ) : (
                      <span>3 eligible suppliers verified against corporate catalog records.</span>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Order Volume</div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: '#4f46e5' }}>{state.final_order_quantity} units</div>
                </div>
              </div>

              {/* AI Recommendation Banner */}
              {state.recommended_supplier && (
                <div style={{ padding: '8px 12px', borderRadius: 8, background: '#eff6ff', border: '1px solid #bfdbfe', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#1d4ed8' }}>
                    <Icon path={ICONS.sparkle} size={14} color="#2563eb" />
                    <span><strong>AI Recommendation:</strong> {getSupplierName(state.recommended_supplier)} (Transparent trade-off evaluation)</span>
                  </div>
                  <span style={{ fontSize: 10, color: '#64748b' }}>
                    Selection Mode: <strong>{state.supplier_selection_mode || 'RECOMMENDED'}</strong>
                  </span>
                </div>
              )}

              {/* Supplier Quote Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {state.eligible_quotes.map((q, idx) => {
                  const isChosen = state.selected_supplier_name === q.name || getSupplierName(proc.supplier) === q.name || getSupplierName(state.selected_supplier) === q.name;
                  const isRecommended = getSupplierName(state.recommended_supplier) === q.name;
                  const total = q.total_price || (q.unit_price * (state.final_order_quantity || 1));
                  return (
                    <div
                      key={q.name || idx}
                      style={{
                        padding: '12px 14px', borderRadius: 8,
                        background: isChosen ? '#f0fdf4' : '#fff',
                        border: `1.5px solid ${isChosen ? '#22c55e' : '#e2e8f0'}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12
                      }}
                    >
                      <div style={{ flex: 2 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 13, fontWeight: 800, color: '#0f172a' }}>{q.name}</span>
                          {isRecommended && (
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#dbeafe', color: '#1e40af', border: '1px solid #bfdbfe' }}>
                              AI Recommended
                            </span>
                          )}
                          {isChosen && (
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#dcfce7', color: '#15803d', border: '1px solid #86efac' }}>
                              ✓ Buyer Selection
                            </span>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: 12, marginTop: 4, fontSize: 11, color: '#64748b' }}>
                          <span>Lead time: <strong>{q.delivery_days} days</strong></span>
                          <span>Rating: <strong>★ {q.rating}</strong></span>
                          <span>Reliability: <strong>{Math.round((q.reliability_score || 0.95) * 100)}%</strong></span>
                          <span>Stock: <strong style={{ color: q.in_stock ? '#16a34a' : '#dc2626' }}>{q.in_stock ? 'In Stock' : 'Out of Stock'}</strong></span>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right', flex: 1 }}>
                        <div style={{ fontSize: 11, color: '#64748b' }}>₹{q.unit_price?.toLocaleString()} {q.currency || 'INR'} / unit</div>
                        <div style={{ fontSize: 15, fontWeight: 800, color: total > 100000 ? '#dc2626' : '#0f172a' }}>
                          ₹{total?.toLocaleString()}
                        </div>
                        {total > 100000 && <span style={{ fontSize: 9, color: '#dc2626', fontWeight: 700 }}>Exceeds ₹100k cap</span>}
                      </div>

                      <div>
                        <button
                          onClick={() => handleConfigure({ supplierName: q.name })}
                          disabled={loading || isChosen}
                          style={{
                            padding: '7px 14px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                            background: isChosen ? '#dcfce7' : '#f8fafc',
                            border: `1.5px solid ${isChosen ? '#86efac' : '#cbd5e1'}`,
                            color: isChosen ? '#15803d' : '#334155',
                            cursor: loading || isChosen ? 'default' : 'pointer'
                          }}
                        >
                          {isChosen ? 'Active Supplier' : 'Select Supplier'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {proc.decision_rationale && (
                <div style={{ marginTop: 12, fontSize: 11, color: '#475569', background: '#f8fafc', padding: '8px 12px', borderRadius: 6, border: '1px solid #e2e8f0', lineHeight: 1.5 }}>
                  <strong>Trade-off Rationale:</strong> {proc.decision_rationale}
                </div>
              )}
            </Card>
          )}

          {/* ─── Web Research Agent: Online Marketplace Price Comparison ── */}
          {isProcurementFlow && (
            <Card style={{ padding: 22, border: '1.5px solid #93c5fd', background: '#f8fafc' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <SectionTitle icon="globe">Live Online Marketplace Comparison (Web Research Agent)</SectionTitle>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: -10 }}>
                    {state?.web_offers && state.web_offers.length > 0 ? (
                      <span>Discovered {state.web_offers.length} public online listings compared against internal catalog quotes.</span>
                    ) : state?.web_research_status === 'SKIPPED' ? (
                      <span style={{ color: '#64748b' }}>Web research skipped (internal suppliers requested or research disabled).</span>
                    ) : (
                      <span>No online listings matched product specifications.</span>
                    )}
                  </div>
                </div>
                {state?.web_offers && state.web_offers.length > 0 && (
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 999, background: '#dbeafe', color: '#1e40af', border: '1px solid #bfdbfe' }}>
                      🌐 {state.web_offers.length} Live Offers
                    </span>
                  </div>
                )}
              </div>

              {/* Trade-off Comparison Summary Banner */}
              {proc.online_comparison_summary && (
                <div style={{ padding: '9px 12px', borderRadius: 8, background: '#eff6ff', border: '1px solid #bfdbfe', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: '#1e40af', lineHeight: 1.5 }}>
                  <Icon path={ICONS.sparkle} size={15} color="#2563eb" />
                  <span><strong>AI Market Intelligence:</strong> {proc.online_comparison_summary}</span>
                </div>
              )}

              {/* Online Offer Cards */}
              {state?.web_offers && state.web_offers.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {state.web_offers.map((offer, idx) => {
                    const isChosen = state?.selected_supplier_name === offer.name || getSupplierName(proc.supplier) === offer.name || (state?.selected_supplier && state.selected_supplier.name === offer.name);
                    const total = offer.total_price || (offer.unit_price ? offer.unit_price * (state.final_order_quantity || 1) : 0);
                    const isVerified = offer.verification_status === 'VERIFIED';
                    return (
                      <div
                        key={offer.offer_id || idx}
                        style={{
                          padding: '13px 15px', borderRadius: 8,
                          background: isChosen ? '#eff6ff' : '#fff',
                          border: `1.5px solid ${isChosen ? '#3b82f6' : '#e2e8f0'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12
                        }}
                      >
                        <div style={{ flex: 2 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 10, fontWeight: 800, padding: '2px 7px', borderRadius: 999, background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd' }}>
                              {offer.source_name}
                            </span>
                            <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{offer.model || offer.title}</span>
                            {isVerified ? (
                              <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#dcfce7', color: '#15803d', border: '1px solid #86efac' }}>
                                ✓ Verified Offer
                              </span>
                            ) : (
                              <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#fef3c7', color: '#b45309', border: '1px solid #fcd34d' }}>
                                ⚠️ Unverified Price
                              </span>
                            )}
                            {isChosen && (
                              <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 999, background: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd' }}>
                                ✓ Buyer Selected (Online)
                              </span>
                            )}
                          </div>

                          <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                            {offer.title}
                          </div>

                          {/* Metadata and Specs */}
                          <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 11, color: '#64748b', flexWrap: 'wrap', alignItems: 'center' }}>
                            <span>Lead time: <strong>{offer.delivery_estimate || 'Unknown'}</strong></span>
                            <span>Stock: <strong style={{ color: offer.in_stock ? '#16a34a' : '#dc2626' }}>{offer.availability || 'Unknown'}</strong></span>
                            {offer.rating && <span>Rating: <strong>★ {offer.rating}</strong></span>}
                            <span>Shipping: <strong>{offer.shipping_note || 'Unverified'}</strong></span>
                            {offer.url && (
                              <a
                                href={offer.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: 3, color: '#2563eb', fontSize: 11, fontWeight: 600, textDecoration: 'none' }}
                              >
                                View Listing <Icon path={ICONS.externalLink} size={11} color="#2563eb" />
                              </a>
                            )}
                          </div>

                          {/* Missing / Unverified Information Warning */}
                          {offer.unverified_fields && offer.unverified_fields.length > 0 && (
                            <div style={{ fontSize: 10, color: '#b45309', marginTop: 4 }}>
                              ⚠️ Unverified at source: {offer.unverified_fields.join(', ')} (Checkout calculation required)
                            </div>
                          )}
                        </div>

                        <div style={{ textAlign: 'right', flex: 1 }}>
                          <div style={{ fontSize: 11, color: '#64748b' }}>
                            {offer.unit_price ? `₹${offer.unit_price?.toLocaleString()} ${offer.currency || 'INR'} / unit` : 'Price unlisted'}
                          </div>
                          <div style={{ fontSize: 15, fontWeight: 800, color: total > 100000 ? '#dc2626' : '#0f172a' }}>
                            {total ? `₹${total?.toLocaleString()}` : '—'}
                          </div>
                          {total > 100000 && <span style={{ fontSize: 9, color: '#dc2626', fontWeight: 700 }}>Exceeds ₹100k cap</span>}
                          {offer.retrieved_at && (
                            <div style={{ fontSize: 9, color: '#94a3b8', marginTop: 2 }}>
                              Retrieved: {new Date(offer.retrieved_at).toLocaleTimeString()}
                            </div>
                          )}
                        </div>

                        <div>
                          <button
                            onClick={() => handleConfigure({ supplierName: offer.name || offer.offer_id })}
                            disabled={loading || isChosen || !offer.unit_price}
                            style={{
                              padding: '7px 14px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                              background: isChosen ? '#dbeafe' : '#f8fafc',
                              border: `1.5px solid ${isChosen ? '#93c5fd' : '#cbd5e1'}`,
                              color: isChosen ? '#1d4ed8' : '#334155',
                              cursor: loading || isChosen || !offer.unit_price ? 'default' : 'pointer'
                            }}
                          >
                            {isChosen ? 'Selected (Online)' : 'Select This Offer'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: '#64748b', textAlign: 'center', padding: '16px 0' }}>
                  No online marketplace offers available for this query.
                </div>
              )}
            </Card>
          )}

          {/* ─── Multi-Agent Execution Pipeline ───────────────────────── */}
          {(state || loading) && (
            <Card style={{ padding: 22 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <SectionTitle icon="bot">Multi-Agent Execution Pipeline</SectionTitle>
                {state?.intent && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 9px',
                    borderRadius: 999, fontSize: 10, fontWeight: 700,
                    background: intentMeta.bg, color: intentMeta.color, border: `1px solid ${intentMeta.color}33`
                  }}>
                    <Icon path={ICONS[intentMeta.icon]} size={12} color={intentMeta.color} />
                    {intentMeta.label}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {traces.map((trace, idx) => (
                  <div key={idx} style={{ padding: '12px 14px', borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{trace.agent_name}</span>
                        <LLMPill mode={trace.llm_mode} />
                        <Badge label={trace.status} status={trace.status} />
                      </div>
                      {trace.tools_used && trace.tools_used.length > 0 && (
                        <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'monospace' }}>
                          [{trace.tools_used.join(', ')}]
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: '#334155', lineHeight: 1.5 }}>
                      {trace.decision}
                    </div>

                    {/* Stock separation display */}
                    {trace.agent_name === 'Inventory Agent' && trace.evidence?.requested_quantity !== undefined && (
                      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                        {[
                          { label: 'Requested Demand', value: `${trace.evidence.requested_quantity} units`, highlight: true },
                          { label: 'Current Stock', value: `${trace.evidence.current_stock} units`, highlight: false },
                          { label: 'Demand Shortfall', value: `${trace.evidence.demand_shortfall} units`, highlight: true },
                          { label: 'Safety Threshold', value: `${trace.evidence.minimum_stock_level} units`, highlight: false },
                          { label: 'Safety Replenishment', value: `${trace.evidence.replenishment_quantity} units`, highlight: false },
                          { label: 'Quantity to Order', value: `${trace.evidence.quantity_to_order} units`, highlight: true },
                        ].map(({ label, value, highlight }) => (
                          <div key={label} style={{ padding: '3px 8px', borderRadius: 6, background: highlight ? '#eff6ff' : '#fff', border: `1px solid ${highlight ? '#bfdbfe' : '#e2e8f0'}`, fontSize: 10 }}>
                            <div style={{ color: '#94a3b8', fontWeight: 600, fontSize: 8, textTransform: 'uppercase' }}>{label}</div>
                            <div style={{ fontWeight: 700, color: highlight ? '#1d4ed8' : '#334155' }}>{value}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Audit Trail Drawer Toggle */}
          {state?.audit_log && state.audit_log.length > 0 && (
            <div style={{ textAlign: 'right' }}>
              <button
                onClick={() => setAuditOpen(!auditOpen)}
                style={{ background: 'none', border: 'none', color: '#6366f1', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
              >
                {auditOpen ? 'Hide Full Audit Trail' : 'View Full Audit Trail'}
              </button>
              {auditOpen && (
                <Card style={{ padding: 16, marginTop: 10, textAlign: 'left', background: '#0f172a', color: '#94a3b8', fontFamily: 'monospace', fontSize: 11, maxHeight: 220, overflowY: 'auto' }}>
                  {state.audit_log.map((log, i) => (
                    <div key={i} style={{ marginBottom: 8, whiteSpace: 'pre-line' }}>{log}</div>
                  ))}
                </Card>
              )}
            </div>
          )}

        </div>

        {/* ─── RIGHT COLUMN ────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Route & Intent Status */}
          {overallStatus && (
            <Card style={{ padding: 18 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>
                Workflow Route & Intent
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Badge label={overallStatus.replace(/_/g, ' ')} status={overallStatus} />
                  {state?.llm_mode && <LLMPill mode={state.llm_mode} />}
                </div>
                {state?.intent && (
                  <div style={{ fontSize: 12, color: '#475569', marginTop: 4 }}>
                    Intent: <strong>{intentMeta.label}</strong>
                  </div>
                )}
                {state?.route_taken && (
                  <div style={{ fontSize: 11, color: '#64748b' }}>
                    Route: <code style={{ background: '#f1f5f9', padding: '2px 5px', borderRadius: 4 }}>{state.route_taken}</code>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* ─── Detailed Procurement Summary (Section D) ────────────────── */}
          {isProcurementFlow && proc.supplier && (
            <Card style={{ padding: 18 }}>
              <SectionTitle icon="package">Procurement Specification</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'Product Item', value: state?.product || '—' },
                  { label: 'Purchasing Strategy', value: state?.selected_strategy?.replace(/_/g, ' ') || '—', highlight: true },
                  { label: 'Requested Demand', value: state?.requested_quantity ? `${state.requested_quantity} units` : 'Not specified' },
                  { label: 'Available Stock', value: state?.current_stock !== undefined ? `${state.current_stock} units` : '—' },
                  { label: 'Demand Shortfall', value: state?.demand_shortfall !== undefined ? `${state.demand_shortfall} units` : '—' },
                  { label: 'Safety Replenishment', value: state?.replenishment_quantity !== undefined ? `${state.replenishment_quantity} units` : '—' },
                  { label: 'Final Order Volume', value: `${proc.quantity} units`, bold: true, highlight: true },
                  { label: 'Selected Supplier', value: `${getSupplierName(proc.supplier)} (${state?.external_purchase_selected ? 'Online Marketplace' : (state?.supplier_selection_mode || 'RECOMMENDED')})` },
                  { label: 'Fulfillment Method', value: state?.external_purchase_selected ? 'External Merchant Checkout' : 'Internal Corporate PO', highlight: state?.external_purchase_selected },
                  { label: 'Unit Price', value: `₹${proc.unit_price?.toLocaleString()} ${proc.currency || 'INR'}` },
                  { label: 'Total Purchase Cost', value: `₹${proc.total_cost?.toLocaleString()}`, bold: true, highlight: true },
                  { label: 'Delivery Lead Time', value: proc.delivery_days ? `${proc.delivery_days} days` : '—' },
                  { label: 'Remaining Budget', value: finance.remaining_budget !== undefined ? `₹${finance.remaining_budget?.toLocaleString()}` : '—', color: finance.status === 'APPROVED' ? '#16a34a' : '#dc2626' },
                  { label: 'Risk Governance', value: risk.level || '—' },
                ].map(({ label, value, bold, highlight, color }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '4px 0', borderBottom: '1px solid #f8fafc' }}>
                    <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>{label}</span>
                    <span style={{ fontSize: 12, fontWeight: bold ? 800 : 600, color: color || (highlight ? '#4338ca' : '#0f172a') }}>
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ─── Mandatory Human-in-the-Loop Approval Gate ──────────────── */}
          {isPaused && (
            <Card style={{ padding: 20, border: '2px solid #f59e0b', background: '#fffbeb' }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 14 }}>
                <Icon path={ICONS.alert} size={20} color="#d97706" />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: '#92400e' }}>Human Authorization Gate</div>
                  <div style={{ fontSize: 11, color: '#b45309', marginTop: 2 }}>
                    Mandatory policy: Every purchase requires explicit supervisor sign-off
                  </div>
                </div>
              </div>

              {state?.external_purchase_selected && (
                <div style={{ padding: '8px 10px', borderRadius: 6, background: '#e0f2fe', border: '1px solid #7dd3fc', marginBottom: 12, fontSize: 11, color: '#0369a1', lineHeight: 1.4 }}>
                  🌐 <strong>External Merchant Selected:</strong> Authorizing confirms corporate budget approval. Buyer must complete checkout on the external merchant site via the provided product link.
                </div>
              )}

              <div style={{ background: '#fff', borderRadius: 8, padding: 12, marginBottom: 14, border: '1px solid #fde68a', fontSize: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, color: '#92400e', fontWeight: 700, textTransform: 'uppercase' }}>Product</div>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{state?.product || '—'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: '#92400e', fontWeight: 700, textTransform: 'uppercase' }}>Strategy</div>
                    <div style={{ fontWeight: 700, color: '#4338ca' }}>{state?.selected_strategy?.replace(/_/g, ' ') || 'standard'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: '#92400e', fontWeight: 700, textTransform: 'uppercase' }}>Order Volume</div>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{proc.quantity} units</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: '#92400e', fontWeight: 700, textTransform: 'uppercase' }}>Supplier</div>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>
                      {getSupplierName(proc.supplier)} {state?.external_purchase_selected && '(Online)'}
                    </div>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <div style={{ fontSize: 10, color: '#92400e', fontWeight: 700, textTransform: 'uppercase' }}>Total Amount & Remaining Budget</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 2 }}>
                      <span style={{ fontWeight: 800, color: '#b45309', fontSize: 15 }}>₹{proc.total_cost?.toLocaleString()}</span>
                      <span style={{ fontSize: 11, color: '#16a34a', fontWeight: 600 }}>Budget: ₹{finance.remaining_budget?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ fontSize: 10, color: '#92400e', marginBottom: 12, fontStyle: 'italic' }}>
                Note: Approving authorizes this exact supplier and volume. If any parameters are changed, approval is automatically invalidated.
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button
                  onClick={() => handleApproval('APPROVE')}
                  disabled={loading}
                  style={{
                    padding: '11px 0', borderRadius: 8, fontSize: 13, fontWeight: 700,
                    background: loading ? '#a7f3d0' : (state?.external_purchase_selected ? 'linear-gradient(135deg,#2563eb,#1d4ed8)' : 'linear-gradient(135deg,#16a34a,#15803d)'),
                    border: 'none', color: '#fff', cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    boxShadow: '0 2px 6px rgba(37,99,235,.25)',
                  }}
                >
                  <Icon path={ICONS.check} size={15} color="#fff" />
                  {state?.external_purchase_selected ? 'AUTHORIZE EXTERNAL PURCHASE' : 'AUTHORIZE PURCHASE ORDER'}
                </button>
                <button
                  onClick={() => handleApproval('REJECT')}
                  disabled={loading}
                  style={{
                    padding: '9px 0', borderRadius: 8, fontSize: 12, fontWeight: 700,
                    background: '#fff', border: '1.5px solid #ef4444', color: '#dc2626',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}
                >
                  <Icon path={ICONS.x} size={14} color="#dc2626" />
                  REJECT PURCHASE
                </button>
              </div>
            </Card>
          )}

          {/* Executed PO Confirmation */}
          {exec && (
            <Card style={{ padding: 18, border: `1.5px solid ${exec.is_external ? '#93c5fd' : '#86efac'}`, background: exec.is_external ? '#eff6ff' : '#f0fdf4' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <Icon path={ICONS.check} size={18} color={exec.is_external ? '#2563eb' : '#16a34a'} />
                <span style={{ fontSize: 13, fontWeight: 800, color: exec.is_external ? '#1d4ed8' : '#15803d' }}>
                  {exec.is_external ? 'EXTERNAL PURCHASE AUTHORIZED' : 'PURCHASE ORDER ISSUED'}
                </span>
              </div>
              <div style={{ fontSize: 12, color: exec.is_external ? '#1e40af' : '#166534', lineHeight: 1.5 }}>
                {exec.is_external ? 'Auth Reference' : 'PO Reference'}: <strong>{exec.po_id}</strong><br />
                {exec.is_external ? 'Merchant / Platform' : 'Vendor'}: <strong>{getSupplierName(exec?.supplier || exec?.platform)}</strong><br />
                Volume: <strong>{exec.quantity} units</strong><br />
                Total Authorized: <strong>₹{exec.total_cost?.toLocaleString()}</strong><br />
                Status: <strong>{exec.status}</strong>
                {exec.is_external && exec.message && (
                  <div style={{ marginTop: 8, fontSize: 11, color: '#1e40af', background: '#dbeafe', padding: '6px 10px', borderRadius: 6 }}>
                    ℹ️ {exec.message}
                  </div>
                )}
                {exec.is_external && exec.external_url && (
                  <div style={{ marginTop: 12 }}>
                    <a
                      href={exec.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 6,
                        padding: '9px 16px', borderRadius: 6, background: '#2563eb', color: '#fff',
                        fontSize: 12, fontWeight: 700, textDecoration: 'none',
                        boxShadow: '0 2px 6px rgba(37,99,235,0.3)'
                      }}
                    >
                      Complete Purchase on {exec.platform || 'Merchant Portal'} <Icon path={ICONS.externalLink} size={13} color="#fff" />
                    </a>
                  </div>
                )}
              </div>
            </Card>
          )}

        </div>

      </div>
    </div>
  );
}
