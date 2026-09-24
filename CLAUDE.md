# YardOS canonical pipeline

This is the entire YardOS processing pipeline. Preserve this architecture unless a product decision explicitly changes it:

```text
DJI drone photos
        ↓
NodeODM photogrammetry
        ↓
one georeferenced yard map / orthomosaic
        ↓
YOLO aerial object detection
        ↓
VisDrone bootstrap understanding
  "truck here"
  "truck here"
  "car here"
        ↓
fine-tune on our own labeled Houston yard dataset
        ↓
YardOS-specific understanding
  "53-ft trailer here"
  "container here"
  "chassis here"
```

The fuller system diagram and integration boundaries live in `ARCHITECTURE.md`; treat that file as the source of truth. In particular, still imagery and video form two intentional branches: stills produce an orthomosaic through NodeODM, while sampled video frames may flow directly to the detector. Both normalize into georeferenced YardOS detections before PostGIS, change analysis, tracking, and UI queries.

## Architectural rules

- DJI/drone images are the source inputs.
- NodeODM is the production-facing photogrammetry service. It turns an overlapping image set into one yard orthomosaic and related geospatial outputs.
- YOLO analyzes the resulting yard map. Do not run detection independently on every source photo in the normal production flow.
- VisDrone is only the bootstrap dataset for aerial vehicle understanding: `car`, `van`, `truck`, and `bus`.
- Never claim that VisDrone provides YardOS-specific labels such as trailers, containers, tractors, chassis, or heavy equipment.
- The labeled Houston yard dataset is the path to YardOS-specific classes, including `trailer`, `shipping_container`, `tractor`, `chassis`, `heavy_equipment`, and `car`.
- Keep NodeODM and the FastAPI vision service isolated behind their existing service interfaces. Do not copy or reimplement their photogrammetry or neural-network internals in the YardOS application.
- Detection output must remain structured and scan-scoped: scan ID, class, confidence, bounding box, center coordinates, and model version.
- Do not add tracking, OCR, custom neural-network architectures, or infrastructure complexity until the core pipeline is working reliably.

## Product definition

YardOS is not a drone manufacturer, drone fleet, or commodity mapping service. It is the physical-inventory and change-intelligence layer between recurring aerial imagery and an industrial operator's system of record.

The customer, its existing drone contractor, or a YardOS capture partner supplies recurring imagery. YardOS converts it into:

- a current, searchable physical inventory map;
- counts and locations by configured asset class and operating zone;
- a capture-to-capture ledger of objects that appeared, disappeared, or moved;
- an exception queue for misplaced assets, congestion, excessive dwell, blocked access, and inventory discrepancies;
- reconciliation exports or integrations for the customer's TMS, WMS, terminal operating system, dispatch spreadsheet, maintenance system, or asset registry;
- operational reports with reviewable image evidence and confidence.

The concise product promise is:

> Your drone already collects the pictures. YardOS tells you what changed, what is missing, and what needs attention.

For logistics customers, use the more specific formulation:

> YardOS reconciles the physical yard with the system of record after every drone capture.

An orthomosaic is an intermediate artifact, not the product. The recurring value comes from the normalized inventory, history, exceptions, operator corrections, and integration with operational workflows.

## Initial product: YardOS Yard Reconciliation

The initial commercial workflow should answer:

1. What relevant assets are physically present?
2. Where are they and which operating zone contains them?
3. What appeared, disappeared, or moved since the previous capture?
4. Which zones are congested or obstructed?
5. Where does the physical observation disagree with the customer's system of record?
6. What requires a manager's attention today?

The first logistics classes are `trailer`, `shipping_container`, `chassis`, `tractor`, `iso_tank`, and major yard equipment. These classes require YardOS-specific labeled data and validated models. The current VisDrone bootstrap model must not be presented as a validated yard-inventory model.

Do not initially promise reliable container-number OCR, continuous real-time tracking, survey-grade measurements, autonomous decisions, or replacement of a TMS/WMS/terminal operating system. Begin with counts, zones, visible changes, reviewable exceptions, and human quality assurance.

## Ideal early customer

The best first design partner is not necessarily a global enterprise. Prefer a private Houston-area operator that has:

- one or more outdoor yards with visible containers, trailers, chassis, ISO tanks, railcars, or equipment;
- recurring inventory, location, dwell, congestion, inspection, or reconciliation problems;
- an employee-operated drone or an existing Part 107 contractor;
- many images but no automated operational interpretation;
- an operations leader able to approve a $5,000-$15,000 pilot;
- willingness to provide inventory exports and validate YardOS results.

