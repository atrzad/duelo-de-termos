from pydantic import BaseModel, Field


class CriarSalaPayload(BaseModel):
    nome: str = Field(min_length=1, max_length=24)


class EntrarSalaPayload(BaseModel):
    nome: str = Field(min_length=1, max_length=24)
    codigo: str = Field(min_length=4, max_length=4)


class EnviarPalpitePayload(BaseModel):
    palavra: str = Field(min_length=5, max_length=5, pattern=r"^[A-Za-z]+$")
