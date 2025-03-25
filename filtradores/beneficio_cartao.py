import pandas as pd
import streamlit as st
from datetime import datetime

def filtro_beneficio_e_cartao(base, convenio, quant_bancos, comissao_minima, margem_emprestimo_limite, selecao_lotacao, selecao_vinculos, configuracoes):
    if base.empty:
        st.error("Erro: A base está vazia!")
        return pd.DataFrame()
    
    base = base.iloc[:, :26]
    
    base['valor_liberado_beneficio'] = 0
    base['valor_liberado_cartao'] = 0

    if 'Nome_Cliente' in base.columns and base['Nome_Cliente'].notna().any():
        base['Nome_Cliente'] = base['Nome_Cliente'].apply(lambda x: x.title() if isinstance(x, str) else x)
    
    base['CPF'] = base['CPF'].str.replace(".", "", regex=False).str.replace("-", "", regex=False)

    if convenio == 'govsp':
        base = base[base['Lotacao'] != 'ALESP']
        base['margem_beneficio_usado'] = base['MG_Beneficio_Saque_Total'] - base['MG_Beneficio_Saque_Disponivel']
        base['margem_cartao_usada'] = base['MG_Cartao_Total'] - base['MG_Cartao_Disponivel']
        usou_beneficio = base.loc[base['margem_beneficio_usado'] > 0]
        usou_cartao = base.loc[base['margem_cartao_usada'] > 0]


    base['tratado_beneficio'] = False
    base['tratado_cartao'] = False
    for config in configuracoes:
        cartao_escolhido = config['Cartao_Escolhido']
        banco = config['Banco']
        coeficiente1 = config['Coeficiente']
        coeficiente2 = config['Coeficiente2']
        comissao = (config['Comissão'] / 100)
        parcelas = config['Parcelas']
        coluna_condicional = config['Coluna Condicional']
        valor_condicional = config['Valor Condicional']
        coeficiente_parcela = config['Coeficiente_Parcela']
        margem_minima_cartao = config['Margem_Minima_Cartao']

        if coluna_condicional != "Aplicar a toda a base":
            if isinstance(valor_condicional, str):
                if cartao_escolhido == 'Benefício':
                    mask = (base[coluna_condicional].str.contains(valor_condicional, na=False, case=False)) & (~base['tratado_beneficio'])
                elif cartao_escolhido == 'Consignado':
                    mask = (base[coluna_condicional].str.contains(valor_condicional, na=False, case=False)) & (~base['tratado_cartao'])
            else:
                if cartao_escolhido == 'Benefício':
                    mask = (base[coluna_condicional].isin(valor_condicional)) & (~base['tratado_beneficio'])
                elif cartao_escolhido == 'Consignado':
                    mask = (base[coluna_condicional].isin(valor_condicional)) & (~base['tratado_cartao'])
        else:
            if cartao_escolhido == 'Benefício':
                mask = ~base['tratado_beneficio']
            elif cartao_escolhido == 'Consignado':
                mask = ~base['tratado_cartao']

        
        if convenio == 'goval':
            if cartao_escolhido == 'Benefício':
                condicao_1 = (
                    (base['MG_Beneficio_Saque_Disponivel'] == base['MG_Beneficio_Saque_Total']) &
                    (base['MG_Beneficio_Compra_Disponivel'] == base['MG_Beneficio_Compra_Total']) &
                    ((base['MG_Beneficio_Saque_Disponivel'] + base['MG_Beneficio_Compra_Disponivel']) >= margem_minima_cartao) &
                    (mask)
                )
                
                condicao_2 = (
                    ((base['MG_Beneficio_Saque_Disponivel'] != base['MG_Beneficio_Saque_Total']) |
                    (base['MG_Beneficio_Compra_Disponivel'] != base['MG_Beneficio_Compra_Total'])) &
                    (base['MG_Beneficio_Saque_Disponivel'] >= margem_minima_cartao) &
                    (mask)
                )
                
                # Inicializando coeficiente e valor liberado
                base['coeficiente'] = 0
                base['coeficiente'] = base['coeficiente'].astype(float)

                base['valor_liberado_beneficio'] = 0
                base['valor_liberado_beneficio'] = base['valor_liberado_beneficio'].astype(float)

                base = base.loc[base['MG_Emprestimo_Disponivel'] < margem_emprestimo_limite]


                # Aplicando as condições
                base.loc[condicao_1, 'coeficiente'] = coeficiente1
                base.loc[condicao_1, 'valor_liberado_beneficio'] = (
                    (base['MG_Beneficio_Saque_Disponivel'] + base['MG_Beneficio_Compra_Disponivel']) * base['coeficiente']
                ).round(2)
                
                base.loc[condicao_2, 'coeficiente'] = coeficiente2
                base.loc[condicao_2, 'valor_liberado_beneficio'] = (
                    base['MG_Beneficio_Saque_Disponivel'] * base['coeficiente']
                ).round(2)

                base['valor_liberado_beneficio'] = base['valor_liberado_beneficio'].astype(float)


                base.loc[(mask), 'valor_parcela_beneficio'] = (base['valor_liberado_beneficio'] / coeficiente_parcela).round(2)
                base.drop(columns=['coeficiente'], inplace=True)

                

            elif cartao_escolhido == 'Consignado':
                base.loc[(base['MG_Cartao_Disponivel'] == base['MG_Cartao_Total']) &
                         (base['MG_Cartao_Disponivel'] >= margem_minima_cartao) & 
                         (mask),
                         "valor_liberado_cartao"] = (base['MG_Cartao_Disponivel'] * coeficiente1).round(2)
                
                base.loc[(base['MG_Cartao_Disponivel'] >= margem_minima_cartao) & (mask),
                         'valor_parcela_cartao'] = (base['valor_liberado_cartao'] / coeficiente_parcela).round(2)
                
                base['valor_liberado_cartao'] = base['valor_liberado_cartao'].astype(float)
        
        elif convenio == 'govsp':
            if cartao_escolhido == 'Benefício':
                base.loc[
                    (base['MG_Beneficio_Saque_Disponivel'] >= margem_minima_cartao) &
                    (base['MG_Beneficio_Saque_Total'] == base['MG_Beneficio_Saque_Disponivel']) &
                    (mask),
                    'valor_liberado_beneficio'
                ] = (base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] * coeficiente1).round(2)
                
                base.loc[(base['valor_liberado_beneficio'] != 0) &
                         (base['Matricula'].isin(usou_beneficio['Matricula'])),
                          'valor_liberado_beneficio'] = 0
                
                base.loc[mask, 'valor_parcela_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela).round(2)

            elif cartao_escolhido == 'Consignado':
                base.loc[
                    (base['MG_Cartao_Disponivel'] >= margem_minima_cartao) &
                    (base['MG_Cartao_Total'] == base['MG_Cartao_Disponivel']),
                    'valor_liberado_cartao'
                ] = (base.loc[mask, 'MG_Cartao_Disponivel'] * coeficiente1).round(2)
                
                base.loc[(base['valor_liberado_cartao'] != 0) &
                         (base['Matricula'].isin(usou_cartao['Matricula'])),
                         'valor_liberado_cartao'] = 0
                
                base.loc[mask, 'valor_parcela_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] / coeficiente_parcela).round(2)
        
        else:
            if cartao_escolhido == 'Benefício':
                base.loc[(base['MG_Beneficio_Saque_Disponivel'] >= margem_minima_cartao) &
                         (base['MG_Beneficio_Saque_Total'] == base['MG_Beneficio_Saque_Disponivel']) &
                         (mask),
                         'valor_liberado_beneficio'] = (base.loc[mask, 'MG_Beneficio_Saque_Disponivel'] * coeficiente1).round(2)
                base.loc[mask, 'valor_parcela_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] / coeficiente_parcela).round(2)
            elif cartao_escolhido == 'Consignado':
                base.loc[(base['MG_Cartao_Disponivel'] >= margem_minima_cartao) &
                         (base['MG_Cartao_Total'] == base['MG_Cartao_Disponivel']) &
                         (mask),
                         'valor_liberado_cartao'] = (base.loc[mask, 'MG_Cartao_Disponivel'] * coeficiente1).round(2)

                base.loc[mask, 'valor_parcela_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] / coeficiente_parcela).round(2)
        
        if cartao_escolhido == 'Benefício':
            base.loc[mask, 'comissao_beneficio'] = (base.loc[mask, 'valor_liberado_beneficio'] * comissao).round(2)
            base.loc[mask, 'banco_beneficio'] = banco
            base.loc[mask, 'prazo_beneficio'] = parcelas
            base['prazo_beneficio'] = base['prazo_beneficio'].astype(str).str.replace(".0", "")
            base.loc[mask, 'tratado_beneficio'] = True
        elif cartao_escolhido == 'Consignado':
            base.loc[mask, 'comissao_cartao'] = (base.loc[mask, 'valor_liberado_cartao'] * comissao).round(2)
            base.loc[mask, 'banco_cartao'] = banco
            base.loc[mask, 'prazo_cartao'] = parcelas
            base['prazo_cartao'] = base['prazo_cartao'].astype(str).str.replace(".0", "")
            base.loc[mask, 'tratado_cartao'] = True

    
    base['comissao_total'] = (base['comissao_beneficio'] + base['comissao_cartao']).round(2)
    base = base.sort_values(by='comissao_total', ascending=False)
    base = base[base['comissao_total'] >= comissao_minima]
    base = base.drop_duplicates(subset=['CPF'])

    if selecao_lotacao:
        base = base.loc[~base['Lotacao'].isin(selecao_lotacao)]
    if selecao_vinculos:
        base = base.loc[~base['Vinculo_Servidor'].isin(selecao_vinculos)]

    base = base.loc[base['MG_Emprestimo_Disponivel'] < margem_emprestimo_limite]

    colunas_adicionais = [
        'FONE1', 'FONE2', 'FONE3', 'FONE4',
        'valor_liberado_emprestimo',
        'comissao_emprestimo',
        'valor_parcela_emprestimo',
        'banco_emprestimo',
        'prazo_emprestimo',
        'Campanha'
    ]

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
    base['Campanha'] = convenio + "_" + data_hoje + "_" + "benef&cartao" + "_" + "outbound"

    st.write(base.shape)
    return base
    
            
        
