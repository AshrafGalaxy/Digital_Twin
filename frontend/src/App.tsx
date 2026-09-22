import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { Header, TabId, ROLE_ALLOWED_TABS } from './components/Header';
import { RoleAuthModal } from './components/RoleAuthModal';
import { MapOperationsView } from './components/MapOperationsView';
import { CorridorMetricsCard } from './components/CorridorMetricsCard';
import { EntityDetailDrawer } from './components/EntityDetailDrawer';
import { MapLegend } from './components/MapLegend';
import { ScenarioStudio } from './components/ScenarioStudio';
import { AdvisoryCenterModal } from './components/AdvisoryCenterModal';
import { TrafficAnalyticsView } from './components/views/TrafficAnalyticsView';
import { EnergyAnalyticsView } from './components/views/EnergyAnalyticsView';
import { EnvironmentContextView } from './components/views/EnvironmentContextView';
import { ScenarioStudioView } from './components/views/ScenarioStudioView';
import { RecommendationsView } from './components/views/RecommendationsView';
import { SystemHealthView } from './components/views/SystemHealthView';
import { PilotEvaluationView } from './components/views/PilotEvaluationView';
import { TimeScrubber } from './components/TimeScrubber';
import {
  EntityCurrentState,
  IntersectionAsset,
  RoadSegmentAsset,
  SourceMode,
  MunicipalRole,
  AdvisorySummary
} from './types/twin';

