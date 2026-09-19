"""
fiware_adapter.py

Smart City Interoperability Adapter for FIWARE Orion-LD and NGSI-LD Context Brokers.
Transforms internal canonical digital twin entities into standard NGSI-LD 1.3 compliant
Context Information payloads with typed Property, Relationship, and GeoProperty structures.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

NGSI_LD_CORE_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
SMART_DATA_MODELS_CONTEXT = "https://smartdatamodels.org/context.jsonld"


class FIWAREOrionLDAdapter:
    """
    Transforms internal digital twin assets into standard NGSI-LD context entities.
    Compatible with FIWARE Orion-LD, Scorpio, and Stellio context brokers.
    """

    @classmethod
    def get_core_context(cls) -> Dict[str, Any]:
        """Returns the local smart city NGSI-LD context specification."""
        return {
            "@context": [
                NGSI_LD_CORE_CONTEXT,
                SMART_DATA_MODELS_CONTEXT,
                {
                    "averageSpeed": "https://smartdatamodels.org/dataModel.Transportation/averageSpeed",
                    "congestionIndex": "https://smartdatamodels.org/dataModel.Transportation/congestionIndex",
                    "queueLength": "https://smartdatamodels.org/dataModel.Transportation/queueLength",
                    "activePower": "https://smartdatamodels.org/dataModel.Energy/activePower",
                    "pm25": "https://smartdatamodels.org/dataModel.Environment/pm25"
                }
            ]
        }

    @classmethod
    def to_ngsi_ld_intersection(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converts an internal intersection dict to an NGSI-LD RoadIntersection entity."""
        coords = item.get("coordinates", [73.9168, 18.5602])
        return {
            "id": item.get("id", "urn:ngsi-ld:Intersection:PUNE:VN-01"),
            "type": "RoadIntersection",
            "@context": [NGSI_LD_CORE_CONTEXT, SMART_DATA_MODELS_CONTEXT],
            "name": {
                "type": "Property",
                "value": item.get("name", "Viman Nagar Chowk")
            },
            "controlType": {
                "type": "Property",
                "value": item.get("controlType", "SIGNALIZED")
            },
            "cycleTimeSec": {
                "type": "Property",
                "value": item.get("cycleTimeSec", 120),
                "unitCode": "SEC"
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": coords
                }
            },
            "connectedSegments": {
                "type": "Relationship",
                "object": item.get("connectedSegments", [])
            }
        }

    @classmethod
    def to_ngsi_ld_road_segment(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converts an internal road segment dict to an NGSI-LD RoadSegment entity."""
        coords = item.get("coordinates", [[73.9168, 18.5602], [73.9280, 18.5630]])
        return {
            "id": item.get("id", "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"),
            "type": "RoadSegment",
            "@context": [NGSI_LD_CORE_CONTEXT, SMART_DATA_MODELS_CONTEXT],
            "name": {
                "type": "Property",
                "value": item.get("name", "Nagar Road Eastbound")
            },
            "lengthMeters": {
                "type": "Property",
                "value": item.get("lengthMeters", 450.0),
                "unitCode": "MTR"
            },
            "freeFlowSpeed": {
                "type": "Property",
                "value": item.get("freeFlowSpeedKmh", 45.0),
                "unitCode": "KMH"
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "LineString",
                    "coordinates": coords
                }
            },
            "startIntersection": {
                "type": "Relationship",
                "object": item.get("startIntersectionId", "")
            },
            "endIntersection": {
                "type": "Relationship",
                "object": item.get("endIntersectionId", "")
            }
        }

    @classmethod
    def to_ngsi_ld_building(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converts an internal commercial building dict to an NGSI-LD Building entity."""
        coords = item.get("coordinates", [73.9172, 18.5618])
        return {
            "id": item.get("id", "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"),
            "type": "Building",
            "@context": [NGSI_LD_CORE_CONTEXT, SMART_DATA_MODELS_CONTEXT],
            "name": {
                "type": "Property",
                "value": item.get("name", "Phoenix Marketcity Mall")
            },
            "category": {
                "type": "Property",
                "value": item.get("category", "COMMERCIAL_RETAIL")
            },
            "floorAreaSqm": {
                "type": "Property",
                "value": item.get("floorAreaSqm", 120000.0),
                "unitCode": "MTK"
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": coords
                }
            }
        }

    @classmethod
    def export_all_entities(cls, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads registered corridor assets and converts them into NGSI-LD entity objects.
        """
        entities: List[Dict[str, Any]] = []

        # 1. Load corridor assets
        corridor_path = DATA_DIR / "samples" / "corridor_assets.json"
        if corridor_path.exists():
            with open(corridor_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if entity_type is None or entity_type.lower() in ["roadintersection", "intersection"]:
                    for item in data.get("intersections", []):
                        entities.append(cls.to_ngsi_ld_intersection(item))
                if entity_type is None or entity_type.lower() in ["roadsegment", "segment"]:
                    for item in data.get("roadSegments", []):
                        entities.append(cls.to_ngsi_ld_road_segment(item))

        # 2. Load energy assets
        energy_path = DATA_DIR / "samples" / "energy_assets.json"
        if energy_path.exists():
            with open(energy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if entity_type is None or entity_type.lower() in ["building"]:
                    for item in data.get("entities", []):
                        entities.append(cls.to_ngsi_ld_building(item))

        return entities
