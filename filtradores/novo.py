import pandas as pd
import streamlit as st
from datetime import datetime

def filtro_novo(base, convenio, quant_bancos, comissao_minima, margem_emprestimo_limite, selecao_lotacao, selecao_vinculos, configuracoes):
    if base.empty:
        st.error("Erro: A base está vazia!")
        return pd.DataFrame()



    #================================================= ESPECIFICIDADES DE CONVENIOS =================================================#
    if convenio == 'govsp':
        negativos = base.loc[base['MG_Emprestimo_Disponivel'] < 0, ['Matricula', 'Nome_Cliente', 'MG_Emprestimo_Disponivel']]
        base = base.loc[~base['Matricula'].isin(negativos['Matricula'])]
    elif convenio == 'govmt':
        base = base.loc[base['MG_Compulsoria_Disponivel'] >= 0]
    #================================================================================================================================#

    # Garantir que apenas as primeiras 23 colunas sejam consideradas
    base = base.iloc[:, :26]


    # Normalização de nomes e CPFs
    if 'Nome_Cliente' in base.columns and base['Nome_Cliente'].notna().any():
        base['Nome_Cliente'] = base['Nome_Cliente'].apply(lambda x: x.title() if isinstance(x, str) else x)
    base['CPF'] = base['CPF'].str.replace(".", "", regex=False).str.replace("-", "", regex=False)

    # Excluir lotações e vínculos selecionados
    if selecao_lotacao:
        base = base.loc[~base['Lotacao'].isin(selecao_lotacao)]
    if selecao_vinculos:
        base = base.loc[~base['Vinculo_Servidor'].isin(selecao_vinculos)]

    # Criar uma máscara para rastrear linhas já tratadas
    base['tratado'] = False

    # Aplicar configurações dos bancos
    for config in configuracoes:
        banco = config['Banco']
        coeficiente = config['Coeficiente']
        comissao = (config['Comissão'] / 100)
        parcelas = config['Parcelas']
        coluna_condicional = config['Coluna Condicional']
        valor_condicional = config['Valor Condicional']
        margem_seguranca = config['Margem seguranca']

        if coluna_condicional != "Aplicar a toda a base":
            if isinstance(valor_condicional, str):
                # Máscara para linhas que contêm a palavra-chave na coluna condicional
                mask = (base[coluna_condicional].str.contains(valor_condicional, na=False, case=False)) & (~base['tratado'])
            else:
                # Máscara para as linhas que atendem à condição específica
                mask = (base[coluna_condicional].isin(valor_condicional)) & (~base['tratado'])
        else:
            # Máscara para todas as linhas não tratadas
            mask = ~base['tratado']

        if margem_seguranca:
            base.loc[mask, 'valor_liberado_emprestimo'] = (base.loc[mask, 'MG_Emprestimo_Disponivel'] * 0.95 * coeficiente).round(2)
            base.loc[mask, 'valor_parcela_emprestimo'] = (base.loc[mask, 'MG_Emprestimo_Disponivel'] * 0.95 * coeficiente).round(2)
        else:
            base.loc[mask, 'valor_liberado_emprestimo'] = (base.loc[mask, 'MG_Emprestimo_Disponivel'] * coeficiente).round(2)
        base.loc[mask, 'comissao_emprestimo'] = (base.loc[mask, 'valor_liberado_emprestimo'] * comissao).round(2)
        base.loc[mask, 'banco_emprestimo'] = banco

        base.loc[mask, 'prazo_emprestimo'] = parcelas
        base['prazo_emprestimo'] = base['prazo_emprestimo'].astype(str).replace(".0", "")

        base.loc[mask, 'valor_parcela_emprestimo'] = base['MG_Emprestimo_Disponivel']

        # Marcar essas linhas como tratadas
        base.loc[mask, 'tratado'] = True

        

    # Filtrar comissões e margens
    base = base.loc[base['MG_Emprestimo_Disponivel'] >= margem_emprestimo_limite]
    base = base.loc[base['comissao_emprestimo'] >= comissao_minima]

    # Ordenar e remover duplicados
    base = base.sort_values(by='valor_liberado_emprestimo', ascending=False)
    base = base.drop_duplicates(subset='CPF')

    # Adicionar colunas adicionais
    colunas_adicionais = [
        'FONE1', 'FONE2', 'FONE3', 'FONE4',
        'valor_liberado_beneficio', 'valor_liberado_cartao',
        'comissao_beneficio', 'comissao_cartao',
        'valor_parcela_beneficio', 'valor_parcela_cartao',
        'banco_beneficio', 'banco_cartao',
        'prazo_beneficio', 'prazo_cartao', 'Campanha'
    ]
    for coluna in colunas_adicionais:
        base[coluna] = ""

    data_hoje = datetime.today().strftime('%d%m%Y')
    base['Campanha'] = convenio + "_" + data_hoje + "_" + "novo" + "_" + "outbound"
    # Seleção final de colunas
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

    # Remover a coluna de controle 'tratado' antes de retornar
    base = base.drop(columns=['tratado'], errors='ignore')


    mapeamento = {
        'Origem_Dado': 'ORIGEM DO DADO',
        'MG_Emprestimo_Total': 'Mg_Emprestimo_Total',
        'MG_Emprestimo_Disponivel': 'Mg_Emprestimo_Disponivel',
        'MG_Beneficio_Saque_Total': 'Mg_Beneficio_Saque_Total',
        'MG_Beneficio_Saque_Disponivel': 'Mg_Beneficio_Saque_Disponivel',
        'MG_Cartao_Total': 'Mg_Cartao_Total',
        'MG_Cartao_Disponivel': 'Mg_Cartao_Disponivel',
    }

    # Renomear as colunas
    base.rename(columns=mapeamento, inplace=True)

    st.write(base.shape)

    return base
