# src/services/openai_service.py

import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

def generate_business_analysis(api_key: str, full_transcription: str, client_info: dict, context_docs: str = "") -> dict:
    """
    Analisa a transcrição e os documentos para gerar um Mapa Mental em Markdown
    e o conteúdo para a Especificação Funcional detalhada.
    """
    openai.api_key = api_key

    prompt_master = f"""
    Você é um Analista de Negócios Sênior especialista em engenharia de requisitos de software.
    Sua tarefa é analisar a transcrição de uma reunião e os documentos de apoio para o cliente '{client_info.get('nome', 'N/A')}' e gerar um objeto JSON estruturado para documentação.

    Gere um objeto JSON com duas chaves principais: "mind_map_markdown" e "specification_content".

    1.  **"mind_map_markdown" (string):**
        * Crie um mapa mental hierárquico em formato Markdown, capturando os pilares do projeto (Objetivo, Módulos, Atores, etc.).

    2.  **"specification_content" (objeto JSON):**
        * Extraia informações para preencher as seguintes chaves, baseando-se no template de Especificação Funcional:
        - "system_name": Um nome para o sistema ou projeto.
        - "document_name": Um título para este documento (ex: "Cadastro de Clientes").
        - "importance": A importância do projeto (Alta, Média, Baixa).
        - "project_code": Um código de referência, se mencionado. Caso contrário, use "A DEFINIR".
        - [cite_start]"document_objective": (string) O objetivo principal deste documento e do projeto. [cite: 61, 68, 69]
        - [cite_start]"user_stories": (string) Descreva as principais histórias de usuário no formato "Como [ator], eu quero [ação] para [resultado]". [cite: 62, 70, 71]
        - [cite_start]"user_flow": (string) Descreva textualmente a jornada principal do usuário. [cite: 63, 72, 73]
        - [cite_start]"user_profiles": (string) Liste os perfis de usuários ou atores envolvidos. [cite: 64, 74, 75]
        - "prototype_link": (string) Se um link de protótipo for mencionado, coloque-o aqui. [cite_start]Caso contrário, "N/A". [cite: 77]
        - "functionalities": (array de objetos) Liste TODAS as funcionalidades discutidas. Cada objeto no array deve ter a seguinte estrutura:
            {{
                "title": (string) "Nome da Funcionalidade",
                [cite_start]"description": (string) "Breve descrição do que a funcionalidade faz.", [cite: 81]
                "trigger": (string) "Como o usuário acessa ou aciona esta funcionalidade.",
                "integrations": (string) "Sistemas ou serviços com os quais esta funcionalidade se integra.",
                "screen_links": (string) "Outras telas ou partes do sistema com as quais esta se conecta.",
                "fields": (string) "Liste os campos do formulário, indicando se são (obrigatórios) ou (opcionais).",
                [cite_start]"functional_requirements": (array de strings) "Liste os requisitos funcionais específicos (RFs) desta funcionalidade. Ex: 'RF01: O sistema deve validar o formato do email.'" [cite: 83]
            }}

    **--- DOCUMENTOS DE APOIO E TRANSCRIÇÃO ---**
    {context_docs}
    {full_transcription}
    **--- FIM DOS DADOS ---**

    Retorne APENAS o objeto JSON completo.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um Analista de Negócios Sênior. Sua saída deve ser um objeto JSON estruturado."},
                {"role": "user", "content": prompt_master}
            ],
            response_format={"type": "json_object"},
            temperature=0.15,
        )
        result_json = json.loads(response.choices[0].message.content)
        return result_json
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI para análise de negócios: {e}")
        error_content = f"Ocorreu um erro ao gerar a análise: {e}"
        return {
            "mind_map_markdown": "# Erro\n- Não foi possível gerar o mapa mental.",
            "specification_content": {"system_name": error_content}
        }

def transcrever_audio(api_key: str, audio_file_path: str) -> str:
    """
    Transcreve um arquivo de áudio usando o modelo Whisper-1 da OpenAI.
    """
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