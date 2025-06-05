from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd
import numpy as np

app = FastAPI()

@app.get("/buscar/")
def buscar_por_id(
    id_eq3_contratante: str = Query(..., description="ID do contratante para buscar contratos")
):
    arquivo = "contratos_fianca.xlsx"
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(arquivo)

        # Verifica se a coluna existe
        if 'id_eq3_contratante' not in df.columns:
            return JSONResponse(status_code=400, content={"erro": "Coluna 'id_eq3_contratante' não encontrada."})

        # Normaliza coluna
        df['id_eq3_contratante'] = df['id_eq3_contratante'].astype(str).str.strip().str.upper()
        id_normalizado = id_eq3_contratante.strip().upper()

        # Filtra
        df_filtrado = df[df['id_eq3_contratante'] == id_normalizado]

        if df_filtrado.empty:
            return JSONResponse(status_code=404, content={"mensagem": "Nenhum contrato encontrado para esse ID."})

        contratos_agrupados = []

        # Conversão segura de tipos
        def converter_tipos(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.bool_)):
                return bool(obj)
            elif pd.isna(obj):
                return None
            elif isinstance(obj, pd.Timestamp):
                return obj.strftime("%Y-%m-%d")
            return obj

        for numero_contrato, grupo in df_filtrado.groupby("numero_contrato"):
            grupo = grupo.where(pd.notnull(grupo), None)
            primeiro = grupo.iloc[0]

            contrato_info = {
                "numero_contrato": numero_contrato,
                "cnpj_contratante": primeiro.get("cnpj_contratante"),
                "nome_contratante": primeiro.get("nome_contratante"),
                "nome_afiançado": primeiro.get("nome_afiançado"),
                "nome_beneficiario": primeiro.get("nome_beneficiario"),
                "valor_contrato_abertura": primeiro.get("valor_contrato_abertura"),
                "valor_saldo_atualizado_contrato": primeiro.get("valor_saldo_atualizado_contrato"),
                "data_inicio_operacao": primeiro.get("data_inicio_operacao"),
                "data_limite_operacao": primeiro.get("data_limite_operacao"),
                "nome_indexador": primeiro.get("nome_indexador"),
                "percentual_taxa_carta": primeiro.get("percentual_taxa_carta"),
                "indicador_renovacao_automatica": primeiro.get("indicador_renovacao_automatica"),
                "tipo_pagamento_comissao": primeiro.get("tipo_pagamento_comissao"),
                "periodicidade_comissao": primeiro.get("periodicidade_comissao"),
                "agencia": primeiro.get("agencia"),
                "conta": primeiro.get("conta"),
                "digito": primeiro.get("digito"),
            }

            # Só monta as comissões se a coluna existir
            if 'numero_comissao' in grupo.columns:
                comissoes = grupo[[
                    "numero_comissao", "tipo_comissao", "situacao_comissao",
                    "valor_pago", "data_inicio_comissao", "data_fim_comissao",
                    "valor_comissao_abertura", "valor_pago_juros", "valor_multa_comissao",
                    "valor_juros_comissao", "valor_apropriado_atual"
                ]].fillna('').to_dict(orient="records")
            else:
                comissoes = []

            contrato_info["comissoes"] = comissoes

            # Conversão de tipos
            for k, v in contrato_info.items():
                if isinstance(v, list):
                    contrato_info[k] = [{ck: converter_tipos(cv) for ck, cv in c.items()} for c in v]
                else:
                    contrato_info[k] = converter_tipos(v)

            contratos_agrupados.append(contrato_info)

        return JSONResponse(content=jsonable_encoder(contratos_agrupados))

    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"erro": f"Arquivo '{arquivo}' não encontrado."})
    except Exception as e:
        return JSONResponse(status_code=50
