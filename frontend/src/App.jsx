import React, { useState, useEffect, useCallback, useRef } from 'react';
import CameraOverlay from './components/CameraOverlay';
import NotificationBar from './components/NotificationBar';
import './App.css';

const REMINDERS_URL  = "http://localhost:8001/get-reminders";
const REGISTER_URL   = "http://localhost:8004/register-new";
const UNKNOWN_COOLDOWN_MS = 30 * 1000;   // 30s before unknown popup can re-trigger
const KNOWN_COOLDOWN_MS   = 10 * 60 * 1000; // 10 min for known persons (in CameraOverlay)

function App() {
  const [reminders, setReminders] = useState([{ id: 1, text: "Google Calendar: Ready" }]);
  const [faceLogs,  setFaceLogs]  = useState([{ id: 101, text: "HUD Initialized — Scanning..." }]);

  // Registration modal state
  const [showModal,   setShowModal]   = useState(false);
  const [regName,     setRegName]     = useState('');
  const [regRelation, setRegRelation] = useState('');
  const [regStatus,   setRegStatus]   = useState('');

  // Cooldown refs
  const lastUnknownRef = useRef(0);         // timestamp of last unknown popup
  const pendingFrameRef = useRef(null);     // frame blob for registration
  const registeredNamesRef = useRef(new Set()); // names registered this session

  // ── Reminders & System Status polling ──────────────────────────────────
  const [sysStatus, setSysStatus] = useState({ is_recording: false, is_summarizing: false });

  useEffect(() => {
    const fetchReminders = async () => {
      try {
        const res = await fetch(REMINDERS_URL);
        if (res.ok) {
          const data = await res.json();
          if (data.length > 0) setReminders(data.map(r => ({ id: r.id, text: r.summary })));
        }
      } catch (_) {}
    };
    
    const fetchSystemStatus = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8004/system-status");
        if (res.ok) {
          const data = await res.json();
          setSysStatus({ is_recording: data.is_recording, is_summarizing: data.is_summarizing });
        }
      } catch (_) {}
    };

    fetchReminders();
    fetchSystemStatus();

    const idReminders = setInterval(fetchReminders, 30000);
    const idStatus = setInterval(fetchSystemStatus, 5000); // Check status every 5 seconds instead of 1.5s

    return () => {
      clearInterval(idReminders);
      clearInterval(idStatus);
    };
  }, []);

  // ── Face detection callback ────────────────────────────
  const addFaceLog = useCallback((result) => {
    const now = Date.now();

    if (result.type === 'unknown') {
      // Don't re-trigger if modal is already open
      if (showModal) return;
      // Don't re-trigger within cooldown
      if (now - lastUnknownRef.current < UNKNOWN_COOLDOWN_MS) return;

      lastUnknownRef.current = now;
      pendingFrameRef.current = result.frameBlob;
      setShowModal(true);
      setRegName('');
      setRegRelation('');
      setRegStatus('');
      return;
    }

    // Known person — build log message
    const name = result.name || 'Unknown';
    const pct  = result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : '';
    let message = `✅ ${name} (${result.relationship || '?'}) — ${pct}`;
    if (result.lastVisit)   message += ` | Last: ${result.lastVisit}`;
    if (result.lastEmotion) message += ` | ${result.lastEmotion}`;

    setFaceLogs(prev => {
      // Remove any existing log for this specific person to keep the list unique
      const filtered = prev.filter(log => !log.text.includes(`✅ ${name}`));
      return [{ id: Date.now(), text: message }, ...filtered].slice(0, 6);
    });
  }, [showModal]);

  // ── Registration submit ────────────────────────────────
  const handleRegister = async () => {
    if (!regName.trim() || !regRelation.trim()) {
      setRegStatus('⚠️ Please fill both fields.');
      return;
    }
    if (!pendingFrameRef.current) {
      setRegStatus('⚠️ No face image captured. Try again.');
      return;
    }

    setRegStatus('⏳ Registering...');
    try {
      const formData = new FormData();
      formData.append('file', pendingFrameRef.current, 'frame.jpg');
      formData.append('name', regName.trim());
      formData.append('relationship', regRelation.trim());

      const res = await fetch(REGISTER_URL, { method: 'POST', body: formData });
      const data = await res.json();

      if (res.ok) {
        const registeredName = regName.trim();
        setRegStatus(`✅ ${data.message}`);

        // Track registered person so they're not triggered again immediately
        registeredNamesRef.current.add(registeredName.toLowerCase());

        // Suppress unknown popup for 10min (this person just registered)
        lastUnknownRef.current = Date.now() + KNOWN_COOLDOWN_MS;

        setFaceLogs(prev => [
          { id: Date.now(), text: `🆕 Registered: ${registeredName} (${regRelation})` },
          ...prev
        ].slice(0, 6));

        setTimeout(() => setShowModal(false), 1500);
      } else {
        setRegStatus(`❌ ${data.detail || 'Registration failed.'}`);
      }
    } catch (e) {
      setRegStatus(`❌ Network error: ${e.message}`);
    }
  };

  return (
    <div className="ar-hud-container">
      <CameraOverlay onFaceDetected={addFaceLog} />

      <div className="floating-hud left-hud">
        <NotificationBar title="EYE-TRACK" items={faceLogs} />
      </div>

      <div className="floating-hud right-hud">
        <NotificationBar title="REMINDERS" items={reminders} />
      </div>

      <div className="system-footer" style={{ display: 'flex', gap: '15px' }}>
        <span>SYSTEM: STABLE | AG-OS v1.0</span>
        {sysStatus.is_recording && (
          <span style={{ color: '#ff4444', fontWeight: 'bold', animation: 'pulse 1.5s infinite' }}>
            🎙️ REC ● LIVE
          </span>
        )}
        {sysStatus.is_summarizing && (
          <span style={{ color: '#f0c040', fontWeight: 'bold', animation: 'pulse 1.5s infinite' }}>
            ⚙️ SUMMARIZING...
          </span>
        )}
      </div>

      {/* REGISTRATION MODAL */}
      {showModal && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h2 style={styles.title}>🆕 Unknown Person Detected</h2>
            <p style={styles.sub}>Register this person to remember them in future.</p>

            <input
              style={styles.input}
              placeholder="Full Name"
              value={regName}
              onChange={e => setRegName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleRegister()}
            />
            <input
              style={styles.input}
              placeholder="Relationship (e.g. Friend, Family)"
              value={regRelation}
              onChange={e => setRegRelation(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleRegister()}
            />

            {regStatus && <p style={styles.status}>{regStatus}</p>}

            <div style={styles.btnRow}>
              <button style={styles.btnPrimary} onClick={handleRegister}>Register</button>
              <button style={styles.btnSecondary} onClick={() => {
                // Set cooldown so popup doesn't immediately re-open
                lastUnknownRef.current = Date.now() + UNKNOWN_COOLDOWN_MS * 2;
                setShowModal(false);
              }}>Skip (1 min)</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.75)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 9999,
    backdropFilter: 'blur(4px)',
  },
  modal: {
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: 12,
    padding: '32px 28px',
    width: 360,
    display: 'flex', flexDirection: 'column', gap: 14,
    boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
  },
  title:  { margin: 0, color: '#e6edf3', fontSize: 20, fontWeight: 700 },
  sub:    { margin: 0, color: '#8b949e', fontSize: 14 },
  input:  {
    background: '#161b22', border: '1px solid #30363d',
    borderRadius: 8, padding: '10px 14px',
    color: '#e6edf3', fontSize: 14, outline: 'none',
  },
  status: { margin: 0, color: '#f0c040', fontSize: 13, minHeight: 18 },
  btnRow: { display: 'flex', gap: 10, marginTop: 4 },
  btnPrimary: {
    flex: 1, padding: '10px 0', borderRadius: 8, cursor: 'pointer',
    background: '#238636', color: '#fff', border: 'none', fontWeight: 600, fontSize: 14,
  },
  btnSecondary: {
    flex: 1, padding: '10px 0', borderRadius: 8, cursor: 'pointer',
    background: '#21262d', color: '#8b949e', border: '1px solid #30363d', fontSize: 14,
  },
};

export default App;
