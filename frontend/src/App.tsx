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
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [currentMode, setCurrentMode] = useState<SourceMode>('SIMULATION');
  const [isScenarioStudioOpen, setIsScenarioStudioOpen] = useState<boolean>(false);
  const [isAdvisoryCenterOpen, setIsAdvisoryCenterOpen] = useState<boolean>(false);
  const [advisorySummary, setAdvisorySummary] = useState<AdvisorySummary | null>(null);

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
        }
      },
      (connected) => setWsConnected(connected)
    );

    return () => disconnect();
  }, []);

  // Compute Corridor Telemetry Aggregates
  const aggregates = useMemo(() => {
    const segmentStates = roadSegments
      .map(seg => liveStates[seg.id]?.metrics)
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
  }, [roadSegments, liveStates]);

  const activeEntityState = selectedEntity ? liveStates[selectedEntity.id] || null : null;

  return (
    <div className="app-layout">
      <Header
        wsConnected={wsConnected}
        currentMode={currentMode}
        lastUpdated={lastUpdated}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        activeAdvisoriesCount={advisorySummary?.totalActive || 0}
      />

      <main className="workspace">
        {/* VIEW 1: Operations Map & Live Corridor Overview */}
        {activeTab === 'operations' && (
          <div className="operations-view-layout">
            <CorridorMetricsCard
              averageSpeed={aggregates.avgSpeed}
              congestionIndex={aggregates.congestionIndex}
              energyDemandKw={aggregates.energyDemandKw}
              activeSensors={aggregates.activeSensors}
              sourceMode={currentMode}
            />

            <MapOperationsView
              studyAreaGeoJson={studyAreaGeoJson}
              roadSegments={roadSegments}
              intersections={intersections}
              liveStates={liveStates}
              onSelectEntity={(entity) => setSelectedEntity(entity)}
            />

            <MapLegend />

            <EntityDetailDrawer
              entity={selectedEntity}
              liveState={activeEntityState}
              onClose={() => setSelectedEntity(null)}
            />
          </div>
        )}

        {/* VIEW 2: Traffic Analytics & Near-Term Forecasting */}
        {activeTab === 'traffic' && (
          <TrafficAnalyticsView
            roadSegments={roadSegments}
            liveStates={liveStates}
            sourceMode={currentMode}
          />
        )}

        {/* VIEW 3: Energy Analytics & Commercial Load Forecasting */}
        {activeTab === 'energy' && (
          <EnergyAnalyticsView sourceMode={currentMode} />
        )}

        {/* VIEW 4: Environmental Context & Air Quality Monitoring */}
        {activeTab === 'environment' && (
          <EnvironmentContextView sourceMode={currentMode} />
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


