# YardOS third-party license inventory

This is an engineering inventory, not legal advice. Package, model-weight, dataset, hosted-service, and map-tile terms can differ. Items marked **REQUIRES LEGAL REVIEW** must be cleared before customer or production use.

| Dependency / upstream | Repository | License reported upstream | How YardOS uses it | Obligations / commercial-use concern |
| --- | --- | --- | --- | --- |
| PX4 Autopilot | https://github.com/PX4/PX4-Autopilot | BSD-3-Clause | Future flight-system upstream; not distributed by this repo | Preserve notices if distributed. Hardware/docs/submodules can have separate terms. |
| MAVSDK | https://github.com/mavlink/MAVSDK | BSD-3-Clause | Optional future Python flight-control client | Preserve license and notices when distributed. Python package transitive inventory still needed. |
| MMDetection | https://github.com/open-mmlab/mmdetection | Apache-2.0 | Preferred optional detector adapter | Preserve license/NOTICE and modification notices. Model weights and their training datasets require separate review. |
| RTMDet model weights | MMDetection model zoo | Varies by checkpoint and training data | Planned production detector | **REQUIRES LEGAL REVIEW:** verify the exact checkpoint, its notice, and dataset-derived restrictions before shipping. |
| Raster Vision | https://github.com/azavea/raster-vision | Apache-2.0 | Architectural reference only; not imported | If added, preserve license/NOTICE. Current tiling code is YardOS-owned and does not copy it. |
| TorchGeo | https://github.com/microsoft/torchgeo | MIT | Architectural reference only; not imported | Preserve copyright/license if later distributed. Dataset wrappers do not license the underlying datasets. |
| Open-CD | https://github.com/likyoo/open-cd | Apache-2.0 | Future adapter target; not imported | Preserve license/NOTICE if added. Each checkpoint and training dataset needs separate review. |
| MapLibre GL JS | https://github.com/maplibre/maplibre-gl-js | BSD-3-Clause plus bundled third-party notices | Interactive browser map | Reproduce the full upstream notices in distributions. Current Esri imagery endpoint has separate service terms. |
| Esri World Imagery | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 | Hosted service terms, not an OSS license | Current dashboard basemap URL | **REQUIRES LEGAL REVIEW:** confirm production access, attribution, rate limits, and offline/demo availability. |
| OpenDroneMap ODM | https://github.com/OpenDroneMap/ODM | AGPL-3.0 | External photogrammetry engine through NodeODM | **REQUIRES LEGAL REVIEW:** network use, distribution, modifications, and source-offer obligations must be assessed. Keep it isolated; do not link/copy source into YardOS. |
| NodeODM | https://github.com/OpenDroneMap/NodeODM | AGPL-3.0 | External Docker HTTP service | **REQUIRES LEGAL REVIEW:** same AGPL concerns; publish corresponding source for modifications when required and retain notices. |
| Ultralytics | https://github.com/ultralytics/ultralytics | AGPL-3.0 or separate Enterprise License | Currently present in the optional vision service and training scripts | **REQUIRES LEGAL REVIEW / PRODUCTION BLOCKER:** remove from the commercial path or obtain an Enterprise License. Do not assume model weights are exempt. |
| VisDrone dataset | https://github.com/VisDrone/VisDrone-Dataset | No clear dataset license identified in the official repository | Bootstrap training data for car/van/truck/bus | **REQUIRES LEGAL REVIEW:** public download and academic citation do not establish commercial training rights. Do not redistribute images or annotations. |
| Brighton Beach drone dataset | https://github.com/pierotofy/drone_dataset_brighton_beach | Repository declares BSD-2-Clause; the license file does not separately enumerate the photographs | Opt-in photogrammetry integration fixture, downloaded locally | Preserve copyright/license. Do not redistribute or commit imagery. Verify an explicit imagery grant with the owner before relying on it for commercial use. |
| PostgreSQL | https://www.postgresql.org | PostgreSQL License | Primary relational database | Permissive; preserve notices when redistributing binaries. |
| PostGIS | https://postgis.net | GPL-2.0-or-later (project distribution) | Spatial extension in a separate database container | **REQUIRES LEGAL REVIEW:** assess obligations for container/image distribution; YardOS communicates over SQL rather than linking PostGIS code. |
| FastAPI | https://github.com/fastapi/fastapi | MIT | API framework | Preserve copyright/license. |
| SQLAlchemy | https://github.com/sqlalchemy/sqlalchemy | MIT | ORM | Preserve copyright/license. |
| GeoAlchemy2 | https://github.com/geoalchemy/geoalchemy2 | MIT | PostGIS ORM types | Preserve copyright/license. |
| Rasterio | https://github.com/rasterio/rasterio | BSD-3-Clause; links GDAL | GeoTIFF metadata/affine reader | Preserve notices; audit bundled GDAL and binary dependencies when distributing containers. |
| pyproj | https://github.com/pyproj4/pyproj | MIT; bundles/links PROJ | CRS transformation | Preserve notices; inventory PROJ data/licenses in the built image. |
| Next.js | https://github.com/vercel/next.js | MIT | Web application framework | Preserve copyright/license. |
| React | https://github.com/facebook/react | MIT | UI runtime | Preserve copyright/license. |

## Policy

1. Pin exact package and container versions before release; floating `latest` images are not auditable.
2. Generate npm and Python dependency SBOM/license reports from the release images.
3. Record each production model checksum, source, license, training dataset, and approval owner.
4. Do not commit third-party datasets or model weights until legal approval and redistribution terms are recorded.
5. Preserve the NodeODM/ODM service boundary and document any local modifications and corresponding source location.
