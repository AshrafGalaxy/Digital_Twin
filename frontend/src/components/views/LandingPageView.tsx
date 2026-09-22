import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  Zap,
  Car,
  Cpu,
  Eye,
  Layers,
  ChevronDown,
  ChevronUp,
  FileText,
  Compass,
  Database,
  Lock,
  BarChart3
} from 'lucide-react';
import { TabId } from '../Header';

interface LandingPageViewProps {
  onLaunchConsole: (tab?: TabId) => void;
}

export const LandingPageView: React.FC<LandingPageViewProps> = ({ onLaunchConsole }) => {
  const [activeFaq, setActiveFaq] = useState<number | null>(0);
  const [activePreviewMode, setActivePreviewMode] = useState<'simulation' | 'replay'>('simulation');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  // Scroll Reveal Observer for Sections
  const revealRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    revealRefs.current.forEach((el) => {
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  // Tagline Scroll Animation per B11 (Word-by-word illumination)
  const taglineWords = [
    'Urban', 'analytics', 'without', 'unverified', 'assertions.',
    'Every', 'insight', 'backed', 'by', 'physical', 'sensors,',
    'conformal', 'error', 'bounds,', 'and', 'human', 'in', 'the', 'loop', 'governance.'
  ];
  const [illuminatedCount, setIlluminatedCount] = useState<number>(0);
  const taglineSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = taglineSectionRef.current;
    if (!el) return;

    const handleScroll = () => {
      const rect = el.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      
      // Calculate scroll progress through the tagline section (0 to 1)
      const startTrigger = windowHeight * 0.85;
      const endTrigger = windowHeight * 0.25;
      
      if (rect.top > startTrigger) {
        setIlluminatedCount(0);
      } else if (rect.top < endTrigger) {
        setIlluminatedCount(taglineWords.length);
      } else {
        const progress = Math.min(1, Math.max(0, (startTrigger - rect.top) / (startTrigger - endTrigger)));
        const targetWords = Math.floor(progress * taglineWords.length);
        setIlluminatedCount(targetWords);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [taglineWords.length]);

  const scrollToAnchor = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const faqItems = [
    {
      q: 'Does this digital twin automatically actuate physical traffic signals?',
      a: 'No. The platform operates strictly as read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action. Physical signal controller actuation is strictly prohibited by architectural invariants.'
    },
    {
      q: 'How does the system enforce state separation between simulation and reality?',
      a: 'Observed telemetry (LIVE/REPLAY), physical SUMO simulation (SIMULATION), and machine learning forecasts (PREDICTED) are partitioned into isolated database tables. Simulations and forecasts can never overwrite observed twin state.'
    },
    {
      q: 'What physical corridor boundary is monitored?',
      a: 'The 1.8 kilometer arterial segment on Nagar Road, Pune, Maharashtra between Viman Nagar Chowk (INT-VN-01) and Somnath Nagar Chowk (INT-SN-01), encompassing 10 road segments and the Phoenix Marketcity commercial building zone (BLD-PHOENIX-01).'
    },
    {
      q: 'How are model uncertainties and forecasting errors communicated?',
      a: 'Every forecast provides 80% and 90% conformal prediction intervals and top-5 TreeSHAP feature attributions. Population Stability Index (PSI) drift monitoring continuously tracks feature shifts against the training baseline.'
    },
    {
      q: 'Does the twin ingest camera feeds, license plates, or individual commuter GPS traces?',
      a: 'Strictly no. Ingestion is restricted to macroscopic road segment velocities, loop detector counts, environmental air quality indices, and commercial building aggregate meter power. Facial recognition, automated license plate recognition, and individual vehicle tracking are strictly forbidden.'
    },
    {
      q: 'How are sensor failures and network disconnects handled?',
      a: 'Telemetry observations exceeding freshness thresholds (>180 seconds for traffic velocity, >900 seconds for building power) are automatically tagged as STALE. Stale or invalid data is highlighted in amber/red and rejected by decision-support algorithms.'
    }
  ];

  return (
    <div className="landing-root">
      {/* 1. Fluid Island Navigation per B7 */}
      <nav className="landing-island-nav" aria-label="Main Navigation">
        <div className="landing-nav-inner">
          <div className="landing-nav-brand" onClick={() => scrollToAnchor('hero')}>
            <Activity size={18} color="var(--color-primary)" style={{ filter: 'drop-shadow(0 0 8px rgba(47, 129, 247, 0.6))' }} />
            <span className="brand-name">Digital Twin</span>
            <span className="brand-corridor">Pune Nagar Road</span>
          </div>

          <div className="landing-nav-links">
            <button className="landing-nav-link" onClick={() => scrollToAnchor('pillars')}>Pillars</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('how-it-works')}>Architecture</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('provenance')}>Provenance</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('faq')}>FAQ</button>
          </div>

          <div className="landing-nav-actions">
            <button
              className="landing-btn-primary"
              onClick={() => onLaunchConsole('operations')}
              title="Open real-time digital twin operations console"
            >
              <span>Launch Twin Console</span>
              <ArrowRight size={14} />
            </button>
            <button
              className={`landing-mobile-toggle ${isMobileMenuOpen ? 'open' : ''}`}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              <span className="toggle-bar"></span>
              <span className="toggle-bar"></span>
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Panel */}
        {isMobileMenuOpen && (
          <div className="landing-mobile-menu">
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('pillars')}>Pillars</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('how-it-works')}>Architecture</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('provenance')}>Provenance</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('faq')}>FAQ</button>
            <button className="landing-mobile-item highlight" onClick={() => onLaunchConsole('operations')}>
              Launch Twin Console <ArrowRight size={14} />
            </button>
          </div>
        )}
      </nav>

      {/* 2. Above The Fold Hero Section */}
      <header id="hero" className="landing-hero-section">
        <div className="landing-hero-content">
          {/* Proof Pill */}
          <div className="landing-status-badge">
            <span className="landing-pulse-dot"></span>
            <span className="badge-text">1.8 km Nagar Road Arterial • Viman Nagar ↔ Somnath Nagar</span>
          </div>

          {/* Headline per B5 (No hyphens, meaningful breaks, left-to-right gradient) */}
          <h1 className="landing-hero-headline">
            Evidence backed urban decision support for arterial corridors
          </h1>

          {/* Subheadline */}
          <p className="landing-hero-subheadline">
            Synchronize traffic velocity, building energy consumption, and environmental metrics along the Nagar Road corridor with verifiable mathematical provenance.
          </p>

          {/* CTA Group */}
          <div className="landing-cta-group">
            <button
              className="landing-btn-large-primary"
              onClick={() => onLaunchConsole('operations')}
            >
              <span>Launch Twin Console</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="landing-btn-large-secondary"
              onClick={() => scrollToAnchor('provenance')}
            >
              <Eye size={16} />
              <span>Inspect Provenance Guarantee</span>
            </button>
          </div>

          {/* Risk Reversal & Trust Signal */}
          <div className="landing-trust-signals">
            <div className="trust-item">
              <ShieldCheck size={14} color="var(--color-success)" />
              <span>Strict non-actuation decision support</span>
            </div>
            <div className="trust-item">
              <Lock size={14} color="var(--color-primary)" />
              <span>Zero private vehicle tracking</span>
            </div>
            <div className="trust-item">
              <Database size={14} color="var(--color-simulation)" />
              <span>Auditable PostgreSQL / TimescaleDB</span>
            </div>
          </div>
        </div>

        {/* Hero Visual: Interactive Corridor Twin Preview Card */}
        <div className="landing-hero-visual-card">
          <div className="preview-card-header">
            <div className="preview-window-controls">
              <span className="window-dot red"></span>
              <span className="window-dot yellow"></span>
              <span className="window-dot green"></span>
            </div>
            <div className="preview-title-bar">
              <Compass size={13} color="var(--color-primary)" />
              <span>corridor-telemetry-twin • Nagar Road Eastbound / Westbound</span>
            </div>
            <div className="preview-mode-switch">
              <button
                className={`preview-mode-btn ${activePreviewMode === 'simulation' ? 'active' : ''}`}
                onClick={() => setActivePreviewMode('simulation')}
              >
                SIMULATION
              </button>
              <button
                className={`preview-mode-btn ${activePreviewMode === 'replay' ? 'active' : ''}`}
                onClick={() => setActivePreviewMode('replay')}
              >
                REPLAY
              </button>
            </div>
          </div>

          <div className="preview-card-body">
            {/* Interactive Corridor Visual Representation */}
            <div className="preview-map-schematic">
              <div className="schematic-road-strip">
                <div className="schematic-intersection west">
                  <div className="node-marker">INT-VN-01</div>
                  <div className="node-label">Viman Nagar Chowk</div>
                  <span className="node-status-pill green">Coordinated (110s)</span>
                </div>

                <div className="schematic-corridor-links">
                  <div className="schematic-segment top">
                    <span className="seg-name">SEG-NR-EB-01 (Nagar Rd EB)</span>
                    <span className="seg-speed">{activePreviewMode === 'simulation' ? '34.2 km/h' : '28.6 km/h'}</span>
                    <div className="seg-flow-bar" style={{ width: activePreviewMode === 'simulation' ? '68%' : '78%' }}></div>
                  </div>
                  <div className="schematic-building-anchor">
                    <div className="building-box">
                      <div className="building-icon"><Zap size={13} /></div>
                      <div className="building-meta">
                        <span className="building-name">BLD-PHOENIX-01</span>
                        <span className="building-power">{activePreviewMode === 'simulation' ? '4,862.0 kW' : '4,910.4 kW'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="schematic-segment bottom">
                    <span className="seg-name">SEG-NR-WB-01 (Nagar Rd WB)</span>
                    <span className="seg-speed">{activePreviewMode === 'simulation' ? '31.8 km/h' : '26.4 km/h'}</span>
                    <div className="seg-flow-bar" style={{ width: activePreviewMode === 'simulation' ? '72%' : '84%' }}></div>
                  </div>
                </div>

                <div className="schematic-intersection east">
                  <div className="node-marker">INT-SN-01</div>
                  <div className="node-label">Somnath Nagar Chowk</div>
                  <span className="node-status-pill green">Coordinated (110s)</span>
                </div>
              </div>
            </div>

            {/* Real-Time Corridor Telemetry Matrix */}
            <div className="preview-telemetry-grid">
              <div className="preview-metric">
                <span className="metric-label">Corridor Speed</span>
                <span className="metric-value font-mono">{activePreviewMode === 'simulation' ? '33.0 km/h' : '27.5 km/h'}</span>
                <span className="metric-provenance simulation">Mode: {activePreviewMode.toUpperCase()}</span>
              </div>
              <div className="preview-metric">
                <span className="metric-label">Commercial Peak Load</span>
                <span className="metric-value font-mono">4,862 kW</span>
                <span className="metric-provenance live">HVAC Cooling: 62%</span>
              </div>
              <div className="preview-metric">
                <span className="metric-label">Conformal Uncertainty</span>
                <span className="metric-value font-mono">± 3.4 km/h</span>
                <span className="metric-provenance predicted">90% Coverage Band</span>
              </div>
              <div className="preview-metric">
                <span className="metric-label">Actuation Authority</span>
                <span className="metric-value font-mono text-success">Read-Only</span>
                <span className="metric-provenance replay">Advisory Mode</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 3. Mandatory B11 Tagline Reveal Section */}
      <section className="landing-tagline-section" ref={taglineSectionRef}>
        <div className="landing-tagline-container">
          <p className="landing-tagline-copy">
            {taglineWords.map((word, idx) => (
              <span
                key={idx}
                className={`tagline-word ${idx < illuminatedCount ? 'illuminated' : 'dim'}`}
              >
                {word}{' '}
              </span>
            ))}
          </p>
        </div>
      </section>

      {/* 4. Core Pillars Section (Asymmetric Grid) */}
      <section id="pillars" className="landing-section" ref={(el) => (revealRefs.current[0] = el)}>
        <div className="section-header">
          <span className="section-eyebrow">Corridor Capabilities</span>
          <h2 className="section-title">Four architectural pillars engineered for municipal rigor</h2>
          <p className="section-subtitle">
            Purpose-built to replace speculative dashboards with deterministic, reproducible urban engineering.
          </p>
        </div>

        <div className="pillars-asymmetric-grid">
          {/* Card 1: Traffic Velocity */}
          <div className="pillar-card large-feature">
            <div className="pillar-icon-wrapper">
              <Car size={22} color="var(--color-primary)" />
            </div>
            <h3 className="pillar-title">Traffic Velocity Synchronization</h3>
            <p className="pillar-desc">
              Continuous microscopic velocity tracking across 10 corridor segments on Nagar Road. Calibrated with physics-grounded SUMO simulation feeds and historical loop-detector replays.
            </p>
            <div className="pillar-metrics-strip">
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">1.8 km</span>
                <span className="stat-desc">Arterial length</span>
              </div>
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">10</span>
                <span className="stat-desc">Monitored segments</span>
              </div>
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">2</span>
                <span className="stat-desc">Signalized junctions</span>
              </div>
            </div>
            <button className="pillar-action-link" onClick={() => onLaunchConsole('traffic')}>
              <span>View Traffic Analytics</span>
              <ArrowRight size={13} />
            </button>
          </div>

          {/* Card 2: Commercial Energy */}
          <div className="pillar-card">
            <div className="pillar-icon-wrapper">
              <Zap size={22} color="var(--color-warning)" />
            </div>
            <h3 className="pillar-title">Commercial Energy Intelligence</h3>
            <p className="pillar-desc">
              High-resolution commercial load profiling for the Phoenix Marketcity building zone. Correlates outdoor temperature, solar irradiation, and commuter ingress with building cooling demand.
            </p>
            <div className="pillar-meta-badge">
              <span className="font-mono">4,862 kW Peak • 15m Horizon</span>
            </div>
            <button className="pillar-action-link" onClick={() => onLaunchConsole('energy')}>
              <span>Inspect Building Load</span>
              <ArrowRight size={13} />
            </button>
          </div>

          {/* Card 3: Conformal ML & XAI */}
          <div className="pillar-card">
            <div className="pillar-icon-wrapper">
              <Cpu size={22} color="var(--color-accent-violet)" />
            </div>
            <h3 className="pillar-title">Conformal Uncertainty & XAI</h3>
            <p className="pillar-desc">
              Never accept bare point forecasts. All travel velocity forecasts feature 80% and 90% conformal prediction intervals and top-5 TreeSHAP local feature attributions.
            </p>
            <div className="pillar-meta-badge">
              <span className="font-mono">Coverage 90% • PSI Drift Guard</span>
            </div>
            <button className="pillar-action-link" onClick={() => onLaunchConsole('scenarios')}>
              <span>Explore Scenarios</span>
              <ArrowRight size={13} />
            </button>
          </div>

          {/* Card 4: Strict Non-Actuation Advisory */}
          <div className="pillar-card large-feature">
            <div className="pillar-icon-wrapper">
              <ShieldCheck size={22} color="var(--color-success)" />
            </div>
            <h3 className="pillar-title">Strict Non-Actuation Advisory Governance</h3>
            <p className="pillar-desc">
              Complete physical isolation between analytical models and field traffic signal controllers. Recommendations are delivered as structured advisories requiring human authorization outside the platform before any field action.
            </p>
            <div className="pillar-metrics-strip">
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">0</span>
                <span className="stat-desc">Field writes</span>
              </div>
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">100%</span>
                <span className="stat-desc">Human authorized</span>
              </div>
              <div className="pillar-mini-stat">
                <span className="stat-num font-mono">4</span>
                <span className="stat-desc">Municipal roles</span>
              </div>
            </div>
            <button className="pillar-action-link" onClick={() => onLaunchConsole('recommendations')}>
              <span>Inspect Governance Advisories</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </section>

      {/* 5. How It Works Section (3-Step Pipeline) */}
      <section id="how-it-works" className="landing-section dark-alt" ref={(el) => (revealRefs.current[1] = el)}>
        <div className="section-header">
          <span className="section-eyebrow">Execution Pipeline</span>
          <h2 className="section-title">How the corridor twin functions</h2>
          <p className="section-subtitle">
            A three-stage data and simulation architecture enforcing mathematical reproducibility from edge ingestion to municipal decision delivery.
          </p>
        </div>

        <div className="steps-container">
          {/* Step 1 */}
          <div className="step-card">
            <div className="step-number-tag font-mono">01</div>
            <div className="step-content">
              <div className="step-header">
                <Database size={18} color="var(--color-primary)" />
                <h3 className="step-title">Ingest Corridor Telemetry</h3>
              </div>
              <p className="step-description">
                Continuous ingestion of loop detector counts, average segment velocities, weather indices, and building smart meter pulses. Inputs are bound-validated and timestamp-ordered.
              </p>
              <ul className="step-list">
                <li>Physical speed bounds clamp at 0 to 120 km/h</li>
                <li>Strict chronological 80/10/10 ML data splits</li>
                <li>Stale threshold triggers if feed exceeds 180s</li>
              </ul>
            </div>
          </div>

          {/* Step 2 */}
          <div className="step-card">
            <div className="step-number-tag font-mono">02</div>
            <div className="step-content">
              <div className="step-header">
                <Layers size={18} color="var(--color-simulation)" />
                <h3 className="step-title">Enforce Tri-State Separation</h3>
              </div>
              <p className="step-description">
                Authoritative PostgreSQL/TimescaleDB tables guarantee that raw telemetry, SUMO physics outputs, and machine learning inferences remain strictly isolated in distinct storage schemas.
              </p>
              <ul className="step-list">
                <li>Observed twin state is never overwritten</li>
                <li>Simulations are isolated in scenario runs</li>
                <li>Predictions carry conformal confidence intervals</li>
              </ul>
            </div>
          </div>

          {/* Step 3 */}
          <div className="step-card">
            <div className="step-number-tag font-mono">03</div>
            <div className="step-content">
              <div className="step-header">
                <FileText size={18} color="var(--color-success)" />
                <h3 className="step-title">Deliver Calibrated Advisories</h3>
              </div>
              <p className="step-description">
                The advisory rule engine synthesizes traffic queue lengths, transit priority windows, and building cooling loads into prioritized, auditable decision-support advisories.
              </p>
              <ul className="step-list">
                <li>Signal phase adjustment advisory delivery</li>
                <li>Commercial building peak tariff warning alerts</li>
                <li>Complete municipal audit trail with source mode</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Provenance & Data Honesty Showcase */}
      <section id="provenance" className="landing-section" ref={(el) => (revealRefs.current[2] = el)}>
        <div className="section-header">
          <span className="section-eyebrow">Integrity Contract</span>
          <h2 className="section-title">Strict provenance and data honesty standards</h2>
          <p className="section-subtitle">
            Every dynamic measurement, model output, and visualization badge across the platform is explicitly labeled with its authoritative source mode.
          </p>
        </div>

        <div className="provenance-table-wrapper">
          <table className="provenance-matrix-table">
            <thead>
              <tr>
                <th>Source Mode</th>
                <th>Definition & Operating Contract</th>
                <th>Corridor Example</th>
                <th>Quality Assurance Guarantee</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <span className="mode-badge-cell live">LIVE</span>
                </td>
                <td>Verified direct feed from on-corridor physical sensors or permitted real-time APIs.</td>
                <td className="font-mono">SEG-NR-EB-01 Velocity</td>
                <td>Active freshness verification with sub-180 second heartbeat threshold.</td>
              </tr>
              <tr>
                <td>
                  <span className="mode-badge-cell replay">REPLAY</span>
                </td>
                <td>Historical corridor telemetry played back chronologically from authoritative archives.</td>
                <td className="font-mono">TimeScrubber -30m replay</td>
                <td>Never labeled as live. Preserves exact historical sensor timeline.</td>
              </tr>
              <tr>
                <td>
                  <span className="mode-badge-cell simulation">SIMULATION</span>
                </td>
                <td>Output of behavioral or physics simulation (e.g. microscopic SUMO corridor engine).</td>
                <td className="font-mono">Rain Deluge Scenario</td>
                <td>Never claimed as observed reality. Synthetic kinematics strictly isolated.</td>
              </tr>
              <tr>
                <td>
                  <span className="mode-badge-cell predicted">PREDICTED</span>
                </td>
                <td>Machine learning forecast output with calibrated conformal uncertainty bounds.</td>
                <td className="font-mono">15m Travel Time Forecast</td>
                <td>Always paired with 80%/90% confidence intervals and TreeSHAP attributions.</td>
              </tr>
              <tr>
                <td>
                  <span className="mode-badge-cell stale">STALE</span>
                </td>
                <td>Valid telemetry observation exceeding the allowed freshness threshold.</td>
                <td className="font-mono">Sensors exceeding 180s</td>
                <td>Automatically flagged in amber, blocking stale data from polluting advisory logic.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 7. Organic Corridor Metrics Strip */}
      <section className="landing-stats-strip">
        <div className="stats-strip-container">
          <div className="stat-column">
            <span className="stat-value font-mono">1.8 km</span>
            <span className="stat-label">Arterial Corridor</span>
            <span className="stat-sub">Nagar Road, Pune</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">10</span>
            <span className="stat-label">Monitored Segments</span>
            <span className="stat-sub">Eastbound & Westbound</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">2</span>
            <span className="stat-label">Signalized Nodes</span>
            <span className="stat-sub">INT-VN-01 & INT-SN-01</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">4,862 kW</span>
            <span className="stat-label">Peak Commercial Load</span>
            <span className="stat-sub">Phoenix Marketcity</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono text-success">0</span>
            <span className="stat-label">Field Actuations</span>
            <span className="stat-sub">Read-Only Advisory</span>
          </div>
        </div>
      </section>

      {/* 8. Frequently Asked Questions */}
      <section id="faq" className="landing-section dark-alt" ref={(el) => (revealRefs.current[3] = el)}>
        <div className="section-header">
          <span className="section-eyebrow">Municipal Inquiries</span>
          <h2 className="section-title">Frequently asked questions</h2>
          <p className="section-subtitle">
            Direct, plain-language answers addressing municipal safety, predictive modeling, and system privacy.
          </p>
        </div>

        <div className="faq-container">
          {faqItems.map((item, index) => (
            <div
              key={index}
              className={`faq-card ${activeFaq === index ? 'expanded' : ''}`}
              onClick={() => setActiveFaq(activeFaq === index ? null : index)}
            >
              <div className="faq-question-row">
                <h3 className="faq-question-text">{item.q}</h3>
                <button className="faq-toggle-btn" aria-label="Toggle answer">
                  {activeFaq === index ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
              </div>
              {activeFaq === index && (
                <div className="faq-answer-row">
                  <p className="faq-answer-text">{item.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 9. Final Conversion CTA Section */}
      <section className="landing-final-cta-section">
        <div className="final-cta-card">
          <div className="final-cta-badge">
            <Activity size={14} color="var(--color-primary)" />
            <span>Ready for Municipal Demonstration</span>
          </div>
          <h2 className="final-cta-title">
            Inspect the Nagar Road corridor digital twin live
          </h2>
          <p className="final-cta-subtitle">
            Explore 2D and 3D geospatial views, time scrubber historical replay, microscopic scenario simulations, and commercial energy advisories in real time.
          </p>
          <div className="final-cta-actions">
            <button
              className="landing-btn-large-primary"
              onClick={() => onLaunchConsole('operations')}
            >
              <span>Launch Twin Console</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="landing-btn-large-secondary"
              onClick={() => onLaunchConsole('evaluation')}
            >
              <BarChart3 size={16} />
              <span>Review Pilot Evaluation Report</span>
            </button>
          </div>
        </div>
      </section>

      {/* 10. Semantic Footer */}
      <footer className="landing-footer">
        <div className="footer-top-row">
          <div className="footer-brand-column">
            <div className="footer-brand">
              <Activity size={18} color="var(--color-primary)" />
              <span className="brand-title">Digital Twin Analytics</span>
            </div>
            <p className="footer-description">
              Evidence backed urban decision-support platform for arterial transportation and commercial energy corridor analytics.
            </p>
            <div className="footer-corridor-badge">
              <span>Boundary: Viman Nagar Chowk ↔ Somnath Nagar Chowk (1.8 km)</span>
            </div>
          </div>

          <div className="footer-links-grid">
            <div className="footer-link-group">
              <span className="group-title">Navigation</span>
              <button className="footer-link" onClick={() => onLaunchConsole('operations')}>Operations Console</button>
              <button className="footer-link" onClick={() => onLaunchConsole('traffic')}>Traffic Analytics</button>
              <button className="footer-link" onClick={() => onLaunchConsole('energy')}>Energy Analytics</button>
              <button className="footer-link" onClick={() => onLaunchConsole('scenarios')}>Scenario Studio</button>
            </div>

            <div className="footer-link-group">
              <span className="group-title">Governance</span>
              <button className="footer-link" onClick={() => onLaunchConsole('recommendations')}>Advisory Center</button>
              <button className="footer-link" onClick={() => onLaunchConsole('evaluation')}>Pilot Evaluation</button>
              <button className="footer-link" onClick={() => onLaunchConsole('health')}>System Health</button>
              <button className="footer-link" onClick={() => scrollToAnchor('provenance')}>Provenance Contract</button>
            </div>

            <div className="footer-link-group">
              <span className="group-title">Architecture</span>
              <span className="footer-info">FastAPI & Python 3.12</span>
              <span className="footer-info">TimescaleDB & PostgreSQL</span>
              <span className="footer-info">CesiumJS & MapLibre GL</span>
              <span className="footer-info">SUMO Physics Simulation</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom-row">
          <div className="footer-legal">
            <span>Decision Support Demonstration • Strictly Non-Actuating • Pune Smart City</span>
          </div>
          <div className="footer-status font-mono">
            <span className="status-dot"></span>
            <span>System Status: Authoritative Seed Active (100% Provenance Compliance)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
