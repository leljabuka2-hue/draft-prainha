import streamlit as st
import pandas as pd
from io import BytesIO
import json

# Configuração da página
st.set_page_config(page_title="Draft Prainha 2025", layout="wide")

# URL da sua planilha formatada para exportação CSV
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1MHJb0-6JPDKkrfGREXJoWn7voglI4rvzdM-J9OKwma8/export?format=csv"

POSICOES_PADRAO = ['Goleiro', 'Lateral', 'Zagueiro', 'Volante', 'Meia', 'Atacante']

# --- FUNÇÃO PARA CARREGAR DADOS ---
def carregar_dados():
    try:
        df_lido = pd.read_csv(URL_PLANILHA)
        # Limpeza básica de nomes de colunas
        df_lido.columns = [c.strip() for c in df_lido.columns]
        return df_lido
    except Exception as e:
        return None

# --- INICIALIZAÇÃO ---
if 'jogadores' not in st.session_state:
    dados = carregar_dados()
    if dados is not None and not dados.empty:
        st.session_state.jogadores = dados
        if 'Status' not in st.session_state.jogadores.columns:
            st.session_state.jogadores['Status'] = 'Disponível'
        if 'Time' not in st.session_state.jogadores.columns:
            st.session_state.jogadores['Time'] = None
        if 'Nota' not in st.session_state.jogadores.columns:
            st.session_state.jogadores['Nota'] = 0
    else:
        st.error("⚠️ Erro ao ler a planilha ou planilha vazia. Verifique as colunas (Nome, Posicao, Nota) e o compartilhamento.")
        st.stop()

if 'lista_times' not in st.session_state:
    st.session_state.lista_times = [f"Time {i}" for i in range(1, 9)]

if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- INTERFACE ---
df = st.session_state.jogadores

with st.sidebar:
    st.header("⚙️ Gestão")
    
    with st.expander("🏆 Editar Nomes dos Times"):
        for i, nome_antigo in enumerate(st.session_state.lista_times):
            novo_nome = st.text_input(f"Time {i+1}:", value=nome_antigo, key=f"t_{i}")
            if novo_nome != nome_antigo:
                st.session_state.lista_times[i] = novo_nome
                st.session_state.jogadores.loc[df['Time'] == nome_antigo, 'Time'] = novo_nome
                st.rerun()

    if st.button("🗑️ Resetar Draft Local", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("⚽ Draft Prainha 2025")
t1, t2, t3 = st.tabs(["📋 Mercado", "📢 Draft", "📊 Elencos"])

with t1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    # Proteção caso a coluna Posicao esteja com nomes diferentes
    goleiros = len(df[df['Posicao'].str.contains('Goleiro', na=False, case=False)]) if 'Posicao' in df.columns else 0
    c2.metric("Goleiros", goleiros)
    c3.metric("Disponíveis", len(df[df['Status']=='Disponível']))
    
    busca = st.text_input("🔍 Pesquisar jogador:")
    view = df[df['Status']=='Disponível']
    if busca: view = view[view['Nome'].str.contains(busca, case=False, na=False)]
    st.dataframe(view[['Nome', 'Posicao', 'Nota']], use_container_width=True, hide_index=True)

with t2:
    col_j, col_t = st.columns(2)
    disp = df[df['Status'] == 'Disponível']
    
    with col_j:
        id_sel = st.selectbox("Jogador:", disp.index.tolist(), 
                             format_func=lambda x: f"{df.at[x, 'Nome']} ({df.at[x, 'Posicao']})", 
                             index=None, placeholder="Selecione...")
    with col_t:
        time_sel = st.selectbox("Time:", st.session_state.lista_times, index=None, placeholder="Selecione...")
    
    if st.button("✅ Confirmar Draft", type="primary", use_container_width=True):
        if id_sel is not None and time_sel:
            st.session_state.jogadores.at[id_sel, 'Status'] = 'Indisponível'
            st.session_state.jogadores.at[id_sel, 'Time'] = time_sel
            st.session_state.historico.append(f"✅ {time_sel} escolheu {df.at[id_sel, 'Nome']}")
            st.rerun()
    
    st.write("---")
    st.markdown("### 🔍 Disponíveis por Posição")
    
    # CORREÇÃO DO ERRO: Verifica se existem posições antes de criar colunas
    pos_disponiveis = disp['Posicao'].dropna().unique().tolist()
    if pos_disponiveis:
        cols_pos = st.columns(len(pos_disponiveis))
        for i, p in enumerate(sorted(pos_disponiveis)):
            with cols_pos[i]:
                st.write(f"**{p}**")
                st.dataframe(disp[disp['Posicao']==p][['Nome', 'Nota']], hide_index=True)
    else:
        st.write("Nenhum jogador disponível nas posições.")

with t3:
    cols_t = st.columns(2)
    for i, t in enumerate(st.session_state.lista_times):
        elenco = df[df['Time'] == t]
        with cols_t[i % 2]:
            with st.expander(f"{t} ({len(elenco)})"):
                for idx, row in elenco.iterrows():
                    c_n, c_r = st.columns([4, 1])
                    c_n.write(f"{row['Nome']} ({row['Posicao']})")
                    if c_r.button("❌", key=f"del_{idx}"):
                        st.session_state.jogadores.at[idx, 'Status'] = 'Disponível'
                        st.session_state.jogadores.at[idx, 'Time'] = None
                        st.rerun()
