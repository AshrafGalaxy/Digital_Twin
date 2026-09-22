import React, { useEffect, useState, useMemo } from 'react';
import { Header, TabId } from './components/Header';
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

  // Theme State per DESIGN_SYSTEM.md §4 (Light / Dark Switcher)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  });

  // Sync theme attribute on <html> document element and persist in localStorage
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Screen Reader Live Announcement per WCAG 2.1 AA (Criteria 4.1.3 Status Messages)
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>(
    'Corridor decision-support platform initialized. Source mode: SIMULATION.'
  );

  // Historical Time Scrubber State (P1-B)
  const [scrubberMinutesAgo, setScrubberMinutesAgo] = useState<number>(0);
  const [isScrubberPlaying, setIsScrubberPlaying] = useState<boolean>(false);
  const [scrubberSpeed, setScrubberSpeed] = useState<number>(1);
  const [historicalStates, setHistoricalStates] = useState<Record<string, EntityCurrentState>>({});

  // Fetch historical snapshot when scrubber position changes
  useEffect(() => {
    if (scrubberMinutesAgo > 0) {
      fetchHistoricalSnapshot(scrubberMinutesAgo)
        .then((snapshot) => {
          if (snapshot && snapshot.length > 0) {
            const map: Record<string, EntityCurrentState> = {};
            snapshot.forEach(s => { map[s.entityId] = s; });
            setHistoricalStates(map);
          }
        })
        .catch(err => console.error('Historical snapshot fetch error:', err));
    }
  }, [scrubberMinutesAgo]);

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
        if (data.eventType === 'TRAFFIC_STATE_UPDATED') {
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

    if (segmentStates.length === 0) {
      return {
        avgSpeed: 42.5,
        congestionIndex: 0.15,
        energyDemandKw: 4850.0,
        activeSensors: 10
      };
    }

    const totalSpeed = segmentStates.reduce((acc, m) => acc + (m?.averageSpeedKmh || 45.0), 0);
    const totalCongestion = segmentStates.reduce((acc, m) => acc + (m?.congestionIndex || 0.1), 0);

    return {
      avgSpeed: totalSpeed / segmentStates.length,
      congestionIndex: totalCongestion / segmentStates.length,
      energyDemandKw: 5120.0,
      activeSensors: 10
    };
  }, [roadSegments, effectiveStates]);

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
        theme={theme}
        onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
      />

      <main id="main-content" tabIndex={-1} className="workspace" aria-label="Main Operational Workspace">
        {/* VIEW 1: Operations Map & Live Corridor Overview */}
        {activeTab === 'operations' && (
          <div className="operations-view-layout">
            <CorridorMetricsCard
              averageSpeed={aggregates.avgSpeed}
              congestionIndex={aggregates.congestionIndex}
              energyDemandKw={aggregates.energyDemandKw}
              activeSensors={aggregates.activeSensors}
              sourceMode={effectiveMode}
            />

            <MapOperationsView
              studyAreaGeoJson={studyAreaGeoJson}
              roadSegments={roadSegments}
              intersections={intersections}
              liveStates={effectiveStates}
              selectedEntity={selectedEntity}
              compareEntity={compareEntity}
              currentTheme={theme}
              onSelectEntity={(entity) => {
                setSelectedEntity(entity);
                if (compareEntity && compareEntity.id === entity.id) {
                  setCompareEntity(null);
                }
              }}
              onSelectCompareEntity={(comp) => setCompareEntity(comp)}
            />

            <MapLegend />

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
            <TimeScrubber
              minutesAgo={scrubberMinutesAgo}
              isPlaying={isScrubberPlaying}
              playbackSpeed={scrubberSpeed}
              onScrubChange={(mins) => {
                setScrubberMinutesAgo(mins);
                controlReplaySession({ action: 'seek', minutes_ago: mins });
              }}
              onTogglePlay={() => {
                const nextPlaying = !isScrubberPlaying;
                setIsScrubberPlaying(nextPlaying);
                controlReplaySession({ action: nextPlaying ? 'play' : 'pause', minutes_ago: scrubberMinutesAgo });
              }}
              onSpeedChange={(spd) => {
                setScrubberSpeed(spd);
                controlReplaySession({ action: 'speed', speed: spd });
              }}
              onJumpToLive={() => {
                setScrubberMinutesAgo(0);
                setIsScrubberPlaying(false);
                controlReplaySession({ action: 'jump_to_live' });
              }}
            />
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
      </main>
    </div>
  );
};


