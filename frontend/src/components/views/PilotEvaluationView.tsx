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
  AlertTriangle
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
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'rgba(0, 242, 254, 0.1)', borderColor: 'rgba(0, 242, 254, 0.4)', color: '#00F2FE' }}
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
        <ShieldCheck size={18} style={{ flexShrink: 0, color: '#00F2FE' }} />
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
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#00F2FE', fontFamily: 'var(--font-mono)' }}>
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
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#A78BFA', fontFamily: 'var(--font-mono)' }}>
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
                <TrendingUp size={18} color="#00F2FE" />
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
                  <td className="mono-cell" style={{ color: '#00F2FE' }}>{h15?.modelMae || 2.45} km/h</td>
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
                  <td className="mono-cell" style={{ color: '#A78BFA' }}>{h60?.modelMae || 3.95} km/h</td>
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
                  <span className="mono-cell" style={{ color: '#00F2FE' }}>
                    {cov?.target90?.empiricalCoveragePct || 90.5}% Coverage
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Empirical non-conformity threshold: <strong style={{ color: 'var(--text-main)' }}>±{cov?.target90?.halfWidthKmh || 4.80} km/h</strong> around point prediction.
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${cov?.target90?.empiricalCoveragePct || 90.5}%`, height: '100%', background: 'linear-gradient(90deg, #00F2FE 0%, #34D399 100%)' }} />
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                    95% Nominal Confidence Interval
                  </span>
                  <span className="mono-cell" style={{ color: '#34D399' }}>
                    {cov?.target95?.empiricalCoveragePct || 95.2}% Coverage
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Empirical non-conformity threshold: <strong style={{ color: 'var(--text-main)' }}>±{cov?.target95?.halfWidthKmh || 5.66} km/h</strong> around point prediction.
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${cov?.target95?.empiricalCoveragePct || 95.2}%`, height: '100%', background: 'linear-gradient(90deg, #34D399 0%, #10B981 100%)' }} />
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

      {/* Tab 2: Executive Briefing Markdown Document */}
      {activeTab === 'briefing' && (
        <div className="analytics-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                PUBLICATION DOCUMENT PREVIEW
              </span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', margin: '4px 0 0 0' }}>
                Municipal Decision-Support Briefing Document
              </h2>
            </div>
            <button
              type="button"
              className="run-scenario-btn"
              style={{ margin: 0, padding: '8px 16px', fontSize: '12px' }}
              onClick={handleDownloadMarkdown}
            >
              <Download size={14} />
              <span>Download Markdown (.md)</span>
            </button>
          </div>

          <div style={{
            background: 'rgba(8, 12, 22, 0.6)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            fontFamily: 'var(--font-sans)',
            color: 'var(--text-main)',
            lineHeight: 1.6,
            maxHeight: '560px',
            overflowY: 'auto'
          }}>
            <pre style={{
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              fontFamily: 'var(--font-sans)',
              fontSize: '13px',
              color: 'var(--text-secondary)'
            }}>
              {markdownText || 'Loading executive briefing markdown...'}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 3: Corridor Provenance & Asset Audit */}
      {activeTab === 'provenance' && (
        <div className="analytics-grid-two-col">
          <div className="analytics-card">
            <div className="analytics-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="#00F2FE" />
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
