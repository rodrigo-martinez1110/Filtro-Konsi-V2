import pandas as pd
import streamlit as st
from datetime import datetime
import re

def filtro_beneficio(base, convenio, data_limite, quant_bancos, comissao_minima, margem_emprestimo_limite, selecao_lotacao, selecao_vinculos, convai, equipes, configuracoes):
    if base.empty:
        st.error("Erro: A base está vazia!")
        return pd.DataFrame()
    
    base = base.iloc[:, :26]
    base['CPF'] = base['CPF'].str.replace(".", "", regex=False).str.replace("-", "", regex=False)

    if 'Nome_Cliente' in base.columns and base['Nome_Cliente'].notna().any():
        base['Nome_Cliente'] = base['Nome_Cliente'].apply(lambda x: x.title() if isinstance(x, str) else x)

    if convenio == 'govsp':
        base['margem_beneficio_usado'] = base['MG_Beneficio_Saque_Total'] - base['MG_Beneficio_Saque_Disponivel']
        usou_beneficio = base.loc[base['margem_beneficio_usado'] > 0]
        base = base.loc[base['MG_Beneficio_Saque_Disponivel'] == base['MG_Beneficio_Saque_Total']]
        base = base[base['Lotacao'] != "ALESP"]

    
    conv_excluidos = ['prefrj', 'govpi', 'goval', 'govce']     # Convenios que não precisa ter TOTAL = DISPONIVEL
    if convenio not in conv_excluidos:
        base = base.loc[base['MG_Beneficio_Saque_Disponivel'] == base['MG_Beneficio_Saque_Total']]

    if selecao_lotacao:
        base = base.loc[~base['Lotacao'].isin(selecao_lotacao)]
    if selecao_vinculos:
        base = base.loc[~base['Vinculo_Servidor'].isin(selecao_vinculos)]
    

    # Convênios que não precisa ser virgem na margem beneficio
    
    
    
    base = base.sort_values(by='MG_Beneficio_Saque_Disponivel', ascending = False)
    
    #================================================================================================================================#


    # Criar uma máscara para rastrear linhas já tratadas
    base['tratado'] = False
    st.write(configuracoes) 
    for config in configuracoes:
        banco = config['Banco']
        coeficiente = config['Coeficiente']
        coeficiente2 = config['Coeficiente2']
        comissao = (config['Comissão'] / 100)
        parcelas = config['Parcelas']
        coluna_condicional = config['Coluna Condicional']
        valor_condicional = config['Valor Condicional']
        coeficiente_parcela = config['Coeficiente_Parcela']
        usar_margem_compra = config['Usar_Margem_Compra']

        if coluna_condicional != "Aplicar a toda a base":
            if isinstance(valor_condicional, str) and ";" in valor_condicional:
                # Se for uma string separada por ";", transforma em lista removendo espaços extras
                valor_condicional = [item.strip() for item in valor_condicional.split(";")]

            # Se for uma lista o codigo vai me criar uma regex para buscar qualquer uma das palavras
            if isinstance(valor_condicional, list):
                regex_pattern = "|".join(map(re.escape, valor_condicional))
                #teste
                mask = (base[coluna_condicional].str.contains(regex_pattern, na=False, case=False)) & (~base['tratado'])
            else:
                # Se for apenas uma string vai buscar exatamente a unica palavra
                mask = (base[coluna_condicional].str.contains(re.escape(valor_condicional), na=False, case=False)) & (~base['tratado'])
        else:
            # Máscara para todas as linhas não tratadas
            mask = ~base['tratado']

        if convenio == 'goval':
            condicao = (
            (base['MG_Beneficio_Saque_Disponivel'] == base['MG_Beneficio_Saque_Total']) &
            (base['MG_Beneficio_Compra_Disponivel'] == base['MG_Beneficio_Compra_Total'])
        )
            
            base['coeficiente'] = coeficiente2
            base.loc[condicao, 'coeficiente'] = coeficiente

            base.loc[condicao, 'MG_Beneficio_Saque_Disponivel'] = (base['MG_Beneficio_Saque_Disponivel'] + base['MG_Beneficio_Compra_Disponivel']).round(2)
            
            base.loc[(base['MG_Beneficio_Saque_Disponivel'] > 20) & (mask), "valor_liberado_beneficio"
                    ] = (base['MG_Beneficio_Saque_Disponivel'] * base['coeficiente']).round(2)
            
            base.loc[mask, 'valor_parcela_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela).round(2)
            
            base.drop(columns=['coeficiente'], inplace=True)

        elif convenio == 'govam':
            if usar_margem_compra:
                mask = (
                    mask &
                    (base['MG_Beneficio_Compra_Total'] == base['MG_Beneficio_Compra_Disponivel']) &
                    (base['MG_Beneficio_Saque_Total'] == base['MG_Beneficio_Saque_Disponivel'])
                )

                # A margem saque subirá no hubspot com a margem compra (saque + compra)
                base.loc[mask, 'MG_Beneficio_Saque_Total'] = base.loc[mask, 'MG_Beneficio_Compra_Total']
                base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] = base.loc[mask, 'MG_Beneficio_Compra_Disponivel']
                
                base.loc[mask, 'valor_liberado_beneficio'] = (
                    base.loc[mask, 'MG_Beneficio_Compra_Disponivel'] * coeficiente
                ).round(2)

                base.loc[mask, 'valor_parcela_beneficio'] = (
                    base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela
                ).round(2)
            else:
                mask = (
                    mask &
                    (base['MG_Beneficio_Compra_Total'] != base['MG_Beneficio_Compra_Disponivel']) &
                    (base['MG_Beneficio_Saque_Total'] == base['MG_Beneficio_Saque_Disponivel'])
                )
                
                base.loc[mask, 'valor_liberado_beneficio'] = (
                    base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] * coeficiente
                ).round(2)

                base.loc[mask, 'valor_parcela_beneficio'] = (
                    base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela
                ).round(2)
            

        elif convenio == 'govsp':
            base.loc[mask, 'valor_liberado_beneficio'] = (base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] * coeficiente).round(2)
            base.loc[(base['valor_liberado_beneficio'] != 0) & (base['Matricula'].isin(usou_beneficio['Matricula'])), 'valor_liberado_beneficio'] = 0
            base.loc[mask, 'valor_parcela_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela).round(2)
        else:
            base.loc[mask, 'valor_liberado_beneficio'] = (base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] * coeficiente).round(2)
            base.loc[mask, 'valor_parcela_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela).round(2)

        base.loc[mask, 'comissao_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] * comissao).round(2)
        base.loc[mask, 'banco_beneficio'] = banco
        base.loc[mask, 'prazo_beneficio'] = parcelas
        base['prazo_beneficio'] = base['prazo_beneficio'].astype(str).str.replace(".0", "")

        # Marcar essas linhas como tratadas
        base.loc[mask, 'tratado'] = True

    base = base.loc[base['MG_Emprestimo_Disponivel'] < margem_emprestimo_limite]
    base = base.loc[base['comissao_beneficio'] >= comissao_minima]

    base = base.sort_values(by='valor_liberado_beneficio', ascending=False)
    base = base.drop_duplicates(subset='CPF')

    colunas_adicionais = [
        'FONE1', 'FONE2', 'FONE3', 'FONE4',
        'valor_liberado_emprestimo', 'valor_liberado_cartao',
        'comissao_emprestimo', 'comissao_cartao',
        'valor_parcela_emprestimo', 'valor_parcela_cartao',
        'banco_emprestimo', 'banco_cartao',
        'prazo_emprestimo', 'prazo_cartao', 'Campanha'
    ]

    # Filtrar pela idade (Caso tenha coluna de Data de Nascimento)
    if data_limite:
        base = base[pd.to_datetime(base["Data_Nascimento"], dayfirst=True).dt.date >= data_limite]

    for coluna in colunas_adicionais:
        base[coluna] = ""

    colunas = [
        'Origem_Dado', 'Nome_Cliente', 'Matricula', 'CPF', 'Data_Nascimento',
        'MG_Emprestimo_Total', 'MG_Emprestimo_Disponivel',
        'MG_Beneficio_Saque_Total', 'MG_Beneficio_Saque_Disponivel',
        'MG_Cartao_Total', 'MG_Cartao_Disponivel',
        'Convenio', 'Vinculo_Servidor', 'Lotacao', 'Secretaria',
        'FONE1', 'FONE2', 'FONE3', 'FONE4',
        'valor_liberado_emprestimo', 'valor_liberado_beneficio', 'valor_liberado_cartao',
        'comissao_emprestimo', 'comissao_beneficio', 'comissao_cartao',
        'valor_parcela_emprestimo', 'valor_parcela_beneficio', 'valor_parcela_cartao',
        'banco_emprestimo', 'banco_beneficio', 'banco_cartao',
        'prazo_emprestimo', 'prazo_beneficio', 'prazo_cartao',
        'Campanha'
    ]
    base = base[colunas]


    mapeamento = {
        'Origem_Dado': 'ORIGEM DO DADO',
        'MG_Emprestimo_Total': 'Mg_Emprestimo_Total',
        'MG_Emprestimo_Disponivel': 'Mg_Emprestimo_Disponivel',
        'MG_Beneficio_Saque_Total': 'Mg_Beneficio_Saque_Total',
        'MG_Beneficio_Saque_Disponivel': 'Mg_Beneficio_Saque_Disponivel',
        'MG_Cartao_Total': 'Mg_Cartao_Total',
        'MG_Cartao_Disponivel': 'Mg_Cartao_Disponivel',
    }
    base.rename(columns=mapeamento, inplace=True)

    base = base.drop(columns=['tratado'], errors='ignore')

    data_hoje = datetime.today().strftime('%d%m%Y')
    base['Campanha'] = convenio + "_" + data_hoje + "_" + "benef" + "_" + equipes
    if convai > 0:
        n_convai = int((convai / 100) * len(base))
        
        # Amostra aleatória de índices
        indices_convai = base.sample(n=n_convai, random_state=42).index
        
        # Aplica a tag "convai" apenas nessas linhas
        base.loc[indices_convai, 'Campanha'] = convenio + "_" + data_hoje + "_" + "benef" + "_" + equipes


    st.write(base.shape)
    st.write(convenio)
    return base
