import streamlit as st
import json
from github import Github
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GLOBAL", page_icon="🌐", layout="centered")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
css_style = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Estilo dos Títulos */
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 5px;
        text-align: left;
    }
    .main-subtitle {
        font-size: 16px;
        color: #6B7280;
        margin-bottom: 35px;
        text-align: left;
    }
    
    /* Botão Primário (Entrar / Enviar Pontos) */
    div.stButton > button:first-child {
        background-color: #2563EB !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* Botão Secundário (Sair) */
    div.stButton > button[key="btn_sair"] {
        background-color: #EF4444 !important;
        color: white !important;
    }
    div.stButton > button[key="btn_sair"]:hover {
        background-color: #DC2626 !important;
    }
</style>
"""
st.markdown(css_style, unsafe_allowed_html=True)

# --- CONFIGURAÇÕES DE ACESSO AO GITHUB ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "clientes.json"

# --- FUNÇÕES DE BANCO DE DADOS (GITHUB) ---
def carregar_dados_github():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_contents = repo.get_contents(FILE_PATH)
        dados = json.loads(file_contents.decoded_content.decode("utf-8"))
        return dados, file_contents.sha
    except Exception:
        return {"config": {"codigo_lojista": "#loja123"}, "clientes": {}}, None

def salvar_dados_github(dados, sha):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        conteudo_json = json.dumps(dados, indent=4, ensure_ascii=False)
        if sha:
            repo.update_file(FILE_PATH, "Atualizando banco de dados GLOBAL", conteudo_json, sha)
        else:
            repo.create_file(FILE_PATH, "Iniciando banco de dados GLOBAL", conteudo_json)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

# --- CONTROLE DE SESSÃO DO USUÁRIO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = None
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

dados, sha = carregar_dados_github()
CODIGO_LOJISTA = dados.get("config", {}).get("codigo_lojista", "#loja123")

# --- MÁSCARAS E VALIDAÇÕES INTELIGENTES ---
def formatar_telefone(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])
    apenas_numeros = apenas_numeros[:11]
    
    if len(apenas_numeros) == 0:
        return ""
    elif len(apenas_numeros) <= 2:
        return f"({apenas_numeros}"
    elif len(apenas_numeros) <= 7:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:]}"
    else:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"

# --- TELA DE LOGIN / IDENTIFICAÇÃO ---
if not st.session_state.logado:
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allowed_html=True)
    st.markdown('<div class="main-subtitle">Um movimento que une lojas e clientes</div>', unsafe_allowed_html=True)
    
    id_input = st.text_input("Identificação (Telefone ou Código)", placeholder="(00) 00000-0000", max_chars=15)
    id_limpo = id_input.strip()
    
    if st.button("Entrar"):
        if id_limpo == CODIGO_LOJISTA:
            st.session_state.logado = True
            st.session_state.tipo_usuario = "lojista"
            st.rerun()
        elif id_limpo:
            tel_formatado = formatar_telefone(id_limpo)
            if len([c for c in id_limpo if c.isdigit()]) >= 10:
                st.session_state.logado = True
                st.session_state.tipo_usuario = "cliente"
                st.session_state.usuario_atual = tel_formatado if tel_formatado else id_limpo
                st.rerun()
            else:
                st.warning("Por favor, digite um número de telefone válido com DDD ou código do lojista.")
        else:
            st.error("O campo de identificação não pode estar vazio.")

# --- TELA DO CLIENTE ---
elif st.session_state.logado and st.session_state.tipo_usuario == "cliente":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allowed_html=True)
    st.markdown('<div class="main-subtitle">Sua Loja Parceira</div>', unsafe_allowed_html=True)
    
    cliente = st.session_state.usuario_atual
    pontos = dados.get("clientes", {}).get(cliente, 0)
    
    st.markdown(f"Olá! Seu saldo atual de pontos registrado sob o telefone **{cliente}** é:")
    
    st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 2px solid #BFDBFE; border-radius: 12px; padding: 25px; text-align: center; margin: 20px 0;">
            <span style="font-size: 48px; font-weight: 700; color: #1E40AF;">{pontos}</span>
            <p style="margin: 0; color: #1E40AF; font-weight: 600;">pontos acumulados</p>
        </div>
    """, unsafe_allowed_html=True)
    
    if st.button("Sair", key="btn_sair"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()

# --- PAINEL DO LOJISTA ---
elif st.session_state.logado and st.session_state.tipo_usuario == "lojista":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allowed_html=True)
    st.markdown('<div class="main-subtitle">Painel do Lojista</div>', unsafe_allowed_html=True)
    
    st.subheader("Registrar Vendas no Movimento GLOBAL")
    
    # max_value adicionado para travar digitações infinitas por engano
    valor_venda = st.number_input("Valor da Venda (R$)", min_value=0.0, max_value=100000.0, value=0.0, step=0.50, format="%.2f")
    tel_cliente_input = st.text_input("Telefone do Cliente", placeholder="(00) 00000-0000", max_chars=15)
    
    if st.button("Enviar Pontos"):
        tel_cliente = formatar_telefone(tel_cliente_input)
        if not tel_cliente or len([c for c in tel_cliente if c.isdigit()]) < 10:
            st.error("Insira um número de telefone válido do cliente para computar os pontos.")
        elif valor_venda <= 0:
            st.error("O valor da venda precisa ser maior que R$ 0,00.")
        else:
            pontos_novos = int(valor_venda)
            
            if "clientes" not in dados:
                dados["clientes"] = {}
                
            if tel_cliente in dados["clientes"]:
                dados["clientes"][tel_cliente] += pontos_novos
            else:
                dados["clientes"][tel_cliente] = pontos_novos
                
            if salvar_dados_github(dados, sha):
                st.success(f"Sucesso! {pontos_novos} pontos adicionados para {tel_cliente}.")
                st.rerun()

    st.write("---")
    
    with st.expander("⚙️ Painel de Gestão e Configurações"):
        st.subheader("Métricas de Crescimento Real")
        
        todos_clientes = dados.get("clientes", {})
        
        # Proteção contra falhas de renderização numérica
        try:
            total_pontos_sistema = sum(int(v) for v in todos_clientes.values())
            equivalenca_dinheiro = total_pontos_sistema * 0.10
        except Exception:
            total_pontos_sistema = 0
            equivalenca_dinheiro = 0.0

        col1, col2 = st.columns(2)
        col1.metric("Total de Pontos Emitidos", f"{total_pontos_sistema} pts")
        col2.metric("Equivalência Estimada", f"R$ {equivalenca_dinheiro:,.2f}")
        
        st.write("---")
        st.subheader("Lista de Clientes Cadastrados")
        
        if todos_clientes:
            for cli, pts in list(todos_clientes.items()):
                col_c, col_p, col_a = st.columns([2, 1, 1])
                col_c.write(f"📱 {cli}")
                col_p.write(f"**{pts}** pts")
                if col_a.button("Excluir", key=f"del_{cli}"):
                    del dados["clientes"][cli]
                    salvar_dados_github(dados, sha)
                    st.rerun()
        else:
            st.info("Nenhum cliente cadastrado no momento.")
            
        st.write("---")
        st.subheader("Alterar Código de Acesso do Lojista")
        novo_codigo = st.text_input("Novo Código", value=CODIGO_LOJISTA)
        if st.button("Salvar Novo Código"):
            if novo_codigo.strip():
                if "config" not in dados:
                    dados["config"] = {}
                dados["config"]["codigo_lojista"] = novo_codigo.strip()
                salvar_dados_github(dados, sha)
                st.success("Código de acesso atualizado!")
                st.rerun()
                
        if st.button("🚨 Zerar Todos os Clientes", type="primary"):
            dados["clientes"] = {}
            salvar_dados_github(dados, sha)
            st.success("Banco de dados resetado!")
            st.rerun()

    if st.button("Sair", key="btn_sair"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.rerun()
