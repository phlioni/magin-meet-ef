# src/core/orchestrator.py

import os
from datetime import datetime
from dotenv import load_dotenv
from src.services import openai_service
from src.services.openai_service import transcrever_audio
from src.services.database_operations import get_text_from_file
from src.config import TEMPLATES_PATH

load_dotenv()

def run_analysis_and_generate_artifacts(transcription: str, info_cliente: dict, doc_paths: list, progress_callback=None) -> tuple[str, dict]:
    """
    Etapa 1: Orquestra a análise da IA para gerar o mapa mental e o conteúdo da especificação.
    """
    def report_progress(message):
        if progress_callback: progress_callback(message)

    context_docs = ""
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        error_msg = "ERRO: Chave da API da OpenAI não encontrada."
        report_progress(f"-> [❌] {error_msg}")
        return error_msg, {}

    if doc_paths:
        report_progress(f"-> [⚙️] Processando {len(doc_paths)} documento(s) de apoio...")
        AUDIO_EXTENSIONS = ['.ogg', '.mp3', '.m4a', '.wav', '.mp4', '.mpeg']

        for path in doc_paths:
            try:
                _, file_extension = os.path.splitext(path)
                if file_extension.lower() in AUDIO_EXTENSIONS:
                    context_docs += f"--- TRANSCRIÇÃO DO ÁUDIO: {os.path.basename(path)} ---\n"
                    context_docs += transcrever_audio(openai_api_key, path)
                else:
                    context_docs += f"--- CONTEÚDO DO DOCUMENTO: {os.path.basename(path)} ---\n"
                    context_docs += get_text_from_file(path)
                context_docs += "\n\n"
            except Exception as e:
                report_progress(f"-> [⚠️] Falha ao processar o arquivo {path}: {e}")

    report_progress("-> [🤖] IA está analisando a reunião. Isso pode levar um momento...")
    analysis_result = openai_service.generate_business_analysis(
        api_key=openai_api_key,
        full_transcription=transcription,
        client_info=info_cliente,
        context_docs=context_docs
    )
    report_progress("-> [✅] Análise da IA concluída.")

    mind_map_md = analysis_result.get("mind_map_markdown", "# Erro\n- Análise falhou.")
    spec_content = analysis_result.get("specification_content", {})

    return mind_map_md, spec_content

def generate_specification_document(spec_content: dict, client_name: str) -> str:
    """
    Etapa 2: Preenche o template da especificação funcional com o conteúdo gerado pela IA.
    """
    try:
        template_path = os.path.join(TEMPLATES_PATH, "functional_specification_template.txt")
        if not os.path.exists(template_path):
            return "ERRO: O arquivo 'functional_specification_template.txt' não foi encontrado."

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Adiciona dados que não vêm da IA
        spec_content['date'] = datetime.now().strftime("%d/%m/%Y")

        # Substitui os placeholders simples
        for key, value in spec_content.items():
            if key != 'functionalities': # Trata a lista de funcionalidades separadamente
                template = template.replace(f"{{{key}}}", str(value))

        # Monta a seção de funcionalidades
        functionalities_text = ""
        if 'functionalities' in spec_content and spec_content['functionalities']:
            for i, func in enumerate(spec_content['functionalities']):
                functionalities_text += f"6.{i+1} {func.get('title', 'Funcionalidade sem título')}\n"
                functionalities_text += f"----------------------------------------\n"
                functionalities_text += f"Descrição: {func.get('description', 'N/A')}\n"
                functionalities_text += f"Acionador: {func.get('trigger', 'N/A')}\n"
                functionalities_text += f"Integrações: {func.get('integrations', 'N/A')}\n"
                functionalities_text += f"Vínculo com Telas: {func.get('screen_links', 'N/A')}\n"
                functionalities_text += f"Campos: {func.get('fields', 'N/A')}\n\n"
                functionalities_text += f"Requisitos Funcionais:\n"
                if func.get('functional_requirements'):
                    for req in func['functional_requirements']:
                        functionalities_text += f"- {req}\n"
                functionalities_text += "\n\n"
        
        template = template.replace("{functionalities_section}", functionalities_text)

        return template
    except Exception as e:
        return f"Erro ao gerar o documento de especificação: {e}"