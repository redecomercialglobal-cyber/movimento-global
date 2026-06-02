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

# --- CONTROLE DE SESSÃO ---
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
# 2. TELA DO CLIENTE
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
            nome_loja_exibir = dados.get("dados_lojas", {}).get(loja, {}).get("nome_fantasia", loja)
            st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 18px; font-weight:600; color:#1F2937;">🏢 Loja: {nome_loja_exibir}</span>
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
    nome_loja_p = dados.get("dados_lojas", {}).get(loja_id, {}).get("nome_fantasia", loja_id)
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="main-subtitle">Painel Operacional — {nome_loja_p}</div>', unsafe_allow_html=True)
    
    st.subheader("Registrar Vendas")
    # Adicionado autocomplete="off" via html no input
    valor_venda_raw = st.text_input("Valor da Venda (R$)", value="0,00", key="txt_venda", on_change=callback_venda_input, help="autocomplete='off'")
    # Adicionado autocomplete="off" para evitar histórico
    cpf_cliente_input = st.text_input("CPF do Cliente", key="txt_cliente_cpf", on_change=callback_cliente_cpf_input, help="autocomplete='off'")
    
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
            pontos_novos = int(valor_venda * 10)
            
            if loja_id not in dados["clientes_por_loja"]:
                dados["clientes_por_loja"][loja_id] = {}
                
            if cpf_formatado in dados["clientes_por_loja"][loja_id]:
                dados["clientes_por_loja"][loja_id][cpf_formatado] += pontos_novos
            else:
                dados["clientes_por_loja"][loja_id][cpf_formatado] = pontos_novos
                
            if salvar_dados_github(dados, sha):
                # EFEITO DE COMEMORAÇÃO E SUCESSO
                st.balloons()
                st.success(f"Sucesso! {pontos_novos} pontos adicionados para o CPF {cpf_formatado}.")
                # Pequena pausa para o usuário ver o sucesso antes do rerun
                import time
                time.sleep(2)
                st.rerun()

    st.write("---")
    if st.button("Sair", key="btn_sair_painel"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = None
        st.session_state.usuario_atual = None
        st.rerun()


# =========================================================
# 4. PAINEL ADMINISTRATIVO DO GESTOR GLOBAL
# =========================================================
elif st.session_state.logado and st.session_state.tipo_usuario == "gestor":
    
    # -----------------------------------------------------
    # VISTA A: LISTAGEM DE CATEGORIAS
    # -----------------------------------------------------
    if st.session_state.gestor_view == "categorias":
        st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Painel de Gestão — Categorias</div>', unsafe_allow_html=True)
        
        for cat_id, cat_info in list(dados["categorias"].items()):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            if cat_info.get("capa_b64"):
                try:
                    html_img = f'<div class="container-imagem-capa"><img src="data:image/png;base64,{cat_info["capa_b64"]}"/></div>'
                    st.markdown(html_img, unsafe_allow_html=True)
                except Exception:
                    st.warning("Erro ao carregar imagem de capa.")
            else:
                st.info("Nenhuma imagem de capa cadastrada para esta categoria.")
            
            st.markdown(f'<div class="categoria-card-titulo">📂 {cat_info["nome"]}</div>', unsafe_allow_html=True)
            
            if st.button(f"Entrar em {cat_info['nome']}", key=f"entrar_cat_{cat_id}"):
                st.session_state.categoria_selecionada = cat_id
                st.session_state.gestor_view = "dentro_categoria"
                st.rerun()
            
            st.write("") 
            
            with st.expander("⚙️ Configurações da Categoria"):
                if cat_info.get("capa_b64"):
                    if st.button("🗑️ Remover Capa Atual", key=f"btn_remover_capa_{cat_id}"):
                        cat_info["capa_b64"] = ""
                        salvar_dados_github(dados, sha)
                        st.rerun()
                
                nova_img = st.file_uploader("Alterar Imagem de Capa", type=["png", "jpg", "jpeg"], key=f"upload_{cat_id}")
                
                if nova_img is not None:
                    st.session_state.imagens_temp_cache[cat_id] = nova_img.getvalue()
                else:
                    if cat_id in st.session_state.imagens_temp_cache:
                        del st.session_state.imagens_temp_cache[cat_id]
                
                if cat_id in st.session_state.imagens_temp_cache:
                    st.image(st.session_state.imagens_temp_cache[cat_id], caption="💡 Pré-visualização da imagem", width=200)
                    if st.button("💾 Salvar Nova Capa", key=f"btn_salvar_img_{cat_id}"):
                        bytes_data = st.session_state.imagens_temp_cache[cat_id]
                        cat_info["capa_b64"] = base64.b64encode(bytes_data).decode("utf-8")
                        del st.session_state.imagens_temp_cache[cat_id]
                        salvar_dados_github(dados, sha)
                        st.rerun()
                    
                nome_editado = st.text_input("Editar Nome", value=cat_info["nome"], key=f"nome_{cat_id}")
                if nome_editado != cat_info["nome"] and nome_editado.strip() != "":
                    cat_info["nome"] = nome_editado.strip()
                    salvar_dados_github(dados, sha)
                    st.rerun()
                
                if st.button("Excluir Categoria do Sistema", key=f"rem_cat_{cat_id}"):
                    if cat_id in st.session_state.imagens_temp_cache:
                        del st.session_state.imagens_temp_cache[cat_id]
                    del dados["categorias"][cat_id]
                    salvar_dados_github(dados, sha)
                    st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("Criar Nova Categoria")
        nova_cat_nome = st.text_input("Nome da Nova Categoria", placeholder="Ex: Vestuário, Farmácias...")
        if st.button("Adicionar Categoria"):
            if nova_cat_nome.strip():
                lista_ids = [int(k.split('_')[1]) for k in dados['categorias'].keys() if '_' in k]
                proximo_id = max(lista_ids) + 1 if lista_ids else 1
                novo_id = f"cat_{proximo_id}"
                
                dados["categorias"][novo_id] = {"nome": nova_cat_nome.strip(), "capa_b64": "", "lojas": []}
                if salvar_dados_github(dados, sha):
                    st.success("Categoria adicionada com sucesso!")
                    st.rerun()
            else:
                st.error("Digite um nome válido.")
                
        if st.button("Sair do Painel", key="btn_sair_gestor_raiz"):
            st.session_state.logado = False
            st.session_state.tipo_usuario = None
            st.rerun()

    # -----------------------------------------------------
    # VISTA B: DENTRO DE UMA CATEGORIA (LISTAGEM DE LOJAS)
    # -----------------------------------------------------
    elif st.session_state.gestor_view == "dentro_categoria":
        cat_id = st.session_state.categoria_selecionada
        cat_nome = dados["categorias"][cat_id]["nome"]
        
        if st.button("⬅️ Voltar para Categorias"):
            st.session_state.gestor_view = "categorias"
            st.session_state.categoria_selecionada = None
            st.rerun()
            
        st.markdown(f'<div class="main-title">{cat_nome}</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Lojas pertencentes a este segmento</div>', unsafe_allow_html=True)
        
        lojas_da_categoria = dados["categorias"][cat_id].get("lojas", [])
        
        if lojas_da_categoria:
            for idx_loj, loj in enumerate(lojas_da_categoria):
                info_cadastro = dados["dados_lojas"].get(loj, {})
                nome_fantasia_exibicao = info_cadastro.get("nome_fantasia", f"Loja Sem Nome ({loj})")
                
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">🏢 Loja: {nome_fantasia_exibicao}</div>
                        <div style="font-size:13px; color:#6B7280; margin-top:-5px;
 margin-bottom:10px;">Código de Acesso: <b>{loj}</b></div>
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
        
        col_cad1, col_cad2 = st.columns(2)
        novo_nome_loja = col_cad1.text_input("Nome da Loja (Nome Fantasia)", placeholder="Ex: Pet Shop do Totó")
        novo_codigo_loja = col_cad2.text_input("Código de Acesso Customizado", placeholder="Ex: #totopet").strip()
        
        if st.button("Criar Card de Loja"):
            nome_limpo = novo_nome_loja.strip()
            cod_limpo = novo_codigo_loja.strip()
            
            if not nome_limpo:
                st.error("O nome da loja não pode estar vazio.")
            elif not cod_limpo or cod_limpo == "#":
                st.error("Defina um Código de Acesso válido para a loja.")
            else:
                if not cod_limpo.startswith("#"):
                    cod_limpo = f"#{cod_limpo}"
                
                if cod_limpo in dados["dados_lojas"]:
                    st.error(f"O código {cod_limpo} já está em uso por outra loja! Escolha um código diferente.")
                else:
                    dados["categorias"][cat_id]["lojas"].append(cod_limpo)
                    
                    if cod_limpo not in dados["clientes_por_loja"]:
                        dados["clientes_por_loja"][cod_limpo] = {}
                        
                    dados["dados_lojas"][cod_limpo] = {
                        "nome_fantasia": nome_limpo,
                        "razao_social": "", "cnpj": "", "inscricao_estadual": "", "inscricao_municipal": "",
                        "endereco_completo": "", "telefone": "", "whatsapp": "", "email": "",
                        "nome_proprietario": "", "cpf_representante": "", "rg_representante": "",
                        "dados_bancarios": "", "chave_pix": "", "segmento": cat_nome, "contrato_b64": ""
                    }
                    
                    if salvar_dados_github(dados, sha):
                        st.success(f"Loja '{nome_limpo}' vinculada com sucesso! Código de acesso: {cod_limpo}")
                        st.rerun()

    # -----------------------------------------------------
    # VISTA C: DETALHAMENTO ISOLADO E FICHA CADASTRAL DA LOJA
    # -----------------------------------------------------
    elif st.session_state.gestor_view == "dentro_loja":
        cat_id = st.session_state.categoria_selecionada
        loja_id = st.session_state.loja_selecionada
        
        info_loja = dados["dados_lojas"].setdefault(loja_id, {
            "nome_fantasia": loja_id,
            "razao_social": "", "cnpj": "", "inscricao_estadual": "", "inscricao_municipal": "",
            "endereco_completo": "", "telefone": "", "whatsapp": "", "email": "",
            "nome_proprietario": "", "cpf_representante": "", "rg_representante": "",
            "dados_bancarios": "", "chave_pix": "", "segmento": "", "contrato_b64": ""
        })
        
        if st.button(f"⬅️ Voltar para {dados['categorias'][cat_id]['nome']}"):
            st.session_state.gestor_view = "dentro_categoria"
            st.session_state.loja_selecionada = None
            st.session_state.contrato_temp_cache = None
            st.session_state.deletar_cliente_id = None
            st.session_state.zerar_loja_id = False
            st.rerun()
            
        st.markdown(f'<div class="main-title">{info_loja.get("nome_fantasia")}</div>', unsafe_allow_html=True)
        st.markdown(f'<code>Código de Acesso Técnico Operacional: {loja_id}</code>', unsafe_allow_html=True)
        
        tab_metricas, tab_cadastro, tab_contrato = st.tabs(["📊 Métricas e Clientes", "📋 Ficha Cadastral", "📝 Contrato Digital"])
        
        with tab_metricas:
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
                    
                    # Interface de confirmação individual por cliente
                    if st.session_state.deletar_cliente_id == cli:
                        col_a.warning("Tem certeza?")
                        c_sim, c_nao = col_a.columns(2)
                        if c_sim.button("Sim", key=f"conf_del_sim_{idx}"):
                            del dados["clientes_por_loja"][loja_id][cli]
                            st.session_state.deletar_cliente_id = None
                            salvar_dados_github(dados, sha)
                            st.rerun()
                        if c_nao.button("Não", key=f"conf_del_nao_{idx}"):
                            st.session_state.deletar_cliente_id = None
                            st.rerun()
                    else:
                        if col_a.button("Excluir Cliente", key=f"del_cli_{idx}"):
                            st.session_state.deletar_cliente_id = cli
                            st.rerun()
                
                st.write("---")
                
                # Interface de confirmação para ZERAR toda a loja
                if st.session_state.zerar_loja_id:
                    st.warning("⚠️ VOCÊ TEM CERTEZA ABSOLUTA? Isso vai apagar TODOS os clientes e pontos desta loja permanentemente!")
                    c_reset_sim, c_reset_nao = st.columns(2)
                    if c_reset_sim.button("💥 Sim, zerar tudo!", key="conf_reset_loja_sim"):
                        dados["clientes_por_loja"][loja_id] = {}
                        st.session_state.zerar_loja_id = False
                        salvar_dados_github(dados, sha)
                        st.success("Dados da loja limpos com sucesso!")
                        st.rerun()
                    if c_reset_nao.button("Cancelar", key="conf_reset_loja_nao"):
                        st.session_state.zerar_loja_id = False
                        st.rerun()
                else:
                    if st.button("🚨 Zerar Banco de Dados desta Loja", type="primary", key="btn_reset_loja_completo"):
                        st.session_state.zerar_loja_id = True
                        st.rerun()
            else:
                st.info("Nenhum cliente comprou nesta loja até agora.")
                
        with tab_cadastro:
            st.subheader("Informações Empresariais e Contratuais")
            
            with st.form(key=f"form_cadastro_{loja_id}"):
                st.markdown("##### Dados de Identificação Oficial")
                c1, c2 = st.columns(2)
                f_fantasia = c1.text_input("Nome Fantasia", value=info_loja.get("nome_fantasia", ""))
                f_razao = c2.text_input("Razão Social", value=info_loja.get("razao_social", ""))
                
                c3, c4, c5 = st.columns(3)
                f_cnpj = c3.text_input("CNPJ", value=info_loja.get("cnpj", ""))
                f_ie = c4.text_input("Inscrição Estadual", value=info_loja.get("inscricao_state", ""))
                f_im = c5.text_input("Inscrição Municipal", value=info_loja.get("inscricao_municipal", ""))
                
                st.markdown("##### Endereço e Contatos")
                f_end = st.text_input("Endereço Completo", value=info_loja.get("endereco_completo", ""))
                
                c6, c7, c8 = st.columns(3)
                f_tel = c6.text_input("Telefone", value=info_loja.get("telefone", ""))
                f_whatsapp = c7.text_input("WhatsApp", value=info_loja.get("whatsapp", ""))
                f_email = c8.text_input("E-mail Comercial", value=info_loja.get("email", ""))
                
                st.markdown("##### Representação Legal")
                f_proprietario = st.text_input("Nome do Proprietário", value=info_loja.get("nome_proprietario", ""))
                c9, c10 = st.columns(2)
                f_cpf_rep = c9.text_input("CPF do Representante Legal", value=info_loja.get("cpf_representante", ""))
                f_rg_rep = c10.text_input("RG do Representante Legal", value=info_loja.get("rg_representante", ""))
                
                st.markdown("##### Financeiro e Faturamento")
                f_banco = st.text_input("Dados Bancários (Banco, Agência, Conta)", value=info_loja.get("dados_bancarios", ""))
                f_pix = st.text_input("Chave PIX", value=info_loja.get("chave_pix", ""))
                f_segmento = st.text_input("Segmento Comercial da Empresa", value=info_loja.get("segmento",
 dados["categorias"][cat_id]["nome"]))
                
                salvar_cadastro = st.form_submit_button(label="💾 Salvar Ficha Cadastral")
                
                if salvar_cadastro:
                    info_loja["nome_fantasia"] = f_fantasia
                    info_loja["razao_social"] = f_razao
                    info_loja["cnpj"] = f_cnpj
                    info_loja["inscricao_state"] = f_ie
                    info_loja["inscricao_municipal"] = f_im
                    info_loja["endereco_completo"] = f_end
                    info_loja["telefone"] = f_tel
                    info_loja["whatsapp"] = f_whatsapp
                    info_loja["email"] = f_email
                    info_loja["nome_proprietario"] = f_proprietario
                    info_loja["cpf_representante"] = f_cpf_rep
                    info_loja["rg_representante"] = f_rg_rep
                    info_loja["dados_bancarios"] = f_banco
                    info_loja["chave_pix"] = f_pix
                    info_loja["segmento"] = f_segmento
                    
                    if salvar_dados_github(dados, sha):
                        st.success("Ficha cadastral salva com sucesso!")
                        st.rerun()
                        
        with tab_contrato:
            st.subheader("Contrato de Parceria GLOBAL")
            
            doc_contrato = st.file_uploader("Anexar novo contrato (Formatos aceitos: PDF)", type=["pdf"], key=f"pdf_{loja_id}")
            
            if doc_contrato is not None:
                st.session_state.contrato_temp_cache = doc_contrato.getvalue()
                st.info("Documento carregado na memória temporária.")
                if st.button("🔒 Confirmar e Vincular Contrato", key=f"btn_salvar_pdf_{loja_id}"):
                    bytes_pdf = st.session_state.contrato_temp_cache
                    info_loja["contrato_b64"] = base64.b64encode(bytes_pdf).decode("utf-8")
                    st.session_state.contrato_temp_cache = None
                    if salvar_dados_github(dados, sha):
                        st.success("Contrato oficial anexado com sucesso!")
                        st.rerun()
            
            st.write("---")
            if info_loja.get("contrato_b64"):
                st.success("📝 Há um contrato assinado e ativo para esta empresa no banco de dados.")
                
                pdf_bytes_down = base64.b64decode(info_loja["contrato_b64"])
                st.download_button(
                    label="📥 Baixar e Visualizar Contrato Vinculado (PDF)",
                    data=pdf_bytes_down,
                    file_name=f"contrato_global_{loja_id.replace('#','')}.pdf",
                    mime="application/pdf"
                )
                
                if st.button("🗑️ Remover Contrato Vigente", key=f"del_pdf_{loja_id}"):
                    info_loja["contrato_b64"] = ""
                    salvar_dados_github(dados, sha)
                    st.success("Contrato excluído!")
                    st.rerun()
            else:
                st.warning("Nenhum contrato de parceria digitalizado anexado até o momento.")
