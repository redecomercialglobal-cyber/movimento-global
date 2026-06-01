import streamlit as st
import json
from github import Github
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GLOBAL", page_icon="🌐", layout="centered")

# --- ESTILIZAÇÃO CUSTOMIZADA E MÁSCARAS EM TEMPO REAL (JS/CSS) ---
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
    
    <script>
    // Injeção de comportamento de máscara em tempo real nos inputs do Streamlit
    const MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
    const observer = new MutationObserver(function(mutations, instance) {
        // 1. Máscara de CPF no Login e no campo do Cliente
        const cpfInputs = document.querySelectorAll('input[aria-label="Identificação (CPF)"], input[aria-label="CPF do Cliente"]');
        cpfInputs.forEach(input => {
            if (!input.dataset.maskApplied) {
                input.addEventListener('input', function(e) {
                    let value = e.target.value;
                    // Se começar com @ ou #, permite tudo (Passo dos códigos especiais)
                    if (value.startsWith('@') || value.startsWith('#')) {
                        return;
                    }
                    // Caso contrário, limpa tudo que não for número
                    value = value.replace(/\D/g, "");
                    // Aplica a máscara de CPF dinamicamente
                    if (value.length > 9) {
                        value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
                    } else if (value.length > 6) {
                        value = value.replace(/^(\d{3})(\d{3})(\d{1,3})$/, "$1.$2.$3");
                    } else if (value.length > 3) {
                        value = value.replace(/^(\d{3})(\d{1,3})$/, "$1.$2");
                    }
                    e.target.value = value;
                    // Dispara o evento para o Streamlit capturar a mudança interna
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
                input.dataset.maskApplied = true;
            }
        });

        // 2. Máscara Monetária com divisão milenar no Valor da Venda
        const moneyInputs = document.querySelectorAll('input[aria-label="Valor da Venda (R$)"]');
        moneyInputs.forEach(input => {
            if (!input.dataset.maskApplied) {
                input.addEventListener('input', function(e) {
                    let value = e.target.value.replace(/\D/g, "");
                    if (value === "") value = "0";
                    // Transforma em valor numérico centesimal
                    const options = { minimumFractionDigits: 2, maximumFractionDigits: 2 };
                    const result = (parseFloat(value) / 100).toLocaleString('pt-BR', options);
                    e.target.value = result;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
                input.dataset.maskApplied = true;
            }
        });
    });

    // Vincula o observador ao documento
    observer.observe(document, {
        childList: true,
        subtree: true
    });
    </script>
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

# --- CONTROLE DE SESSÃO DO USUÁRIO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = None
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

dados, sha = carregar_dados_github()
if not isinstance(dados, dict):
    dados = {"lojistas": ["#loja123"], "clientes": {}}

if "lojistas" not in dados:
    dados["lojistas"] = ["#loja123"]
if "clientes" not in dados:
    dados["clientes"] = {}

# --- FUNÇÃO AUXILIAR DE LIMPEZA/FORMATAÇÃO DO LADO DO SERVIDOR ---
def limpar_e_formatar_cpf(texto):
    numeros = "".join([c for c in texto if c.isdigit()])
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return None

# --- TELA DE LOGIN / IDENTIFICAÇÃO ---
if not st.session_state.logado:
    st.markdown('<div class="main-title">GLOBAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Um movimento que une lojas e clientes</div>', unsafe_allow_html=True)
    
    id_cru = st.text_input("Identificação (CPF)", key="input_login_usuario")
    id_limpo = id_cru.strip()

    if st.button("Entrar", key="btn_entrar_login"):
        if id_limpo:
            # 1. Validação do Gestor Global
            if id_limpo.startswith("@"):
                if id_limpo == "@Romanos0828":
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "gestor"
                    st.session_state.usuario_atual = "Gestor Global"
                    st.rerun()
                else:
                    st.error("Acesso negado.")
            
            # 2. Validação dos Lojistas Cadastrados
            elif id_limpo.startswith("#"):
                if id_limpo in dados["lojistas"]:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "lojista"
                    st.session_state.usuario_atual = id_limpo
                    st.rerun()
                else:
                    st.error("Acesso negado.")
            
            # 3. Validação do Cliente (CPF)
            else:
                cpf_validado = limpar_e_formatar_cpf(id_limpo)
                if cpf_validado:
                    st.session_state.logado = True
                    st.session_state.tipo_usuario = "cliente"
                    st.session_state.usuario_atual = cpf_validado
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
    
    # Campo tratado textualmente para suportar a máscara dinâmica em tempo real via JS
    valor_venda_raw = st.text_input("Valor da Venda (R$)", value="0,00")
    cpf_cliente_input = st.text_input("CPF do Cliente", max_chars=14)
    
    if st.button("Enviar Pontuação", key="btn_enviar_pontos_lojista"):
        # Converte o valor formatado "1.250,50" para float puro 1250.50
        try:
            limpo_valor = valor_venda_raw.replace(".", "").replace(",", ".")
            valor_venda = float(limpo_valor)
        except ValueError:
            valor_venda = 0.0

        cpf_formatado = limpar_e_formatar_cpf(cpf_cliente_input)
        
        if not cpf_formatado:
            st.error("Insira um CPF válido com 11 dígitos para computar os pontos.")
        elif valor_venda <= 0:
            st.error("O valor da venda precisa ser maior que R$ 0,00.")
        else:
            pontos_novos = int(valor_venda)
            
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
        equivalenca_dinheiro = total_pontos_sistema * 0.10
    except Exception:
        total_pontos_sistema = 0
        equivalenca_dinheiro = 0.0

    col1, col2 = st.columns(2)
    col1.metric("Total de Pontos Emitidos (Global)", f"{total_pontos_sistema} pts")
    col2.metric("Equivalência Financeira Estimada", f"R$ {equivalenca_dinheiro:,.2f}")
    
    st.write("---")
    st.subheader("Gerenciar Lojistas Autoritários")
    
    novo_lojista_code = st.text_input("Cadastrar Código de Novo Lojista (Deve iniciar com #)", placeholder="#exemplo123")
    if st.button("Criar Novo Lojista"):
        codigo_limpo = novo_lojista_code.strip()
        if codigo_limpo.startswith("#") and len(codigo_limpo) > 1:
            if codigo_limpo not in dados["lojistas"]:
                dados["lojistas"].append(codigo_limpo)
                if salvar_dados_github(dados, sha):
                    st.success(f"Lojista {codigo_limpo} cadastrado com sucesso!")
                    st.rerun()
            else:
                st.warning("Este código de lojista já está cadastrado.")
        else:
            st.error("O código de lojista obrigatoriamente deve começar com '#' seguido do identificador.")

    st.write("**Lojistas Ativos no Sistema:**")
    for idx_loj, loj in enumerate(dados["lojistas"]):
        col_l_nome, col_l_btn = st.columns([3, 1])
        col_l_nome.write(f"🏢 Código: `{loj}`")
        if col_l_btn.button("Remover Lojista", key=f"rem_loj_{idx_loj}"):
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
