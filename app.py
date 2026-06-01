import streamlit as st
import json
from github import Github
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GLOBAL", page_icon="🌐", layout="centered")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
def aplicar_estilo():
    css_style = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main-title { font-size: 42px; font-weight: 700; color: #1E3A8A; margin-bottom: 5px; text-align: left; }
        .main-subtitle { font-size: 16px; color: #6B7280; margin-bottom: 35px; text-align: left; }
        div.stButton > button:first-child { background-color: #2563EB !important; color: white !important; font-size: 16px !important; font-weight: 600 !important; padding: 12px 24px !important; border-radius: 8px !important; border: none !important; width: 100% !important; transition: all 0.2s ease; }
        div.stButton > button:first-child:hover { background-color: #1D4ED8 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); }
        div.stButton > button[key="btn_sair"], div.stButton > button[key="btn_sair_painel"], div.stButton > button[key="btn_sair_gestor"] { background-color: #EF4444 !important; color: white !important; }
        div.stButton > button[key="btn_sair"]:hover, div.stButton > button[key="btn_sair_painel"]:hover, div.stButton > button[key="btn_sair_gestor"]:hover { background-color: #DC2626 !important; }
    </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)

aplicar_estilo()

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
        return {"lojistas": ["#loja123"], "clientes": {}}, None

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

# --- CONTROLE DE SESSÃO E MÁSCARAS ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = None
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

if "login_raw" not in st.session_state:
    st.session_state.login_raw = ""
if "cliente_cpf_raw" not in st.session_state:
    st.session_state.cliente_cpf_raw = ""

dados, sha = carregar_dados_github()
if not isinstance(dados, dict):
    dados = {"lojistas": ["#loja123"], "clientes": {}}

if "lojistas" not in dados:
    dados["lojistas"] = ["#loja123"]
if "clientes" not in dados:
    dados["clientes"] = {}

def formatar_para_cpf(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])[:11]
    if len(apenas_numeros) <= 3:
        return apenas_numeros
    elif len(apenas_numeros) <= 6:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"
    elif len(apenas_numeros) <= 9:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
    else:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"

def formatar_para_moeda(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])
    if not apenas_numeros:
        return "0,00"
    valor_float = float(apenas_numeros) / 100
    return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CALLBACKS ---
def callback_login_input():
    val = st.session_state.txt_login
    if val.startswith("@") or val.startswith("#"):
        st.session_state.login_raw = val
    else:
        st.session_state.login_raw = formatar_para_cpf(val)
    st.session_state.txt_login = st.session_state.login_raw

def callback_venda_input():
    val = st.session_state.txt_venda
    st.session_state.txt_venda = formatar_para_moeda(val)

def callback_cliente_cpf_input():
    val = st.session_state.txt_cliente_cpf
    st.session_state.cliente_cpf_raw = formatar_para_cpf(val)
    st.session_state.txt_cliente_cpf = st.session_state.cliente_cpf_raw


# --- TELA DE LOGIN / IDENTIFICAÇÃO ---
if not st.session_state.logado:
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Um movimento que une lojas e clientes</div>', unsafe_allow_html=True)
    
    id_limpo = st.text_input(
        "Identificação (CPF)", 
        key="txt_login", 
        on_change=callback_login_input
    ).strip()

    if st.button("Entrar", key="btn_entrar_login"):
        if id_limpo:
            if id_limpo.startswith("@"):
                if id_limpo == "@Romanos0828":
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "gestor"
                    st.session_state.usuario_atual = "Gestor Global"
                    st.rerun()
                else:
                    st.error("Acesso negado.")
            
            elif id_limpo.startswith("#"):
                if id_limpo in dados["lojistas"]:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "lojista"
                    st.session_state.usuario_atual = id_limpo
                    st.rerun()
                else:
                    st.error("Acesso negado.")
            
            else:
                numeros_cpf = "".join([c for c in id_limpo if c.isdigit()])
                if len(numeros_cpf) == 11:
                    cpf_formatado = formatar_para_cpf(numeros_cpf)
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "cliente"
                    st.session_state.usuario_atual = cpf_formatado
                    st.rerun()
                else:
                    st.error("Por favor, digite um CPF válido com 11 dígitos.")
        else:
            st.error("O campo de identificação não pode estar vazio.")

# --- TELA DO CLIENTE ---
elif st.session_state.logado and st.session_state.tipo_usuario == "cliente":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Sua Loja Parceira</div>', unsafe_allow_html=True)
    
    cliente_cpf = st.session_state.usuario_atual
    pontos = dados.get("clientes", {}).get(cliente_cpf, 0)
    
    st.markdown(f"Olá! Seu saldo atual de pontos registrado sob o CPF **{cliente_cpf}** é:")
    st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 2px solid #BFDBFE; border-radius: 12px; padding: 25px; text-align: center; margin: 20px 0;">
            <span style="font-size: 48px; font-weight: 700; color: #1E40AF;">{pontos}</span>
            <p style="margin: 0; color: #1E40AF; font-weight: 600;">pontos acumulados</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Sair", key="btn_sair"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()

# --- TELA OPERACIONAL DO LOJISTA ---
elif st.session_state.logado and st.session_state.tipo_usuario == "lojista":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Painel Operacional do Lojista</div>', unsafe_allow_html=True)
    st.subheader("Registrar Vendas no Movimento GLOBAL")
    
    valor_venda_raw = st.text_input("Valor da Venda (R$)", value="0,00", key="txt_venda", on_change=callback_venda_input)
    cpf_cliente_input = st.text_input("CPF do Cliente", key="txt_cliente_cpf", on_change=callback_cliente_cpf_input)
    
    if st.button("Enviar Pontuação", key="btn_enviar_pontos_lojista"):
        try:
            limpo_valor = valor_venda_raw.replace(".", "").replace(",", ".")
            valor_venda = float(limpo_valor)
        except ValueError:
            valor_venda = 0.0

        numeros_cpf = "".join([c for c in cpf_cliente_input if c.isdigit()])
        
        if len(numeros_cpf) < 11:
            st.error("Insira um CPF válido com 11 dígitos para computar os pontos.")
        elif valor_venda <= 0:
            st.error("O valor da venda precisa ser maior que R$ 0,00.")
        else:
            cpf_formatado = formatar_para_cpf(numeros_cpf)
            pontos_novos = int(valor_venda * 10)
            
            if cpf_formatado in dados["clientes"]:
                dados["clientes"][cpf_formatado] += pontos_novos
            else:
                dados["clientes"][cpf_formatado] = pontos_novos
                
            if salvar_dados_github(dados, sha):
                st.success(f"Sucesso! {pontos_novos} pontos adicionados para o CPF {cpf_formatado}.")
                st.rerun()

    st.write("---")
    if st.button("Sair", key="btn_sair_painel"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()

# --- PAINEL ADMINISTRATIVO DO GESTOR GLOBAL ---
elif st.session_state.logado and st.session_state.tipo_usuario == "gestor":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Painel de Gestão e Administração Global</div>', unsafe_allow_html=True)
    
    st.subheader("Métricas de Controle Administrativo")
    todos_clientes = dados.get("clientes", {})
    
    try:
        total_pontos_sistema = sum(int(v) for v in todos_clientes.values())
        equivalenca_dinheiro = total_pontos_sistema / 10
    except Exception:
        total_pontos_sistema = 0
        equivalenca_dinheiro = 0.0

    col1, col2 = st.columns(2)
    col1.metric("Total de Pontos Emitidos (Global)", f"{total_pontos_sistema} pts")
    col2.metric("Movimentação Financeira Equivalente", f"R$ {equivalenca_dinheiro:,.2f}")
    
    st.write("---")
    
    # SEÇÃO ATUALIZADA: APENAS EDIÇÃO E REMOÇÃO DE LOJISTAS EXISTENTES
    st.subheader("Gerenciar Lojistas Cadastrados")
    st.write("Modifique o código diretamente no campo e clique em **Salvar Alteração** para atualizar.")

    for idx_loj, loj in enumerate(dados["lojistas"]):
        # Cria colunas para organizar o input de edição, o botão de salvar e o botão de remover
        col_input, col_salvar, col_remover = st.columns([2, 1, 1])
        
        # Campo de texto pré-preenchido com o código atual do lojista
        codigo_editado = col_input.text_input(
            f"Código do Lojista {idx_loj + 1}", 
            value=loj, 
            key=f"edit_loj_{idx_loj}"
        ).strip()
        
        # Botão para salvar a alteração efetuada
        if col_salvar.button("Salvar Alteração", key=f"btn_salvar_{idx_loj}"):
            if codigo_editado.startswith("#") and len(codigo_editado) > 1:
                # Substitui o código antigo pelo novo na lista de lojistas
                dados["lojistas"][idx_loj] = codigo_editado
                if salvar_dados_github(dados, sha):
                    st.success(f"Código atualizado para {codigo_editado}!")
                    st.rerun()
            else:
                st.error("O código editado precisa começar com '#'.")
                
        # Botão tradicional para remover o lojista do sistema
        if col_remover.button("Remover Lojista", key=f"rem_loj_{idx_loj}"):
            dados["lojistas"].remove(loj)
            salvar_dados_github(dados, sha)
            st.rerun()

    st.write("---")
    st.subheader("Lista Geral de Clientes Cadastrados")
    if todos_clientes:
        for idx, (cli, pts) in enumerate(list(todos_clientes.items())):
            col_c, col_p, col_a = st.columns([2, 1, 1])
            col_c.write(f"💳 CPF: {cli}")
            col_p.write(f"**{pts}** pts")
            if col_a.button("Excluir Cliente", key=f"del_item_{idx}"):
                del dados["clientes"][cli]
                salvar_dados_github(dados, sha)
                st.rerun()
                
        st.write("---")
        st.subheader("Zerar Banco de Dados de Clientes")
        if st.button("🚨 Zerar Clientela Completa", type="primary", key="btn_reset_completo_sistema"):
            dados["clientes"] = {}
            salvar_dados_github(dados, sha)
            st.success("Toda a clientela global foi zerada com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum cliente cadastrado no sistema até o momento.")

    st.write("---")
    if st.button("Sair do Painel de Gestor", key="btn_sair_gestor"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()
