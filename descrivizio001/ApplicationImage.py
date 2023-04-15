from pydantic import BaseModel


class ApplicationImage(BaseModel):
    content: bytes
