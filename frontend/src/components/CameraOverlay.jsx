import React, { useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';

const FACE_API_URL = 'http://localhost:8004/identify';
const POLL_INTERVAL_MS = 3000;         // scan every 3 seconds
const COOLDOWN_MS = 5 * 60 * 1000;    // 5 minutes per person

const CameraOverlay = ({ onFaceDetected }) => {
  const webcamRef = useRef(null);
  const intervalRef = useRef(null);
  const lastSeenRef = useRef({});  // { personName: timestamp }

  const captureAndIdentify = useCallback(async () => {
    const webcam = webcamRef.current;
    if (!webcam || !webcam.video || webcam.video.readyState !== 4) return;

    const now = Date.now();
    // OPTIMIZATION: If any known person was identified recently, 
    // skip the scan entirely until their 5-min cooldown (COOLDOWN_MS) expires.
    const recentlySeen = Object.values(lastSeenRef.current).some(ts => now - ts < COOLDOWN_MS);
    if (recentlySeen) return;

    // Capture frame from webcam as JPEG blob
    const canvas = document.createElement('canvas');
    const video = webcam.video;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(async (blob) => {
      if (!blob) return;

      try {
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');

        const res = await fetch(FACE_API_URL, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) return;

        const data = await res.json();
        const now = Date.now();

        if (data.person_detected && data.match_status !== 'unknown' && data.match_status !== 'embedding_failed') {
          const personKey = data.person_name || 'uncertain';
          const lastSeen = lastSeenRef.current[personKey] || 0;

          if (now - lastSeen < COOLDOWN_MS) {
            // Still in cooldown - don't notify App.jsx (prevents HUD duplicate logs)
            return;
          }
          lastSeenRef.current[personKey] = now;

          onFaceDetected({
            type: data.match_status,           // 'confirmed' or 'uncertain'
            name: data.person_name || 'Unknown',
            relationship: data.relationship || '',
            confidence: data.confidence,
            lastVisit: data.last_visit,
            lastSummary: data.last_summary,
            lastEmotion: data.last_emotion,
          });

        } else if (data.person_detected && data.match_status === 'unknown') {
          // Unknown person — pass the frame blob so App.jsx can use it for registration
          onFaceDetected({ type: 'unknown', confidence: data.confidence, frameBlob: blob });
        }
        // No person in frame → do nothing
      } catch (err) {
        console.warn('Face API error:', err.message);
      }
    }, 'image/jpeg', 0.85);
  }, [onFaceDetected]);

  useEffect(() => {
    // Start polling every POLL_INTERVAL_MS
    intervalRef.current = setInterval(captureAndIdentify, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [captureAndIdentify]);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        background: 'black',
      }}
    >
      <Webcam
        ref={webcamRef}
        muted={true}
        style={{ width: '100vw', height: '100vh', objectFit: 'cover' }}
        screenshotFormat="image/jpeg"
      />
    </div>
  );
};

export default CameraOverlay;