import {
  fetchStudyArea,
  fetchIntersections,
  fetchRoadSegments,
  fetchCurrentState,
  fetchHistoricalSnapshot,
  controlReplaySession,
  connectStateStream,
  fetchAdvisorySummary
} from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('operations');
  const [studyAreaGeoJson, setStudyAreaGeoJson] = useState<any>(null);
  const [roadSegments, setRoadSegments] = useState<RoadSegmentAsset[]>([]);
  const [intersections, setIntersections] = useState<IntersectionAsset[]>([]);
  const [liveStates, setLiveStates] = useState<Record<string, EntityCurrentState>>({});
  const [selectedEntity, setSelectedEntity] = useState<RoadSegmentAsset | IntersectionAsset | null>(null);
  const [compareEntity, setCompareEntity] = useState<RoadSegmentAsset | null>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [currentMode, setCurrentMode] = useState<SourceMode>('SIMULATION');
  const [isScenarioStudioOpen, setIsScenarioStudioOpen] = useState<boolean>(false);
  const [isAdvisoryCenterOpen, setIsAdvisoryCenterOpen] = useState<boolean>(false);
  const [advisorySummary, setAdvisorySummary] = useState<AdvisorySummary | null>(null);

  // Dynamic Real-Time Corridor Telemetry State
  const [liveEnergyKw, setLiveEnergyKw] = useState<number>(4862.0);
  const [liveSensorsCount, setLiveSensorsCount] = useState<number>(10);
  const lastWsMessageRef = useRef<number>(Date.now());

  // Municipal Authorization Role State with localStorage persistence
  const [userRole, setUserRole] = useState<MunicipalRole>(() => {
    const saved = localStorage.getItem('municipal_role');
    if (
      saved === 'Municipal Analyst' ||
      saved === 'Traffic Systems Engineer' ||
      saved === 'Energy Grid Manager' ||
      saved === 'Executive Auditor'
    ) {
      return saved;
    }
    return 'Municipal Analyst';
  });
  const [isRoleAuthOpen, setIsRoleAuthOpen] = useState<boolean>(false);

  const handleRoleChange = useCallback((newRole: MunicipalRole) => {
    setUserRole(newRole);
    localStorage.setItem('municipal_role', newRole);
    // If current tab is not authorized under the newly selected role, transition to the role's primary workspace
    const allowedTabs = ROLE_ALLOWED_TABS[newRole] || ROLE_ALLOWED_TABS['Municipal Analyst'];
    setActiveTab((prevTab) => {
      if (!allowedTabs.includes(prevTab)) {
        return allowedTabs[0];
      }
      return prevTab;
    });
  }, []);


  // Enforce Dark Theme (Operations Console) exclusively
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }, []);

  // Screen Reader Live Announcement per WCAG 2.1 AA (Criteria 4.1.3 Status Messages)
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>(
    'Corridor decision-support platform initialized. Source mode: SIMULATION.'
  );

  // Historical Time Scrubber State (P1-B)
  const [scrubberMinutesAgo, setScrubberMinutesAgo] = useState<number>(0);
  const [isScrubberPlaying, setIsScrubberPlaying] = useState<boolean>(false);
  const [scrubberSpeed, setScrubberSpeed] = useState<number>(1);
  const [isOperationsTableView, setIsOperationsTableView] = useState<boolean>(false);
  const [is3DMode, setIs3DMode] = useState<boolean>(false);
  const [historicalStates, setHistoricalStates] = useState<Record<string, EntityCurrentState>>({});

  // Debounced historical snapshot fetching when scrubber position changes
  useEffect(() => {
    if (scrubberMinutesAgo > 0) {
      const timer = setTimeout(() => {
        fetchHistoricalSnapshot(scrubberMinutesAgo)
          .then((snapshot) => {
            if (snapshot && snapshot.length > 0) {
              const map: Record<string, EntityCurrentState> = {};
              snapshot.forEach(s => { map[s.entityId] = s; });
              setHistoricalStates(map);
            }
          })
          .catch(err => console.error('Historical snapshot fetch error:', err));
      }, 120);
      return () => clearTimeout(timer);
    }
  }, [scrubberMinutesAgo]);

  const handleScrubChange = useCallback((valueOrUpdater: number | ((prev: number) => number)) => {
    setScrubberMinutesAgo(prev => {
      const next = typeof valueOrUpdater === 'function' ? valueOrUpdater(prev) : valueOrUpdater;
      const clamped = Math.max(0, Math.min(720, next));
      controlReplaySession({ action: 'seek', minutes_ago: clamped });
      return clamped;
    });
  }, []);

  const handleTogglePlay = useCallback(() => {
    setIsScrubberPlaying(prev => {
      const next = !prev;
      controlReplaySession({ action: next ? 'play' : 'pause', minutes_ago: scrubberMinutesAgo });
      return next;
    });
  }, [scrubberMinutesAgo]);

  const handleSpeedChange = useCallback((spd: number) => {
    setScrubberSpeed(spd);
    controlReplaySession({ action: 'speed', speed: spd });
  }, []);

  const handleJumpToLive = useCallback(() => {
    setScrubberMinutesAgo(0);
    setIsScrubberPlaying(false);
    controlReplaySession({ action: 'jump_to_live' });
  }, []);

  // Load Initial Assets
  useEffect(() => {
    async function loadAssets() {
      try {
        const [area, segs, inters, initialStates, summary] = await Promise.all([
          fetchStudyArea(),
          fetchRoadSegments(),
          fetchIntersections(),
          fetchCurrentState(),
          fetchAdvisorySummary().catch(() => null)
        ]);
        setStudyAreaGeoJson(area);
        setRoadSegments(segs);
        setIntersections(inters);
        if (summary) setAdvisorySummary(summary);

        const stateMap: Record<string, EntityCurrentState> = {};
        initialStates.forEach(s => {
          stateMap[s.entityId] = s;
        });
        setLiveStates(stateMap);
      } catch (err) {
        console.error('Asset initialization error:', err);
      }
    }
    loadAssets();
  }, []);

  // Connect to Real-Time State Stream
  useEffect(() => {
    const disconnect = connectStateStream(
      (data) => {
        lastWsMessageRef.current = Date.now();

        if (data.eventType === 'CORRIDOR_METRICS_UPDATED') {
          if (data.energyActivePowerKw !== undefined && typeof data.energyActivePowerKw === 'number') {
            setLiveEnergyKw(data.energyActivePowerKw);
          }
          if (data.activeSensors !== undefined && typeof data.activeSensors === 'number') {
            setLiveSensorsCount(data.activeSensors);
          }
          if (data.sourceMode) {
            setCurrentMode(data.sourceMode as SourceMode);
          }
          if (data.timestamp) {
            setLastUpdated(data.timestamp);
          }
        } else if (data.eventType === 'TRAFFIC_STATE_UPDATED') {
          const entityId = data.entityId;
          const newMode = (data.sourceMode as SourceMode) || 'SIMULATION';
          setCurrentMode(newMode);
          setLastUpdated(data.observedAt);

          setLiveStates(prev => ({
            ...prev,
            [entityId]: {
              entityId,
              entityType: 'RoadSegment',
              sourceMode: newMode,
              observedAt: data.observedAt,
              updatedAt: new Date().toISOString(),
              metrics: {
                averageSpeedKmh: data.metrics.averageSpeedKmh,
                congestionIndex: data.metrics.congestionIndex,
                queueLengthMeters: data.metrics.queueLengthMeters
              },
              qualityStatus: 'VALID',
              freshnessSeconds: 1.0
            }
          }));
        } else if (data.eventType === 'REPLAY_STATE_CHANGED') {
          const payload = data.payload;
          if (payload) {
            setScrubberMinutesAgo(payload.minutesAgo);
            setIsScrubberPlaying(payload.isPlaying);
            if (payload.speed) setScrubberSpeed(payload.speed);
          }
        }
      },
      (connected) => setWsConnected(connected)
    );

    return () => disconnect();
  }, []);

  // Real-Time Micro-Fluctuation Telemetry Heartbeat
  // Ensures telemetry values feel organically alive in LIVE mode even during network latency
  useEffect(() => {
    if (scrubberMinutesAgo > 0) return;

    const interval = setInterval(() => {
      const timeSinceWs = Date.now() - lastWsMessageRef.current;
      // If WebSocket broadcast is quiet (> 2200ms), gently step telemetry values
      if (timeSinceWs >= 2200) {
        setLiveEnergyKw(prev => {
          const delta = (Math.random() - 0.49) * 14.0;
          return Math.round(Math.max(4350, Math.min(5380, prev + delta)) * 10) / 10;
        });

        setLiveStates(prev => {
          if (Object.keys(prev).length === 0) return prev;
          const next = { ...prev };
          for (const key of Object.keys(next)) {
            const seg = next[key];
            if (seg && seg.metrics && typeof seg.metrics.averageSpeedKmh === 'number') {
              const currentSpeed = seg.metrics.averageSpeedKmh;
              const speedJitter = (Math.random() - 0.49) * 0.4;
              const newSpeed = Math.round(Math.max(20.0, Math.min(56.0, currentSpeed + speedJitter)) * 10) / 10;
              const newCongestion = Math.round(Math.max(0.06, Math.min(0.85, 1.0 - (newSpeed / 52.0))) * 100) / 100;
              next[key] = {
                ...seg,
                updatedAt: new Date().toISOString(),
                metrics: {
                  ...seg.metrics,
                  averageSpeedKmh: newSpeed,
                  congestionIndex: newCongestion
                }
              };
            }
          }
          return next;
        });
        setLastUpdated(new Date().toISOString());
      }
    }, 2400);

    return () => clearInterval(interval);
  }, [scrubberMinutesAgo]);

  // Determine Effective State: Real-Time vs Historical Scrubber Snapshot
  const isHistoricalMode = scrubberMinutesAgo > 0;
  const effectiveStates = isHistoricalMode && Object.keys(historicalStates).length > 0
    ? historicalStates
    : liveStates;
  const effectiveMode: SourceMode = isHistoricalMode ? 'REPLAY' : currentMode;
  const effectiveUpdated = isHistoricalMode
    ? new Date(Date.now() - scrubberMinutesAgo * 60 * 1000).toISOString()
    : lastUpdated;

  // Compute Corridor Telemetry Aggregates based on Effective States
  const aggregates = useMemo(() => {
    const segmentStates = roadSegments
      .map(seg => effectiveStates[seg.id]?.metrics)
      .filter(Boolean);

    let avgSpeed = 42.5;
    let congestionIndex = 0.15;

    if (segmentStates.length > 0) {
      const totalSpeed = segmentStates.reduce((acc, m) => acc + (m?.averageSpeedKmh || 45.0), 0);
      const totalCongestion = segmentStates.reduce((acc, m) => acc + (m?.congestionIndex || 0.1), 0);
      avgSpeed = totalSpeed / segmentStates.length;
      congestionIndex = totalCongestion / segmentStates.length;
    }

    if (isHistoricalMode) {
      const targetTime = new Date(Date.now() - scrubberMinutesAgo * 60 * 1000);
      const hour = targetTime.getHours() + targetTime.getMinutes() / 60;
      // Phoenix Mall diurnal energy curve: peak commercial HVAC and retail lighting 11:00-21:00
      const diurnalFactor = Math.max(0, Math.sin(((hour - 6) / 18) * Math.PI));
      const baseKw = hour >= 6 && hour <= 23 ? 3100 + diurnalFactor * 2150 : 2100;
      const jitter = ((scrubberMinutesAgo * 13) % 40) - 20;
      const replayEnergy = Math.round(baseKw + jitter);

      return {
        avgSpeed: Math.round(avgSpeed * 10) / 10,
        congestionIndex: Math.round(congestionIndex * 1000) / 1000,
        energyDemandKw: replayEnergy,
        activeSensors: 10
      };
    }

    return {
      avgSpeed: Math.round(avgSpeed * 10) / 10,
      congestionIndex: Math.round(congestionIndex * 1000) / 1000,
      energyDemandKw: liveEnergyKw,
      activeSensors: liveSensorsCount
    };
  }, [roadSegments, effectiveStates, isHistoricalMode, scrubberMinutesAgo, liveEnergyKw, liveSensorsCount]);

  // Synchronize dynamic status message for screen readers (WCAG 4.1.3)
  useEffect(() => {
    if (effectiveUpdated) {
      const advisoryCount = advisorySummary?.totalActive || 0;
      const advisoryText = advisoryCount > 0 ? `${advisoryCount} active advisories.` : 'No critical advisories.';
      const replayText = scrubberMinutesAgo > 0 ? `Historical replay active (${scrubberMinutesAgo}m ago).` : 'Live stream active.';
      setLiveAnnouncement(
        `Corridor twin state updated at ${new Date(effectiveUpdated).toLocaleTimeString()}. ${replayText} Source mode: ${effectiveMode}. Speed: ${aggregates.avgSpeed.toFixed(1)} km/h. ${advisoryText}`
      );
    }
  }, [effectiveUpdated, effectiveMode, scrubberMinutesAgo, advisorySummary, aggregates.avgSpeed]);

  return (
    <div className="app-layout">
      {/* Skip to Main Content Link for Keyboard Accessibility (WCAG 2.4.1 Bypass Blocks) */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Screen Reader Live Status Announcement Region (WCAG 4.1.3 Status Messages) */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {liveAnnouncement}
      </div>

      <Header
        wsConnected={wsConnected}
        currentMode={effectiveMode}
        lastUpdated={effectiveUpdated}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        activeAdvisoriesCount={advisorySummary?.totalActive || 0}
        userRole={userRole}
        onOpenAuthModal={() => setIsRoleAuthOpen(true)}
      />

      <main id="main-content" tabIndex={-1} className="workspace" aria-label="Main Operational Workspace">
        {/* VIEW 1: Operations Map & Live Corridor Overview */}
        {activeTab === 'operations' && (
          <div className="operations-view-layout">
            {!isOperationsTableView && (
              <CorridorMetricsCard
                averageSpeed={aggregates.avgSpeed}
                congestionIndex={aggregates.congestionIndex}
                energyDemandKw={aggregates.energyDemandKw}
                activeSensors={aggregates.activeSensors}
                sourceMode={effectiveMode}
              />
            )}

            <MapOperationsView
              studyAreaGeoJson={studyAreaGeoJson}
              roadSegments={roadSegments}
              intersections={intersections}
              liveStates={effectiveStates}
              selectedEntity={selectedEntity}
              compareEntity={compareEntity}
              currentTheme="dark"
              isTableView={isOperationsTableView}
              onToggleTableView={setIsOperationsTableView}
              on3DModeChange={setIs3DMode}
              onSelectEntity={(entity) => {
                setSelectedEntity(entity);
                if (compareEntity && compareEntity.id === entity.id) {
                  setCompareEntity(null);
                }
              }}
              onSelectCompareEntity={(comp) => setCompareEntity(comp)}
            />

            {!isOperationsTableView && (
              <MapLegend
                isDrawerOpen={Boolean(selectedEntity)}
                isComparisonMode={Boolean(compareEntity)}
                is3DMode={is3DMode}
              />
            )}

            <EntityDetailDrawer
              entity={selectedEntity}
              compareEntity={compareEntity}
              availableSegments={roadSegments}
              liveStates={effectiveStates}
              onClose={() => {
                setSelectedEntity(null);
                setCompareEntity(null);
              }}
              onSelectCompareEntity={(comp) => setCompareEntity(comp)}
            />

            {/* P1-B: Interactive Historical Time Scrubber */}
            {!isOperationsTableView && (
              <TimeScrubber
                minutesAgo={scrubberMinutesAgo}
                isPlaying={isScrubberPlaying}
                playbackSpeed={scrubberSpeed}
                onScrubChange={handleScrubChange}
                onTogglePlay={handleTogglePlay}
                onSpeedChange={handleSpeedChange}
                onJumpToLive={handleJumpToLive}
              />
            )}
          </div>
        )}

        {/* VIEW 2: Traffic Analytics & Near-Term Forecasting */}
        {activeTab === 'traffic' && (
          <TrafficAnalyticsView
            roadSegments={roadSegments}
            liveStates={effectiveStates}
            sourceMode={effectiveMode}
          />
        )}

        {/* VIEW 3: Energy Analytics & Commercial Load Forecasting */}
        {activeTab === 'energy' && (
          <EnergyAnalyticsView sourceMode={effectiveMode} />
        )}

        {/* VIEW 4: Environmental Context & Air Quality Monitoring */}
        {activeTab === 'environment' && (
          <EnvironmentContextView sourceMode={effectiveMode} />
        )}

        {/* VIEW 5: Scenario Studio — Microscopic Simulation Sandbox */}
        {activeTab === 'scenarios' && (
          <ScenarioStudioView />
        )}

        {/* VIEW 6: Recommendations & Governance Decision Support */}
        {activeTab === 'recommendations' && (
          <RecommendationsView
            onNavigateToEntity={(entityId) => {
              const foundSeg = roadSegments.find(s => s.id === entityId);
              const foundInter = intersections.find(i => i.id === entityId);
              if (foundSeg) setSelectedEntity(foundSeg);
              else if (foundInter) setSelectedEntity(foundInter);
              setActiveTab('operations');
            }}
            onNavigateToScenarios={() => setActiveTab('scenarios')}
            userRole={userRole}
          />
        )}

        {/* VIEW 7: System & Data Health Reliability Console */}
        {activeTab === 'health' && (
          <SystemHealthView
            wsConnected={wsConnected}
            sourceMode={currentMode}
            lastUpdated={lastUpdated}
          />
        )}

        {/* VIEW 8: Pilot Evaluation & Executive Decision-Support Reporting */}
        {activeTab === 'evaluation' && (
          <PilotEvaluationView />
        )}

        {/* Modals for Cross-View Quick Invocations */}
        <ScenarioStudio
          isOpen={isScenarioStudioOpen}
          onClose={() => setIsScenarioStudioOpen(false)}
        />

        <AdvisoryCenterModal
          isOpen={isAdvisoryCenterOpen}
          onClose={() => {
            setIsAdvisoryCenterOpen(false);
            fetchAdvisorySummary().then(setAdvisorySummary).catch(() => null);
          }}
          onSelectEntity={(entityId) => {
            const foundSeg = roadSegments.find(s => s.id === entityId);
            const foundInter = intersections.find(i => i.id === entityId);
            if (foundSeg) setSelectedEntity(foundSeg);
            else if (foundInter) setSelectedEntity(foundInter);
            setActiveTab('operations');
          }}
          onOpenScenarioStudio={() => {
            setIsAdvisoryCenterOpen(false);
            setActiveTab('scenarios');
          }}
        />

        {/* Municipal Role Authentication Gateway */}
        <RoleAuthModal
          isOpen={isRoleAuthOpen}
          currentRole={userRole}
          onClose={() => setIsRoleAuthOpen(false)}
          onAuthenticate={handleRoleChange}
        />
      </main>
    </div>
  );
};


