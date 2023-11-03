from typing import Any, Dict

import base64
import json
import os
import re
import time

from datetime import datetime, timedelta

from prettytable import PrettyTable, FRAME, HEADER, NONE
from thefuzz import fuzz

from cws_data import PrePostagemModalidadePagamento, PrePostagemQueryFilter, PrePostagemStatus, PrePostagemTipoObjeto
from cws_handler import CwsHandler
from mongodb_handler import MongoDBHandler
from wsa_handler import WsaHandler
from wix_data import FilterOperator, FulfillmentStatus, PaymentStatus, OrderFulfillment, OrderQueryFilter, OrderQuerySort
from wix_order_handler import WixOrderHandler


class Ecommerce:
    cws_handler: CwsHandler
    mongodb_handler: MongoDBHandler
    wsa_handler: WsaHandler
    wix_order_handler: WixOrderHandler

    def __init__(self, cws_handler: CwsHandler, mongodb_handler: MongoDBHandler, wsa_handler: WsaHandler, wix_order_handler: WixOrderHandler):
        self.cws_handler = cws_handler
        self.mongodb_handler = mongodb_handler
        self.wsa_handler = wsa_handler
        self.wix_order_handler = wix_order_handler

########################################

    # CwsHandler, MongoDBHandler, WixOrderHandler
    def ecommerce_pre_postagem_nova(self, order_number: str) -> None:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        correios_pre_postagem = self.correios_pre_postagem_nova(
            order_number
        )

        codigo_objeto = correios_pre_postagem.get("codigoObjeto")

        pre_postagem_id = self.mongodb_handler.collection_insert(
            "ecommerce", "pre_postagem", correios_pre_postagem
        )

        self.wix_order_fulfillment_create(
            order_number, codigo_objeto
        )

    # CwsHandler , WixOrderHandler
    def ecommerce_pre_postagem_cancela(self, order_number: str) -> None:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        self.correios_pre_postagem_cancela(order_number)

        self.wix_order_fulfillment_delete(
            order_number
        )

