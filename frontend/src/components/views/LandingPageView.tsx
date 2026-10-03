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
  FileText,
  Database,
  Lock,
  LogOut,
  Gauge,
  MapPin
} from 'lucide-react';
import { TabId } from '../Header';
import { AuthUser } from '../../types/twin';
import { DigitalTwinLogo } from '../common/DigitalTwinLogo';
import { ArterialWaveAsset } from '../landing/ArterialWaveAsset';
import { EnergyCurveAsset } from '../landing/EnergyCurveAsset';
import { ConformalBandsAsset } from '../landing/ConformalBandsAsset';
import { MicroscopicPhysicsAsset } from '../landing/MicroscopicPhysicsAsset';
import { CorridorDioramaAsset } from '../landing/CorridorDioramaAsset';
import { CorridorAssetsShowcase } from '../landing/CorridorAssetsShowcase';
import { ContactAccessModal } from '../landing/ContactAccessModal';

interface LandingPageViewProps {
  onLaunchConsole: (tab?: TabId) => void;
  onNavigateAuth?: (mode?: 'signin' | 'signup') => void;
  authUser?: AuthUser | null;
  onSignOut?: () => void;
}

export const LandingPageView: React.FC<LandingPageViewProps> = ({
  onLaunchConsole,
  authUser,
  onSignOut
}) => {
  const [activeFaq, setActiveFaq] = useState<number | null>(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState<boolean>(false);

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



  const scrollToAnchor = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const faqItems = [
    {
      q: 'Does this digital twin automatically actuate physical traffic signals or grid switches?',
      a: 'No. The platform operates strictly as read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action. Physical signal controller actuation is strictly prohibited by architectural invariants.'
    },
    {
      q: 'How does the platform enforce state separation between simulation and reality?',
      a: 'Observed telemetry (LIVE/REPLAY), physical SUMO simulation (SIMULATION), and machine learning forecasts (PREDICTED) are partitioned into isolated database tables. Simulations and forecasts can never overwrite observed twin state.'
    },
    {
      q: 'How are new corridors, intersections, and microgrid facilities onboarded?',
      a: 'The platform utilizes modular NGSI-LD semantic schemas. Roadway geometry, detector loops, signal timing plans, and building smart meters are provisioned declaratively through geographic GeoJSON corridors and validated against physical boundary schemas.'
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
      q: 'How do agencies and research partners obtain operational access?',
      a: 'Access to the live operations console is provisioned per authorized agency. Prospective municipal authorities, transit agencies, and research partners can submit an access inquiry via the Request Access intake portal.'
    }
  ];

  return (
    <div className="landing-root">
      {/* Top Header Progressive Gradient Blur Scrim */}
      <div className="landing-nav-scrim" aria-hidden="true" />

      {/* 1. Structured Command Navigation */}
      <nav className="landing-command-nav" aria-label="Main Navigation">
        <div className="landing-nav-inner">
          <div className="landing-nav-brand" onClick={() => scrollToAnchor('hero')}>
            <DigitalTwinLogo size={24} glow />
            <span className="brand-name">Digital Twin</span>
          </div>

          <div className="landing-nav-links">
            <button className="landing-nav-link" onClick={() => scrollToAnchor('pillars')}>Telemetry</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('assets-showcase')}>Physical Assets</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('how-it-works')}>Architecture</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('provenance')}>Provenance</button>
            <button className="landing-nav-link" onClick={() => scrollToAnchor('faq')}>FAQ</button>
          </div>

          <div className="landing-nav-actions">
            {authUser ? (
              <>
                <button
                  type="button"
                  className="landing-btn-signin"
                  onClick={onSignOut}
                  title="Sign out of active session"
                >
                  <LogOut size={13} />
                  <span>Sign Out</span>
                </button>
                <button
                  className="landing-btn-primary"
                  onClick={() => onLaunchConsole('operations')}
                  title="Open real-time digital twin operations dashboard"
                >
                  <span>Dashboard</span>
                  <ArrowRight size={14} />
                </button>
              </>
            ) : (
              <button
                className="landing-btn-primary"
                onClick={() => setIsContactModalOpen(true)}
                title="Request agency access or consultation"
              >
                <span>Request Access</span>
                <ArrowRight size={14} />
              </button>
            )}
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
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('pillars')}>Telemetry</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('assets-showcase')}>Physical Assets</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('how-it-works')}>Architecture</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('provenance')}>Provenance</button>
            <button className="landing-mobile-item" onClick={() => scrollToAnchor('faq')}>FAQ</button>
            {authUser ? (
              <>
                <button className="landing-mobile-item" onClick={onSignOut}>
                  Sign Out
                </button>
                <button className="landing-mobile-item highlight" onClick={() => onLaunchConsole('operations')}>
                  Dashboard <ArrowRight size={14} />
                </button>
              </>
            ) : (
              <button
                className="landing-mobile-item highlight"
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  setIsContactModalOpen(true);
                }}
              >
                Request Access <ArrowRight size={14} />
              </button>
            )}
          </div>
        )}
      </nav>

      {/* 2. Above The Fold Hero Section */}
      <header id="hero" className="landing-hero-section">
        <div className="landing-hero-content">
          {/* Luminous Shimmer Tag */}
          <div className="landing-shimmer-tag">
            <span className="shimmer-pulse-gem"></span>
            <span className="shimmer-tag-title">PRECISION URBAN DIGITAL TWIN</span>
            <span className="shimmer-tag-sep">/</span>
            <span className="shimmer-tag-metric">MULTI-DOMAIN DECISION SUPPORT</span>
          </div>

          {/* Headline per B5 (No hyphens, meaningful breaks, left-to-right gradient) */}
          <h1 className="landing-hero-headline">
            Evidence backed urban decision support for arterial corridors
          </h1>

          {/* Subheadline */}
          <p className="landing-hero-subheadline">
            Synchronize hydrodynamic traffic mobility, commercial building microgrids, environmental air quality, and structural health with mathematical provenance and human-in-the-loop governance.
          </p>

          {/* CTA Group */}
          <div className="landing-cta-group">
            {authUser ? (
              <button
                className="landing-btn-large-primary"
                onClick={() => onLaunchConsole('operations')}
              >
                <span>Dashboard</span>
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                className="landing-btn-large-primary"
                onClick={() => setIsContactModalOpen(true)}
              >
                <span>Request Access</span>
                <ArrowRight size={16} />
              </button>
            )}
            <button
              className="landing-btn-large-secondary"
              onClick={() => scrollToAnchor('how-it-works')}
            >
              <Eye size={16} />
              <span>Explore Architecture</span>
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

        {/* Hero Visual: Contained Telemetry Stage */}
        <div className="landing-hero-stage">
          <div className="hero-stage-card">
            {/* Topbar with Clean Status & Badge */}
            <div className="hero-stage-topbar">
              <div className="hero-stage-status">
                <span className="stage-pulse-dot"></span>
                <span className="stage-status-text font-mono">LIVE TELEMETRY STREAM</span>
              </div>
              <span className="hero-stage-badge font-mono">
                MULTIMODAL ARTERIAL / 1.8 KM
              </span>
            </div>

            <div className="landing-hero-orbit-canvas">
              <div className="orbit-radar-crosshair-x"></div>
              <div className="orbit-radar-crosshair-y"></div>

              {/* High-Precision SVG Orbital Engine with Luminous Comet Trails */}
              <svg
                className="orbit-vector-system"
                viewBox="0 0 400 400"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <defs>
                  {/* Outer Orbit (Cyan) Gradient Trail */}
                  <linearGradient
                    id="orbit-trail-cyan"
                    x1="52"
                    y1="200"
                    x2="200"
                    y2="52"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0" />
                    <stop offset="65%" stopColor="#38BDF8" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.95" />
                  </linearGradient>

                  {/* Mid Orbit (Violet) Gradient Trail */}
                  <linearGradient
                    id="orbit-trail-violet"
                    x1="308"
                    y1="200"
                    x2="200"
                    y2="92"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop offset="0%" stopColor="#A78BFA" stopOpacity="0" />
                    <stop offset="65%" stopColor="#A78BFA" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#A78BFA" stopOpacity="0.95" />
                  </linearGradient>

                  {/* Inner Orbit (Amber) Gradient Trail */}
                  <linearGradient
                    id="orbit-trail-amber"
                    x1="132"
                    y1="200"
                    x2="200"
                    y2="132"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop offset="0%" stopColor="#F59E0B" stopOpacity="0" />
                    <stop offset="65%" stopColor="#F59E0B" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.95" />
                  </linearGradient>

                  {/* Glow Filters for Telemetry Beacons */}
                  <filter id="glow-cyan" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                  <filter id="glow-violet" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                  <filter id="glow-amber" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                {/* Concentric Radar Guideways */}
                <circle
                  cx="200"
                  cy="200"
                  r="148"
                  stroke="rgba(56, 189, 248, 0.16)"
                  strokeWidth="1"
                  strokeDasharray="3 5"
                />
                <circle
                  cx="200"
                  cy="200"
                  r="108"
                  stroke="rgba(167, 139, 250, 0.14)"
                  strokeWidth="1"
                />
                <circle
                  cx="200"
                  cy="200"
                  r="68"
                  stroke="rgba(245, 158, 11, 0.18)"
                  strokeWidth="1"
                  strokeDasharray="2 4"
                />

                {/* Orbit 1: Outer Cyan Satellite (r=148, Clockwise, 7.5s) */}
                <g className="orbit-vector-group orbit-outer-cw">
                  <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="0 200 200"
                    to="360 200 200"
                    dur="7.5s"
                    repeatCount="indefinite"
                  />
                  {/* Sweeping Luminous Comet Trail */}
                  <path
                    d="M 52 200 A 148 148 0 0 1 200 52"
                    stroke="url(#orbit-trail-cyan)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                  {/* Leading Beacon */}
                  <circle cx="200" cy="52" r="9" fill="rgba(56, 189, 248, 0.22)" />
                  <circle cx="200" cy="52" r="4.5" fill="#38BDF8" filter="url(#glow-cyan)" />
                  <circle cx="200" cy="52" r="2" fill="#FFFFFF" />
                </g>

                {/* Orbit 2: Mid Violet Satellite (r=108, Counter-Clockwise, 5.4s) */}
                <g className="orbit-vector-group orbit-mid-ccw">
                  <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="120 200 200"
                    to="-240 200 200"
                    dur="5.4s"
                    repeatCount="indefinite"
                  />
                  {/* Sweeping Luminous Comet Trail */}
                  <path
                    d="M 308 200 A 108 108 0 0 0 200 92"
                    stroke="url(#orbit-trail-violet)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                  {/* Leading Beacon */}
                  <circle cx="200" cy="92" r="8" fill="rgba(167, 139, 250, 0.22)" />
                  <circle cx="200" cy="92" r="4.5" fill="#A78BFA" filter="url(#glow-violet)" />
                  <circle cx="200" cy="92" r="2" fill="#FFFFFF" />
                </g>

                {/* Orbit 3: Inner Amber Satellite (r=68, Clockwise, 3.8s) */}
                <g className="orbit-vector-group orbit-inner-cw">
                  <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="240 200 200"
                    to="600 200 200"
                    dur="3.8s"
                    repeatCount="indefinite"
                  />
                  {/* Sweeping Luminous Comet Trail */}
                  <path
                    d="M 132 200 A 68 68 0 0 1 200 132"
                    stroke="url(#orbit-trail-amber)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                  {/* Leading Beacon */}
                  <circle cx="200" cy="132" r="7" fill="rgba(245, 158, 11, 0.24)" />
                  <circle cx="200" cy="132" r="4" fill="#F59E0B" filter="url(#glow-amber)" />
                  <circle cx="200" cy="132" r="1.8" fill="#FFFFFF" />
                </g>
              </svg>

              <div className="orbit-core">
                <DigitalTwinLogo size={44} glow />
              </div>

              {/* Minimalist Floating Telemetry Cards */}
              <div className="orbit-metric-card orbit-mc-1">
                <span className="orbit-mc-label font-mono">CORRIDOR SPEED</span>
                <span className="orbit-mc-value font-mono">34.2 km/h</span>
                <span className="orbit-mc-tag live">LIVE</span>
              </div>
              <div className="orbit-metric-card orbit-mc-2">
                <span className="orbit-mc-label font-mono">MICROGRID LOAD</span>
                <span className="orbit-mc-value font-mono">4,862 kW</span>
                <span className="orbit-mc-tag live">OBSERVED</span>
              </div>
              <div className="orbit-metric-card orbit-mc-3">
                <span className="orbit-mc-label font-mono">STREAM LATENCY</span>
                <span className="orbit-mc-value font-mono">42 ms</span>
                <span className="orbit-mc-tag simulation">VERIFIED</span>
              </div>
            </div>

            {/* Stage Telemetry Footer Matrix */}
            <div className="hero-stage-footer">
              <div className="stage-footer-item">
                <span className="stage-footer-dot green"></span>
                <span className="stage-footer-label font-mono">INGESTION</span>
                <span className="stage-footer-val font-mono">&lt; 42ms</span>
              </div>
              <div className="stage-footer-item">
                <span className="stage-footer-dot cyan"></span>
                <span className="stage-footer-label font-mono">DATA INTEGRITY</span>
                <span className="stage-footer-val font-mono">100% SHA-256</span>
              </div>
              <div className="stage-footer-item">
                <span className="stage-footer-dot purple"></span>
                <span className="stage-footer-label font-mono">CALIBRATION</span>
                <span className="stage-footer-val font-mono">CONFORMAL 90%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Full-Width Multi-Domain Platform Capabilities Banner */}
        <div className="landing-hero-stats-strip">
          <div className="hero-stat-block">
            <span className="hero-stat-value font-mono">&lt; 100ms</span>
            <span className="hero-stat-label">Telemetry Ingestion Latency</span>
          </div>
          <div className="hero-stat-sep"></div>
          <div className="hero-stat-block">
            <span className="hero-stat-value font-mono">Multi-Domain</span>
            <span className="hero-stat-label">Mobility &amp; Microgrid Sync</span>
          </div>
          <div className="hero-stat-sep"></div>
          <div className="hero-stat-block">
            <span className="hero-stat-value font-mono">Conformal 90%</span>
            <span className="hero-stat-label">Calibrated Forecast Bounds</span>
          </div>
          <div className="hero-stat-sep"></div>
          <div className="hero-stat-block">
            <span className="hero-stat-value font-mono">Strict Separation</span>
            <span className="hero-stat-label">Observed vs Simulated State</span>
          </div>
          <div className="hero-stat-sep"></div>
          <div className="hero-stat-block">
            <span className="hero-stat-value font-mono">Zero PII</span>
            <span className="hero-stat-label">Privacy-Preserving Telemetry</span>
          </div>
        </div>
      </header>

      {/* 3. Operational Integrity & Core Philosophy Section */}
      <section className="landing-tagline-section">
        <div className="landing-tagline-container">
          <div className="tagline-eyebrow font-mono">
            <span className="eyebrow-pulse"></span>
            <span>CORE PHILOSOPHY &amp; OPERATIONAL INTEGRITY</span>
          </div>
          <h2 className="landing-tagline-headline">
            Urban analytics without unverified assertions.
          </h2>
          <p className="landing-tagline-subcopy">
            Every operational insight backed by physical sensors, calibrated conformal bounds, and human-in-the-loop municipal governance.
          </p>
        </div>
      </section>

      {/* 4. Core Capabilities (Interactive Animated Bento Grid) */}
      <section id="pillars" className="landing-section" ref={(el) => (revealRefs.current[0] = el)}>
        <div className="section-header">
          <div className="landing-badge font-mono">
            <Activity size={13} color="var(--color-primary)" />
            <span>MULTI-DOMAIN URBAN TELEMETRY</span>
          </div>
          <h2 className="section-title">High-Fidelity Urban Intelligence Architecture</h2>
          <p className="section-subtitle">
            Engineered with hydrodynamic traffic dynamics, building thermal microgrids, conformal uncertainty envelopes, and strict mathematical provenance.
          </p>
        </div>

        <div className="landing-bento-grid">
          {/* Bento Cell 1: Span 2 cols - Arterial Kinematics Waveform */}
          <div className="bento-card bento-span-2">
            <div className="bento-card-header">
              <div className="bento-title-group">
                <div className="bento-icon-box"><Car size={18} color="var(--color-primary)" /></div>
                <div>
                  <h3 className="bento-title">Hydrodynamic Traffic Mobility & Arterial Progression</h3>
                  <span className="bento-sub font-mono">10 Monitored Segments • Dual Arterial Corridor</span>
                </div>
              </div>
            </div>
            <p className="bento-text">
              Real-time velocity tracking across 10 corridor segments calibrated against physical loop detector arrays and microscopic SUMO traffic simulations.
            </p>
            <ArterialWaveAsset />
          </div>

          {/* Bento Cell 2: Span 1 col - Commercial Building Energy Load */}
          <div className="bento-card bento-span-1">
            <div className="bento-card-header">
              <div className="bento-title-group">
                <div className="bento-icon-box"><Zap size={18} color="var(--color-warning)" /></div>
                <div>
                  <h3 className="bento-title">Commercial Microgrid & Chiller Demands</h3>
                  <span className="bento-sub font-mono">2R-2C ETP Modeling • 15m Telemetry</span>
                </div>
              </div>
            </div>
            <p className="bento-text">
              15-minute interval power profiling with automated pre-cooling advisories to shave 380 kW during peak tariff hours.
            </p>
            <EnergyCurveAsset />
          </div>

          {/* Bento Cell 3: Span 1 col - In-Pavement Ground Sensors */}
          <div className="bento-card bento-span-1">
            <div className="bento-card-header">
              <div className="bento-title-group">
                <div className="bento-icon-box"><Cpu size={18} color="var(--color-accent-violet)" /></div>
                <div>
                  <h3 className="bento-title">In-Pavement Ground Sensors</h3>
                  <span className="bento-sub font-mono">Flush Loop Arrays • Physical Calibration</span>
                </div>
              </div>
            </div>
            <p className="bento-text">
              Precision in-pavement inductive detectors capture vehicle presence, axle counts, and occupancy to establish physical ground truth.
            </p>
            <ConformalBandsAsset />
          </div>

          {/* Bento Cell 4: Span 1 col - Edge Telemetry Cabinets */}
          <div className="bento-card bento-span-1">
            <div className="bento-card-header">
              <div className="bento-title-group">
                <div className="bento-icon-box"><Gauge size={18} color="var(--color-success)" /></div>
                <div>
                  <h3 className="bento-title">Edge Telemetry Cabinets</h3>
                  <span className="bento-sub font-mono">NEMA Enclosures • Field Ingestion</span>
                </div>
              </div>
            </div>
            <p className="bento-text">
              Pole-mounted weatherproof hardware aggregates roadside detector signals and signal phases before transmission to the central pipeline.
            </p>
            <MicroscopicPhysicsAsset />
          </div>

          {/* Bento Cell 5: Span 1 col - Physical Corridor Topology */}
          <div className="bento-card bento-span-1">
            <div className="bento-card-header">
              <div className="bento-title-group">
                <div className="bento-icon-box"><MapPin size={18} color="var(--color-primary-hover)" /></div>
                <div>
                  <h3 className="bento-title">Physical Corridor Topology</h3>
                  <span className="bento-sub font-mono">Architectural Scale Twin • Arterial Spines</span>
                </div>
              </div>
            </div>
            <p className="bento-text">
              Physical illuminated scale replica registering signalized nodes, directional lanes, and the central commercial microgrid facility.
            </p>
            <CorridorDioramaAsset />
          </div>
        </div>
      </section>

      {/* 5. Corridor Physical Assets Interactive Showcase */}
      <CorridorAssetsShowcase />

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
                <td className="font-mono">SEG-01 Arterial Velocity</td>
                <td>Active freshness verification with sub-180 second heartbeat threshold.</td>
              </tr>
              <tr>
                <td>
                  <span className="mode-badge-cell replay">REPLAY</span>
                </td>
                <td>Historical corridor telemetry played back chronologically from authoritative archives.</td>
                <td className="font-mono">Playback -30m Stream</td>
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
            <span className="stat-value font-mono">10 Seg</span>
            <span className="stat-label">Arterial Corridor</span>
            <span className="stat-sub">Dual Direction Topology</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">Multimodal</span>
            <span className="stat-label">Integrated Domains</span>
            <span className="stat-sub">Mobility, Energy & AQI</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">2</span>
            <span className="stat-label">Signalized Nodes</span>
            <span className="stat-sub">Coordinated Phasing</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-column">
            <span className="stat-value font-mono">4,862 kW</span>
            <span className="stat-label">Peak Commercial Load</span>
            <span className="stat-sub">Commercial Microgrid</span>
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
          <span className="section-eyebrow">Common Questions</span>
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
                <div className={`faq-indicator-icon ${activeFaq === index ? 'rotated' : ''}`}>
                  <ChevronDown size={15} />
                </div>
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
            <span>Agency & Municipal Access Intake</span>
          </div>
          <h2 className="final-cta-title">
            Request Access to the Urban Digital Twin Platform
          </h2>
          <p className="final-cta-subtitle">
            Explore 2D and 3D geospatial views, time scrubber historical replay, microscopic scenario simulations, and commercial microgrid advisories with full provenance guarantees.
          </p>
          <div className="final-cta-actions">
            {authUser ? (
              <button
                className="landing-btn-large-primary"
                onClick={() => onLaunchConsole('operations')}
              >
                <span>Dashboard</span>
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                className="landing-btn-large-primary"
                onClick={() => setIsContactModalOpen(true)}
              >
                <span>Request Access</span>
                <ArrowRight size={16} />
              </button>
            )}
            <button
              className="landing-btn-large-secondary"
              onClick={() => scrollToAnchor('how-it-works')}
            >
              <Layers size={16} />
              <span>Explore Architecture</span>
            </button>
          </div>
        </div>
      </section>

      {/* 10. Semantic Footer */}
      <footer className="landing-footer">
        <div className="footer-top-row">
          <div className="footer-brand-column">
            <div className="footer-brand">
              <DigitalTwinLogo size={20} />
              <span className="brand-title">Digital Twin</span>
            </div>
            <p className="footer-description">
              Evidence backed urban decision-support platform for multi-domain transportation and commercial microgrid operations.
            </p>
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
          </div>
        </div>

        <div className="footer-bottom-row">
          <div className="footer-legal">
            <span>Precision Urban Digital Twin • Strictly Non-Actuating Decision Support</span>
          </div>
        </div>
      </footer>

      {/* Enterprise Contact & Access Intake Modal */}
      <ContactAccessModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
        onLaunchConsole={onLaunchConsole}
      />
    </div>
  );
};
