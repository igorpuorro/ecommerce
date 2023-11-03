import json
import time

from app_config import AppConfig
from app_logger import AppLogger
from cws_client import CwsClient
from cws_data import PrePostagemModalidadePagamento, PrePostagemQueryFilter, PrePostagemStatus, PrePostagemTipoObjeto


class CwsHandler:
    app_config: AppConfig
    app_logger: AppLogger
    cws_client: CwsClient

    def __init__(self, app_config: AppConfig, ambiente: str, app_logger: AppLogger):
        self.app_config = app_config
        self.cws_client = CwsClient(
            app_config, ambiente, app_logger
        )

        if self.app_config.has_option(ambiente, "numero_cartao_postagem"):
            self.cws_client.post_token_v1_autentica_cartaopostagem()
        else:
            self.cws_client.post_token_v1_autentica()

    def cep_endereco(self, cep: str) -> dict:
        try:
            response = self.cws_client.get_cep_v2_enderecos(cep)

            return response

        except Exception:
            return {}

    def codigo_servico(self, descricao: str) -> str:
        try:
            response = self.cws_client.get_meucontrato_v1_empresas_contratos_cartoes_servicos(
                descricao
            )

            return response.get("codigo")

        except Exception:
            return ""

    def pre_postagem_query(self, pre_postagem_query_filter: PrePostagemQueryFilter) -> list:
        try:
            response = self.cws_client.get_prepostagem_v2_prepostagens(
                pre_postagem_query_filter
            )

            return response.get("itens", [])

        except Exception:
            return []

    def pre_postagem_nova(self, json_data: dict) -> dict:
        return self.cws_client.post_prepostagem_v1_prepostagens(
            json_data
        )

    def pre_postagem_cancela(self, codigo_objeto: str) -> None:
        self.cws_client.delete_prepostagem_v1_prepostagens_objeto(
            codigo_objeto
        )

    def pre_postagem_declaracao_conteudo(self, id_pre_postagem: str) -> str:
        return self.cws_client.get_prepostagem_v1_prepostagens_declaracaoconteudo(id_pre_postagem)

    def pre_postagem_rotulo(self, codigo_objeto: list) -> dict:
        if len(codigo_objeto) > 0:
            recibo_response = self.cws_client.post_prepostagem_v1_prepostagens_rotulo_assincrono_pdf(
                codigo_objeto
            )

            id_recibo = recibo_response.get("idRecibo")

            time.sleep(1)

            pdf_response = self.cws_client.get_prepostagem_v1_prepostagens_rotulo_download_assincrono(
                id_recibo
            )

            return pdf_response
