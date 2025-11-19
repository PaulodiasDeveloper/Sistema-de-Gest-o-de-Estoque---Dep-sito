import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Sistema de Estoque - Depósito",
    page_icon="📦",
    layout="wide"
)

# Configurações do arquivo Excel
ARQUIVO_EXCEL = "estoque_deposito.xlsx"
SHEET_ESTOQUE = "estoque"
SHEET_CONFIG = "configuracoes"

# Inicialização do arquivo Excel
def inicializar_excel():
    if not os.path.exists(ARQUIVO_EXCEL):
        # Criar DataFrame vazio para estoque
        estoque_df = pd.DataFrame({
            'produto_id': [],
            'nome_produto': [],
            'categoria': [],
            'quantidade': [],
            'prateleira': [],
            'corredor': [],
            'data_entrada': [],
            'fornecedor': []
        })
        
        # Criar DataFrame para configurações
        config_df = pd.DataFrame({
            'prateleiras': [
                'A:A1,A2,A3,A4',
                'B:B1,B2,B3,B4', 
                'C:C1,C2,C3,C4'
            ]
        })
        
        # Salvar no Excel com múltiplas abas
        with pd.ExcelWriter(ARQUIVO_EXCEL, engine='openpyxl') as writer:
            estoque_df.to_excel(writer, sheet_name=SHEET_ESTOQUE, index=False)
            config_df.to_excel(writer, sheet_name=SHEET_CONFIG, index=False)

# Carregar dados do Excel
def carregar_estoque():
    try:
        df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=SHEET_ESTOQUE)
        # Converter data_entrada para datetime se existir
        if 'data_entrada' in df.columns and not df.empty:
            df['data_entrada'] = pd.to_datetime(df['data_entrada'])
        return df
    except:
        return pd.DataFrame()

def carregar_prateleiras():
    try:
        config_df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=SHEET_CONFIG)
        prateleiras = {}
        for item in config_df['prateleiras']:
            corredor, prats = item.split(':')
            prateleiras[corredor] = prats.split(',')
        return prateleiras
    except:
        return {
            'A': ['A1', 'A2', 'A3', 'A4'],
            'B': ['B1', 'B2', 'B3', 'B4'],
            'C': ['C1', 'C2', 'C3', 'C4']
        }

