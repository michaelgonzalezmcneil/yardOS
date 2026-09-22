from __future__ import annotations

from typing import Callable, Sequence

from packages.contracts import Detection, Track, TrackPoint


class SimpleTrackingProvider:
    """Baseline association using an optional upstream identity key."""

    def associate_detections(self, detections: Sequence[Detection]) -> dict[str, list[Detection]]:
        groups: dict[str, list[Detection]] = {}
        for detection in detections:
            key = str(detection.metadata.get("identity_key", detection.id))
            groups.setdefault(key, []).append(detection)
        return groups

    def build_tracks(self, site_id: str, groups: dict[str, list[Detection]]) -> list[Track]:
        tracks = []
        for observations in groups.values():
            points = [TrackPoint(timestamp=item.timestamp, geometry_geo=item.centroid_geo, detection_id=item.id) for item in observations if item.centroid_geo]
            if points:
                tracks.append(Track(site_id=site_id, class_name=observations[0].class_name, points=points))
        return tracks


class GeoTraxProvider(SimpleTrackingProvider):
    """Adapter boundary for a Geo-trax runner returning identity-keyed detections."""

    def __init__(self, runner: Callable[[Sequence[Detection]], dict[str, list[Detection]]]):
        self.runner = runner

    def associate_detections(self, detections: Sequence[Detection]) -> dict[str, list[Detection]]:
        return self.runner(detections)
