import React, { useState, useRef, useCallback } from 'react';
import {
  SlidersHorizontal,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Zap,
  Clock,
  ShieldAlert,
  ShieldCheck,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export const CorridorCompareSlider: React.FC = () => {
  const [sliderPosition, setSliderPosition] = useState<number>(50); // percentage 0 to 100
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const clampedPercentage = Math.min(Math.max((x / rect.width) * 100, 5), 95);
    setSliderPosition(clampedPercentage);
  }, []);

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      handleMove(e.clientX);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches[0]) {
      handleMove(e.touches[0].clientX);
    }
  };

  return (
    <section id="transformation" className="landing-section compare-slider-section">
      <div className="section-header">
        <span className="section-eyebrow">Operational Transformation</span>
        <h2 className="section-title">Conventional operations versus synchronized digital twin</h2>
        <p className="section-subtitle">
          Drag the interactive slider to compare legacy uncoordinated municipal management with multi-domain digital twin synchronization.
        </p>
      </div>

      {/* Preset View Switcher */}
      <div className="compare-mode-presets">
        <button
          type="button"
          className={`compare-preset-btn ${sliderPosition >= 80 ? 'active' : ''}`}
          onClick={() => setSliderPosition(90)}
        >
          <AlertTriangle size={13} color="#F87171" />
          <span>CONVENTIONAL LEGACY</span>
        </button>
        <button
          type="button"
          className={`compare-preset-btn ${sliderPosition >= 40 && sliderPosition <= 60 ? 'active' : ''}`}
          onClick={() => setSliderPosition(50)}
        >
          <SlidersHorizontal size={13} color="#38BDF8" />
          <span>SPLIT COMPARISON (50/50)</span>
        </button>
        <button
          type="button"
          className={`compare-preset-btn ${sliderPosition <= 20 ? 'active' : ''}`}
          onClick={() => setSliderPosition(10)}
        >
          <CheckCircle2 size={13} color="#34D399" />
          <span>DIGITAL TWIN SYNCHRONIZATION</span>
        </button>
      </div>

      {/* Interactive Visual Comparison Stage */}
      <div
        className="compare-stage-container"
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleMouseUp}
      >
        {/* Layer 1: Right Side (Digital Twin Synchronized View - Underneath) */}
        <div className="compare-layer layer-twin">
          <img
            src="/assets/images/urban-mobility-flow-twilight.png"
            alt="Synchronized digital twin corridor"
            className="compare-stage-image"
          />
          <div className="compare-overlay-twin" />

          {/* Twin Metadata Annotations */}
          <div className="compare-badge-stack twin-badges">
            <div className="compare-status-badge twin font-mono">
              <ShieldCheck size={13} color="#10B981" />
              <span>DIGITAL TWIN SYNCHRONIZED</span>
            </div>
            <div className="compare-metric-card twin">
              <div className="card-row">
                <Activity size={14} color="#38BDF8" />
                <span className="card-label font-mono">GREEN-WAVE COORDINATION</span>
              </div>
              <span className="card-value font-mono">CONTINUOUS 1 Hz OPTIMIZATION</span>
              <span className="card-subtext font-mono">Dynamic split balancing prevents arterial queue back-propagation</span>
            </div>
            <div className="compare-metric-card twin">
              <div className="card-row">
                <Zap size={14} color="#F59E0B" />
                <span className="card-label font-mono">DISTRICT ENERGY TWIN</span>
              </div>
              <span className="card-value font-mono">380 kW TARIFF SHAVED</span>
              <span className="card-subtext font-mono">15-minute predictive pre-cooling scheduled prior to peak utility tariff</span>
            </div>
          </div>
        </div>

        {/* Layer 2: Left Side (Conventional Legacy View - Clipped) */}
        <div
          className="compare-layer layer-legacy"
          style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
        >
          <img
            src="/assets/images/urban-mobility-flow-twilight.png"
            alt="Conventional legacy traffic operations"
            className="compare-stage-image legacy-filter"
          />
          <div className="compare-overlay-legacy" />

          {/* Legacy Metadata Annotations */}
          <div className="compare-badge-stack legacy-badges">
            <div className="compare-status-badge legacy font-mono">
              <ShieldAlert size={13} color="#EF4444" />
              <span>CONVENTIONAL MUNICIPAL OPERATIONS</span>
            </div>
            <div className="compare-metric-card legacy">
              <div className="card-row">
                <AlertTriangle size={14} color="#EF4444" />
                <span className="card-label font-mono">FRAGMENTED SIGNAL CONTROL</span>
              </div>
              <span className="card-value font-mono">RIGID TIME-OF-DAY CYCLES</span>
              <span className="card-subtext font-mono">Isolated intersection controllers blind to upstream arterial queue surges</span>
            </div>
            <div className="compare-metric-card legacy">
              <div className="card-row">
                <Clock size={14} color="#F87171" />
                <span className="card-label font-mono">PEAK TARIFF SURCHARGE</span>
              </div>
              <span className="card-value font-mono">UNMITIGATED DEMAND SPIKES</span>
              <span className="card-subtext font-mono">Chiller plants hit maximum utility demand tariffs without predictive dispatch</span>
            </div>
          </div>
        </div>

        {/* Draggable Divider Handle */}
        <div
          className="compare-handle-line"
          style={{ left: `${sliderPosition}%` }}
          onMouseDown={handleMouseDown}
          onTouchStart={handleMouseDown}
        >
          <div className="compare-handle-knob" aria-label="Drag to compare">
            <ChevronLeft size={14} />
            <ChevronRight size={14} />
          </div>
        </div>
      </div>

      {/* Comparison Specifications Summary Grid */}
      <div className="compare-specs-summary">
        <div className="specs-summary-card legacy">
          <div className="summary-header">
            <span className="summary-tag font-mono">LEGACY PARADIGM</span>
            <h3 className="summary-title">Fragmented Department Silos</h3>
          </div>
          <ul className="summary-bullets">
            <li>Siloed traffic SCADA and utility meters with zero operational communication.</li>
            <li>Static signal phase splits uncalibrated to sudden downstream queue spillback.</li>
            <li>Black-box heuristics lacking mathematical bounds or verifiable audit trails.</li>
            <li>Costly utility demand surcharges during simultaneous HVAC peak cooling hours.</li>
          </ul>
        </div>

        <div className="specs-summary-card twin">
          <div className="summary-header">
            <span className="summary-tag font-mono">TWIN SYNCHRONIZED</span>
            <h3 className="summary-title">Integrated Municipal Intelligence</h3>
          </div>
          <ul className="summary-bullets">
            <li>Multi-asset spatial synchronization across signal networks, transit, and microgrids.</li>
            <li>Continuous 1 Hz telemetry validation with automatic STALE threshold isolation.</li>
            <li>Conformal 80%/90% confidence bands paired with top-5 TreeSHAP model explainability.</li>
            <li>Advisory-only human-in-the-loop delivery with immutable TimescaleDB logging.</li>
          </ul>
        </div>
      </div>
    </section>
  );
};