# Salvar dados no Excel
def salvar_estoque(df):
    try:
        # Carregar arquivo existente
        with pd.ExcelWriter(ARQUIVO_EXCEL, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=SHEET_ESTOQUE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# Funções do sistema
def adicionar_produto(produto_id, nome, categoria, quantidade, prateleira, fornecedor):
    novo_produto = {
        'produto_id': produto_id,
        'nome_produto': nome,
        'categoria': categoria,
        'quantidade': quantidade,
        'prateleira': prateleira,
        'corredor': prateleira[0],
        'data_entrada': datetime.now(),
        'fornecedor': fornecedor
    }
    
    # Carregar estoque atual
    estoque_df = carregar_estoque()
    
    # Verificar se produto já existe
    produto_existente = estoque_df[estoque_df['produto_id'] == produto_id]
    
    if not produto_existente.empty:
        # Atualizar quantidade se produto já existe
        idx = produto_existente.index[0]
        estoque_df.loc[idx, 'quantidade'] += quantidade
        estoque_df.loc[idx, 'data_entrada'] = datetime.now()
    else:
        # Adicionar novo produto
        estoque_df = pd.concat([estoque_df, pd.DataFrame([novo_produto])], ignore_index=True)
    
    # Salvar no Excel
    if salvar_estoque(estoque_df):
        st.session_state.estoque = estoque_df
        return True
    return False

def remover_produto(produto_id, quantidade):
    estoque_df = carregar_estoque()
    
    if produto_id in estoque_df['produto_id'].values:
        idx = estoque_df[estoque_df['produto_id'] == produto_id].index[0]
        quantidade_atual = estoque_df.loc[idx, 'quantidade']
        
        if quantidade_atual >= quantidade:
            estoque_df.loc[idx, 'quantidade'] -= quantidade
            
            # Remove o produto se a quantidade chegar a zero
            if estoque_df.loc[idx, 'quantidade'] == 0:
                estoque_df = estoque_df.drop(idx)
            
            # Salvar no Excel
            if salvar_estoque(estoque_df):
                st.session_state.estoque = estoque_df
                return True
    return False

def atualizar_produto(produto_id, campo, novo_valor):
    estoque_df = carregar_estoque()
    
    if produto_id in estoque_df['produto_id'].values:
        idx = estoque_df[estoque_df['produto_id'] == produto_id].index[0]
        estoque_df.loc[idx, campo] = novo_valor
        
        if salvar_estoque(estoque_df):
            st.session_state.estoque = estoque_df
            return True
    return False

# Função para formatar a data para exibição
def formatar_data_para_exibicao(df):
    df_exibicao = df.copy()
    if 'data_entrada' in df_exibicao.columns and not df_exibicao.empty:
        df_exibicao['data_entrada'] = df_exibicao['data_entrada'].dt.strftime("%Y-%m-%d %H:%M")
    return df_exibicao

# Inicializar sistema
inicializar_excel()

# Carregar dados na session state
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_estoque()

if 'prateleiras' not in st.session_state:
    st.session_state.prateleiras = carregar_prateleiras()

# Interface do aplicativo
st.title("📦 Sistema de Gestão de Estoque - Depósito (Excel)")

# Sidebar para navegação
menu = st.sidebar.selectbox(
    "Menu",
    ["🏠 Dashboard", "➕ Adicionar Produto", "📋 Lista de Produtos", 
     "🗑️ Remover Produto", "✏️ Editar Produto", "🗺️ Mapa do Depósito", "📊 Relatórios"]
)

# Info do arquivo
st.sidebar.markdown("---")
st.sidebar.info(f"📊 **Arquivo:** {ARQUIVO_EXCEL}")
st.sidebar.info(f"📦 **Produtos:** {len(st.session_state.estoque)}")

# Botão para recarregar dados
if st.sidebar.button("🔄 Recarregar Dados"):
    st.session_state.estoque = carregar_estoque()
    st.rerun()

# Botão para backup
if st.sidebar.button("💾 Backup dos Dados"):
    if not st.session_state.estoque.empty:
        csv = st.session_state.estoque.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 Baixar Backup CSV",
            data=csv,
            file_name=f"backup_estoque_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

if menu == "🏠 Dashboard":
    st.header("Dashboard do Estoque")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_produtos = len(st.session_state.estoque)
        st.metric("Total de Produtos", total_produtos)
    
    with col2:
        total_itens = st.session_state.estoque['quantidade'].sum() if not st.session_state.estoque.empty else 0
        st.metric("Total de Itens", int(total_itens))
    
    with col3:
        categorias = st.session_state.estoque['categoria'].nunique() if not st.session_state.estoque.empty else 0
        st.metric("Categorias", categorias)
    
    with col4:
        prateleiras_ocupadas = st.session_state.estoque['prateleira'].nunique() if not st.session_state.estoque.empty else 0
        st.metric("Prateleiras Ocupadas", prateleiras_ocupadas)
    
    # Gráfico de produtos por categoria
    if not st.session_state.estoque.empty:
        st.subheader("Produtos por Categoria")
        produtos_por_categoria = st.session_state.estoque.groupby('categoria')['quantidade'].sum()
        st.bar_chart(produtos_por_categoria)

elif menu == "➕ Adicionar Produto":
    st.header("Adicionar Novo Produto")
    
    with st.form("adicionar_produto"):
        col1, col2 = st.columns(2)
        
        with col1:
            produto_id = st.text_input("ID do Produto*")
            nome_produto = st.text_input("Nome do Produto*")
            categoria = st.selectbox("Categoria*", 
                ["Eletrônicos", "Roupas", "Alimentação", "Livros", "Casa", "Outros"])
            quantidade = st.number_input("Quantidade*", min_value=1, value=1)
        
        with col2:
            corredor = st.selectbox("Corredor*", list(st.session_state.prateleiras.keys()))
            prateleira = st.selectbox("Prateleira*", st.session_state.prateleiras[corredor])
            fornecedor = st.text_input("Fornecedor")
        
        submitted = st.form_submit_button("Adicionar Produto")
        
        if submitted:
            if produto_id and nome_produto:
                if adicionar_produto(produto_id, nome_produto, categoria, 
                                   quantidade, prateleira, fornecedor):
                    st.success(f"✅ Produto {nome_produto} adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao adicionar produto!")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios (*)!")

elif menu == "📋 Lista de Produtos":
    st.header("Lista de Produtos em Estoque")
    
    if not st.session_state.estoque.empty:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_categoria = st.selectbox(
                "Filtrar por Categoria",
                ["Todas"] + list(st.session_state.estoque['categoria'].unique())
            )
        
        with col2:
            filtro_corredor = st.selectbox(
                "Filtrar por Corredor",
                ["Todos"] + list(st.session_state.estoque['corredor'].unique())
            )
        
        with col3:
            filtro_prateleira = st.selectbox(
                "Filtrar por Prateleira",
                ["Todas"] + list(st.session_state.estoque['prateleira'].unique())
            )
        
        # Aplicar filtros
        dados_filtrados = st.session_state.estoque.copy()
        
        if filtro_categoria != "Todas":
            dados_filtrados = dados_filtrados[dados_filtrados['categoria'] == filtro_categoria]
        
        if filtro_corredor != "Todos":
            dados_filtrados = dados_filtrados[dados_filtrados['corredor'] == filtro_corredor]
        
        if filtro_prateleira != "Todas":
            dados_filtrados = dados_filtrados[dados_filtrados['prateleira'] == filtro_prateleira]
        
        # Formatar datas para exibição
        dados_filtrados_exibicao = formatar_data_para_exibicao(dados_filtrados)
        
        st.dataframe(dados_filtrados_exibicao, use_container_width=True)
        
        # Estatísticas dos dados filtrados
        st.info(f"📊 Mostrando {len(dados_filtrados)} produtos com total de {dados_filtrados['quantidade'].sum()} itens")
        
    else:
        st.info("ℹ️ Nenhum produto cadastrado no estoque.")

elif menu == "🗑️ Remover Produto":
    st.header("Remover Produto do Estoque")
    
    if not st.session_state.estoque.empty:
        produto_selecionado = st.selectbox(
            "Selecione o produto",
            st.session_state.estoque['nome_produto'].unique()
        )
        
        if produto_selecionado:
            produto_info = st.session_state.estoque[
                st.session_state.estoque['nome_produto'] == produto_selecionado
            ].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {produto_info['produto_id']}")
                st.write(f"**Categoria:** {produto_info['categoria']}")
                st.write(f"**Fornecedor:** {produto_info['fornecedor']}")
            
            with col2:
                st.write(f"**Quantidade atual:** {produto_info['quantidade']}")
                st.write(f"**Localização:** Corredor {produto_info['corredor']}, Prateleira {produto_info['prateleira']}")
                st.write(f"**Data de entrada:** {produto_info['data_entrada'].strftime('%d/%m/%Y %H:%M')}")
            
            quantidade_remover = st.number_input(
                "Quantidade a remover",
                min_value=1,
                max_value=int(produto_info['quantidade']),
                value=1
            )
            
            if st.button("Remover Produto", type="primary"):
                if remover_produto(produto_info['produto_id'], quantidade_remover):
                    st.success(f"✅ {quantidade_remover} unidade(s) removida(s) com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao remover produto.")
    else:
        st.info("ℹ️ Nenhum produto cadastrado no estoque.")

elif menu == "✏️ Editar Produto":
    st.header("Editar Produto")
    
    if not st.session_state.estoque.empty:
        produto_selecionado = st.selectbox(
            "Selecione o produto para editar",
            st.session_state.estoque['nome_produto'].unique()
        )
        
        if produto_selecionado:
            produto_info = st.session_state.estoque[
                st.session_state.estoque['nome_produto'] == produto_selecionado
            ].iloc[0]
            
            with st.form("editar_produto"):
                col1, col2 = st.columns(2)
                
                with col1:
                    novo_nome = st.text_input("Nome do Produto", value=produto_info['nome_produto'])
                    nova_categoria = st.selectbox("Categoria", 
                        ["Eletrônicos", "Roupas", "Alimentação", "Livros", "Casa", "Outros"],
                        index=["Eletrônicos", "Roupas", "Alimentação", "Livros", "Casa", "Outros"].index(produto_info['categoria']))
                    nova_quantidade = st.number_input("Quantidade", min_value=0, value=int(produto_info['quantidade']))
                
                with col2:
                    novo_corredor = st.selectbox("Corredor", list(st.session_state.prateleiras.keys()),
                                               index=list(st.session_state.prateleiras.keys()).index(produto_info['corredor']))
                    nova_prateleira = st.selectbox("Prateleira", st.session_state.prateleiras[novo_corredor],
                                                 index=st.session_state.prateleiras[novo_corredor].index(produto_info['prateleira']))
                    novo_fornecedor = st.text_input("Fornecedor", value=produto_info['fornecedor'])
                
                submitted = st.form_submit_button("Salvar Alterações")
                
                if submitted:
                    # Atualizar cada campo individualmente
                    campos_atualizados = False
                    
                    if novo_nome != produto_info['nome_produto']:
                        atualizar_produto(produto_info['produto_id'], 'nome_produto', novo_nome)
                        campos_atualizados = True
                    
                    if nova_categoria != produto_info['categoria']:
                        atualizar_produto(produto_info['produto_id'], 'categoria', nova_categoria)
                        campos_atualizados = True
                    
                    if nova_quantidade != produto_info['quantidade']:
                        atualizar_produto(produto_info['produto_id'], 'quantidade', nova_quantidade)
                        campos_atualizados = True
                    
                    if nova_prateleira != produto_info['prateleira']:
                        atualizar_produto(produto_info['produto_id'], 'prateleira', nova_prateleira)
                        atualizar_produto(produto_info['produto_id'], 'corredor', novo_corredor)
                        campos_atualizados = True
                    
                    if novo_fornecedor != produto_info['fornecedor']:
                        atualizar_produto(produto_info['produto_id'], 'fornecedor', novo_fornecedor)
                        campos_atualizados = True
                    
                    if campos_atualizados:
                        st.success("✅ Produto atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Nenhuma alteração foi feita.")
    else:
        st.info("ℹ️ Nenhum produto cadastrado no estoque.")

elif menu == "🗺️ Mapa do Depósito":
    st.header("Mapa do Depósito")
    
    col1, col2, col3 = st.columns(3)
    
    for corredor, prateleiras in st.session_state.prateleiras.items():
        with col1 if corredor == 'A' else col2 if corredor == 'B' else col3:
            st.subheader(f"Corredor {corredor}")
            
            for prateleira in prateleiras:
                produtos_na_prateleira = st.session_state.estoque[
                    st.session_state.estoque['prateleira'] == prateleira
                ]
                
                if not produtos_na_prateleira.empty:
                    total_itens = produtos_na_prateleira['quantidade'].sum()
                    st.warning(f"**Prateleira {prateleira}**\n\n"
                              f"📦 Produtos: {len(produtos_na_prateleira)}\n"
                              f"🔢 Total itens: {total_itens}")
                else:
                    st.success(f"**Prateleira {prateleira}**\n\n✅ Disponível")

elif menu == "📊 Relatórios":
    st.header("Relatórios de Estoque")
    
    if not st.session_state.estoque.empty:
        tab1, tab2, tab3 = st.tabs(["Estoque Baixo", "Produtos por Localização", "Movimentação"])
        
        with tab1:
            st.subheader("Produtos com Estoque Baixo")
            estoque_baixo = st.session_state.estoque[
                st.session_state.estoque['quantidade'] < 10
            ]
            
            if not estoque_baixo.empty:
                estoque_baixo_exibicao = formatar_data_para_exibicao(estoque_baixo)
                st.dataframe(estoque_baixo_exibicao[['nome_produto', 'quantidade', 'prateleira']])
                
                # Alerta para reabastecimento
                st.error(f"⚠️ **Alerta:** {len(estoque_baixo)} produtos com estoque baixo!")
            else:
                st.success("✅ Nenhum produto com estoque baixo!")
        
        with tab2:
            st.subheader("Produtos por Localização")
            produtos_por_local = st.session_state.estoque.groupby(
                ['corredor', 'prateleira']
            )['quantidade'].sum().reset_index()
            st.dataframe(produtos_por_local)
            
            # Gráfico de ocupação
            st.subheader("Ocupação por Corredor")
            ocupacao_corredor = st.session_state.estoque.groupby('corredor')['quantidade'].sum()
            st.bar_chart(ocupacao_corredor)
        
        with tab3:
            st.subheader("Últimas Entradas")
            ultimas_entradas = st.session_state.estoque.sort_values('data_entrada', ascending=False).head(10)
            ultimas_entradas_exibicao = formatar_data_para_exibicao(ultimas_entradas)
            st.dataframe(ultimas_entradas_exibicao)
    
    else:
        st.info("ℹ️ Nenhum dado disponível para relatórios.")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info(
    "Sistema de Gestão de Estoque v2.0\n\n"
    "💾 Armazenamento em Excel\n"
    "Desenvolvido com Streamlit"
)