The economic buyer is normally a terminal manager, yard manager, depot manager, VP/director of operations, intermodal operations manager, equipment-control manager, or operational-excellence leader. Lead discovery with: "How do you currently verify what is physically in the yard, where it is, and what does not agree with your operating system?"

### Houston design-partner prospects

Prioritize approachable private operators before large ports and energy companies:

1. SteerPoint Logistics — private gated container storage and drayage near Port Houston.
2. Global Container Industries — Baytown inland container depot with container storage and chassis management.
3. IsoChem Logistics — Houston ISO-tank depot, cleaning, repair, chassis, and transportation operations.
4. W.W. Rowland Trucking — bonded Houston yard with loaded and empty intermodal storage, repair, and drop-lot operations.
5. Watco Houston Texas Terminal — secured transload facility with outdoor laydown storage.
6. Watco Coady Transload Terminal — Baytown rail, truck, container, and outdoor laydown operation.
7. Gulf Winds International — multiple Houston-area yards, warehouses, trucks, and chassis.
8. Jacintoport International — large secure cargo and stevedoring terminal.
9. Cooper/Ports America — terminal operations, container depots, chassis maintenance, and project cargo.
10. Houston Terminal, LLC — major Bayport and Barbours Cut container operator.
11. TGS Cedar Port Industrial Park — large rail-and-barge-served industrial park with storage and development activity.
12. Port Houston — high-value future target, but subject to longer procurement, integration, security, and flight-approval cycles.

Treat this as a prospect list based on public operational fit, not evidence that any company has expressed interest.

## Companies validating the in-house drone thesis

The following organizations demonstrate that large operators already generate aerial imagery internally or through established drone programs:

- Shell: asset-owned drone programs at multiple facilities, including Deer Park and Shell Technology Center Houston, for tank-farm inspection, construction models, pipelines, and repetitive site observation.
- CenterPoint Energy: drone use for storm response, inaccessible equipment, thermal inspection, flooded infrastructure, and development of a formal drone program.
- Bechtel: drones integrated into construction, terrain, progress, environmental, and project-planning workflows.
- Chevron: drones for visual and thermal inspection, emissions detection, pipeline surveillance, and development of drone-in-a-box operations.
- Dow: drones and robotics for elevated, underwater, and confined-space inspection and reduction of hazardous worker exposure.
- DSV: automated warehouse drones that scan inventory and update a dashboard.
- Railroad Commission of Texas: a formal drone program for authorized regulatory activities.

These organizations validate the market but are generally future enterprise targets because of procurement, security, governance, established vendors, and internal robotics teams. YardOS should first prove the workflow with smaller operators, then use measured accuracy, ROI, and proprietary labeled data to approach enterprise accounts.

## Pilot and pricing hypothesis

The standard design-partner offer is a paid six-to-eight-week **YardOS Yard Reconciliation Pilot** priced at approximately **$7,500**, adjusted within a $5,000-$15,000 range for site size and complexity.

The customer supplies four compliant image sets through its own drone program or contractor. YardOS supplies:

- capture specifications and image-quality validation;
- four processed site maps;
- detection and counts for the agreed asset classes;
- zone-level physical inventory;
- capture-to-capture change reports;
- comparison with a customer-provided inventory export;
- an operator-reviewed exception queue;
- manual quality assurance;
- a final accuracy, workflow, and ROI assessment.

Agree on measurable success criteria before capture, including target count accuracy, turnaround time, reduction in manual audit effort, and whether the pilot discovers valuable discrepancies or exceptions.

After validation, the provisional subscription bands are:

- $1,500-$2,500 per site per month for customer-provided imagery and basic recurring analysis;
- $3,000-$5,000 per site per month for higher-frequency reconciliation, alerts, history, and integrations;
- enterprise pricing for multiple sites, specialized models, SLAs, security requirements, and system integrations.

These are hypotheses to validate through customer discovery and paid pilots, not fixed public pricing.

## Capital strategy

Do not build or finance a drone fleet before product-market validation. Use, in priority order:

1. imagery captured by the customer's existing drone program;
2. the customer's existing drone contractor;
3. a YardOS-managed network of insured Part 107 capture partners;
4. one YardOS-owned demonstration and validation aircraft when justified;
5. customer-funded or customer-leased autonomous hardware only after recurring demand supports it.

YardOS should own the software, normalized data model, analytics, operational workflow, customer relationship, and learning loop. Capture hardware should remain interchangeable infrastructure.
