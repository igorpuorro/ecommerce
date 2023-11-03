import base64
import json
import re

import requests

from requests.exceptions import RequestException
from retrying import retry

from app_config import AppConfig
from app_logger import AppLogger
from cws_data import PrePostagemModalidadePagamento, PrePostagemQueryFilter, PrePostagemStatus, PrePostagemTipoObjeto


class CwsClient:
    app_config: AppConfig
    ambiente: str
    app_logger: AppLogger
    response_data_autentica: dict

    def __init__(self, app_config: AppConfig, ambiente: str, app_logger: AppLogger):
        self.app_config = app_config
        self.ambiente = ambiente
        self.app_logger = app_logger

    def delete_prepostagem_v1_prepostagens_objeto(self, codigo_objeto: str) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        usuario_meu_correios = self.app_config.get(
            self.ambiente, "usuario_meu_correios"
        )
        url = f"{base_url}/prepostagem/v1/prepostagens/objeto/{codigo_objeto}?idCorreiosSolicitanteCancelamento={usuario_meu_correios}"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        try:
            response = requests.delete(url, headers=headers, timeout=10)

            self.app_logger.log_request_response(
                response
            )

            if response.status_code == 200:
                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def get_cep_v2_enderecos(self, cep: str) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        cep_digits_only = ''.join(re.findall(r'\d', cep))
        url = f"{base_url}/cep/v2/enderecos/{cep_digits_only}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()

    def get_meucontrato_v1_empresas_contratos_cartoes_servicos(self, descricao: str) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        cnpj = self.app_config.get(self.ambiente, "cnpj")
        numero_contrato = self.app_config.get(self.ambiente, "numero_contrato")
        numero_cartao_postagem = self.app_config.get(
            self.ambiente, "numero_cartao_postagem"
        )
        url = f"{base_url}/meucontrato/v1/empresas/{cnpj}/contratos/{numero_contrato}/cartoes/{numero_cartao_postagem}/servicos?page=0&size=200"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            response_data = response.json()

            for item in response_data["itens"]:
                if item.get("descricao", "").lower() == descricao.lower():
                    return item

    def get_prepostagem_v1_prepostagens_declaracaoconteudo(self, id_pre_postagem: str) -> str:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/prepostagem/v1/prepostagens/declaracaoconteudo/{id_pre_postagem}"

        headers = {
            "Accept": "application/json, text/html, text/plain",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.text

            self.app_logger.log_request_response(
                response
            )

            response.raise_for_status()

        except requests.exceptions.HTTPError:
            return ""

        except requests.exceptions.RequestException:
            return ""

    def get_prepostagem_v2_prepostagens(self, pre_postagem_query_filter: PrePostagemQueryFilter) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        endpoint_url = f"{base_url}/prepostagem/v2/prepostagens?"

        params = []

        if pre_postagem_query_filter.codigo_objeto:
            params.append(
                f"codigoObjeto={pre_postagem_query_filter.codigo_objeto}"
            )

        if pre_postagem_query_filter.modalidade_pagamento:
            params.append(
                f"modalidadePagamento={pre_postagem_query_filter.modalidade_pagamento.value}"
            )

        if pre_postagem_query_filter.tipo_objeto:
            params.append(
                f"tipoObjeto={pre_postagem_query_filter.tipo_objeto.value}"
            )

        if pre_postagem_query_filter.status:
            params.append(
                f"status={pre_postagem_query_filter.status.value}"
            )

        url = endpoint_url + '&'.join(params) + "&page=0&size=100"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def post_prepostagem_v1_prepostagens(self, request_data: dict) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/prepostagem/v1/prepostagens"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        try:
            response = requests.post(
                url, headers=headers, json=request_data, timeout=10
            )

            self.app_logger.log_request_response(
                response
            )

            if response.status_code == 200:
                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def post_prepostagem_v1_prepostagens_rotulo_assincrono_pdf(self, codigo_objeto_list: list) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/prepostagem/v1/prepostagens/rotulo/assincrono/pdf"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        numero_cartao_postagem = self.app_config.get(
            self.ambiente, "numero_cartao_postagem"
        )

        request_data = {
            "codigosObjeto": codigo_objeto_list,
            "numeroCartaoPostagem": numero_cartao_postagem,
            "tipoRotulo": "P",
            "formatoRotulo": "ET",
            "imprimeRemetente": "S"
        }

        response = requests.post(
            url, headers=headers, json=request_data, timeout=10
        )

        if response.status_code == 200:
            return response.json()

    def get_prepostagem_v1_prepostagens_rotulo_download_assincrono(self, id_recibo: str) -> dict:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/prepostagem/v1/prepostagens/rotulo/download/assincrono/{id_recibo}"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.response_data_autentica.get('token')}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            response.raise_for_status()

        except requests.exceptions.HTTPError:
            return ""

        except requests.exceptions.RequestException:
            return ""

    @retry(wait_fixed=5, stop_max_attempt_number=3)
    def post_token_v1_autentica(self) -> None:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/token/v1/autentica"

        usuario_meu_correios = self.app_config.get(
            self.ambiente, "usuario_meu_correios"
        )
        codigo_acesso_api = self.app_config.get(
            self.ambiente, "codigo_acesso_api"
        )

        authorization_string = base64.b64encode(
            f"{usuario_meu_correios}:{codigo_acesso_api}".encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {authorization_string}"
        }

        try:
            response = requests.post(
                url, headers=headers, timeout=10
            )

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                response_data = response.json()

                self.response_data_autentica = response_data

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")

        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")

        except Exception as e:
            print(f"Unexpected Error: {e}")

    @retry(wait_fixed=5, stop_max_attempt_number=3)
    def post_token_v1_autentica_cartaopostagem(self) -> None:
        base_url = self.app_config.get(self.ambiente, "base_url")
        url = f"{base_url}/token/v1/autentica/cartaopostagem"

        usuario_meu_correios = self.app_config.get(
            self.ambiente, "usuario_meu_correios"
        )
        codigo_acesso_api = self.app_config.get(
            self.ambiente, "codigo_acesso_api"
        )
        numero_cartao_postagem = self.app_config.get(
            self.ambiente, "numero_cartao_postagem"
        )

        authorization_string = base64.b64encode(
            f"{usuario_meu_correios}:{codigo_acesso_api}".encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {authorization_string}"
        }

        data = {
            "numero": numero_cartao_postagem
        }

        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=10
            )

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                response_data = response.json()

                self.response_data_autentica = response_data

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")

        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")

        except Exception as e:
            print(f"Unexpected Error: {e}")
