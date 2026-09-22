# Open-source service boundary

YardOS keeps OpenDroneMap ODM and NodeODM in a separate container and communicates with NodeODM over HTTP. No ODM or NodeODM source is copied into, imported by, or linked with YardOS application code.

This technical separation is intentional but is not itself a legal conclusion. ODM and NodeODM are AGPL-3.0 projects. Any production deployment, redistribution of their images, or modification of their code requires legal review and compliance with their actual license terms. See `THIRD_PARTY_LICENSES.md` for the current inventory.
