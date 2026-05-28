import streamlit as st
import json
import os
from github import Github  # Você precisará da biblioteca PyGithub

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="GLOBAL - Movimento de Fidelidade", page_icon="🔵", layout="centered")

# Visual limpo padrão do GLOBAL
st.markdown("""
    <style>
    .main h1 { color: #2563eb; text-align: center; margin-bottom: 5px; }
    .subtitle { text-align: center; color: #64748b; font-size: 0.95rem; font-style: italic; margin-bottom: 25px; }
    div.stButton > button { width: 100%; background-color: #2563eb; color: white; border-radius: 6px; padding: 10px; font-weight: bold; }
    div.stButton > button:hover { background-color: #1d4ed8; border-color: #1d4ed8; }
    .points-display { font-size: 3.5rem; font-weight: bold; text-align: center; color: #10b981; margin: 15px 0; }
    </style>
""", unsafe_html=True)

# 2. CONEXÃO DIRETA COM O GITHUB (BANCO DE DADOS JSON)
# O Streamlit pegará o Token e o nome do repositório das configurações secretas que faremos no Passo 3
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] # Exemplo: "seu-usuario/movimento-global"
except:
    st.error("Configure os Segredos (Secrets) no painel do Streamlit antes de continuar.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
FILE_PATH = "clientes.json"

# Função para ler os dados do banco de dados direto do GitHub
def ler_dados_github():
    try:
        file_content = repo.get_contents(FILE_PATH)
        dados = json.loads(file_content.decoded_content.decode())
        return dados, file_content.sha
    except:
        # Se o arquivo não existir ainda no GitHub, cria um modelo inicial básico
        dados_iniciais = {
            "merchantCode": "#loja123",
            "clients": {
                "(11) 99999-9999": 250,
                "(11) 98888-8888": 100
            }
        }
        return dados_iniciais, None

# Função para salvar os dados atualizados fazendo um Commit/Push automático para o GitHub
def salvar_dados_github(novos_dados, sha):
    conteudo_json = json.dumps(novos_dados, indent=4, ensure_ascii=False)
    if sha:
        repo.update_file(FILE_PATH, "Atualização de pontos - GLOBAL", conteudo_json, sha)
    else:
        repo.create_file(FILE_PATH, "Inicialização do banco de dados - GLOBAL", conteudo_json)

# Carrega os dados mais recentes do GitHub
dados, file_sha = ler_dados_github()

# 3. CONTROLE DE SESSÃO
if "tela" not in st.session_state:
    st.session_state.tela = "login"
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

def formatar_telefone(tel):
    digitos = ''.join(filter(str.isdigit, tel))[:11]
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    return tel

# --- TELA DE LOGIN ---
if st.session_state.tela == "login":
    st.markdown("<h1>GLOBAL</h1>", unsafe_html=True)
    st.markdown("<div class='subtitle'>Um movimento que une lojas e clientes</div>", unsafe_html=True)
    
    login_input = st.text_input("Identificação (Telefone)", placeholder="(00) 00000-0000").strip()
    
    if st.button("Entrar"):
        if login_input == "@Romanos0828":
            st.session_state.tela = "gestor"
            st.rerun()
        elif login_input == dados["merchantCode"]:
            st.session_state.tela = "lojista"
            st.rerun()
        else:
            tel_formatado = formatar_telefone(login_input)
            if len(''.join(filter(str.isdigit, tel_formatado))) == 11:
                st.session_state.usuario_logado = tel_formatado
                st.session_state.tela = "cliente"
                st.rerun()
            else:
                st.error("Identificação inválida. Digite seu telefone com DDD ou códigos de acesso.")

# --- TELA DO CLIENTE ---
elif st.session_state.tela == "cliente":
    st.markdown("<h1>GLOBAL</h1>", unsafe_html=True)
    st.markdown("<div class='subtitle'>Sua Loja Parceira</div>", unsafe_html=True)
    
    tel = st.session_state.usuario_logado
    pontos = dados["clients"].get(tel, 0)
    
    st.markdown("<p style='text-align: center;'>Olá! Seu saldo atual de pontos é:</p>", unsafe_html=True)
    st.markdown(f"<div class='points-display'>{pontos}</div>", unsafe_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>Registrado sob o telefone: {tel}</p>", unsafe_html=True)
    
    if st.button("Sair"):
        st.session_state.tela = "login"
        st.rerun()

# --- TELA DO LOJISTA ---
elif st.session_state.tela == "lojista":
    st.markdown("<h1>Painel do Lojista</h1>", unsafe_html=True)
    st.markdown("<div class='subtitle'>Registrar Vendas no Movimento GLOBAL</div>", unsafe_html=True)
    
    valor_venda = st.number_input("Valor da Venda (R$)", min_value=0.0, step=0.50, format="%.2f")
    tel_cliente = st.text_input("Telefone do Cliente", placeholder="(00) 00000-0000")
    
    if st.button("Enviar Pontos"):
        tel_formatado = formatar_telefone(tel_cliente)
        if len(''.join(filter(str.isdigit, tel_formatado))) != 11:
            st.error("Por favor, insira um telefone válido com DDD.")
        elif valor_venda <= 0:
            st.error("Insira um valor de venda maior que R$ 0,00.")
        else:
            novos_pontos = int(valor_venda * 10)
            
            # Altera os dados locais e sincroniza com o GitHub
            if tel_formatado in dados["clients"]:
                dados["clients"][tel_formatado] += novos_pontos
            else:
                dados["clients"][tel_formatado] = novos_pontos
                
            salvar_dados_github(dados, file_sha)
            st.success(f"Sucesso! Creditados {novos_pontos} pontos para o cliente {tel_formatado} no GitHub!")
            st.balloons()

    if st.button("Sair"):
        st.session_state.tela = "login"
        st.rerun()

# --- TELA DO GESTOR ---
elif st.session_state.tela == "gestor":
    st.markdown("<h1>Painel do Gestor (GLOBAL)</h1>", unsafe_html=True)
    
    with st.expander("⚙️ Configuração do Lojista", expanded=False):
        novo_codigo = st.text_input("Código de Acesso do Lojista:", value=dados["merchantCode"])
        if st.button("Salvar Novo Código"):
            if not novo_codigo.startswith("#"):
                st.error("Por segurança, o código precisa começar com '#'!")
            else:
                dados["merchantCode"] = novo_codigo
                salvar_dados_github(dados, file_sha)
                st.success("Código atualizado com sucesso!")
                st.rerun()

    st.markdown("### Métricas de Crescimento Real")
    total_pontos = sum(dados["clients"].values())
    equivalencia_dinheiro = total_pontos / 10
    
    col1, col2 = st.columns(2)
    col1.metric("Total de Pontos", f"{total_pontos} pts")
    col2.metric("Equivalência em Dinheiro", f"R$ {equivalencia_dinheiro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("### Lista de Clientes e Pontuações")
    if not dados["clients"]:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        # Cria cópia para iteração segura enquanto deleta itens
        lista_clientes = list(dados["clients"].items())
        for phone, points in lista_clientes:
            c_col1, c_col2, c_col3 = st.columns([2, 1, 1])
            c_col1.write(phone)
            c_col2.write(f"{points} pts")
            
            if c_col3.button("Excluir", key=f"del_{phone}"):
                st.warning(f"Tem certeza que deseja deletar {phone}?")
                if st.button("Sim, confirmar exclusão", key=f"conf_{phone}"):
                    del dados["clients"][phone]
                    salvar_dados_github(dados, file_sha)
                    st.success("Cliente removido!")
                    st.rerun()
                    
        st.markdown("---")
        if st.button("🚨 Zerar Todos os Clientes"):
            st.error("Isso apagará TODOS os clientes do banco de dados do GitHub!")
            if st.button("CONFIRMAR RESET TOTAL"):
                dados["clients"] = {}
                salvar_dados_github(dados, file_sha)
                st.success("Banco de dados resetado com sucesso!")
                st.rerun()

    if st.button("Sair"):
        st.session_state.tela = "login"
        st.rerun()