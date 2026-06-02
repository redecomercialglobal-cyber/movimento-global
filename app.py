import streamlit as st
import json
from github import Github
import base64
from io import BytesIO

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
        
        /* Estilização dos Cards */
        .card { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .card-title { font-size: 20px; font-weight: 700; color: #1F2937; margin-bottom: 10px; }
        
        /* Ajuste Focado para Capas de Categorias */
        .container-imagem-capa { text-align: center; margin-bottom: 15px; background-color: #F9FAFB; border-radius: 8px; padding: 10px; }
        .container-imagem-capa img { max-height: 190px; object-fit: contain; border-radius: 6px; }
        
        /* Nome da Categoria muito mais visível */
        .categoria-card-titulo { font-size: 26px; font-weight: 700; color: #111827; text-align: center; margin-top: 5px; margin-bottom: 15px; }
        
        /* Botões Padrão */
        div.stButton > button:first-child { background-color: #2563EB !important; color: white !important; font-size: 16px !important; font-weight: 600 !important; padding: 10px 20px !important; border-radius: 8px !important; border: none !important; width: 100% !important; transition: all 0.2s ease; }
        div.stButton > button:first-child:hover { background-color: #1D4ED8 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); }
        
        /* Botão Principal de Navegação (Destaque Ampliado) */
        div.stButton > button[key^="entrar_cat_"] { background-color: #10B981 !important; font-size: 18px !important; padding: 12px 20px !important; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.1); }
        div.stButton > button[key^="entrar_cat_"]:hover { background-color: #059669 !important; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3); }
        
        /* Botões de Exclusão / Perigo */
        div.stButton > button[key^="btn_sair"], div.stButton > button[key^="rem_"], div.stButton > button[key^="del_"], div.stButton > button[key^="btn_reset"], div.stButton > button[key^="btn_remover_capa"], div.stButton > button[key^="conf_del_"], div.stButton > button[key^="conf_reset_"] { background-color: #EF4444 !important; color: white !important; }
        div.stButton > button[key^="btn_sair"]:hover, div.stButton > button[key^="rem_"]:hover, div.stButton > button[key^="del_"]:hover, div.stButton > button[key^="btn_reset"]:hover, div.stButton > button[key^="btn_remover_capa"]:hover, div.stButton > button[key^="conf_del_"]:hover, div.stButton > button[key^="conf_reset_"]:hover { background-color: #DC2626 !important; }
    </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)

aplicar_estilo()

# --- CONFIGURAÇÕES DE ACESSO AO GITHUB ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "clientes.json"

# --- FUNÇÕES DO BANCO DE DADOS (GITHUB) ---
def carregar_dados_github():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_contents = repo.get_contents(FILE_PATH)
        dados = json.loads(file_contents.decoded_content.decode("utf-8"))
        return dados, file_contents.sha
    except Exception:
        estrutura_inicial = {
            "categorias": {
                "cat_1": {"nome": "Alimentação", "capa_b64": "", "lojas": ["#loja123"]}
            },
            "clientes_por_loja": {
                "#loja123": {}
            },
            "dados_lojas": {
                "#loja123": {"nome_fantasia": "Loja Exemplo Inicial"}
            }
        }
        return estrutura_inicial, None

def salvar_dados_github(dados, sha):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        conteudo_json = json.dumps(dados, indent=4, ensure_ascii=False)
        if sha:
            repo.update_file(FILE_PATH, "Atualizando estrutura categórica GLOBAL", conteudo_json, sha)
        else:
            repo.create_file(FILE_PATH, "Iniciando estrutura categórica GLOBAL", conteudo_json)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

# --- CONTROLE DE SESSÃO E ROTEAMENTO ---
if "logado" not in st.session_state: st.session_state.logado = False
if "tipo_usuario" not in st.session_state: st.session_state.tipo_usuario = None
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = None
if "gestor_view" not in st.session_state: st.session_state.gestor_view = "categorias"
if "categoria_selecionada" not in st.session_state: st.session_state.categoria_selecionada = None
if "loja_selecionada" not in st.session_state: st.session_state.loja_selecionada = None
if "login_raw" not in st.session_state: st.session_state.login_raw = ""
if "cliente_cpf_raw" not in st.session_state: st.session_state.cliente_cpf_raw = ""
if "imagens_temp_cache" not in st.session_state: st.session_state.imagens_temp_cache = {}
if "contrato_temp_cache" not in st.session_state: st.session_state.contrato_temp_cache = None
if "deletar_cliente_id" not in st.session_state: st.session_state.deletar_cliente_id = None
if "zerar_loja_id" not in st.session_state: st.session_state.zerar_loja_id = False

dados, sha = carregar_dados_github()

def formatar_para_cpf(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])[:11]
    if len(apenas_numeros) <= 3: return apenas_numeros
    elif len(apenas_numeros) <= 6: return f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"
    elif len(apenas_numeros) <= 9: return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
    else: return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"

# --- CALLBACKS ---
def callback_login_input():
    val = st.session_state.txt_login
    if val.startswith("@") or val.startswith("#"): st.session_state.login_raw = val
    else: st.session_state.login_raw = formatar_para_cpf(val)
    st.session_state.txt_login = st.session_state.login_raw

def callback_cliente_cpf_input():
    val = st.session_state.txt_cliente_cpf
    st.session_state.cliente_cpf_raw = formatar_para_cpf(val)
    st.session_state.txt_cliente_cpf = st.session_state.cliente_cpf_raw

# =========================================================
# 1. TELA DE LOGIN / IDENTIFICAÇÃO
# =========================================================
if not st.session_state.logado:
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Um movimento que une lojas e clientes</div>', unsafe_allow_html=True)
    id_limpo = st.text_input("Identificação (CPF)", key="txt_login", on_change=callback_login_input).strip()
    if st.button("Entrar", key="btn_entrar_login"):
        if id_limpo:
            if id_limpo == "@Romanos0828":
                st.session_state.logado = True
                st.session_state.tipo_usuario = "gestor"
                st.session_state.usuario_atual = "Gestor Global"
                st.rerun()
            elif id_limpo.startswith("#"):
                loja_encontrada = any(id_limpo in cat_info.get("lojas", []) for cat_info in dados["categorias"].values())
                if loja_encontrada:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "lojista"
                    st.session_state.usuario_atual = id_limpo
                    st.rerun()
                else: st.error("Código de lojista não identificado.")
            else:
                numeros_cpf = "".join([c for c in id_limpo if c.isdigit()])
                if len(numeros_cpf) == 11:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "cliente"
                    st.session_state.usuario_atual = formatar_para_cpf(numeros_cpf)
                    st.rerun()
                else: st.error("Por favor, insira um CPF válido.")

# =========================================================
# 2. TELA DO CLIENTE
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "cliente":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    cliente_cpf = st.session_state.usuario_atual
    st.write(f"CPF: **{cliente_cpf}**")
    st.subheader("Seus Pontos por Loja Parceira")
    encontrou = False
    for loja, listagem in dados.get("clientes_por_loja", {}).items():
        if cliente_cpf in listagem:
            encontrou = True
            nome_loja = dados.get("dados_lojas", {}).get(loja, {}).get("nome_fantasia", loja)
            st.markdown(f'<div class="card">🏢 {nome_loja}: <b>{listagem[cliente_cpf]} pts</b></div>', unsafe_allow_html=True)
    if not encontrou: st.info("Nenhum ponto acumulado.")
    if st.button("Sair"): st.session_state.logado = False; st.rerun()

# =========================================================
# 3. TELA OPERACIONAL DO LOJISTA
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "lojista":
    loja_id = st.session_state.usuario_atual
    st.markdown(f'<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.subheader(f"Registrar Venda - {loja_id}")
    
    # Campo manual (sem máscara)
    valor_venda_input = st.text_input("Valor da Venda (R$)", placeholder="0.00")
    cpf_cliente_input = st.text_input("CPF do Cliente", key="txt_cliente_cpf", on_change=callback_cliente_cpf_input)
    
    if st.button("Enviar Pontuação", key="btn_enviar_pontos_lojista"):
        try:
            # Substitui vírgula por ponto para garantir conversão decimal
            valor_venda = float(valor_venda_input.replace(",", "."))
        except: valor_venda = 0.0

        numeros_cpf = "".join([c for c in cpf_cliente_input if c.isdigit()])
        if len(numeros_cpf) < 11: st.error("CPF inválido.")
        elif valor_venda <= 0: st.error("Valor inválido.")
        else:
            cpf_f = formatar_para_cpf(numeros_cpf)
            pts = int(valor_venda * 10)
            if loja_id not in dados["clientes_por_loja"]: dados["clientes_por_loja"][loja_id] = {}
            dados["clientes_por_loja"][loja_id][cpf_f] = dados["clientes_por_loja"][loja_id].get(cpf_f, 0) + pts
            
            if salvar_dados_github(dados, sha):
                st.balloons() # Efeito de comemoração
                st.success(f"Sucesso! {pts} pts adicionados para {cpf_f}.")
                # Opcional: st.rerun() se quiser limpar os campos

    if st.button("Sair"): st.session_state.logado = False; st.rerun()

# ... (Restante do código do Gestor permanece inalterado)
# Nota: O código do Gestor é extenso, apenas certifique-se de manter o 
# resto conforme o seu original a partir daqui.
