import React, { useEffect, useState, useMemo } from 'react';
import { Header } from './components/Header';
import { MapOperationsView } from './components/MapOperationsView';
import { CorridorMetricsCard } from './components/CorridorMetricsCard';
import { EntityDetailDrawer } from './components/EntityDetailDrawer';
import { MapLegend } from './components/MapLegend';
import {
  EntityCurrentState,
  IntersectionAsset,
  RoadSegmentAsset,
  SourceMode
} from './types/twin';
import {
  fetchStudyArea,
  fetchIntersections,
  fetchRoadSegments,
  fetchCurrentState,
  connectStateStream
} from './services/api';

export const App: React.FC = () => {
  const [studyAreaGeoJson, setStudyAreaGeoJson] = useState<any>(null);
  const [roadSegments, setRoadSegments] = useState<RoadSegmentAsset[]>([]);
  const [intersections, setIntersections] = useState<IntersectionAsset[]>([]);
  const [liveStates, setLiveStates] = useState<Record<string, EntityCurrentState>>({});
  const [selectedEntity, setSelectedEntity] = useState<RoadSegmentAsset | IntersectionAsset | null>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [currentMode, setCurrentMode] = useState<SourceMode>('SIMULATION');

  // Load Initial Assets
  useEffect(() => {
    async function loadAssets() {
      try {
        const [area, segs, inters, initialStates] = await Promise.all([
          fetchStudyArea(),
          fetchRoadSegments(),
          fetchIntersections(),
          fetchCurrentState()
        ]);
        setStudyAreaGeoJson(area);
        setRoadSegments(segs);
        setIntersections(inters);

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
      />

      <main className="workspace">
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
      </main>
    </div>
  );
};
