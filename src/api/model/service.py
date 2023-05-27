from typing import Optional

from pydantic import Field
from src.api.model.utils import OrmModel, make_all_required


class ServiceBase(OrmModel):
    name: Optional[str] = Field(
        title="Name",
        description="The service's name",
        min_length=2,
        max_length=31,
        default=None,
    )
    url: Optional[str] = Field(
        title="URL",
        description="The service's web address",
        max_length=255,
        default=None,
    )
    path: Optional[str] = Field(
        title="Path regex",
        description="The regex matching paths redirected to the service",
        max_length=255,
        default=None,
    )


class PatchService(ServiceBase):
    blocked: Optional[bool] = Field(
        title="Is blocked?",
        description="True if the service is blocked, false if it isn't",
        default=None,
    )


class AllRequiredServiceBase(ServiceBase):
    pass


make_all_required(AllRequiredServiceBase)


class AddService(AllRequiredServiceBase):
    blocked: bool = Field(
        title="Is blocked?",
        description="True if the service is blocked, false if it isn't",
        default=False,
    )


class Service(AllRequiredServiceBase):
    id: int = Field(
        title="ID",
        description="The service's unique ID",
    )
    blocked: bool = Field(
        title="Is blocked?",
        description="True if the service is blocked, false if it isn't",
    )
    up: bool = Field(
        title="Service is up?",
        description="True if the service is up, false if it isn't",
        default=False,
    )

    def __hash__(self) -> int:
        return hash(self.id)


class ServiceWithApikey(Service):
    apikey: str = Field(
        title="API key",
        description="The API key associated to the service",
        max_length=255,
        default=None,
    )
