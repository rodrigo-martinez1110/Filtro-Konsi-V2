import streamlit as st
import pandas as pd
from juntar_bases import juntar_bases
from datetime import datetime, timedelta
import numpy


from filtradores.novo import filtro_novo
from filtradores.beneficio import filtro_beneficio
from filtradores.cartao import filtro_cartao
from filtradores.beneficio_cartao import filtro_beneficio_e_cartao

st.set_page_config(layout="wide",
                   initial_sidebar_state='expanded',
                   page_title='Filtrador de Campanhas V2')

# Listas e configurações iniciais
lista_codigos_bancos = ['2', '33', '74', '243', '318', '422', '465', '623', '643', '707', '955', '6613']
colunas_condicao = ['Vinculo_Servidor', 'Lotacao', 'Secretaria', 'Aplicar a toda a base']  # Adicionando a opção de aplicar a toda a base

st.title("Filtro de Campanhas - Konsi")

# Upload de arquivos
arquivos = st.sidebar.file_uploader('Arraste os arquivos CSV de higienização', accept_multiple_files=True, type=['csv'])

if arquivos:
    # Junta as bases carregadas
    base = juntar_bases(arquivos)
    if not base.empty:
        st.write("Prévia dos dados carregados:")
        st.write(base.head(50))
        
        # Seleção do tipo de campanha
        st.sidebar.write("---")
        with st.sidebar.expander("Configurações iniciais"):
            campanha = st.selectbox(
                "Tipo da Campanha:",
                ['Novo', 'Benefício', 'Cartão', 'Benefício & Cartão'],
                key="selectbox_tipo_campanha"
            )


            if campanha == 'Benefício & Cartão':
                quantidade_de_bancos = 2
            else:
                quantidade_de_bancos = 1
            # Seleção da quantidade de bancos
            quant_bancos = st.number_input("Quantidade de Bancos:", min_value=1, max_value=10, step=1, value=quantidade_de_bancos)

            comissao_minima = st.number_input(f"Comissão mínima da campanha {campanha}:")
            margem_emprestimo_limite = st.number_input(f"Margem de empréstimo limite da campanha {campanha}:")


            botao_lotacao = st.checkbox("Retirar lotações")

            convenio = base.loc[1, 'Convenio']
            lotacao = list(base['Lotacao'].unique())
            vinculo = list(base['Vinculo_Servidor'].unique())

            selecao_lotacao = None
            selecao_vinculos = None

            if botao_lotacao:
                selecao_lotacao = st.multiselect(
                    f"Selecione as lotações que deseja excluir do convênio {convenio}",
                    options=lotacao
                )

            botao_vinculo = st.checkbox("Retirar vínculos")
            if botao_vinculo:
                selecao_vinculos = st.multiselect(
                    f"Selecione os vínculos que deseja excluir do convênio {convenio}",
                    options=vinculo
                )


        with st.sidebar.expander("Equipes:"):
            equipes = st.selectbox(
                "Equipe da Campanha:",
                ['outbound', 'csapp', 'csativacao', 'cscdx', 'csport', 'outbound_virada'],
                key="selectbox_equipe_campanha"
            )
            convai = st.number_input("Porcentagem com tag para a IA", 0.0, 100.0, step=1.0, key="convai_input", value=0.0)



        # Só mostrar a configuração de bancos após selecionar o número
        if quant_bancos > 0:
            configuracoes = []
            st.header("Configurações dos Bancos")
            if not base['Data_Nascimento'].isna().any():
              idade_max = st.sidebar.number_input("Idade máxima", 0, 120, 72, step=1, key='idade_max1')
              hoje = datetime.today()
              data_limite = (hoje - pd.DateOffset(years=idade_max)).date()

            # Loop dinâmico para configurar cada banco
            for i in range(quant_bancos):
                with st.expander(f"Configurações do Banco {i + 1}"):
                    data_limite = None
                    if not base['Data_Nascimento'].isna().any():
                        st.sidebar.write("---")
                        
                        

                    if campanha == 'Benefício & Cartão':
                        opcao = st.radio("Escolha o tipo de cartão:", ['Benefício', 'Consignado'],
                                         key=f'opcao{i}')
                        banco = st.selectbox(f"Selecione o Banco {i + 1}:", 
                                            options=lista_codigos_bancos, 
                                            key=f"banco_{i}")
                        coeficiente = st.number_input(f"Coeficiente {opcao} no Banco {i+1}:",
                                                      min_value=0.0,
                                                      max_value=100.0,
                                                      step=0.01,
                                                      key=f'coeficiente_{i}'
                                                      )
                        coeficiente2 = None
                        if convenio == 'goval' and (campanha == 'Benefício' or campanha == 'Benefício & Cartão'):
                            if opcao == 'Benefício':
                                coeficiente2 = st.number_input(f"Coeficiente 2 Banco {i + 1}:",
                                                            min_value=0.0,
                                                            max_value=100.0,
                                                            step=0.01,
                                                            key=f"coeficiente2_{i + 1}")
                        comissao = st.number_input(f"Comissão {opcao} Banco {i + 1} (%):", min_value=0.0, max_value=100.0, step=0.01, key=f"comissao_{i}")
                        
                        parcelas = st.number_input(f"Parcelas {opcao} Banco {i + 1}:", min_value=1, max_value=200, step=1, key=f"parcelas_{i}")
                        
                        coeficiente_parcela_str = st.text_input(f"Coeficiente da Parcela Banco {i + 1}:", key=f"coeficiente_parcela{i}")
                        coeficiente_parcela_str = coeficiente_parcela_str.replace(",", ".")
                        try:
                            coeficiente_parcela = float(coeficiente_parcela_str)
                            if coeficiente_parcela < 0.0 or coeficiente_parcela > 100.0:
                                st.error("O coeficiente deve estar entre 0 e 100.")
                                coeficiente_parcela = None  # Ou qualquer outro valor padrão ou erro
                        except ValueError:
                            st.error("Por favor, insira um valor numérico válido.")
                            coeficiente_parcela = None  # Ou qualquer outro valor padrão ou erro

                        margem_minima_cartao = st.number_input(f"Margem Mínima {opcao} {i + 1}:",
                                                           min_value=0.0,
                                                           max_value=10000.0,
                                                           step=0.01,
                                                           key=f"mg_minima{i}",
                                                           value=30.0)

                    else:
                        if convenio == 'govam':
                            somar_margem_compra = st.checkbox("Usar margem compra (GOV AM)", key=f'checkbox_compra{i}')
                        else:
                            somar_margem_compra = False

                        banco = st.selectbox(f"Selecione o Banco {i + 1}:",
                                options=lista_codigos_bancos, 
                                key=f"banco_{i}_{campanha}")
                        coeficiente = st.number_input(f"Coeficiente Banco {i + 1}:",
                                                    min_value=0.0, max_value=100.0, step=0.01, 
                                                    key=f"coeficiente_{i}_{campanha}")  # Chave única   
                                            
                        coeficiente2 = None
                        if convenio == 'goval' and (campanha == 'Benefício' or campanha == 'Benefício & Cartão'):
                            coeficiente2 = st.number_input(f"Coeficiente 2 Banco {i + 1}:", min_value=0.0, max_value=100.0, step=0.01, key=f"coeficiente2_{i}")
                        
                        comissao = st.number_input(f"Comissão Banco {i + 1} (%):", min_value=0.0, max_value=100.0, step=0.01, key=f"comissao_{i}")
                        parcelas = st.number_input(f"Parcelas Banco {i + 1}:", min_value=1, max_value=200, step=1, key=f"parcelas_{i}")

                        if campanha == 'Novo':
                            col1, col2 = st.columns(2)
                            with col1:
                                margem_seguranca = st.checkbox("Margem Segurança", value=False, key=f"margem_seguranca_bool{i}")
                                if margem_seguranca:
                                    with col1:
                                        margem_seguranca = st.number_input("Valor percentual da Margem de Segurança", min_value=0.0, max_value=100.0, step=0.01, key=f"margem_seguranca{i}")
                                        margem_seguranca = 1 - (margem_seguranca / 100) 

                        if campanha == 'Benefício' or campanha == 'Cartão':
                            coeficiente_parcela_str = st.text_input(f"Coeficiente da Parcela Banco {i + 1}:", key=f"coeficiente_parcela{i}")
                            coeficiente_parcela_str = coeficiente_parcela_str.replace(",", ".")
                            try:
                                coeficiente_parcela = float(coeficiente_parcela_str)
                                if coeficiente_parcela < 0.0 or coeficiente_parcela > 100.0:
                                    st.error("O coeficiente deve estar entre 0 e 100.")
                                    coeficiente_parcela = None  # Ou qualquer outro valor padrão ou erro
                            except ValueError:
                                st.error("Por favor, insira um valor numérico válido.")
                                coeficiente_parcela = None  # Ou qualquer outro valor padrão ou erro
                    

                    
                    # Escolha de coluna condicional
                    coluna_condicao = st.selectbox('Selecione a coluna condicional para aplicar configurações:',
                                                   options=colunas_condicao,
                                                   key=f"coluna_{i}")

                    # Valores únicos disponíveis na coluna selecionada
                    if coluna_condicao != "Aplicar a toda a base":
                        usar_palavra_chave = st.checkbox(
                            f"Usar palavra-chave para o Banco {i + 1}",
                            value=False,
                            key=f"usar_palavra_chave_{i}"
                        )

                        if usar_palavra_chave:
                            palavra_chave = st.text_input(
                                f"Digite a palavra-chave para a coluna '{coluna_condicao}' do Banco {i + 1}:",
                                key=f"palavra_chave_{i}"
                            )
                            valor_condicao = palavra_chave
                        else:
                            valores_disponiveis = base[coluna_condicao].dropna().unique()
                            valor_condicao = st.selectbox(
                                f"Selecione o valor condicional do Banco {i + 1}:",
                                options=valores_disponiveis,
                                key=f"valor_{i}"
                            )
                    else:
                        valor_condicao = None  # Caso escolha aplicar a toda a base

                    # Adiciona a configuração do banco
                    if campanha == 'Novo':
                        configuracoes.append({
                            "Banco": banco,
                            "Coeficiente": coeficiente,
                            "Margem seguranca": margem_seguranca,
                            "Comissão": comissao,
                            "Parcelas": parcelas,
                            "Coluna Condicional": coluna_condicao,
                            "Valor Condicional": valor_condicao
                        })
                    elif campanha == 'Benefício' or campanha == 'Cartão':
                        configuracoes.append({
                            "Banco": banco,
                            "Coeficiente": coeficiente,
                            "Coeficiente2": coeficiente2,
                            "Comissão": comissao,
                            "Parcelas": parcelas,
                            "Coluna Condicional": coluna_condicao,
                            "Valor Condicional": valor_condicao,
                            "Coeficiente_Parcela": coeficiente_parcela,
                            "Usar_Margem_Compra": somar_margem_compra
                        })
                    
                    elif campanha == 'Benefício & Cartão':
                        configuracoes.append({
                            "Cartao_Escolhido": opcao,
                            "Banco": banco,
                            "Coeficiente": coeficiente,
                            "Coeficiente2": coeficiente2,
                            "Comissão": comissao,
                            "Parcelas": parcelas,
                            "Coluna Condicional": coluna_condicao,
                            "Valor Condicional": valor_condicao,
                            "Coeficiente_Parcela": coeficiente_parcela,
                            "Margem_Minima_Cartao": margem_minima_cartao
                        })
            
            st.write(campanha)
            if st.button("Aplicar configurações"): 
                if campanha == 'Novo':
                    base_filtrada = filtro_novo(base, convenio, data_limite, quant_bancos,
                                                    comissao_minima, margem_emprestimo_limite, selecao_lotacao,
                                                    selecao_vinculos, convai, equipes,
                                                    configuracoes)
                elif campanha == 'Benefício':
                    base_filtrada = filtro_beneficio(base, convenio, data_limite, quant_bancos, comissao_minima, margem_emprestimo_limite, 
                                                     selecao_lotacao, selecao_vinculos, convai, equipes,
                                                    configuracoes)
                    
                elif campanha == 'Cartão':
                    base_filtrada = filtro_cartao(base, convenio, data_limite, quant_bancos,
                                                  comissao_minima, margem_emprestimo_limite,
                                                  selecao_lotacao, selecao_vinculos, convai, equipes,
                                                  configuracoes)
                
                elif campanha == 'Benefício & Cartão':
                    base_filtrada = filtro_beneficio_e_cartao(base, convenio, data_limite, quant_bancos,
                                                              comissao_minima, margem_emprestimo_limite,
                                                              selecao_lotacao, selecao_vinculos, convai, equipes,
                                                              configuracoes)


                def convert_df(df):
                    return df.to_csv(index=False, sep = ';').encode('utf-8')

                csv = convert_df(base_filtrada)
                st.download_button(
                    label="Baixar CSV",
                    data=csv,
                    file_name=f'{convenio} - {campanha}.csv',
                    mime='text/csv'
                )
