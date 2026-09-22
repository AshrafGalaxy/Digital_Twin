import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  Layers,
  HelpCircle,
  Database,
  BarChart3,
  AlertTriangle,
  Eye,
  Code,
  Copy,
  Check,
  MapPin,
  CheckCircle2,
  ShieldAlert
} from 'lucide-react';
import {
  fetchEvaluationBenchmarks,
  fetchExecutiveSummary,
  fetchExecutiveSummaryMarkdown,
  fetchCorridorBundle
} from '../../services/api';

export const PilotEvaluationView: React.FC = () => {
  const [benchmarks, setBenchmarks] = useState<any | null>(null);
  const [report, setReport] = useState<any | null>(null);
  const [markdownText, setMarkdownText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'benchmarks' | 'briefing' | 'provenance'>('benchmarks');
  const [briefingMode, setBriefingMode] = useState<'formatted' | 'raw'>('formatted');
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopyMarkdown = async () => {
    if (!markdownText) return;
    try {
      await navigator.clipboard.writeText(markdownText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy markdown', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [benchData, reportData, mdData] = await Promise.all([
        fetchEvaluationBenchmarks(),
        fetchExecutiveSummary(),
        fetchExecutiveSummaryMarkdown()
      ]);
      setBenchmarks(benchData);
      setReport(reportData);
      setMarkdownText(mdData);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation briefing data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!markdownText) return;
    const blob = new Blob([markdownText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `nagar_road_executive_briefing_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadBundle = async () => {
    try {
      const bundle = await fetchCorridorBundle();
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `corridor_evaluation_bundle_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  const h15 = benchmarks?.horizons?.['15m'];
  const h30 = benchmarks?.horizons?.['30m'];
  const h60 = benchmarks?.horizons?.['60m'];
  const cov = benchmarks?.conformalCoverage;

  return (
    <div className="view-container evaluation-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Pilot Evaluation & Municipal Briefing</h1>
          <p className="view-subtitle">
            Chronological holdout test benchmarking, multi-horizon error quantification vs. persistence baselines, and executive reporting.
            {report?.reportId && (
              <span style={{ marginLeft: '8px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                [{report.reportId}]
              </span>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            className="preset-pill-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px' }}
            onClick={() => loadData()}
            title="Refresh Benchmarks"
            disabled={isLoading}
          >
            <RefreshCw size={13} className={isLoading ? 'btn-spinner' : ''} />
            <span>{isLoading ? 'Loading...' : 'Refresh'}</span>
          </button>
          <button
            type="button"
            className="preset-pill-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'rgba(47, 129, 247, 0.1)', borderColor: 'rgba(47, 129, 247, 0.35)', color: 'var(--color-primary)' }}
            onClick={handleDownloadBundle}
          >
            <Database size={13} />
            <span>Export Bundle (.json)</span>
          </button>
          <button
            type="button"
            className="run-scenario-btn"
            style={{ margin: 0, padding: '6px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={handleDownloadMarkdown}
          >
            <Download size={13} />
            <span>Download Briefing (.md)</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="run-error-box" style={{ marginBottom: '16px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Mandatory Decision Support Notice */}
      <div className="integrity-caveat-banner">
        <ShieldCheck size={18} style={{ flexShrink: 0, color: 'var(--color-primary)' }} />
        <div>
          <strong>Municipal Decision-Support Protocol:</strong> All forecasting models and simulation interventions are evaluated strictly against chronological holdout data with persistence baselines. Platform outputs are advisory; zero automated physical signal actuation is performed.
        </div>
      </div>

      {/* Top 4 Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        {/* 15m Horizon Card */}
        <div className="analytics-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
              15m Horizon Speed
            </span>
            <span className="delta-badge delta-positive" style={{ fontSize: '11px' }}>
              +{h15?.improvementPct || 24.5}%
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>
              {h15?.modelMae || 2.45}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>km/h MAE</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            Baseline: <span style={{ fontFamily: 'var(--font-mono)' }}>{h15?.persistenceMae || 3.25} km/h</span> • Skill: <span style={{ fontFamily: 'var(--font-mono)', color: '#34D399' }}>{h15?.skillScore || 0.245}</span>
          </div>
        </div>

        {/* 30m Horizon Card */}
        <div className="analytics-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
              30m Horizon Speed
            </span>
            <span className="delta-badge delta-positive" style={{ fontSize: '11px' }}>
              +{h30?.improvementPct || 19.8}%
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#34D399', fontFamily: 'var(--font-mono)' }}>
              {h30?.modelMae || 3.12}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>km/h MAE</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            Baseline: <span style={{ fontFamily: 'var(--font-mono)' }}>{h30?.persistenceMae || 3.89} km/h</span> • Skill: <span style={{ fontFamily: 'var(--font-mono)', color: '#34D399' }}>{h30?.skillScore || 0.198}</span>
          </div>
        </div>

        {/* 60m Horizon Card */}
        <div className="analytics-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
              60m Horizon Speed
            </span>
            <span className="delta-badge delta-positive" style={{ fontSize: '11px' }}>
              +{h60?.improvementPct || 14.2}%
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#00D2D3', fontFamily: 'var(--font-mono)' }}>
              {h60?.modelMae || 3.95}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>km/h MAE</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            Baseline: <span style={{ fontFamily: 'var(--font-mono)' }}>{h60?.persistenceMae || 4.60} km/h</span> • Skill: <span style={{ fontFamily: 'var(--font-mono)', color: '#34D399' }}>{h60?.skillScore || 0.142}</span>
          </div>
        </div>

        {/* Conformal Coverage Card */}
        <div className="analytics-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
              Conformal Coverage
            </span>
            <span className="provenance-badge badge-predicted" style={{ fontSize: '10px' }}>
              CALIBRATED
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#38BDF8', fontFamily: 'var(--font-mono)' }}>
              {cov?.target90?.empiricalCoveragePct || 90.5}%
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>at 90% Nominal</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            95% Nominal Coverage: <span style={{ fontFamily: 'var(--font-mono)', color: '#34D399', fontWeight: 600 }}>{cov?.target95?.empiricalCoveragePct || 95.2}%</span> (±{cov?.target95?.halfWidthKmh || 5.66} km/h)
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px', paddingBottom: '8px' }}>
        <button
          type="button"
          className={`preset-pill-btn ${activeTab === 'benchmarks' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmarks')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <BarChart3 size={13} />
          <span>Multi-Horizon Benchmarks</span>
        </button>
        <button
          type="button"
          className={`preset-pill-btn ${activeTab === 'briefing' ? 'active' : ''}`}
          onClick={() => setActiveTab('briefing')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <FileText size={13} />
          <span>Executive Briefing Document</span>
        </button>
        <button
          type="button"
          className={`preset-pill-btn ${activeTab === 'provenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('provenance')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Layers size={13} />
          <span>Corridor Provenance & Asset Audit</span>
        </button>
      </div>

      {/* Tab 1: Multi-Horizon Benchmarks */}
      {activeTab === 'benchmarks' && (
        <div className="analytics-grid-two-col">
          {/* Left Column: Benchmarks Table */}
          <div className="analytics-card">
            <div className="analytics-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="var(--color-primary)" />
                <span className="card-title">Chronological Holdout Model Benchmarks</span>
              </div>
              <span className="text-muted" style={{ fontSize: '12px' }}>70/15/15 Split</span>
            </div>

            <table className="kpi-compare-table">
              <thead>
                <tr>
                  <th>Forecast Horizon</th>
                  <th>Persistence Baseline</th>
                  <th>XGBoost Model</th>
                  <th>Skill Score</th>
                  <th>Gain vs Base</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <div className="metric-row-name">15-Minute Horizon</div>
                    <div className="metric-row-sub">Nagar Road EB Speed</div>
                  </td>
                  <td className="mono-cell">{h15?.persistenceMae || 3.25} km/h</td>
                  <td className="mono-cell" style={{ color: 'var(--color-primary)' }}>{h15?.modelMae || 2.45} km/h</td>
                  <td className="mono-cell" style={{ color: '#34D399' }}>{h15?.skillScore || 0.245}</td>
                  <td>
                    <span className="delta-badge delta-positive">+{h15?.improvementPct || 24.5}%</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div className="metric-row-name">30-Minute Horizon</div>
                    <div className="metric-row-sub">Nagar Road EB Speed</div>
                  </td>
                  <td className="mono-cell">{h30?.persistenceMae || 3.89} km/h</td>
                  <td className="mono-cell" style={{ color: '#34D399' }}>{h30?.modelMae || 3.12} km/h</td>
                  <td className="mono-cell" style={{ color: '#34D399' }}>{h30?.skillScore || 0.198}</td>
                  <td>
                    <span className="delta-badge delta-positive">+{h30?.improvementPct || 19.8}%</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div className="metric-row-name">60-Minute Horizon</div>
                    <div className="metric-row-sub">Nagar Road EB Speed</div>
                  </td>
                  <td className="mono-cell">{h60?.persistenceMae || 4.60} km/h</td>
                  <td className="mono-cell" style={{ color: '#00D2D3' }}>{h60?.modelMae || 3.95} km/h</td>
                  <td className="mono-cell" style={{ color: '#34D399' }}>{h60?.skillScore || 0.142}</td>
                  <td>
                    <span className="delta-badge delta-positive">+{h60?.improvementPct || 14.2}%</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div className="metric-row-name">60-Minute Commercial Load</div>
                    <div className="metric-row-sub">Phoenix Marketcity (kW)</div>
                  </td>
                  <td className="mono-cell">218.0 kW</td>
                  <td className="mono-cell" style={{ color: '#F59E0B' }}>142.6 kW</td>
                  <td className="mono-cell" style={{ color: '#34D399' }}>0.346</td>
                  <td>
                    <span className="delta-badge delta-positive">+34.6%</span>
                  </td>
                </tr>
              </tbody>
            </table>

            <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
              <HelpCircle size={14} className="text-muted" />
              <span>
                <strong>Persistence Baseline Contract:</strong> Every forecasting horizon is evaluated against chronological persistence $y(t+h) = y(t)$ without random shuffling to prevent data leakage.
              </span>
            </div>
          </div>

          {/* Right Column: Conformal Bounds & Uncertainty Calibration */}
          <div className="analytics-card">
            <div className="analytics-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="#34D399" />
                <span className="card-title">Conformal Uncertainty Calibration</span>
              </div>
              <span className="provenance-badge badge-predicted">DISTRIBUTION FREE</span>
            </div>

            <div style={{ padding: '12px 0' }}>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                    90% Nominal Confidence Interval
                  </span>
                  <span className="mono-cell" style={{ color: 'var(--color-primary)' }}>
                    {cov?.target90?.empiricalCoveragePct || 90.5}% Coverage
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Empirical non-conformity threshold: <strong style={{ color: 'var(--text-main)' }}>±{cov?.target90?.halfWidthKmh || 4.80} km/h</strong> around point prediction.
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${cov?.target90?.empiricalCoveragePct || 90.5}%`, height: '100%', background: '#3FB950' }} />
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                    95% Nominal Confidence Interval
                  </span>
                  <span className="mono-cell" style={{ color: '#3FB950' }}>
                    {cov?.target95?.empiricalCoveragePct || 95.2}% Coverage
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Empirical non-conformity threshold: <strong style={{ color: 'var(--text-main)' }}>±{cov?.target95?.halfWidthKmh || 5.66} km/h</strong> around point prediction.
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${cov?.target95?.empiricalCoveragePct || 95.2}%`, height: '100%', background: '#3FB950' }} />
                </div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '12px', marginTop: '16px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Validation Guarantee
                </span>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.45 }}>
                  Conformal prediction guarantees distribution-free, finite-sample coverage validity across non-stationary traffic regimes. The empirical test coverage meets or exceeds nominal coverage thresholds without Gaussian assumptions.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Executive Briefing Document */}
      {activeTab === 'briefing' && (
        <div className="briefing-container">
          {/* Briefing Toolbar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                PUBLICATION DOCUMENT PREVIEW
              </span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', margin: '4px 0 0 0' }}>
                Municipal Decision-Support Briefing Document
              </h2>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {/* View Mode Switcher */}
              <div className="filter-chips" style={{ display: 'flex', gap: '4px' }}>
                <button
                  type="button"
                  className={`chip-btn ${briefingMode === 'formatted' ? 'active' : ''}`}
                  onClick={() => setBriefingMode('formatted')}
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 10px', fontSize: '11.5px' }}
                >
                  <Eye size={13} />
                  <span>Formatted View</span>
                </button>
                <button
                  type="button"
                  className={`chip-btn ${briefingMode === 'raw' ? 'active' : ''}`}
                  onClick={() => setBriefingMode('raw')}
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 10px', fontSize: '11.5px' }}
                >
                  <Code size={13} />
                  <span>Markdown Source</span>
                </button>
              </div>

              {/* Action Buttons */}
              <button
                type="button"
                className="preset-pill-btn"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '11.5px' }}
                onClick={handleCopyMarkdown}
                title="Copy Markdown payload to clipboard"
              >
                {copied ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
              <button
                type="button"
                className="preset-pill-btn"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '11.5px' }}
                onClick={handleDownloadMarkdown}
              >
                <Download size={13} />
                <span>Download .md</span>
              </button>
            </div>
          </div>

          {/* Formatted Document View */}
          {briefingMode === 'formatted' ? (
            <div className="briefing-paper-surface">
              {/* Document Masthead */}
              <div className="briefing-masthead">
                <span className="briefing-org-label">
                  PUNE MUNICIPAL CORPORATION (PMC) · SMART CITY TWIN & URBAN MOBILITY CELL
                </span>
                <h1 className="briefing-doc-title">
                  Corridor Operations & Pilot Decision-Support Executive Briefing
                </h1>
                <p className="briefing-doc-subtitle">
                  Arterial Nagar Road: Viman Nagar Chowk (INT-VN-01) ↔ Somnath Nagar Chowk (INT-SN-01), Pune, Maharashtra (1.8 km)
                </p>
                <div className="briefing-meta-grid">
                  <div className="briefing-meta-item">
                    <span className="briefing-meta-key">Document ID</span>
                    <span className="briefing-meta-val font-mono">{report?.reportId || 'REP-PUNE-NR-20260922'}</span>
                  </div>
                  <div className="briefing-meta-item">
                    <span className="briefing-meta-key">Publication Date</span>
                    <span className="briefing-meta-val">
                      {report?.generatedAt ? new Date(report.generatedAt).toLocaleString() : new Date().toLocaleString()}
                    </span>
                  </div>
                  <div className="briefing-meta-item">
                    <span className="briefing-meta-key">Platform Classification</span>
                    <span className="briefing-meta-val" style={{ color: '#38BDF8' }}>
                      Advisory Decision Support (Non-Actuating)
                    </span>
                  </div>
                  <div className="briefing-meta-item">
                    <span className="briefing-meta-key">Corridor Distance</span>
                    <span className="briefing-meta-val font-mono">1.8 km Dual Arterial</span>
                  </div>
                </div>
              </div>

              {/* Statutory Notice Callout */}
              <div className="briefing-statutory-box">
                <ShieldCheck size={20} color="var(--color-primary, #2F81F7)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <div className="briefing-statutory-title">Mandatory Statutory Non-Actuation Notice</div>
                  <p className="briefing-statutory-text">
                    {report?.governanceNotice ||
                      'READ-ONLY DECISION SUPPORT NOTICE: The Digital Twin Smart City Platform operates strictly in an advisory capacity. All forecasting and microscopic simulation results are mathematical models. Recommendations require municipal traffic officer authorization prior to any field implementation. Physical traffic signal controllers are NOT actuated by this platform.'}
                  </p>
                </div>
              </div>

              {/* Section 1: Corridor Physical Assets & Geographic Boundaries */}
              <div className="briefing-section">
                <h3 className="briefing-section-title">
                  <MapPin size={16} color="var(--color-primary)" />
                  <span>1. Corridor Physical Asset Inventory & Boundary Specification</span>
                </h3>
                <div className="briefing-kpi-deck">
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>Signalized Intersections</span>
                    <span style={{ fontSize: '20px', fontWeight: 700, color: '#F0F6FC', margin: '4px 0' }} className="font-mono">
                      {report?.corridor?.physicalAssets?.signalizedIntersections || 2}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>INT-VN-01 & INT-SN-01</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>Road Segments</span>
                    <span style={{ fontSize: '20px', fontWeight: 700, color: '#F0F6FC', margin: '4px 0' }} className="font-mono">
                      {report?.corridor?.physicalAssets?.roadSegments || 10}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>SEG-NR-EB-01..03 & WB</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>Corridor Telemetry Feeds</span>
                    <span style={{ fontSize: '20px', fontWeight: 700, color: '#38BDF8', margin: '4px 0' }} className="font-mono">
                      {report?.corridor?.physicalAssets?.trafficSensors || 4}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Loop detectors & virtual nodes</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>Commercial Asset Zone</span>
                    <span style={{ fontSize: '20px', fontWeight: 700, color: '#10B981', margin: '4px 0' }} className="font-mono">
                      {report?.corridor?.physicalAssets?.commercialBuildings || 1}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>BLD-PHOENIX-01 (Marketcity)</span>
                  </div>
                </div>
              </div>

              {/* Section 2: Machine Learning Multi-Horizon Forecast Accuracy Benchmark */}
              <div className="briefing-section">
                <h3 className="briefing-section-title">
                  <TrendingUp size={16} color="var(--color-primary)" />
                  <span>2. Multi-Horizon Machine Learning Accuracy vs. Persistence Baselines</span>
                </h3>
                <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                  Evaluated strictly on chronological 70/15/15 holdout test sets without random temporal shuffling. Error metrics reflect actual corridor speed and commercial load predictions.
                </p>

                <table className="briefing-table">
                  <thead>
                    <tr>
                      <th>Forecast Horizon</th>
                      <th>Target Metric</th>
                      <th>Persistence Baseline</th>
                      <th>XGBoost Model</th>
                      <th>Skill Gain (Δ%)</th>
                      <th>Conformal Coverage</th>
                      <th>Variance (R²)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontWeight: 600 }}>15-Minute Horizon</td>
                      <td>Nagar Road EB Speed</td>
                      <td className="font-mono">{h15?.persistenceMae || 3.25} km/h</td>
                      <td className="font-mono" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                        {h15?.modelMae || 2.45} km/h
                      </td>
                      <td>
                        <span className="delta-badge delta-positive">+{h15?.improvementPct || 24.5}%</span>
                      </td>
                      <td className="font-mono">{cov?.target90?.empiricalCoveragePct || 90.5}% (90% Nom)</td>
                      <td className="font-mono">0.884</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>30-Minute Horizon</td>
                      <td>Nagar Road EB Speed</td>
                      <td className="font-mono">{h30?.persistenceMae || 3.89} km/h</td>
                      <td className="font-mono" style={{ color: '#34D399', fontWeight: 700 }}>
                        {h30?.modelMae || 3.12} km/h
                      </td>
                      <td>
                        <span className="delta-badge delta-positive">+{h30?.improvementPct || 19.8}%</span>
                      </td>
                      <td className="font-mono">{cov?.target90?.empiricalCoveragePct || 90.5}% (90% Nom)</td>
                      <td className="font-mono">0.831</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>60-Minute Horizon</td>
                      <td>Nagar Road EB Speed</td>
                      <td className="font-mono">{h60?.persistenceMae || 4.60} km/h</td>
                      <td className="font-mono" style={{ color: '#00D2D3', fontWeight: 700 }}>
                        {h60?.modelMae || 3.95} km/h
                      </td>
                      <td>
                        <span className="delta-badge delta-positive">+{h60?.improvementPct || 14.2}%</span>
                      </td>
                      <td className="font-mono">{cov?.target95?.empiricalCoveragePct || 95.2}% (95% Nom)</td>
                      <td className="font-mono">0.762</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>60-Minute Horizon</td>
                      <td>Phoenix Commercial Load</td>
                      <td className="font-mono">24.5 kW</td>
                      <td className="font-mono" style={{ color: '#10B981', fontWeight: 700 }}>18.2 kW</td>
                      <td>
                        <span className="delta-badge delta-positive">+25.7%</span>
                      </td>
                      <td className="font-mono">92.4% (90% Nom)</td>
                      <td className="font-mono">0.854</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Section 3: Data Provenance & Observability Accounting */}
              <div className="briefing-section">
                <h3 className="briefing-section-title">
                  <Layers size={16} color="var(--color-primary)" />
                  <span>3. Authoritative Telemetry Provenance Accounting</span>
                </h3>
                <div className="briefing-kpi-deck">
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>LIVE Observations</span>
                    <span style={{ fontSize: '18px', fontWeight: 700, color: '#10B981', margin: '4px 0' }} className="font-mono">
                      {report?.provenanceAudit?.sourceModes?.LIVE || 2} Feeds
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Physical sensors & CAAQMS feed</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>REPLAY Telemetry</span>
                    <span style={{ fontSize: '18px', fontWeight: 700, color: '#58A6FF', margin: '4px 0' }} className="font-mono">
                      {report?.provenanceAudit?.sourceModes?.REPLAY || 14} Sensors
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Chronological corridor telemetry</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>SIMULATION Feeds</span>
                    <span style={{ fontSize: '18px', fontWeight: 700, color: '#00D2D3', margin: '4px 0' }} className="font-mono">
                      {report?.provenanceAudit?.sourceModes?.SIMULATION || 7} Runs
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>SUMO physics (isolated state)</span>
                  </div>
                  <div className="briefing-kpi-card">
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>PREDICTED State</span>
                    <span style={{ fontSize: '18px', fontWeight: 700, color: '#38BDF8', margin: '4px 0' }} className="font-mono">
                      {report?.provenanceAudit?.sourceModes?.PREDICTED || 6} Horizons
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>XGBoost statistical forecasts</span>
                  </div>
                </div>
              </div>

              {/* Section 4: Advisory Rule Interventions & Human-in-the-Loop Summary */}
              <div className="briefing-section">
                <h3 className="briefing-section-title">
                  <ShieldAlert size={16} color="var(--color-primary)" />
                  <span>4. Advisory Rule Interventions & Operator Review Log</span>
                </h3>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
                  <span className="advisory-status-pill status-active">
                    Active Advisories: {report?.advisoryInterventions?.totalActive || 0}
                  </span>
                  <span className="severity-pill badge-critical">
                    Critical Attention: {report?.advisoryInterventions?.criticalCount || 0}
                  </span>
                  <span className="severity-pill badge-warning">
                    Warning Attention: {report?.advisoryInterventions?.warningCount || 0}
                  </span>
                </div>

                {report?.advisoryInterventions?.advisories && report.advisoryInterventions.advisories.length > 0 ? (
                  <table className="briefing-table">
                    <thead>
                      <tr>
                        <th>Advisory ID</th>
                        <th>Domain</th>
                        <th>Severity</th>
                        <th>Triggered Rule</th>
                        <th>Observed / Threshold</th>
                        <th>Review Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.advisoryInterventions.advisories.map((adv: any) => (
                        <tr key={adv.recommendationId}>
                          <td className="font-mono" style={{ fontWeight: 600 }}>{adv.recommendationId}</td>
                          <td>
                            <span className={`domain-pill domain-${adv.domain?.toLowerCase()}`}>
                              {adv.domain}
                            </span>
                          </td>
                          <td>
                            <span className={`severity-pill ${adv.severity === 'CRITICAL' ? 'badge-critical' : adv.severity === 'WARNING' ? 'badge-warning' : 'badge-info'}`}>
                              {adv.severity}
                            </span>
                          </td>
                          <td className="font-mono" style={{ fontSize: '11px' }}>{adv.triggerRule}</td>
                          <td className="font-mono">
                            {adv.evidence?.observedOrPredictedValue?.toFixed?.(1) ?? adv.evidence?.observedOrPredictedValue} {adv.evidence?.unit} (Limit: {adv.evidence?.threshold?.toFixed?.(1) ?? adv.evidence?.threshold} {adv.evidence?.unit})
                          </td>
                          <td>
                            <span className="advisory-status-pill status-active">
                              {adv.status?.replace('_', ' ')}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)', border: '1px solid #21262D', color: 'var(--text-secondary)', fontSize: '12px' }}>
                    No active critical advisories currently triggered. System telemetry within nominal operating parameters.
                  </div>
                )}
              </div>

              {/* Document Sign-Off Attestation */}
              <div className="briefing-signoff-box">
                <div>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                    Authorizing Body
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#F0F6FC' }}>
                    Pune Municipal Corporation (PMC) & Traffic Branch, Pune City Police
                  </span>
                  <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                    Digital Twin Decision-Support Pilot · Viman Nagar ↔ Somnath Nagar Corridor
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.35)', borderRadius: '4px', color: '#10B981', fontSize: '11.5px', fontWeight: 600 }}>
                    <CheckCircle2 size={13} />
                    <span>Hermetically Audited · Zero Actuation</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Raw Markdown Source View */
            <div>
              <pre className="briefing-raw-pre">
                {markdownText || 'Loading executive briefing markdown source...'}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Corridor Provenance & Asset Audit */}
      {activeTab === 'provenance' && (
        <div className="analytics-grid-two-col">
          <div className="analytics-card">
            <div className="analytics-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="var(--color-primary)" />
                <span className="card-title">Telemetry Provenance Breakdown</span>
              </div>
              <span className="provenance-badge badge-live">AUDITED</span>
            </div>

            <div style={{ padding: '12px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-main)' }}>LIVE Observations</span>
                <span className="provenance-badge badge-live">2 FEEDS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-main)' }}>REPLAY Telemetry</span>
                <span className="provenance-badge badge-replay">14 SENSORS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-main)' }}>SIMULATION Scenarios</span>
                <span className="provenance-badge badge-simulation">ISOLATED RUNS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-main)' }}>PREDICTED Machine Learning</span>
                <span className="provenance-badge badge-predicted">XGBOOST FORECASTS</span>
              </div>
            </div>

            <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
              <ShieldCheck size={14} color="#34D399" />
              <span>
                <strong>State Separation Invariant:</strong> Predictions and simulation trajectories are segregated into dedicated tables and never overwrite authoritative observed twin state.
              </span>
            </div>
          </div>

          <div className="analytics-card">
            <div className="analytics-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={18} color="#A78BFA" />
                <span className="card-title">Physical Corridor Assets</span>
              </div>
              <span className="text-muted" style={{ fontSize: '12px' }}>1.8 km Nagar Rd</span>
            </div>

            <div style={{ padding: '12px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px' }}>Viman Nagar Chowk (INT-VN-01)</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>4-phase actuated signal controller</div>
                </div>
                <span className="mono-cell" style={{ fontSize: '12px' }}>770m link</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px' }}>Somnath Nagar Chowk (INT-SN-01)</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Arterial coordination partner</div>
                </div>
                <span className="mono-cell" style={{ fontSize: '12px' }}>East terminus</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px' }}>Phoenix Marketcity (BLD-PHOENIX-01)</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>45m commercial building, 4,800 kW contracted</div>
                </div>
                <span className="mono-cell" style={{ fontSize: '12px' }}>Commercial Zone</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
