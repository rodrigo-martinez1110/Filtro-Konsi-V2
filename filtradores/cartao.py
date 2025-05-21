import pandas as pd
import streamlit as st
from datetime import datetime

def filtro_cartao(base, convenio, data_limite, quant_bancos, comissao_minima, margem_emprestimo_limite, selecao_lotacao, selecao_vinculos, convai, equipes, configuracoes):
    if base.empty:
        st.error("Erro: A base está vazia!")
        return pd.DataFrame()
    
    base = base.iloc[:, :26]

    if 'Nome_Cliente' in base.columns and base['Nome_Cliente'].notna().any():
        base['Nome_Cliente'] = base['Nome_Cliente'].apply(lambda x: x.title() if isinstance(x, str) else x)

    base['CPF'] = base['CPF'].str.replace(".", "", regex=False).str.replace("-", "", regex=False)

    if selecao_lotacao:
        base = base.loc[~base['Lotacao'].isin(selecao_lotacao)]
    if selecao_vinculos:
        base = base.loc[~base['Vinculo_Servidor'].isin(selecao_vinculos)]

    # Especificidades de convênios
    if convenio == 'govsp':
        base = base[base['Lotacao'] != "ALESP"]
        base['margem_cartao_usado'] = base['MG_Cartao_Total'] - base['MG_Cartao_Disponivel']
        usou_cartao = base.loc[base['margem_cartao_usado'] > 0]
        base = base.loc[base['MG_Cartao_Disponivel'] == base['MG_Cartao_Total']]
    else:
        base = base.loc[base['MG_Cartao_Disponivel'] == base['MG_Cartao_Total']]

    # Criar uma máscara para rastrear linhas já tratadas
    base['tratado'] = False
    st.write(configuracoes) 
    for config in configuracoes:
        banco = config['Banco']
        coeficiente = config['Coeficiente']
        comissao = (config['Comissão'] / 100)
        parcelas = config['Parcelas']
        coluna_condicional = config['Coluna Condicional']
        valor_condicional = config['Valor Condicional']
        coeficiente_parcela = config['Coeficiente_Parcela']

        if coluna_condicional != "Aplicar a toda a base":
            if isinstance(valor_condicional, str):
                mask = (base[coluna_condicional].str.contains(valor_condicional, na=False, case=False)) & (~base['tratado'])
            else:
                mask = (base[coluna_condicional].isin(valor_condicional)) & (~base['tratado'])
        else:
            mask = ~base['tratado']

        if convenio == 'govsp':
            base.loc[mask, 'valor_liberado_cartao'] = (base.loc[mask, 'MG_Cartao_Disponivel'] * coeficiente).round(2)
            base.loc[(base['valor_liberado_cartao'] != 0) & (base['Matricula'].isin(usou_cartao['Matricula'])), 'valor_liberado_cartao'] = 0
            base.loc[mask, 'valor_parcela_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] / coeficiente_parcela).round(2)
            base.loc[(base['valor_liberado_cartao'] == 0) & (base['Matricula'].isin(usou_cartao['Matricula'])), 'valor_parcela_cartao'] = 0
        else:
            base.loc[mask, 'valor_liberado_cartao'] = (base.loc[mask, 'MG_Cartao_Disponivel'] * coeficiente).round(2)
            base.loc[mask, 'valor_parcela_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] / coeficiente_parcela).round(2)

        base.loc[mask, 'comissao_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] * comissao).round(2)
        base.loc[mask, 'banco_cartao'] = banco
        base.loc[mask, 'prazo_cartao'] = parcelas
        base['prazo_cartao'] = base['prazo_cartao'].astype(int)

        base.loc[mask, 'tratado'] = True

    base = base.loc[base['MG_Emprestimo_Disponivel'] < margem_emprestimo_limite]
    base = base.loc[base['comissao_cartao'] >= comissao_minima]

    base = base.sort_values(by='valor_liberado_cartao', ascending=False)
    base = base.drop_duplicates(subset='CPF')

    # Filtrar pela idade (Caso tenha coluna de Data de Nascimento)
    if data_limite:
        base = base[pd.to_datetime(base["Data_Nascimento"], dayfirst=True).dt.date >= data_limite]

    colunas_adicionais = [
        'FONE1', 'FONE2', 'FONE3', 'FONE4',
        'valor_liberado_emprestimo', 'valor_liberado_beneficio',
        'comissao_emprestimo', 'comissao_beneficio',
        'valor_parcela_emprestimo', 'valor_parcela_beneficio',
        'banco_emprestimo', 'banco_beneficio',
        'prazo_emprestimo', 'prazo_beneficio', 'Campanha'
    ]

    for coluna in colunas_adicionais:
        if coluna not in base.columns:
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

    # Começa preenchendo TODAS as linhas com a equipe padrão
    base['Campanha'] = f"{convenio}_{data_hoje}_cartao_{equipes}"

    # Aplica "convai" em uma amostra aleatória proporcional
    if convai > 0:
        n_convai = int((convai / 100) * len(base))
        indices_convai = base.sample(n=n_convai, random_state=42).index

        # Substitui a equipe pelo sufixo convai nas linhas selecionadas
        base.loc[indices_convai, 'Campanha'] = f"{convenio}_{data_hoje}_cartao_convai"


    st.write(base.shape)
    return base
