import React, { useEffect } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Radio,
  Clock
} from 'lucide-react';

interface TimeScrubberProps {
  minutesAgo: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onScrubChange: (minutesAgo: number) => void;
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
  // Auto-advance scrubber when playing
  useEffect(() => {
    if (!isPlaying) return;

    // Interval fires every 1 second; advances time by (5 * speed) minutes towards Live (0)
    const interval = setInterval(() => {
      onScrubChange(Math.max(0, minutesAgo - (5 * playbackSpeed)));
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, minutesAgo, playbackSpeed, onScrubChange]);

  // Format relative time text
  const formatRelativeTime = (mins: number) => {
    if (mins === 0) return 'Real-Time Live';
    const hours = Math.floor(mins / 60);
    const remainder = mins % 60;
    if (hours === 0) return `-${remainder}m ago`;
    if (remainder === 0) return `-${hours}h ago`;
    return `-${hours}h ${remainder}m ago`;
  };

  // Compute calculated timestamp
  const targetDate = new Date(Date.now() - (minutesAgo * 60 * 1000));
  const timeString = targetDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const dateString = targetDate.toLocaleDateString([], { month: 'short', day: 'numeric' });

  // Slider value: left (0) = 720 minutes ago (-12h), right (720) = 0 minutes ago (Live)
  const sliderPosition = 720 - minutesAgo;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPos = Number(e.target.value);
    const newMinutesAgo = 720 - newPos;
    onScrubChange(newMinutesAgo);
  };

  const handleStepBack = () => {
    onScrubChange(Math.min(720, minutesAgo + 15));
  };

  const handleStepForward = () => {
    onScrubChange(Math.max(0, minutesAgo - 15));
  };

  const speedOptions = [1, 2, 5, 10];

  return (
    <div className="time-scrubber-dock">
      {/* Playback Controls */}
      <div className="scrubber-transport-group">
        <button
          className="scrubber-btn"
          onClick={handleStepBack}
          title="Step back 15 minutes"
          disabled={minutesAgo >= 720}
        >
          <SkipBack size={15} />
        </button>

        <button
          className={`scrubber-btn play-btn ${isPlaying ? 'playing' : ''}`}
          onClick={onTogglePlay}
          title={isPlaying ? "Pause playback" : "Play corridor historical progression"}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} style={{ marginLeft: '1px' }} />}
        </button>

        <button
          className="scrubber-btn"
          onClick={handleStepForward}
          title="Step forward 15 minutes"
          disabled={minutesAgo <= 0}
        >
          <SkipForward size={15} />
        </button>

        {/* Speed Selector */}
        <div className="scrubber-speed-selector">
          {speedOptions.map((spd) => (
            <button
              key={spd}
              className={`speed-pill ${playbackSpeed === spd ? 'active' : ''}`}
              onClick={() => onSpeedChange(spd)}
              title={`${spd}x playback speed`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Range Slider with Hour Ticks */}
      <div className="scrubber-track-group">
        <div className="scrubber-ticks-row">
          <span>-12h</span>
          <span>-9h</span>
          <span>-6h</span>
          <span>-3h</span>
          <span>-1h</span>
          <span style={{ color: minutesAgo === 0 ? '#10B981' : 'var(--color-text-muted)', fontWeight: minutesAgo === 0 ? 700 : 500 }}>
            LIVE
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="720"
          step="5"
          value={sliderPosition}
          onChange={handleSliderChange}
          className="scrubber-slider"
          aria-label="Historical corridor timeline scrubber"
        />
      </div>

      {/* Time Display & Mode Badges */}
      <div className="scrubber-info-group">
        <div className="scrubber-timestamp-box">
          <Clock size={14} className="text-muted" />
          <div className="scrubber-time-texts">
            <span className="scrubber-time-val font-mono">{timeString} ({dateString})</span>
            <span className="scrubber-relative-val">{formatRelativeTime(minutesAgo)}</span>
          </div>
        </div>

        {minutesAgo > 0 ? (
          <>
            <span className="provenance-badge badge-replay" style={{ boxShadow: '0 2px 6px rgba(59, 130, 246, 0.3)' }}>
              REPLAY
            </span>
            <button
              className="scrubber-live-btn"
              onClick={onJumpToLive}
              title="Return to real-time live telemetry feed"
            >
              <Radio size={13} />
              <span>Jump to Live</span>
            </button>
          </>
        ) : (
          <span className="provenance-badge badge-live">
            LIVE STREAM
          </span>
        )}
      </div>
    </div>
  );
};
