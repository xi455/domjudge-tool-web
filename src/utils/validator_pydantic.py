from pydantic import BaseModel, validator


class DomServerClientModel(BaseModel):
    host: str
    username: str
    mask_password: str