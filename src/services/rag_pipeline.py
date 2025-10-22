from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from src.config import LLM_MODEL

# --- FUNÇÃO 1: GERAÇÃO INICIAL (EXISTENTE E REFINADA) ---
def generate_proposal_from_template(
    briefing_content: str,
    proposal_template: str,
    vector_store: Chroma
) -> str:
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.15, streaming=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": 12})

    # --- PROMPT AVANÇADO COM LÓGICA DE MVP ---
    prompt_template = """
    Você é um Consultor de Soluções Sênior e Estrategista de Produto. Sua especialidade é transformar briefings de clientes em propostas técnicas completas, que não apenas detalham o projeto inteiro, mas também propõem um MVP (Mínimo Produto Viável) inteligente para gerar valor rápido.

    **PROCESSO DE RACIOCÍNIO OBRIGATÓRIO (SIGA CADA PASSO):**

    **PASSO 1 a 4 (Análise do Projeto Completo):**
    -   Primeiro, execute toda a análise para o **PROJETO COMPLETO**: Defina os Módulos e Funcionalidades, selecione as Fases do projeto, crie a Matriz de Horas e defina o Cronograma total, como instruído anteriormente.

    **PASSO 5: DEFINIÇÃO DO MVP (PENSAMENTO ESTRATÉGICO)**
    -   Agora, com a visão completa do projeto, analise todos os módulos e funcionalidades que você listou.
    -   Identifique a combinação de funcionalidades que entrega o **maior valor de negócio para o cliente no menor tempo possível**.
    -   Seu MVP deve ser: **Usável** (resolve um problema real do usuário), **Viável** (pode ser construído rapidamente, ex: em 1-2 meses) e gerar um **alto valor percebido (Efeito UAU)**.
    -   Selecione um ou dois módulos, ou até mesmo funcionalidades específicas de módulos diferentes, que atendam a esses critérios.

    **PASSO 6: PREENCHIMENTO DO TEMPLATE**
    -   Finalmente, use todas as informações que você estruturou para preencher o TEMPLATE DE PROPOSTA.
    -   Preencha as seções 1 a 5 com as informações do **projeto completo**.
    -   Use sua análise do Passo 5 para preencher a **seção 6 (SUGESTÃO DE MVP)** de forma detalhada:
        -   Liste as funcionalidades do MVP.
        -   Justifique por que essa entrega gerará um impacto positivo imediato.
        -   Calcule e apresente a estimativa de horas e o cronograma **apenas para o MVP**.
        -   Descreva brevemente como os outros módulos seriam adicionados em fases futuras.

    ---
    BRIEFING DO CLIENTE:
    {briefing}
    ---
    CONTEXTO DE PROJETOS ANTERIORES (SUA BASE DE CONHECIMENTO):
    {context}
    ---
    TEMPLATE DE PROPOSTA (SUA ESTRUTURA DE SAÍDA):
    {template}
    """
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = ({"context": retriever, "briefing": RunnablePassthrough(), "template": lambda x: proposal_template} | prompt | llm | StrOutputParser())
    return chain.invoke(briefing_content)


# --- FUNÇÃO 2: REFINAMENTO DA PROPOSTA (EXISTENTE) ---
def refine_proposal(
    user_request: str,
    original_briefing: str,
    previous_proposal: str,
    vector_store: Chroma
) -> str:
    # Esta função se beneficiará automaticamente da nova estrutura, pois refinará o texto já gerado com a seção de MVP.
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.25)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    prompt_template = """
    Você é um assistente especialista em refinar propostas técnicas. Sua tarefa é reescrever e ajustar uma proposta existente com base no pedido do usuário.
    Sua missão é gerar uma **VERSÃO NOVA E COMPLETA** da proposta que incorpore o ajuste solicitado de forma coesa e profissional. Não responda ao usuário em um tom de conversa, apenas reescreva a proposta inteira com a alteração aplicada.
    ---
    BRIEFING ORIGINAL:{briefing}
    ---
    VERSÃO ANTERIOR DA PROPOSTA:{previous_proposal}
    ---
    CONTEXTO ADICIONAL (RAG):{context}
    ---
    PEDIDO DE AJUSTE DO USUÁRIO:{request}
    ---
    PROPOSTA NOVA E REFINADA:
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = ({"briefing": lambda x: original_briefing, "previous_proposal": lambda x: previous_proposal, "context": retriever, "request": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    return chain.invoke(user_request)