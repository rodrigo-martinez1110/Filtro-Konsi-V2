import streamlit as st
import pandas as pd
from juntar_bases import juntar_bases

from filtradores.novo import filtro_novo
from filtradores.beneficio import filtro_beneficio
from filtradores.cartao import filtro_cartao
from filtradores.beneficio_cartao import filtro_beneficio_e_cartao



# Listas e configurações iniciais
lista_codigos_bancos = ['2', '33', '74', '243', '422', '465', '623', '643', '707', '955', '6613']
colunas_condicao = ['Vinculo_Servidor', 'Lotacao', 'Secretaria', 'Aplicar a toda a base']  # Adicionando a opção de aplicar a toda a base

st.title("Filtro de Campanhas - Konsi")

# Upload de arquivos
arquivos = st.file_uploader('Arraste os arquivos CSV de higienização', accept_multiple_files=True, type=['csv'])

if arquivos:
    # Junta as bases carregadas
    base = juntar_bases(arquivos)
    if not base.empty:
        st.write("Prévia dos dados carregados:")
        st.write(base.head(50))
        

        # Seleção do tipo de campanha
        st.sidebar.title("Configurações Iniciais")
        campanha = st.sidebar.selectbox("Tipo da Campanha:", ['Novo', 'Benefício', 'Cartão', 'Benefício & Cartão'])
        if campanha == 'Benefício & Cartão':
            quantidade_de_bancos = 2
        else:
            quantidade_de_bancos = 1
        # Seleção da quantidade de bancos
        quant_bancos = st.sidebar.number_input("Quantidade de Bancos:", min_value=1, max_value=10, step=1, value=quantidade_de_bancos)

        comissao_minima = st.sidebar.number_input(f"Comissão mínima da campanha {campanha}:")
        margem_emprestimo_limite = st.sidebar.number_input(f"Margem de empréstimo limite da campanha {campanha}:")

        st.write("------")

        botao_lotacao = st.sidebar.checkbox("Retirar lotações")

        convenio = base.loc[1, 'Convenio']
        lotacao = list(base['Lotacao'].unique())
        vinculo = list(base['Vinculo_Servidor'].unique())

        selecao_lotacao = None
        selecao_vinculos = None

        if botao_lotacao:
            selecao_lotacao = st.sidebar.multiselect(
                f"Selecione as lotações que deseja excluir do convênio {convenio}",
                options=lotacao
            )

        botao_vinculo = st.sidebar.checkbox("Retirar vínculos")
        if botao_vinculo:
            selecao_vinculos = st.sidebar.multiselect(
                f"Selecione os vínculos que deseja excluir do convênio {convenio}",
                options=vinculo
            )

        # Só mostrar a configuração de bancos após selecionar o número
        if quant_bancos > 0:
            configuracoes = []
            st.header("Configurações dos Bancos")

            # Loop dinâmico para configurar cada banco
            for i in range(quant_bancos):
                with st.expander(f"Configurações do Banco {i + 1}"):
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
                            coeficiente2 = st.number_input(f"Coeficiente Banco {i + 1}:",
                                                           min_value=0.0,
                                                           max_value=100.0,
                                                           step=0.01,
                                                           key=f"coeficiente2_{i}")
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
                                                           key=f"coeficiente2_{i}",
                                                           value=30.0)

                    else:
                        banco = st.selectbox(f"Selecione o Banco {i + 1}:", 
                                            options=lista_codigos_bancos, 
                                            key=f"banco_{i}")
                        coeficiente = st.number_input(f"Coeficiente Banco {i + 1}:", min_value=0.0, max_value=100.0, step=0.01, key=f"coeficiente_{i}")
                        coeficiente2 = None
                        if convenio == 'goval' and (campanha == 'Benefício' or campanha == 'Benefício & Cartão'):
                            coeficiente2 = st.number_input(f"Coeficiente 2 Banco {i + 1}:", min_value=0.0, max_value=100.0, step=0.01, key=f"coeficiente2_{i}")
                        comissao = st.number_input(f"Comissão Banco {i + 1} (%):", min_value=0.0, max_value=100.0, step=0.01, key=f"comissao_{i}")
                        parcelas = st.number_input(f"Parcelas Banco {i + 1}:", min_value=1, max_value=200, step=1, key=f"parcelas_{i}")

                        if campanha == 'Novo':
                            margem_seguranca = st.checkbox("Margem Segurança", value=False, key=f"margem_seguranca{i}")

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
                            "Valor Condicional": valor_condicao,

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
                    base_filtrada = filtro_novo(base, convenio, quant_bancos,
                                                    comissao_minima, margem_emprestimo_limite, selecao_lotacao,
                                                    selecao_vinculos, configuracoes)
                elif campanha == 'Benefício':
                    base_filtrada = filtro_beneficio(base, convenio, quant_bancos,
                                                        comissao_minima, margem_emprestimo_limite, selecao_lotacao,
                                                        selecao_vinculos, configuracoes)
                elif campanha == 'Cartão':
                    base_filtrada = filtro_cartao(base, convenio, quant_bancos,
                                                  comissao_minima, margem_emprestimo_limite,
                                                  selecao_lotacao, selecao_vinculos,
                                                  configuracoes)
                
                elif campanha == 'Benefício & Cartão':
                    base_filtrada = filtro_beneficio_e_cartao(base, convenio, quant_bancos,
                                                              comissao_minima, margem_emprestimo_limite,
                                                              selecao_lotacao, selecao_vinculos,
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
