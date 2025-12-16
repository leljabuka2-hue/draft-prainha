import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Draft Prainha 2025", layout="wide")

# Arquivos de controle
ARQUIVO_SAVE = "dados_draft_2025.json"
POSICOES = ['Goleiro', 'Lateral', 'Zagueiro', 'Volante', 'Meia', 'Atacante']

# --- FUNÇÕES ---

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
        st.title("⚽ Configuração do Draft Prainha")
        col1, col2, col3 = st.columns([1,1,2])
        with col3:
            arquivo_subido = st.file_uploader("Upload do arquivo JSON", type=['json'])
            if arquivo_subido:
                dados_json = json.load(arquivo_subido)
                st.session_state.jogadores = pd.DataFrame(dados_json["jogadores"])
                st.session_state.lista_times = dados_json["times"]
                st.session_state.historico = []
                st.session_state.setup_concluido = True
                salvar_estado(); st.rerun()
        st.stop()

# --- INTERFACE ---

df = st.session_state.jogadores

with st.sidebar:
    st.header("⚙️ Gestão")
    
    # ADICIONAR JOGADOR MANUALMENTE
    with st.expander("➕ Adicionar Novo Jogador"):
        with st.form("form_novo_jogador", clear_on_submit=True):
            novo_nome = st.text_input("Nome do Jogador:")
            nova_pos = st.selectbox("Posição:", POSICOES)
            nova_nota = st.slider("Nota Inicial:", 0, 10, 5)
            if st.form_submit_button("Cadastrar Jogador"):
                if novo_nome:
                    novo_id = int(st.session_state.jogadores['ID'].max() + 1) if not st.session_state.jogadores.empty else 1
                    novo_registro = {
                        "ID": novo_id, "Nome": novo_nome, "Posicao": nova_pos, 
                        "Nota": nova_nota, "Status": "Disponível", "Time": None
                    }
                    st.session_state.jogadores = pd.concat([st.session_state.jogadores, pd.DataFrame([novo_registro])], ignore_index=True)
                    salvar_estado()
                    st.success(f"{novo_nome} adicionado!")
                    st.rerun()

    # EDITAR NOMES DOS TIMES
    with st.expander("🏆 Editar Nomes dos Times"):
        for i, nome_antigo in enumerate(st.session_state.lista_times):
            novo_nome = st.text_input(f"Time {i+1}:", value=nome_antigo, key=f"time_{i}")
            if novo_nome != nome_antigo:
                st.session_state.lista_times[i] = novo_nome
                st.session_state.jogadores.loc[st.session_state.jogadores['Time'] == nome_antigo, 'Time'] = novo_nome
                salvar_estado(); st.rerun()

    st.divider()
    if not df[df['Time'].notna()].empty:
        st.download_button("📥 Baixar Excel", data=exportar_para_excel(df), file_name="draft_prainha.xlsx", use_container_width=True)
    
    if st.button("🗑️ Resetar Draft", type="primary", use_container_width=True):
        if os.path.exists(ARQUIVO_SAVE): os.remove(ARQUIVO_SAVE)
        st.session_state.clear(); st.rerun()

