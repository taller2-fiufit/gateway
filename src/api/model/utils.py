from typing import Type
from pydantic import BaseModel


def make_all_required(cls: Type[BaseModel]) -> Type[BaseModel]:
    """Mark all fields of the class as required"""
    # make class have all fields equal to TrainingBase but with required = True
    for field in cls.__fields__.values():
        field.required = True
        field.allow_none = False

    return cls


class OrmModel(BaseModel):
    class Config:
        # https://docs.pydantic.dev/usage/models/#orm-mode-aka-arbitrary-class-instances
        orm_mode = True
        # https://stackoverflow.com/questions/69433904/assigning-pydantic-fields-not-by-alias
        allow_population_by_field_name = True
