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
    Você é um Analista de Processos de Negócio Sênior e Engenheiro de Requisitos, especialista em BPMN 2.0.
    Sua tarefa é analisar a transcrição de uma reunião e gerar um objeto JSON com duas chaves: "bpmn_xml" e "specification_content". AMBAS AS CHAVES SÃO IGUALMENTE IMPORTANTES E DEVEM SER COMPLETAMENTE PREENCHIDAS.

    **--- TRANSCRIÇÃO E DOCUMENTOS PARA ANÁLISE ---**
    Cliente: '{client_info.get('nome', 'N/A')}'
    Contexto Adicional: {context_docs}
    Transcrição da Reunião: {full_transcription}
    **--- FIM DA ANÁLISE ---**

    Agora, gere o objeto JSON com base na análise acima, seguindo as regras abaixo:

    1.  **"bpmn_xml" (string):**
        * Crie um diagrama de processo de negócio em formato XML padrão BPMN 2.0. O XML deve ser completo, sintaticamente correto e válido.
        * **Lógica do Processo:** Modele o fluxo completo com StartEvent, Tasks (userTask, serviceTask), Gateways para decisões e EndEvents.
        * **Conexões:** Use 'sequenceFlow' para conectar TODOS os elementos sequencialmente.
        * **Layout Visual:** É OBRIGATÓRIO gerar a seção '<bpmndi:BPMNDiagram>' completa, com um '<bpmndi:BPMNPlane>', e incluir um '<bpmndi:BPMNShape>' (com coordenadas em '<dc:Bounds>') para cada tarefa/evento, e um '<bpmndi:BPMNEdge>' (com '<di:waypoint>') para cada conexão.
        * **Lanes:** Use '<bpmn:laneSet>' para agrupar tarefas por responsável (ex: Sistema, Financeiro).

    2.  **"specification_content" (objeto JSON):**
        * Preencha TODAS as chaves a seguir com base na transcrição. NÃO deixe nenhum campo com placeholder.
        * **"system_name"**: (string) O nome do sistema ou projeto.
        * **"document_name"**: (string) Um título para o documento.
        * **"importance"**: (string) A importância do projeto.
        * **"project_code"**: (string) Use "A DEFINIR" se não mencionado.
        * **"document_objective"**: (string) O objetivo do processo.
        * **"user_stories"**: (string) Uma string com MÚLTIPLAS LINHAS no formato "Como um [ator], eu quero [ação] para que [resultado].".
        * **"user_flow"**: (string) A jornada do usuário em um parágrafo.
        * **"user_profiles"**: (string) Os perfis/sistemas envolvidos.
        * **"prototype_link"**: (string) Use "N/A".
        * **"functionalities"**: (array de objetos) Detalhe CADA funcionalidade discutida.

    Retorne APENAS o objeto JSON completo.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sua tarefa é gerar um objeto JSON contendo um XML de BPMN sintaticamente válido e uma Especificação Funcional detalhada. Ambas as partes são obrigatórias."},
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