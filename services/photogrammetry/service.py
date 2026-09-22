from abc import ABC, abstractmethod


class PhotogrammetryService(ABC):
    @abstractmethod
    async def create_map(self, images: list[str]) -> dict: ...


class NodeODMPhotogrammetryService(PhotogrammetryService):
    """HTTP boundary for externally hosted AGPL NodeODM; source is never linked into YardOS."""

    def __init__(self, client): self.client = client

    async def create_map(self, images: list[str]) -> dict:
        task_id = await self.client.create_task(images)
        await self.client.wait_for_completion(task_id)
        return {"task_id": task_id, "orthomosaic": await self.client.get_orthophoto(task_id), "dem": await self.client.get_asset(task_id, "dsm.tif"), "point_cloud": await self.client.get_asset(task_id, "georeferenced_model.laz")}
