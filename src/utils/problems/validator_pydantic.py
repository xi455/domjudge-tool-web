from typing import Optional
from pydantic import BaseModel, validator, Field

class ProblemTestCase(BaseModel):
    sample: bool
    input: str
    output: str

class UnZipFileProblemInfo(BaseModel):
    file_name: str
    problem_title: str
    time_limit: float
    problem_pdf: Optional[bytes] = Field(None, description="The Unzip file problem pdf")
    testcases_data: dict

    @validator("problem_pdf")
    def validate_pdf(cls, value):
        try:
            if not value.startswith(b'%PDF-'):
                raise ValueError("Invalid PDF file")
            
            return value
        
        except Exception as e:
            raise ValueError(e)