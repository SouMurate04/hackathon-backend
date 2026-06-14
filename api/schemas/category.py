from pydantic import BaseModel

class CategoryChild(BaseModel):
    id: int
    name: str

class CategoryTree(BaseModel):
    id: int
    name: str
    children: list[CategoryChild] = []