# src/services/openai_service.py

import openai
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET # Importa a biblioteca de validação XML
import re

load_dotenv()

def clean_xml_string(xml_string):
    """
    Remove caracteres de controle inválidos de uma string XML.
    """
    # Regex para encontrar caracteres de controle inválidos em XML (exceto tab, newline, carriage return)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', xml_string)

def generate_business_analysis(api_key: str, full_transcription: str, client_info: dict, context_docs: str = "") -> dict:
    """
    Analisa a transcrição e os documentos para gerar um diagrama BPMN em XML
    e o conteúdo para a Especificação Funcional.
    """
    openai.api_key = api_key

    prompt_master = f"""
    **PERSONA:**
    Você é um Analista de Negócios e Engenheiro de Requisitos Sênior, com mais de 15 anos de experiência em projetos complexos de software. Sua especialidade é traduzir conversas de negócio em documentação técnica impecável (BPMN 2.0 e Especificações Funcionais). Você é extremamente analítico, crítico e tem um olhar apurado para identificar processos, regras de negócio, exceções e requisitos implícitos que não foram ditos claramente na reunião. Seu trabalho é a principal fonte de verdade para as equipes de desenvolvimento e produto.

    **TAREFA CRÍTICA:**
    Analise a transcrição da reunião e os documentos de contexto abaixo. Sua missão é extrair CADA detalhe relevante e gerar um objeto JSON contendo duas chaves principais: "bpmn_xml" e "specification_content". A qualidade e o detalhamento de ambas as chaves são cruciais para o sucesso do projeto. Falhar em detalhar qualquer uma delas é inaceitável.

    **--- DADOS BRUTOS PARA ANÁLISE ---**
    - **Cliente:** '{client_info.get('nome', 'Não informado')}'
    - **Contexto Adicional (documentos, etc.):** {context_docs}
    - **Transcrição da Reunião:** {full_transcription}
    **--- FIM DOS DADOS BRUTOS ---**

    **REGRAS E DIRETRIZES PARA A GERAÇÃO DO JSON:**

    **1. CHAVE: "bpmn_xml" (Formato: string XML)**
       - **Qualidade do Modelo:** Crie um diagrama BPMN 2.0 em XML que seja completo, válido e represente fielmente o processo de negócio discutido. O modelo deve ser lógico e detalhado.
       - **Elementos Obrigatórios:**
         - **Eventos:** Use `startEvent`, `endEvent` e, se necessário, `intermediateCatchEvent` (ex: para esperas).
         - **Tarefas:** Detalhe as tarefas usando `userTask` (ação de um usuário), `serviceTask` (processo automático do sistema) e `manualTask` (tarefa fora do sistema). Nomeie cada tarefa de forma clara e inequívoca (ex: "Sistema valida disponibilidade de estoque" em vez de "Verifica estoque").
         - **Gateways:** Pense criticamente. Onde estão as decisões? Use `exclusiveGateway` para decisões "SE/SENÃO" (ex: "Estoque disponível?") e `parallelGateway` para atividades que ocorrem ao mesmo tempo.
         - **Fluxo:** Conecte TODOS os elementos com `sequenceFlow`. O diagrama deve ter um fluxo contínuo do início ao fim.
         - **Lanes:** Organize o diagrama em `lanes` dentro de um `laneSet` para representar os diferentes atores (ex: Cliente, Portal, Sistema Zion, Operador de Armazém).
       - **Visual (BPMNDiagram):** É OBRIGATÓRIO gerar a seção `<bpmndi:BPMNDiagram>` completa, com `<bpmndi:BPMNPlane>`, `<bpmndi:BPMNShape>` para cada elemento (com coordenadas em `<dc:Bounds>`) e `<bpmndi:BPMNEdge>` para cada `sequenceFlow` (com waypoints).

    **2. CHAVE: "specification_content" (Formato: objeto JSON)**
       - **Nível de Detalhe:** Preencha TODAS as chaves a seguir com o máximo de detalhes extraídos da conversa. Respostas genéricas como "N/A", "A definir" ou descrições de uma linha são inaceitáveis. Inferir detalhes com base no contexto é parte da sua função como analista sênior.
       - **Estrutura da Especificação:**
         - **"system_name" (string):** O nome exato do sistema ou projeto.
         - **"document_name" (string):** Um título formal para o documento (ex: "Especificação Funcional - Módulo de Agendamento").
         - **"importance" (string):** Justifique a importância do projeto com base nos benefícios de negócio mencionados (ex: "Crucial para reduzir o tempo de processamento manual em 40% e eliminar erros de digitação, impactando diretamente a satisfação do cliente.").
         - **"project_code" (string):** Use "A DEFINIR" apenas se for impossível inferir.
         - **"document_objective" (string):** Descreva o objetivo do processo de negócio em um parágrafo detalhado, explicando o problema a ser resolvido e o estado futuro desejado.
         - **"user_stories" (string):** Crie histórias de usuário detalhadas e em várias linhas, seguindo o formato "Como um [ATOR/PERFIL], eu quero [AÇÃO/FUNCIONALIDADE] para que [BENEFÍCIO/RESULTADO].". Gere pelo menos 3 histórias, cobrindo diferentes perspectivas.
         - **"user_flow" (string):** Descreva a jornada completa do usuário em um parágrafo rico, detalhando cada passo e interação com o sistema.
         - **"user_profiles" (string):** Liste os perfis de usuários ou sistemas envolvidos (atores), descrevendo brevemente a responsabilidade de cada um.
         - **"prototype_link" (string):** Use "N/A" se não mencionado.
         - **"functionalities" (array de objetos):** Esta é a seção mais crítica. Para CADA funcionalidade identificada, crie um objeto com a seguinte estrutura:
           - **"title" (string):** Um nome claro e descritivo (ex: "Agendamento de Coleta com Validação de Estoque"). NUNCA use "Funcionalidade sem título".
           - **"description" (string):** Uma descrição detalhada do que a funcionalidade faz, para quem e por quê.
           - **"trigger" (string):** O que inicia esta funcionalidade? (ex: "Usuário clica no botão 'Agendar Coleta' na tela de consulta de estoque.").
           - **"integrations" (string):** Com quais outros sistemas ou módulos esta funcionalidade se comunica? (ex: "Sistema Zion para consulta de estoque em tempo real via API REST.").
           - **"screen_links" (string):** A quais telas ou componentes de interface esta funcionalidade está associada? (ex: "Tela de Agendamento (F01), Modal de Confirmação (M02)").
           - **"fields" (string):** Quais campos de dados são relevantes? (ex: "ID do Cliente, SKU do Produto, Quantidade, Data Desejada, Endereço de Coleta").
           - **"functional_requirements" (array de strings):** Liste os requisitos funcionais como regras claras e testáveis (ex: ["O sistema deve validar se a quantidade solicitada é menor ou igual ao estoque disponível.", "O sistema deve exibir um erro se a data de agendamento for anterior à data atual.", "Após a confirmação, o sistema deve enviar um e-mail de confirmação para o cliente."]).

    **SAÍDA FINAL:**
    Retorne APENAS o objeto JSON completo e bem formado, sem nenhum texto ou comentário adicional.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um Analista de Negócios Sênior que gera documentação técnica (BPMN e EF) extremamente detalhada a partir de transcrições. Sua saída deve ser um único objeto JSON."},
                {"role": "user", "content": prompt_master}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result_data = json.loads(response.choices[0].message.content)
        
        # --- ETAPA DE VALIDAÇÃO E LIMPEZA DO XML ---
        if 'bpmn_xml' in result_data and result_data['bpmn_xml']:
            cleaned_xml = clean_xml_string(result_data['bpmn_xml'])
            try:
                # Tenta analisar o XML para verificar se é bem formado
                ET.fromstring(cleaned_xml)
                result_data['bpmn_xml'] = cleaned_xml
            except ET.ParseError as e:
                print(f"AVISO: A IA gerou um XML inválido. Erro: {e}. O XML será retornado como está, mas pode não ser importável.")
                # Mantém o XML original (limpo) mesmo que inválido, para depuração
                result_data['bpmn_xml'] = cleaned_xml

        return result_data
        
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI ou processar a resposta: {e}")
        error_content = f"Ocorreu um erro ao gerar a análise: {e}"
        return {
            "bpmn_xml": f"",
            "specification_content": {"system_name": error_content, "document_objective": str(e)}
        }

def transcrever_audio(api_key: str, audio_file_path: str) -> str:
    openai.api_key = api_key
    print(f"-> [🎤] Transcrevendo áudio: {os.path.basename(audio_file_path)}...")
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = openai.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file
            )
        print("-> [✅] Áudio transcrito com sucesso.")
        return transcription.text
    except Exception as e:
        print(f"❌ ERRO ao transcrever o áudio {os.path.basename(audio_file_path)}: {e}")
        return f"Erro ao processar o áudio {os.path.basename(audio_file_path)}."