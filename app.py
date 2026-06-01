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
        
        /* Botões */
        div.stButton > button:first-child { background-color: #2563EB !important; color: white !important; font-size: 16px !important; font-weight: 600 !important; padding: 10px 20px !important; border-radius: 8px !important; border: none !important; width: 100% !important; transition: all 0.2s ease; }
        div.stButton > button:first-child:hover { background-color: #1D4ED8 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); }
        
        /* Botões de Exclusão / Perigo */
        div.stButton > button[key^="btn_sair"], div.stButton > button[key^="rem_"], div.stButton > button[key^="del_"], div.stButton > button[key^="btn_reset"] { background-color: #EF4444 !important; color: white !important; }
        div.stButton > button[key^="btn_sair"]:hover, div.stButton > button[key^="rem_"]:hover, div.stButton > button[key^="del_"]:hover, div.stButton > button[key^="btn_reset"]:hover { background-color: #DC2626 !important; }
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
        # Estrutura inicial padrão caso o arquivo não exista ou falhe
        estrutura_inicial = {
            "categorias": {
                "cat_1": {"nome": "Alimentação", "capa_b64": "", "lojas": ["#loja123"]}
            },
            "clientes_por_loja": {
                "#loja123": {}
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
if "logado" not in st.session_state:
    st.session_state.logado = False
if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = None
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

# Sistema de Navegação para o Gestor Administrador
if "gestor_view" not in st.session_state:
    st.session_state.gestor_view = "categorias"  # categorias | dentro_categoria | dentro_loja
if "categoria_selecionada" not in st.session_state:
    st.session_state.categoria_selecionada = None
if "loja_selecionada" not in st.session_state:
    st.session_state.loja_selecionada = None

# Auxiliares de máscaras
if "login_raw" not in st.session_state:
    st.session_state.login_raw = ""
if "cliente_cpf_raw" not in st.session_state:
    st.session_state.cliente_cpf_raw = ""

dados, sha = carregar_dados_github()

# Garantia de integridade da árvore de dados
if "categorias" not in dados:
    dados["categorias"] = {}
if "clientes_por_loja" not in dados:
    dados["clientes_por_loja"] = {}

def formatar_para_cpf(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])[:11]
    if len(apenas_numeros) <= 3: return apenas_numeros
    elif len(apenas_numeros) <= 6: return f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"
    elif len(apenas_numeros) <= 9: return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
    else: return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"

def formatar_para_moeda(texto):
    apenas_numeros = "".join([c for c in texto if c.isdigit()])
    if not apenas_numeros: return "0,00"
    valor_float = float(apenas_numeros) / 100
    return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CALLBACKS ---
def callback_login_input():
    val = st.session_state.txt_login
    if val.startswith("@") or val.startswith("#"): st.session_state.login_raw = val
    else: st.session_state.login_raw = formatar_para_cpf(val)
    st.session_state.txt_login = st.session_state.login_raw

def callback_venda_input():
    val = st.session_state.txt_venda
    st.session_state.txt_venda = formatar_para_moeda(val)

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
                st.session_state.gestor_view = "categorias"
                st.rerun()
            elif id_limpo.startswith("#"):
                # Procura se a loja existe em alguma categoria
                loja_encontrada = False
                for cat_id, cat_info in dados["categorias"].items():
                    if id_limpo in cat_info.get("lojas", []):
                        loja_encontrada = True
                        break
                if loja_encontrada:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "lojista"
                    st.session_state.usuario_atual = id_limpo
                    st.rerun()
                else:
                    st.error("Código de lojista não identificado no sistema.")
            else:
                numeros_cpf = "".join([c for c in id_limpo if c.isdigit()])
                if len(numeros_cpf) == 11:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "cliente"
                    st.session_state.usuario_atual = formatar_para_cpf(numeros_cpf)
                    st.rerun()
                else:
                    st.error("Por favor, insira um CPF válido.")
        else:
            st.error("O campo de identificação não pode estar vazio.")

# =========================================================
# 2. TELA DO CLIENTE (BUSCA TOTALIZADA POR LOJA)
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "cliente":
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Sua Carteira de Pontos GLOBAL</div>', unsafe_allow_html=True)
    
    cliente_cpf = st.session_state.usuario_atual
    st.write(f"CPF: **{cliente_cpf}**")
    
    st.subheader("Seus Pontos por Loja Parceira")
    encontrou_pontos = False
    
    for loja, listagem in dados.get("clientes_por_loja", {}).items():
        if cliente_cpf in listagem:
            encontrou_pontos = True
            pts = listagem[cliente_cpf]
            st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 18px; font-weight:600; color:#1F2937;">🏢 Loja: {loja}</span>
                        <span style="font-size: 22px; font-weight:700; color:#2563EB;">{pts} pts</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    if not encontrou_pontos:
        st.info("Você ainda não possui pontos acumulados em nenhuma loja do movimento.")
        
    if st.button("Sair", key="btn_sair"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()

# =========================================================
# 3. TELA OPERACIONAL DO LOJISTA
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "lojista":
    loja_id = st.session_state.usuario_atual
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="main-subtitle">Painel Operacional — Loja {loja_id}</div>', unsafe_allow_html=True)
    
    st.subheader("Registrar Vendas")
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
            st.error("Insira um CPF válido para computar os pontos.")
        elif valor_venda <= 0:
            st.error("O valor precisa ser maior que R$ 0,00.")
        else:
            cpf_formatado = formatar_para_cpf(numeros_cpf)
            pontos_novos = int(valor_venda * 10) # R$ 1,00 = 10 pontos
            
            if loja_id not in dados["clientes_por_loja"]:
                dados["clientes_por_loja"][loja_id] = {}
                
            if cpf_formatado in dados["clientes_por_loja"][loja_id]:
                dados["clientes_por_loja"][loja_id][cpf_formatado] += pontos_novos
            else:
                dados["clientes_por_loja"][loja_id][cpf_formatado] = pontos_novos
                
            if salvar_dados_github(dados, sha):
                st.success(f"Sucesso! {pontos_novos} pontos adicionados para o CPF {cpf_formatado}.")
                st.rerun()

    st.write("---")
    if st.button("Sair", key="btn_sair_painel"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()


# =========================================================
# 4. PAINEL ADMINISTRATIVO DO GESTOR GLOBAL (ARQUITETURA DE ABAS/PROCESSO)
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "gestor":
    
    # -----------------------------------------------------
    # VISTA A: LISTAGEM DE CATEGORIAS
    # -----------------------------------------------------
    if st.session_state.gestor_view == "categorias":
        st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Painel de Gestão — Categorias</div>', unsafe_allow_html=True)
        
        # Listagem Vertical Ordenada das Categorias Existentes
        for cat_id, cat_info in list(dados["categorias"].items()):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Exibição da Imagem da Capa (se houver Base64 salvo)
            if cat_info.get("capa_b64"):
                try:
                    bytes_img = base64.b64decode(cat_info["capa_b64"])
                    st.image(bytes_img, use_container_width=True)
                except Exception:
                    st.warning("Erro ao renderizar a imagem da capa.")
            else:
                st.info("Nenhuma imagem de capa cadastrada para esta categoria.")
            
            # Input Grande para Carregar/Modificar Imagem
            nova_img = st.file_uploader("Alterar imagem de capa", type=["png", "jpg", "jpeg"], key=f"upload_{cat_id}")
            if nova_img is not None:
                bytes_data = nova_img.read()
                cat_info["capa_b64"] = base64.b64encode(bytes_data).decode("utf-8")
                salvar_dados_github(dados, sha)
                st.rerun()
                
            # Input para editar o Nome da Categoria
            nome_editado = st.text_input("Nome da Categoria", value=cat_info["nome"], key=f"nome_{cat_id}")
            if nome_editado != cat_info["nome"]:
                cat_info["nome"] = nome_editado
                salvar_dados_github(dados, sha)
                st.rerun()
            
            # Botões de controle do card
            col_entrar, col_excluir = st.columns(2)
            if col_entrar.button(f"Entrar em {cat_info['nome']}", key=f"entrar_cat_{cat_id}"):
                st.session_state.categoria_selecionada = cat_id
                st.session_state.gestor_view = "dentro_categoria"
                st.rerun()
                
            if col_excluir.button("Excluir Categoria", key=f"rem_cat_{cat_id}"):
                del dados["categorias"][cat_id]
                salvar_dados_github(dados, sha)
                st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.write("---")
        # Formulário para criar uma Nova Categoria no final da lista
        st.subheader("Criar Nova Categoria")
        nova_cat_nome = st.text_input("Nome da Nova Categoria", placeholder="Ex: Vestuário, Farmácias...")
        if st.button("Adicionar Categoria"):
            if nova_cat_nome.strip():
                novo_id = f"cat_{int(max([k.split('_')[1] for k in dados['categorias'].keys()] or [0])) + 1}"
                dados["categorias"][novo_id] = {"nome": nova_cat_nome.strip(), "capa_b64": "", "lojas": []}
                if salvar_dados_github(dados, sha):
                    st.success("Categoria adicionada!")
                    st.rerun()
            else:
                st.error("Digite um nome válido.")
                
        if st.button("Sair do Painel", key="btn_sair_gestor_raiz"):
            st.session_state.logado = False
            st.session_state.tipo_usuario = None
            st.rerun()

    # -----------------------------------------------------
    # VISTA B: DENTRO DE UMA CATEGORIA (LISTAGEM DE LOJAS EM CARDS)
    # -----------------------------------------------------
    elif st.session_state.gestor_view == "dentro_categoria":
        cat_id = st.session_state.categoria_selecionada
        cat_nome = dados["categorias"][cat_id]["nome"]
        
        if st.button("⬅️ Voltar para Categorias"):
            st.session_state.gestor_view = "categories"
            st.session_state.gestor_view = "categorias"
            st.rerun()
            
        st.markdown(f'<div class="main-title">{cat_nome}</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Lojas pertencentes a este segmento</div>', unsafe_allow_html=True)
        
        lojas_da_categoria = dados["categorias"][cat_id].get("lojas", [])
        
        if lojas_da_categoria:
            for idx_loj, loj in enumerate(lojas_da_categoria):
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">🏢 Loja: {loj}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_acessar, c_remover = st.columns(2)
                if c_acessar.button("Ver Detalhamento da Loja", key=f"ver_loj_{idx_loj}"):
                    st.session_state.loja_selecionada = loj
                    st.session_state.gestor_view = "dentro_loja"
                    st.rerun()
                if c_remover.button("Remover Loja do Segmento", key=f"rem_loj_{idx_loj}"):
                    dados["categorias"][cat_id]["lojas"].remove(loj)
                    salvar_dados_github(dados, sha)
                    st.rerun()
        else:
            st.info("Nenhuma loja cadastrada para este segmento ainda.")
            
        st.write("---")
        st.subheader("Adicionar Nova Loja nesta Categoria")
        novo_cod_loja = st.text_input("Código identificador da loja (Deve iniciar com #)", placeholder="#exemploLoja")
        if st.button("Criar Card de Loja"):
            cod_limpo = novo_cod_loja.strip()
            if cod_limpo.startswith("#") and len(cod_limpo) > 1:
                if cod_limpo not in dados["categorias"][cat_id]["lojas"]:
                    dados["categorias"][cat_id]["lojas"].append(cod_limpo)
                    if cod_limpo not in dados["clientes_por_loja"]:
                        dados["clientes_por_loja"][cod_limpo] = {}
                    if salvar_dados_github(dados, sha):
                        st.success(f"Loja {cod_limpo} vinculada com sucesso!")
                        st.rerun()
                else:
                    st.warning("Esta loja já está nessa categoria.")
            else:
                st.error("O código deve começar obrigatoriamente com '#'.")

    # -----------------------------------------------------
    # VISTA C: DETALHAMENTO ISOLADO DA LOJA SELECIONADA (TELA DO VÍDEO)
    # -----------------------------------------------------
    elif st.session_state.gestor_view == "dentro_loja":
        cat_id = st.session_state.categoria_selecionada
        loja_id = st.session_state.loja_selecionada
        
        if st.button(f"⬅️ Voltar para a categoria {dados['categorias'][cat_id]['nome']}"):
            st.session_state.gestor_view = "dentro_categoria"
            st.session_state.loja_selecionada = None
            st.rerun()
            
        st.markdown(f'<div class="main-title">Loja {loja_id}</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Métricas e Clientes Isolados</div>', unsafe_allow_html=True)
        
        # Puxa os clientes exclusivos dessa loja específica
        clientes_da_loja = dados["clientes_por_loja"].get(loja_id, {})
        
        try:
            total_pontos = sum(int(v) for v in clientes_da_loja.values())
            faturamento_equivalente = total_pontos / 10
        except Exception:
            total_pontos = 0
            faturamento_equivalente = 0.0
            
        col1, col2 = st.columns(2)
        col1.metric("Total de Pontos Emitidos", f"{total_pontos} pts")
        col2.metric("Movimentação Financeira", f"R$ {faturamento_equivalente:,.2f}")
        
        st.write("---")
        st.subheader("Lista de Clientes Desta Loja")
        
        if clientes_da_loja:
            for idx, (cli, pts) in enumerate(list(clientes_da_loja.items())):
                col_c, col_p, col_a = st.columns([2, 1, 1])
                col_c.write(f"💳 CPF: {cli}")
                col_p.write(f"**{pts}** pts")
                if col_a.button("Excluir Cliente", key=f"del_cli_{idx}"):
                    del dados["clientes_por_loja"][loja_id][cli]
                    salvar_dados_github(dados, sha)
                    st.rerun()
            
            st.write("---")
            if st.button("🚨 Zerar Banco de Dados desta Loja", type="primary", key="btn_reset_loja_completo"):
                dados["clientes_por_loja"][loja_id] = {}
                salvar_dados_github(dados, sha)
                st.success("Dados da loja limpos!")
                st.rerun()
        else:
            st.info("Nenhum cliente comprou nesta loja até agora.")
