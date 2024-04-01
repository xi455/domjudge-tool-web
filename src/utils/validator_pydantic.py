from typing import Optional
from pydantic import BaseModel


class DomServerClientModel(BaseModel):
    host: str
    username: str
    mask_password: str


class TestCase(BaseModel):
    id: str


class ServerContest(BaseModel):
    contest_name: str
    contest_id: str


class WebTestCase(BaseModel):
    deleteid: str
    id: str
    sample: str
    input: str
    output: str


class ContestInfo(BaseModel):
    CID: Optional[str] = None
    name: Optional[str] = None
    shortname: Optional[str] = None
    activate: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    processballoons: Optional[str] = None
    public: Optional[str] = None
    teams: Optional[str] = None
    problems: Optional[str] = None


class ContestDetails(BaseModel):
    contest_name: str
    contest_info: ContestInfo


class ProblemInfo(BaseModel):
    id: str
    name: str