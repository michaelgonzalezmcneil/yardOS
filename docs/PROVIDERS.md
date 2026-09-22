# Provider boundaries

Provider protocols live in `packages/contracts/providers.py`. Business logic imports these protocols and canonical models only.

| Capability | Default/demo | Production adapter | Canonical output |
| --- | --- | --- | --- |
| Photogrammetry | `MockPhotogrammetryProvider` | `ODMPhotogrammetryProvider` | `MappingArtifact[]` |
| Detection | `MockDetectorProvider` | `MMDetectionProvider` | `Detection[]` |
| Segmentation | `MockSegmentationProvider` | `AerialSegmentationProvider` | `Segmentation[]` |
| Change detection | `SimpleDifferenceProvider` | `OpenCDProvider` | `ChangeEvent[]` |
| Tracking | `SimpleTrackingProvider` | `GeoTraxProvider` | `Track[]` |
| Drone control | `MockDroneProvider` | `MAVSDKDroneProvider` | `DroneTelemetry` and mission operations |
| Artifact storage | `LocalArtifactStore` | `MinioArtifactStore` | S3-shaped URIs |

Adapters translate upstream inputs and outputs at the boundary. They must not insert database records directly, invoke the next provider, or leak upstream classes into API schemas.

## Selection

Provider names are environment-driven:

```text
PHOTOGRAMMETRY_PROVIDER=mock|odm
DETECTOR_PROVIDER=mock|mmdetection
SEGMENTATION_PROVIDER=mock|aerial
CHANGE_PROVIDER=simple|opencd
TRACKING_PROVIDER=simple|geotrax
STORAGE_PROVIDER=local|minio
```

Provider factories should be the only modules that import implementation adapters. Tests inject mocks directly.
