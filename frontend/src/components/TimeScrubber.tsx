import React, { useEffect, useState } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Clock,
  Zap,
  Radio
} from 'lucide-react';

interface TimeScrubberProps {
  minutesAgo: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onScrubChange: (minutesAgo: number | ((prev: number) => number)) => void;
  onTogglePlay: () => void;
  onSpeedChange: (speed: number) => void;
  onJumpToLive: () => void;
}

export const TimeScrubber: React.FC<TimeScrubberProps> = ({
  minutesAgo,
  isPlaying,
  playbackSpeed,
  onScrubChange,
  onTogglePlay,
  onSpeedChange,
  onJumpToLive
}) => {
  // Asynchronous real-time clock ticker (advances every second without requiring page reload)
  const [clockNow, setClockNow] = useState<number>(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setClockNow(Date.now());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Asynchronous playback loop: advances time forward towards Live when playing
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      onScrubChange((prev) => {
        // Advance by (1.5 * playbackSpeed) minutes per real second
        const step = Math.max(1, Math.round(2 * playbackSpeed));
        const next = prev - step;
        if (next <= 0) {
          onTogglePlay(); // Auto-pause when reaching Live
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, onScrubChange, onTogglePlay]);

  // Compute calculated timestamp based on ticking clockNow and minutesAgo offset
  const targetDate = new Date(clockNow - minutesAgo * 60 * 1000);
  const timeString = targetDate.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
  const dateString = targetDate.toLocaleDateString([], {
    month: 'short',
    day: 'numeric'
  });

  // Format relative time badge
  const formatRelativeTime = (mins: number) => {
    if (mins === 0) return 'Real-Time Live';
    const hours = Math.floor(mins / 60);
    const remainder = mins % 60;
    if (hours === 0) return `-${remainder}m ago`;
    if (remainder === 0) return `-${hours}h ago`;
    return `-${hours}h ${remainder}m ago`;
  };

  // Slider value: left (0) = 720 minutes ago (-12h), right (720) = 0 minutes ago (Live)
  const sliderPosition = 720 - minutesAgo;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPos = Number(e.target.value);
    const newMinutesAgo = 720 - newPos;
    onScrubChange(newMinutesAgo);
  };

  const handleStepBack = () => {
    onScrubChange((prev) => Math.min(720, prev + 15));
  };

  const handleStepForward = () => {
    onScrubChange((prev) => Math.max(0, prev - 15));
  };

  const speedOptions = [1, 2, 5, 10];

  return (
    <div className="time-scrubber-dock" role="region" aria-label="Corridor Timeline Scrubber">
      {/* 1. Left Group: Mode Indicator & Playback Transport */}
      <div className="scrubber-transport-group">
        {minutesAgo === 0 ? (
          <div className="scrubber-mode-badge live" title="Real-time corridor telemetry stream">
            <span className="live-dot-ping" />
            <Radio size={12} />
            <span>LIVE</span>
          </div>
        ) : (
          <div className="scrubber-mode-badge replay" title="Historical playback active">
            <Clock size={12} />
            <span>REPLAY</span>
          </div>
        )}

        <button
          type="button"
          className={`scrubber-btn play-btn ${isPlaying ? 'playing' : ''}`}
          onClick={onTogglePlay}
          title={isPlaying ? 'Pause playback' : 'Play historical corridor telemetry'}
          aria-label={isPlaying ? 'Pause playback' : 'Play playback'}
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} style={{ marginLeft: '1px' }} />}
        </button>

        <button
          type="button"
          className="scrubber-step-btn"
          onClick={handleStepBack}
          title="Step back 15 minutes in history"
          disabled={minutesAgo >= 720}
        >
          <RotateCcw size={12} />
          <span>15m</span>
        </button>

        <button
          type="button"
          className="scrubber-step-btn"
          onClick={handleStepForward}
          title="Step forward 15 minutes towards live"
          disabled={minutesAgo <= 0}
        >
          <span>15m</span>
          <RotateCw size={12} />
        </button>

        {/* Speed Selector */}
        <div className="scrubber-speed-selector">
          {speedOptions.map((spd) => (
            <button
              key={spd}
              type="button"
              className={`speed-pill ${playbackSpeed === spd ? 'active' : ''}`}
              onClick={() => onSpeedChange(spd)}
              title={`${spd}x playback speed`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>

      {/* 2. Center Group: Range Slider Track with Hour Ticks */}
      <div className="scrubber-track-group">
        <div className="scrubber-ticks-row">
          <span>-12h</span>
          <span>-6h</span>
          <span>-3h</span>
          <span>-1h</span>
          <span style={{ color: minutesAgo === 0 ? '#3FB950' : 'var(--text-muted)', fontWeight: minutesAgo === 0 ? 700 : 500 }}>
            LIVE
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="720"
          step="1"
          value={sliderPosition}
          onChange={handleSliderChange}
          className="scrubber-slider"
          aria-label="Historical corridor timeline scrubber slider"
        />
      </div>

      {/* 3. Right Group: Asynchronous Digital Clock & Return to Live */}
      <div className="scrubber-info-group">
        <div className="scrubber-timestamp-box">
          <Clock size={13} className="text-muted" />
          <div className="scrubber-time-texts">
            <span className="scrubber-time-val font-mono">{timeString}</span>
            <span className="scrubber-relative-val">{dateString} • {formatRelativeTime(minutesAgo)}</span>
          </div>
        </div>

        {minutesAgo > 0 && (
          <button
            type="button"
            className="scrubber-live-btn"
            onClick={onJumpToLive}
            title="Snap back to real-time live corridor stream"
          >
            <Zap size={12} />
            <span>Return to Live</span>
          </button>
        )}
      </div>
    </div>
  );
};