########################################

    # CwsHandler, WixOrderHandler, WsaHandler
    def correios_enderecador_encomendas(self) -> list:
        json_path = os.path.join(
            "openapi_example_value", "cws_pre_postagem.json"
        )

        with open(json_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        json_data_remetente = json_data.get("remetente", {})
        json_data_remetente_endereco = json_data_remetente.get("endereco", {})

        remetente = {
            "nome": json_data_remetente.get("nome"),
            "cpf_cnpj": json_data_remetente.get("cpfCnpj"),
            "logradouro": json_data_remetente_endereco.get("logradouro"),
            "numero": json_data_remetente_endereco.get("numero"),
            "complemento": json_data_remetente_endereco.get("complemento"),
            "bairro": json_data_remetente_endereco.get("bairro"),
            "cidade": json_data_remetente_endereco.get("cidade"),
            "estado": json_data_remetente_endereco.get("uf"),
            "cep": json_data_remetente_endereco.get("cep")
        }

        order_list = self.wix_order_handler.get_order_list()

        group_size = 4
        destinatario_list = []
        file_list = []

        for index, order in enumerate(order_list):
            billing_info = order.get("billingInfo", {})
            shipping_info = order.get("shippingInfo", {})
            shipment_details = shipping_info.get("shipmentDetails", {})

            if len(shipment_details) > 0:
                cpf = billing_info.get("vatId", {}).get("number", "")

                if len(cpf) == 0:
                    cpf_cnpj = "34990164865"
                else:
                    cpf_cnpj = cpf

                address = shipment_details.get("address", {})

                first_name = address.get("fullName", {}).get(
                    "firstName", ""
                ).strip()

                last_name = address.get("fullName", {}).get(
                    "lastName", ""
                ).strip()

                endereco = self.cws_handler.cep_endereco(
                    address.get("zipCode")
                )

                cep = f"{endereco.get('cep', '')[:-3]}-{endereco.get('cep', '')[-3:]}"

                peso_total = order.get("totals", {}).get(
                    "weight"
                ).replace(".", ",")

                destinatario = {
                    "id": f"{order.get('number', '')}",
                    "nome": f"{first_name} {last_name}",
                    "cpf_cnpj": f"{cpf_cnpj}",
                    "logradouro": f"{address.get('street', {}).get('name', '')}",
                    "numero": f"{address.get('street', {}).get('number', '')}",
                    "complemento": f"{address.get('addressLine2', '')}",
                    "bairro": f"{endereco.get('bairro', '')}",
                    "cidade": f"{endereco.get('localidade', '')}",
                    "estado": f"{endereco.get('uf', '')}",
                    "cep": cep,
                    "itens_declaracao_conteudo": self._wix_order_itens_declaracao_conteudo(order),
                    "peso_total": f"{peso_total}"
                }

                destinatario_list.append(destinatario)

            if len(order_list) == index + 1 or len(destinatario_list) == group_size:
                remetente_destinatario_list_dict = {
                    "remetente": remetente,
                    "destinatario": destinatario_list
                }

                response = self.wsa_handler.correios_enderecador_encomendas(
                    remetente_destinatario_list_dict
                )

                file_list.append(response)

                destinatario_list = []

        return file_list

########################################

    # CwsHandler
    def correios_pre_postagem_query(self, pre_postagem_query_filter: PrePostagemQueryFilter) -> list:
        return self.cws_handler.pre_postagem_query(
            pre_postagem_query_filter
        )

    # CwsHandler, WixOrderHandler
    def correios_pre_postagem_nova(self, order_number: str) -> dict:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        json_path = os.path.join(
            "openapi_example_value", "cws_pre_postagem.json"
        )

        with open(json_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        json_data["destinatario"] = self._wix_order_destinatario(order)
        json_data["codigoServico"] = self._wix_order_codigo_servico(order)

        json_data["listaServicoAdicional"][0]["codigoServicoAdicional"] = self._wix_order_codigo_servico_adicional(
            order
        )

        json_data["listaServicoAdicional"][0]["valorDeclarado"] = self._wix_order_valor_declarado(
            order
        )

        json_data["itensDeclaracaoConteudo"] = self._wix_order_itens_declaracao_conteudo(
            order
        )

        json_data["pesoInformado"] = self._wix_order_peso_informado(order)

        json_data["observacao"] = f"number:{order_number}"

        return self.cws_handler.pre_postagem_nova(json_data)

    # CwsHandler, WixOrderHandler
    def correios_pre_postagem_cancela(self, order_number: str) -> None:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        fulfillments = order.get("fulfillments", [])

        if len(fulfillments) > 0:
            for fulfillment in fulfillments:
                tracking_info = fulfillment.get("trackingInfo")
                tracking_number = tracking_info.get("trackingNumber", None)

                if tracking_number:
                    self.cws_handler.pre_postagem_cancela(
                        codigo_objeto=tracking_number
                    )

    # CwsHandler, WixOrderHandler
    def correios_pre_postagem_download_declaracao_conteudo(self, order_number: str) -> str:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        number = order.get("number", "")
        fulfillments = order.get("fulfillments", [])

        if len(fulfillments) > 0:
            for fulfillment in fulfillments:
                tracking_info = fulfillment.get("trackingInfo")
                tracking_number = tracking_info.get("trackingNumber", None)

                if tracking_number:
                    pre_postagem_query_filter = PrePostagemQueryFilter(
                        codigo_objeto=tracking_number
                    )

                    pre_postagem_list = self.cws_handler.lista_pre_postagem(
                        pre_postagem_query_filter
                    )

                    if len(pre_postagem_list) > 0:
                        id_pre_postagem = pre_postagem_list[0].get("id")

                        html_content = self.cws_handler.pre_postagem_declaracao_conteudo(
                            id_pre_postagem
                        )

                        if html_content:
                            html_path = os.path.join(
                                "downloads",
                                f"{number}-{tracking_number}.html"
                            )

                            with open(html_path, "w", encoding="utf-8") as file:
                                file.write(html_content)

                            return html_path

        return ""

    # CwsHandler, WixOrderHandler
    def correios_pre_postagem_download_rotulo(self) -> str:
        order_list = self.wix_order_handler.get_order_list()

        if not order_list:
            raise ValueError

        codigo_objeto_list = []

        for order in order_list:
            fulfillments = order.get("fulfillments", [])

            if len(fulfillments) > 0:
                for fulfillment in fulfillments:
                    tracking_info = fulfillment.get("trackingInfo")
                    tracking_number = tracking_info.get("trackingNumber", None)
                    codigo_objeto_list.append(tracking_number)

        if len(codigo_objeto_list) > 0:
            pdf = self.cws_handler.pre_postagem_rotulo(codigo_objeto_list)

            pdf_filename = pdf.get("nome", None)
            pdf_content = pdf.get("dados", None)

            if pdf_filename and pdf_content:
                pdf_path = os.path.join(
                    "downloads",
                    pdf_filename
                )

                with open(pdf_path, "wb") as pdf_file:
                    pdf_file.write(base64.b64decode(pdf_content))

                return pdf_path

        return ""

########################################

    # WixOrderHandler
    def wix_order_query(self, order_query_filter: OrderQueryFilter, order_query_sort: OrderQuerySort) -> None:
        self.wix_order_handler.order_query(
            order_query_filter, order_query_sort
        )

    # WixOrderHandler
    def wix_order_fulfillment_create(self, order_number: str, tracking_number: str) -> None:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        line_items = order.get("lineItems", [])

        fulfillment_line_items_list = []

        for item in line_items:
            index = item.get("index")
            product_id = item.get("productId")
            quantity = item.get("quantity")

            fulfillment_line_items_list.append({
                "index": index,
                "quantity": quantity
            })

        order_fulfillment = OrderFulfillment(
            tracking_info_shipping_provider="Correios",
            tracking_info_tracking_number=tracking_number,
            tracking_info_tracking_link=f"https://www.websro.com.br/rastreamento-correios.php?P_COD_UNI={tracking_number}",
            line_items=fulfillment_line_items_list
        )

        self.wix_order_handler.order_fulfillment_create(
            order.get("id"),
            order_fulfillment
        )

    # WixOrderHandler
    def wix_order_fulfillment_delete(self, order_number: str, fulfillment_id: str = None) -> None:
        order = self.wix_order_handler.get_order(order_number)

        if not order:
            raise ValueError

        fulfillments = order.get("fulfillments", [])

        for fulfillment in fulfillments:
            if (not fulfillment_id) or (fulfillment_id and fulfillment_id == fulfillment.get("id")):
                self.wix_order_handler.order_fulfillment_delete(
                    order.get("id"),
                    fulfillment.get("id")
                )

    # WixOrderHandler
    def wix_estoque_tabela_retirada_produtos(self) -> None:
        orders = self.wix_order_handler.get_order_list()

        product_quantities = {}

        for order in orders:
            line_items = order.get("lineItems")

            for item in line_items:
                product_id = item.get("productId")
                name = item.get("name")
                quantity = item.get("quantity", 0)

                if product_id in product_quantities:
                    product_quantities[product_id]['quantity'] += quantity
                else:
                    product_quantities[product_id] = {
                        'productId': product_id, 'name': name, 'quantity': quantity}

        table = PrettyTable()
        table.align = "l"
        table.header = True

        table.field_names = ["Product ID", "Name", "Quantity"]

        # Iterate over the data and add rows to the table
        for product_id, product_info in product_quantities.items():
            table.add_row([
                product_info["productId"], product_info["name"], product_info["quantity"]
            ])

        print(
            f"Order number: {self.wix_order_handler.get_order_number_list_string()}\n"
        )
        print(table)

    # CwsHandler, WixOrderHandler
    def wix_pedidos_tabela_enderecos_inconsistentes(self) -> None:
        order_list = self.wix_order_handler.get_order_list()

        table = PrettyTable()
        table.align = "l"
        table.header = True

        table.max_width["Wix Logradouro"] = 25
        table.max_width["CWS Logradouro"] = 25

        table.field_names = [
            "Wix #",
            "Wix Nome",
            "Wix Logradouro",
            "CWS Logradouro",
            "Ratio Log.",
            "Wix Cidade",
            "CWS Cidade"
        ]

        table.sortby = "Wix #"

        tabular_data = []

        for index, order in enumerate(order_list):
            shipping_info = order.get("shippingInfo", {})
            shipment_details = shipping_info.get("shipmentDetails", {})

            if len(shipment_details) == 0:
                continue

            address = shipment_details.get("address", {})

            first_name = address.get("fullName", {}).get(
                "firstName", ""
            ).strip()

            last_name = address.get("fullName", {}).get(
                "lastName", ""
            ).strip()

            wix_number = order.get("number", "")
            wix_nome = first_name
            wix_logradouro = address.get("street", {}).get("name", "")
            wix_numero = address.get("street", {}).get("number", "")
            wix_cidade = address.get("street", {}).get("city", "")
            wix_estado = address.get("street", {}).get("subdivision", "")

            cws_cep_endereco = self.cws_handler.cep_endereco(
                address.get("zipCode")
            )

            if not cws_cep_endereco:
                cws_cep_endereco = {}

            cws_logradouro = cws_cep_endereco.get("logradouro", "")
            cws_numero = f"{cws_cep_endereco.get('numeroInicial', '')} - {cws_cep_endereco.get('numeroFinal', '')}"
            cws_cidade = cws_cep_endereco.get("localidade", "")
            cws_estado = cws_cep_endereco.get("uf", "")

            ratio_logradouro = fuzz.partial_ratio(
                wix_logradouro.lower(), cws_logradouro.lower()
            )

            if ratio_logradouro < 99:
                table.add_row([
                    wix_number,
                    wix_nome,
                    wix_logradouro,
                    cws_logradouro,
                    ratio_logradouro,
                    wix_cidade,
                    cws_cidade,
                ])

        print(
            f"Order number: {self.wix_order_handler.get_order_number_list_string()}\n"
        )
        print(table)

########################################

    # MongoDBHandler
    def mongodb_pre_postagem_collection_create(self) -> None:
        self.mongodb_handler.collection_create(
            "ecommerce", "pre_postagem"
        )

    # MongoDBHandler
    def mongodb_pre_postagem_collection_drop(self) -> None:
        self.mongodb_handler.collection_drop(
            "ecommerce", "pre_postagem"
        )

    # MongoDBHandler
    def mongodb_pre_postagem_collection_list(self):
        return self.mongodb_handler.collection_list("ecommerce", "pre_postagem")

    # MongoDBHandler
    def mongodb_wix_order_collection_create(self) -> None:
        self.mongodb_handler.collection_create(
            "ecommerce", "wix_order"
        )

    # MongoDBHandler
    def mongodb_wix_order_collection_drop(self) -> None:
        self.mongodb_handler.collection_drop(
            "ecommerce", "wix_order"
        )

    # MongoDBHandler
    def mongodb_wix_order_collection_list(self):
        return self.mongodb_handler.collection_list("ecommerce", "wix_order")

    # MongoDBHandler, WixOrderHandler
    def mongodb_wix_order_replicate(self):
        order_list = self.wix_order_handler.get_order_list()

        self.mongodb_handler.wix_order_replicate(
            "ecommerce", "wix_order", order_list
        )


########################################


    def _wix_order_destinatario(self, order: dict) -> dict:
        number = order.get("number", "")
        shipping_info = order.get("shippingInfo", "")
        shipment_details = shipping_info.get("shipmentDetails", "")
        address = shipment_details.get("address", "")

        endereco = self.cws_handler.cep_endereco(address.get("zipCode"))

        pattern = r"[^0-9]"
        phone = re.sub(pattern, "", address.get("phone", ""))
        pattern = r"^(?:55)"
        phone = re.sub(pattern, "", phone)

        destinatario = {
            "nome": f"{address.get('fullName', {}).get('firstName', '')} {address.get('fullName', {}).get('lastName', '')}",
            "dddTelefone": "",
            "telefone": "",
            "dddCelular": f"{phone[:2]}",
            "celular": f"{phone[2:]}",
            "email": f"{address.get('email', '')}",
            "cpfCnpj": f"{address.get('vatId', {}).get('number', '')}",
            "documentoEstrangeiro": "",
            "obs": f"number:{number}",
            "endereco": {
                "cep": f"{endereco.get('cep', '')}",
                "logradouro": f"{endereco.get('logradouro', '')}",
                "numero": f"{address.get('street', {}).get('number', '')}",
                "complemento": f"{address.get('addressLine2', '')}",
                "bairro": f"{endereco.get('bairro', '')}",
                "cidade": f"{endereco.get('localidade', '')}",
                "uf": f"{endereco.get('uf', '')}"
            }
        }

        return destinatario

    def _wix_order_codigo_servico(self, order: dict) -> str:
        shipping_info = order.get("shippingInfo", "")
        delivery_option = shipping_info.get("deliveryOption", "")

        if delivery_option == "PAC":
            # PAC CONTRATO AG
            return "03298"
        elif delivery_option == "SEDEX":
            # SEDEX CONTRATO AG
            return "03220"

    def _wix_order_codigo_servico_adicional(self, order: dict) -> str:
        shipping_info = order.get("shippingInfo", "")
        delivery_option = shipping_info.get("deliveryOption", "")

        if delivery_option == "PAC":
            # PAC CONTRATO AG
            return "064"
        elif delivery_option == "SEDEX":
            # SEDEX CONTRATO AG
            return "019"

    def _wix_order_valor_declarado(self, order: dict) -> float:
        totals = order.get("totals", {})
        subtotal = totals.get("subtotal", "")

        return float(subtotal)

    def _wix_order_itens_declaracao_conteudo(self, order: dict) -> list:
        line_items = order.get("lineItems")
        itens_declaracao_conteudo = []

        for item in line_items:
            item_declaracao_conteudo = {
                "conteudo": item.get("name", ""),
                "quantidade": int(item.get("quantity", "")),
                "valor": float(item.get("priceData", {}).get("totalPrice", ""))
            }

            itens_declaracao_conteudo.append(item_declaracao_conteudo)

        return itens_declaracao_conteudo

    def _wix_order_peso_informado(self, order: dict) -> str:
        totals = order.get("totals", {})

        total_weight_grams = float(totals.get("weight", 0)) * 1000

        return str(int(total_weight_grams))
