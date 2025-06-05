from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd

def buscar_por_id(id_eq3_contratante: str):
    try:
        # Carrega o arquivo
        df = pd.read_parquet("caminho/para/seuarquivo.parquet")  # ajuste o path aqui

        # Verifica se a coluna existe
        if 'id_eq3_contratante' not in df.columns:
            return JSONResponse(status_code=400, content={"erro": "Coluna 'id_eq3_contratante' não encontrada."})

        # Normaliza para comparação
        df['id_eq3_contratante'] = df['id_eq3_contratante'].astype(str).str.strip().str.upper()
        id_normalizado = id_eq3_contratante.strip().upper()

        # Filtra os dados
        df_filtrado = df[df['id_eq3_contratante'] == id_normalizado]

        if df_filtrado.empty:
            return JSONResponse(status_code=404, content={"mensagem": "Nenhum contrato encontrado para esse ID."})

        # Prepara a lista de contratos
        contratos_agrupados = []

        colunas_comissao_esperadas = [
            "tipo_comissao", "taxa_comissao", "situacao_comissao",
            "situacao_comissao_anterior", "valor_saldo_atualizado_comissao",
            "valor_comissao_abertura", "valor_pago", "valor_pago_juros",
            "data_inicio_vigencia_comissao", "datas_fim_vigencia_comissao"
        ]

        for numero_contrato, grupo in df_filtrado.groupby("numero_contrato"):
            grupo = grupo.copy()
            grupo = grupo.where(pd.notnull(grupo), None)  # substitui NaN por None

            primeiro = grupo.iloc[0]

            contrato_info = {
                "numero_contrato": numero_contrato,
                "cnpj_contratante": primeiro.get("Cnpj_contratante"),
                "nome_contratante": primeiro.get("nome_contratante"),
                "nome_afiançado": primeiro.get("nome_afiançado"),
                "nome_beneficiário": primeiro.get("nome_beneficiário"),
                "valor_contrato": primeiro.get("valor_contrato"),
                "valor_saldo_atualizado_contrato": primeiro.get("valor_saldo_atualizado_contrato"),
                "data_abertura_contrato": primeiro.get("data_abertura_contrato"),
                "data_inicio_operacao": primeiro.get("data_inicio_operacao"),
                "data_limite_operacao": primeiro.get("data_limite_operacao"),
                "nome_indexador": primeiro.get("nome_indexador"),
                "percentual_taxa_carta": primeiro.get("percentual_taxa_carta"),
                "indicador_renovacao_automatica": primeiro.get("indicador_renovacao_automatica"),
                "tipo_pagamento_comissao": primeiro.get("tipo_pagamento_comissao"),
                "periodicidade_comissao": primeiro.get("periodicidade_comissao"),
                "agencia": {
                    "agencia": primeiro.get("agencia"),
                    "conta": primeiro.get("conta"),
                    "digito": primeiro.get("digito")
                }
            }

            # Coleta colunas de comissão, se existirem
            colunas_existentes = [col for col in colunas_comissao_esperadas if col in grupo.columns]
            contrato_info["comissoes"] = grupo[colunas_existentes].to_dict(orient="records")

            contratos_agrupados.append(contrato_info)

        return JSONResponse(content=jsonable_encoder(contratos_agrupados))

    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"erro": "Arquivo de dados não encontrado."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})
