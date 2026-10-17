/**
 * corridorConfig.ts
 *
 * Centralized, generalized corridor configuration module for the Digital Twin Platform.
 * In accordance with AGENTS.md Mandatory Generalization Directive:
 * The platform architecture and UI copy remain generalized and modular for any municipal
 * arterial corridor deployment in any city. Reference pilot deployment parameters (Pune Nagar Road)
 * serve strictly as an empirical demonstration instance rather than platform limits.
 */

export interface CorridorConfig {
  id: string;
  name: string;
  shortName: string;
  subTitle: string;
  lengthKm: number;
  city: string;
  state: string;
  country: string;
  referencePilotNotice: string;
  primaryIntersections: {
    id: string;
    name: string;
    shortName: string;
  }[];
}

export const ACTIVE_CORRIDOR_CONFIG: CorridorConfig = {
  id: 'CORRIDOR-PRIMARY-01',
  name: 'Arterial Demonstration Corridor',
  shortName: 'Arterial Corridor',
  subTitle: 'Digital Twin Decision-Support Network',
  lengthKm: 1.8,
  city: 'Reference Pilot Municipality',
  state: 'Maharashtra',
  country: 'IN',
  referencePilotNotice: 'Empirical reference calibration pilot and demonstration instance.',
  primaryIntersections: [
    { id: 'INT-01', name: 'Primary Intersection 01 (Westbound)', shortName: 'Chowk 01' },
    { id: 'INT-02', name: 'Primary Intersection 02 (Eastbound)', shortName: 'Chowk 02' }
  ]
};
