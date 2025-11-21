from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class Documento(BaseModel):
    id: str
    dataHoraJuntada: datetime
    nome: str
    texto: str


class Movimento(BaseModel):
    dataHora: datetime
    descricao: str


class Honorarios(BaseModel):
    contratuais: Optional[float] = None
    periciais: Optional[float] = None
    sucumbenciais: Optional[float] = None


class ProcessoInput(BaseModel):
    numeroProcesso: str
    classe: str
    orgaoJulgador: str
    ultimaDistribuicao: datetime
    assunto: str
    segredoJustica: bool
    justicaGratuita: bool
    siglaTribunal: str
    esfera: str  # "Federal", "Estadual", "Trabalhista", etc.

    valorCausa: Optional[float] = None
    valorCondenacao: Optional[float] = None

    documentos: List[Documento]
    movimentos: List[Movimento]

    honorarios: Optional[Honorarios] = None