# --- ABAS ---
st.title("⚽ Draft Prainha 2025")
tab1, tab2, tab3 = st.tabs(["📋 Mercado", "📢 Draft", "📊 Elencos"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Goleiros", len(df[df['Posicao']=='Goleiro']))
    c3.metric("Disponíveis", len(df[df['Status']=='Disponível']))
    
    busca = st.text_input("🔍 Pesquisar jogador:")
    df_disp = df[df['Status']=='Disponível'].copy()
    if busca:
        df_disp = df_disp[df_disp['Nome'].str.contains(busca, case=False)]

    edited_df = st.data_editor(
        df_disp[['ID', 'Nome', 'Posicao', 'Nota']],
        hide_index=True, use_container_width=True,
        column_config={
            "ID": None,
            "Posicao": st.column_config.SelectboxColumn("Posição", options=POSICOES, required=True),
            "Nota": st.column_config.NumberColumn("Nota", min_value=0, max_value=10, step=1),
        },
        disabled=["ID"], key="mercado_editor"
    )

    if st.button("💾 Salvar Alterações da Tabela"):
        for index, row in edited_df.iterrows():
            idx_orig = df[df['ID'] == row['ID']].index[0]
            st.session_state.jogadores.at[idx_orig, 'Nome'] = row['Nome']
            st.session_state.jogadores.at[idx_orig, 'Posicao'] = row['Posicao']
            st.session_state.jogadores.at[idx_orig, 'Nota'] = row['Nota']
        salvar_estado(); st.success("Salvo!"); st.rerun()

with tab2:
    col_j, col_t = st.columns(2)
    disp = df[df['Status'] == 'Disponível']
    with col_j:
        id_sel = st.selectbox("Jogador:", disp['ID'].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Nome'].values[0]} ({df[df['ID']==x]['Posicao'].values[0]})", index=None)
    with col_t:
        time_sel = st.selectbox("Time:", st.session_state.lista_times, index=None)
    
    c_conf, c_undo = st.columns([3, 1])
    with c_conf:
        if st.button("✅ Confirmar Draft", type="primary", use_container_width=True):
            if id_sel and time_sel:
                idx = df[df['ID'] == id_sel].index[0]
                st.session_state.jogadores.at[idx, 'Status'] = 'Indisponível'
                st.session_state.jogadores.at[idx, 'Time'] = time_sel
                st.session_state.historico.append({"msg": f"✅ {time_sel} escolheu {df.at[idx, 'Nome']}", "id_jogador": id_sel})
                salvar_estado(); st.rerun()
    
    with c_undo:
        if st.button("↩️ Desfazer", use_container_width=True):
            if st.session_state.historico:
                ultima_acao = st.session_state.historico.pop()
                if isinstance(ultima_acao, dict):
                    id_retro = ultima_acao["id_jogador"]
                    idx_r = df[df['ID'] == id_retro].index[0]
                    st.session_state.jogadores.at[idx_r, 'Status'] = 'Disponível'
                    st.session_state.jogadores.at[idx_r, 'Time'] = None
                    salvar_estado(); st.rerun()

    st.write("---")
    st.markdown("### 📜 Últimas Escolhas")
    for h in reversed(st.session_state.historico[-5:]):
        msg = h["msg"] if isinstance(h, dict) else str(h)
        st.caption(msg)
    
    st.write("---")
    st.markdown("### 🔍 Disponíveis por Posição")
    pos_existentes = sorted(disp['Posicao'].unique())
    col_pos = st.columns(len(pos_existentes))
    for i, pos in enumerate(pos_existentes):
        jog_p = disp[disp['Posicao'] == pos].sort_values(by='Nota', ascending=False)
        with col_pos[i]:
            st.markdown(f"**{pos}** ({len(jog_p)})")
            st.dataframe(jog_p[['Nome', 'Nota']], hide_index=True, use_container_width=True, height=250)

with tab3:
    cols = st.columns(2)
    for i, t in enumerate(st.session_state.lista_times):
        elenco = df[df['Time'] == t]
        with cols[i % 2]:
            with st.expander(f"{t} ({len(elenco)})"):
                if not elenco.empty:
                    for _, row in elenco.iterrows():
                        c_n, c_r = st.columns([4, 1])
                        c_n.write(f"{row['Nome']} ({row['Posicao']})")
                        if c_r.button("❌", key=f"del_{row['ID']}"):
                            idx_del = df[df['ID'] == row['ID']].index[0]
                            st.session_state.jogadores.at[idx_del, 'Status'] = 'Disponível'
                            st.session_state.jogadores.at[idx_del, 'Time'] = None
                            st.session_state.historico = [h for h in st.session_state.historico if (h["id_jogador"] if isinstance(h, dict) else None) != row['ID']]
                            salvar_estado(); st.rerun()
                else:
                    st.write("Nenhum jogador escolhido ainda.")
