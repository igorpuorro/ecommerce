from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PrePostagemModalidadePagamento(Enum):
    A_VISTA = "A_VISTA"
    A_FATURAR = "A_FATURAR"
    A_VISTA_FATURAR = "A_VISTA_FATURAR"
    PRESTACAO_CONTAS_REC_PAG = "PRESTACAO_CONTAS_REC_PAG"


class PrePostagemStatus(Enum):
    PREATENDIDO = "PREATENDIDO"
    PREPOSTADO = "PREPOSTADO"
    POSTADO = "POSTADO"
    EXPIRADO = "EXPIRADO"
    CANCELADO = "CANCELADO"
    ESTORNADO = "ESTORNADO"


class PrePostagemTipoObjeto(Enum):
    TODOS = "TODOS"
    SIMPLES = "SIMPLES"
    REGISTRADO = "REGISTRADO"


@dataclass
class PrePostagemQueryFilter:
    codigo_objeto: Optional[str] = None
    modalidade_pagamento: Optional[PrePostagemModalidadePagamento] = None
    tipo_objeto: Optional[PrePostagemTipoObjeto] = None
    status: Optional[PrePostagemStatus] = None

    def to_dict(self):
        pass
