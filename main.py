from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np

app = FastAPI()

def converter_tipos(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    return obj

@app.get("/dados/")
def ler_excel(arquivo: str = "contratos_fianca.xlsx"):
    try:
        df = pd.read_excel(arquivo)

        if 'id_eq3_contratante' not in df.columns:
            return JSONResponse(status_code=400, content={"erro": "Coluna 'id_eq3_contratante' não encontrada."})

        grouped = df.groupby('id_eq3_contratante')
        resultado = {}

        for id_contratante, grupo in grouped:
            lista = grupo.drop(columns=['id_eq3_contratante']).to_dict(orient='records')
            resultado[id_contratante] = lista

        return resultado

    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"erro": f"Arquivo '{arquivo}' não encontrado."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/buscar/")
def buscar_por_id(
    arquivo: str = "contratos_fianca.xlsx",
    id_eq3_contratante: str = Query(..., description="ID do contratante para buscar contratos")
):
    try:
        df = pd.read_excel(arquivo)

        if 'id_eq3_contratante' not in df.columns:
            return JSONResponse(status_code=400, content={"erro": "Coluna 'id_eq3_contratante' não encontrada."})

        # Normaliza strings
        df['id_eq3_contratante'] = df['id_eq3_contratante'].astype(str).str.strip().str.upper()
        id_normalizado = id_eq3_contratante.strip().upper()

        # Filtra por ID
        df_filtrado = df[df['id_eq3_contratante'] == id_normalizado]

        if df_filtrado.empty:
            return JSONResponse(status_code=404, content={"mensagem": "Nenhum contrato encontrado para esse ID."})

        contratos_agrupados = []
        for numero_contrato, grupo in df_filtrado.groupby('numero_contrato'):
            primeiro = grupo.iloc[0]
            contrato_info = {
                "numero_contrato": numero_contrato,
                "cnpj_contratante": primeiro.get("cnpj_contratante"),
                "nome_contratante": primeiro.get("nome_contratante"),
                "nome_afiancado": primeiro.get("nome_afiancado"),
                "nome_beneficiario": primeiro.get("nome_beneficiario"),
                "valor_contrato_abertura": primeiro.get("valor_contrato_abertura"),
                "valor_saldo_atualizado_contrato": primeiro.get("valor_saldo_atualizado_contrato"),
                "data_abertura_contrato": primeiro.get("data_abertura_contrato"),
                "data_inicio_operacao": primeiro.get("data_inicio_operacao"),
                "data_limite_operacao": primeiro.get("data_limite_operacao"),
                "nome_indexador": primeiro.get("nome_indexador"),
                "percentual_taxa_carta": primeiro.get("percentual_taxa_carta"),
                "indicador_renovacao_automatica": primeiro.get("indicador_renovacao_automatica"),
                "tipo_comissionamento": primeiro.get("tipo_comissionamento"),
                "periodicidade_comissao": primeiro.get("periodicidade_comissao"),
                "agencia": primeiro.get("agencia"),
                "conta": primeiro.get("conta"),
                "digito": primeiro.get("digito"),
            }

            comissoes = grupo[[
                "numero_comissao", "tipo_comissao", "taxa_comissao", "situacao_comissao",
                "valor_esperado_abertura_comissao", "valor_comissao_abertura", "valor_saldo_atualizado_comissao",
                "valor_vencimento_comissao", "valor_pago", "valor_pago_juros",
                "data_inicio_vigencia_comissao", "data_fim_vigencia_comissao", "data_vencimento_comissao",
                "indicador_comissao_atraso", "valor_mora_comissao", "valor_multa_comissao",
                "valor_juros_comissao", "valor_apropriar_atual"
            ]].sort_values(by="numero_comissao").to_dict(orient="records")

            contrato_info["comissoes"] = comissoes
            contratos_agrupados.append(contrato_info)

        # Aplicar conversão de tipos nativos recursivamente
        for contrato in contratos_agrupados:
            for k, v in contrato.items():
                if isinstance(v, list):
                    contrato[k] = [{ck: converter_tipos(cv) for ck, cv in c.items()} for c in v]
                else:
                    contrato[k] = converter_tipos(v)

        return contratos_agrupados

    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"erro": f"Arquivo '{arquivo}' não encontrado."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})
