# src/core/orchestrator.py

import os
from dotenv import load_dotenv

# Importa a nova função de transcrição de áudio
from src.services import openai_service, rpa_service
from src.services.openai_service import transcrever_audio
from src.services.database_operations import get_vector_store, get_text_from_file
from src.services.rag_pipeline import generate_proposal_from_template
from src.config import TEMPLATES_PATH

load_dotenv()

def gerar_analise(transcricao: str, info_cliente: dict, doc_paths: list, progress_callback=None) -> tuple[str, str]:
    """
    Etapa 1: Lê documentos e áudios, gera a Pré-Análise e o Prompt para o protótipo.
    """
    def report_progress(message):
        if progress_callback: progress_callback(message)

    contexto_documentos = ""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        return "ERRO: Chave da API da OpenAI não encontrada.", ""

    if doc_paths:
        report_progress(f"-> [⚙️] Lendo e processando {len(doc_paths)} documento(s) de apoio...")
        AUDIO_EXTENSIONS = ['.ogg', '.mp3', '.m4a', '.wav', '.mp4', '.mpeg']

        for path in doc_paths:
            try:
                _, file_extension = os.path.splitext(path)
                file_extension = file_extension.lower()

                if file_extension in AUDIO_EXTENSIONS:
                    contexto_documentos += f"--- TRANSCRIÇÃO DO ÁUDIO: {os.path.basename(path)} ---\n"
                    texto_transcrito = transcrever_audio(openai_api_key, path)
                    contexto_documentos += texto_transcrito
                else:
                    contexto_documentos += f"--- CONTEÚDO DO DOCUMENTO: {os.path.basename(path)} ---\n"
                    contexto_documentos += get_text_from_file(path)
                
                contexto_documentos += "\n\n"

            except Exception as e:
                report_progress(f"-> [⚠️] Não foi possível processar o arquivo {path}: {e}")

    report_progress("-> [⚙️] Analisando transcrição e documentos com a IA...")
    resultado_ia = openai_service.gerar_analise_e_prompt(
        api_key=openai_api_key,
        transcricao_completa=transcricao,
        info_cliente=info_cliente,
        contexto_documentos=contexto_documentos
    )
    report_progress("-> [✅] Análise da IA concluída.")
    
    pre_analise = resultado_ia.get("pre_analise", "Falha ao extrair a pré-análise.")
    prompt_lovable = resultado_ia.get("prompt_lovable", "Error extracting prompt.")
    
    return pre_analise, prompt_lovable

def gerar_prototipo(prompt_lovable: str, logo_path: str, progress_callback=None) -> str:
    """
    Etapa 2 (Opcional): Gera apenas o protótipo usando o RPA.
    """
    if not prompt_lovable or "Error" in prompt_lovable:
        return "Não foi possível gerar o protótipo pois o prompt de análise falhou."
        
    link_prototipo = rpa_service.criar_prototipo_lovable(prompt_lovable, logo_path, progress_callback)
    return link_prototipo

def gerar_proposta_final(analise_editada: str, progress_callback=None) -> str:
    """
    Etapa 3 (Opcional): Envia a análise editada para o Agent RAG e gera a proposta.
    """
    def report_progress(message):
        if progress_callback: progress_callback(message)
    try:
        report_progress("-> [🧠] Conectando à base de conhecimento (RAG)...")
        vector_store = get_vector_store()
        
        template_path = os.path.join(TEMPLATES_PATH, "proposal_template.txt")
        if not os.path.exists(template_path):
            error_msg = "ERRO: Arquivo 'proposal_template.txt' não encontrado."
            report_progress(f"-> [❌] {error_msg}")
            return error_msg
        
        report_progress("-> [📋] Carregando template da proposta...")
        template_content = get_text_from_file(template_path)

        report_progress("-> [🤖] IA está gerando a pré-proposta com base no RAG. Aguarde...")
        proposta_gerada = generate_proposal_from_template(
            briefing_content=analise_editada,
            proposal_template=template_content,
            vector_store=vector_store
        )
        report_progress("-> [✅] Pré-proposta gerada com sucesso!")
        return proposta_gerada
    except Exception as e:
        error_msg = f"Erro ao gerar proposta final: {e}"
        report_progress(f"-> [❌] {error_msg}")
        return error_msg