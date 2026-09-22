from abc import ABC, abstractmethod

from packages.contracts import Capture, ChangeEvent


class ChangeDetectionService(ABC):
    @abstractmethod
    def compare(self, before: list[dict], after: list[dict], *, aligned: bool = False) -> list[dict]: ...


class ObjectDifferenceBaseline(ChangeDetectionService):
    """Object-observation difference, not semantic/pixel change detection."""

    def compare(self, before: list[dict], after: list[dict], *, aligned: bool = False) -> list[dict]:
        if not aligned:
            raise ValueError("Captures must share a CRS and spatial grid before comparison")
        before_by_id, after_by_id = {row["id"]: row for row in before}, {row["id"]: row for row in after}
        events = []
        for item_id in before_by_id.keys() - after_by_id.keys():
            events.append({"type": "disappeared", "confidence": before_by_id[item_id]["confidence"], "geometry": before_by_id[item_id].get("geometry")})
        for item_id in after_by_id.keys() - before_by_id.keys():
            events.append({"type": "appeared", "confidence": after_by_id[item_id]["confidence"], "geometry": after_by_id[item_id].get("geometry")})
        for item_id in before_by_id.keys() & after_by_id.keys():
            first, last = before_by_id[item_id], after_by_id[item_id]
            if (first.get("latitude"), first.get("longitude")) != (last.get("latitude"), last.get("longitude")):
                events.append({"type": "moved", "confidence": min(first["confidence"], last["confidence"]), "geometry": last.get("geometry")})
        return events


class SimpleDifferenceProvider:
    def compare(self, before: Capture, after: Capture) -> list[ChangeEvent]:
        return []


class OpenCDProvider:
    """Adapter around an injected Open-CD inference runner."""

    def __init__(self, runner):
        self.runner = runner

    def compare(self, before: Capture, after: Capture) -> list[ChangeEvent]:
        return [ChangeEvent(site_id=after.site_id, before_capture_id=before.id, after_capture_id=after.id, type=row["type"], confidence=float(row["confidence"]), geometry_geo=row.get("geometry_geo"), metadata={"provider": "open-cd"}) for row in self.runner(before, after)]
