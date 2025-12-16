import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA (ESTILO IPHONE) ---
st.set_page_config(page_title="Draft Prainha 2025", layout="wide", page_icon="⚽")

# --- CSS CUSTOMIZADO ---
def local_css():
    st.markdown("""
    <style>
        .stApp { background-color: #F2F2F7; }
        .card-container {
            background-color: white; border-radius: 20px; padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;
        }
        h1, h2, h3 { font-family: -apple-system, sans-serif; color: #1C1C1E; }
        .stButton > button {
            border-radius: 12px; background-color: #007AFF; color: white; border: none; padding: 10px 20px;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- LÓGICA DO SISTEMA ---
ARQUIVO_SAVE = "dados_draft_2025.json"
POSICOES = ['Goleiro', 'Lateral', 'Zagueiro', 'Volante', 'Meia', 'Atacante']

def salvar_estado():
    dados = {
        "jogadores": st.session_state.jogadores.to_dict('records'),
        "lista_times": st.session_state.lista_times,
        "historico": st.session_state.historico,
        "setup_concluido": True
    }
    with open(ARQUIVO_SAVE, "w", encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def carregar_save_existente():
    if os.path.exists(ARQUIVO_SAVE):
        with open(ARQUIVO_SAVE, "r", encoding='utf-8') as f:
            d = json.load(f)
            st.session_state.jogadores = pd.DataFrame(d["jogadores"])
            st.session_state.lista_times = d["lista_times"]
            st.session_state.historico = d["historico"]
            st.session_state.setup_concluido = True
            return True
    return False

def exportar_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for time in st.session_state.lista_times:
            elenco = df[df['Time'] == time][['Nome', 'Posicao', 'Nota']]
            nome_aba = "".join([c for c in time if c.isalnum() or c==' '])[:30]
            elenco.to_excel(writer, index=False, sheet_name=nome_aba)
    return output.getvalue()

# --- SETUP INICIAL ---
if 'setup_concluido' not in st.session_state:
    if not carregar_save_existente():
        st.markdown("<h1 style='text-align: center;'>⚽ Setup do Draft</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,2])
        with col3:
            st.info("📂 Carregue o arquivo JSON para começar")
            arquivo_subido = st.file_uploader("Upload JSON", type=['json'])
            if arquivo_subido:
                dados_json = json.load(arquivo_subido)
                st.session_state.jogadores = pd.DataFrame(dados_json["jogadores"])
                st.session_state.lista_times = dados_json["times"]
                st.session_state.historico = []
                if 'Status' not in st.session_state.jogadores.columns: st.session_state.jogadores['Status'] = 'Disponível'
                if 'Time' not in st.session_state.jogadores.columns: st.session_state.jogadores['Time'] = None
                st.session_state.setup_concluido = True
                salvar_estado(); st.rerun()
        st.stop()

# --- INTERFACE PRINCIPAL ---
df = st.session_state.jogadores

with st.sidebar:
    st.markdown("### ⚙️ Painel de Controle")
    with st.expander("➕ Novo Jogador"):
        with st.form("form_novo", clear_on_submit=True):
            novo_nome = st.text_input("Nome")
            nova_pos = st.selectbox("Posição", POSICOES)
            nova_nota = st.slider("Nota", 0, 10, 5)
            if st.form_submit_button("Salvar"):
                novo_id = int(st.session_state.jogadores['ID'].max() + 1) if not st.session_state.jogadores.empty else 1
                novo_registro = {"ID": novo_id, "Nome": novo_nome, "Posicao": nova_pos, "Nota": nova_nota, "Status": "Disponível", "Time": None}
                st.session_state.jogadores = pd.concat([st.session_state.jogadores, pd.DataFrame([novo_registro])], ignore_index=True)
                salvar_estado(); st.rerun()

    with st.expander("🏆 Editar Times"):
        for i, nome_antigo in enumerate(st.session_state.lista_times):
            novo_nome = st.text_input(f"Time {i+1}", value=nome_antigo, key=f"time_{i}")
            if novo_nome != nome_antigo:
                st.session_state.lista_times[i] = novo_nome
                st.session_state.jogadores.loc[st.session_state.jogadores['Time'] == nome_antigo, 'Time'] = novo_nome
                salvar_estado(); st.rerun()

    st.write("---")
    if not df[df['Time'].notna()].empty:
        st.download_button("📥 Baixar Excel", data=exportar_para_excel(df), file_name="draft_prainha.xlsx", use_container_width=True)
    if st.button("🗑️ Resetar Tudo"):
        if os.path.exists(ARQUIVO_SAVE): os.remove(ARQUIVO_SAVE)
        st.session_state.clear(); st.rerun()

st.markdown("<h1 style='font-size: 3rem;'>⚽ Draft Prainha 2025</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Mercado", "📢 Sala de Draft", "📊 Elencos"])

# --- ABA 1: MERCADO (EDITÁVEL) ---
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(df))
    col2.metric("Goleiros", len(df[df['Posicao'].str.contains('Goleiro', na=False, case=False)]))
    col3.metric("Disponíveis", len(df[df['Status']=='Disponível']))
    
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    st.markdown("### 🔍 Mercado da Bola")
    
    busca = st.text_input("Buscar jogador...", placeholder="Digite o nome")
    df_disp = df[df['Status']=='Disponível'].copy()
    if busca:
        df_disp = df_disp[df_disp['Nome'].str.contains(busca, case=False, na=False)]

    # AQUI MANTEMOS NUMBERCOLUMN PARA VOCÊ PODER EDITAR
    edited_df = st.data_editor(
        df_disp[['ID', 'Nome', 'Posicao', 'Nota']],
        hide_index=True, use_container_width=True, height=400,
        column_config={
            "ID": None,
            "Posicao": st.column_config.SelectboxColumn("Posição", options=POSICOES, required=True),
            "Nota": st.column_config.NumberColumn("Nota (0-10)", min_value=0, max_value=10, step=1, help="Edite a nota aqui"),
        },
        disabled=["ID"], key="mercado_editor"
    )

    if st.button("💾 Salvar Alterações", type="primary"):
        for index, row in edited_df.iterrows():
            idx_orig = df[df['ID'] == row['ID']].index[0]
            st.session_state.jogadores.at[idx_orig, 'Nome'] = row['Nome']
            st.session_state.jogadores.at[idx_orig, 'Posicao'] = row['Posicao']
            st.session_state.jogadores.at[idx_orig, 'Nota'] = row['Nota']
        salvar_estado(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- ABA 2: DRAFT ---
with tab2:
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    st.markdown("### 🎙️ Fazer Escolha")
    
    c1, c2 = st.columns(2)
    disp = df[df['Status'] == 'Disponível']
    with c1:
        id_sel = st.selectbox("Selecione o Jogador", disp['ID'].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Nome'].values[0]} ({df[df['ID']==x]['Posicao'].values[0]})", index=None)
    with c2:
        time_sel = st.selectbox("Selecione o Time", st.session_state.lista_times, index=None)
    
    if st.button("✅ Confirmar Draft", type="primary", use_container_width=True):
        if id_sel and time_sel:
            idx = df[df['ID'] == id_sel].index[0]
            st.session_state.jogadores.at[idx, 'Status'] = 'Indisponível'
            st.session_state.jogadores.at[idx, 'Time'] = time_sel
            st.session_state.historico.append({"msg": f"✅ {time_sel} escolheu {df.at[idx, 'Nome']}", "id_jogador": id_sel})
            salvar_estado(); st.rerun()
    
    if st.button("↩️ Desfazer Última Escolha", use_container_width=True):
        if st.session_state.historico:
            ultima = st.session_state.historico.pop()
            if isinstance(ultima, dict):
                id_r = ultima["id_jogador"]
                idx_r = df[df['ID'] == id_r].index[0]
                st.session_state.jogadores.at[idx_r, 'Status'] = 'Disponível'
                st.session_state.jogadores.at[idx_r, 'Time'] = None
                salvar_estado(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.historico[-5:]):
        msg = h["msg"] if isinstance(h, dict) else str(h)
        st.markdown(f"<div style='background: white; padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 5px solid #34C759; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>{msg}</div>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("### 🔍 Disponíveis (Nota Visual)")
    todas_posicoes = POSICOES
    for i in range(0, len(todas_posicoes), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(todas_posicoes):
                pos = todas_posicoes[i + j]
                jog_p = disp[disp['Posicao'] == pos].sort_values(by='Nota', ascending=False)
                
                with cols[j]:
                    st.markdown(f"<div style='background: white; padding: 10px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'><h4 style='color:#007AFF; margin:0;'>{pos} <span style='color:gray; font-size:0.8em'>({len(jog_p)})</span></h4></div>", unsafe_allow_html=True)
                    if not jog_p.empty:
                        # AQUI ESTÁ A MUDANÇA VISUAL: ProgressColumn
                        st.dataframe(
                            jog_p[['Nome', 'Nota']], 
                            hide_index=True, use_container_width=True, height=200,
                            column_config={
                                "Nota": st.column_config.ProgressColumn(
                                    "Força",
                                    format="%d",
                                    min_value=0,
                                    max_value=10,
                                )
                            }
                        )
                    else:
                        st.caption("Esgotado")
                    st.write("") 

# --- ABA 3: ELENCOS ---
with tab3:
    cols_t = st.columns(2)
    for i, t in enumerate(st.session_state.lista_times):
        elenco = df[df['Time'] == t]
        with cols_t[i % 2]:
            st.markdown(f"<div style='background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;'><h3 style='margin-bottom: 10px;'>{t} <span style='font-size:0.7em; color:gray;'>({len(elenco)})</span></h3>", unsafe_allow_html=True)
            if not elenco.empty:
                # Elenco também ganha barra de progresso visual
                st.dataframe(
                    elenco[['Nome', 'Posicao', 'Nota']],
                    hide_index=True, use_container_width=True,
                    column_config={
                        "Nota": st.column_config.ProgressColumn("Força", format="%d", min_value=0, max_value=10)
                    }
                )
                # Botões de remover individuais (fora da tabela para simplificar)
                with st.expander("Gerenciar/Remover Jogadores"):
                    for _, row in elenco.iterrows():
                        c_n, c_r = st.columns([4, 1])
                        c_n.write(f"{row['Nome']}")
                        if c_r.button("❌", key=f"del_{row['ID']}"):
                            idx_del = df[df['ID'] == row['ID']].index[0]
                            st.session_state.jogadores.at[idx_del, 'Status'] = 'Disponível'
                            st.session_state.jogadores.at[idx_del, 'Time'] = None
                            st.session_state.historico = [h for h in st.session_state.historico if (h.get("id_jogador") if isinstance(h, dict) else None) != row['ID']]
                            salvar_estado(); st.rerun()
            else:
                st.write("Vazio")
            st.markdown("</div>", unsafe_allow_html=True)
