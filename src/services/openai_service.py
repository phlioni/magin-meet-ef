# src/services/openai_service.py

import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

def gerar_analise_e_prompt(api_key: str, transcricao_completa: str, info_cliente: dict, contexto_documentos: str = "") -> dict:
    """
    Recebe a transcrição, o contexto de documentos, filtra, analisa e gera saídas.
    """
    openai.api_key = api_key
    
    # --- ALTERADO: O prompt foi significativamente melhorado para focar em branding ---
    prompt_mestre = f"""
    Sua tarefa é analisar a transcrição de uma reunião e o conteúdo de documentos de apoio para o cliente '{info_cliente.get('nome', 'N/A')}'.
    Os DOCUMENTOS DE APOIO são a fonte principal de verdade. A TRANSCRIÇÃO da reunião serve como contexto adicional.

    Gere um objeto JSON com duas chaves: "pre_analise" e "prompt_lovable".

    1.  **"pre_analise" (string, em português):**
        * Um documento de pré-análise detalhado. Comece com "Documento de Pré-Análise" e "Cliente: {info_cliente.get('nome', 'N/A')}".
        * Use o conteúdo dos documentos e da transcrição para preencher as seções: "Objetivo Principal:", "Público-Alvo:", "Funcionalidades Essenciais Detalhadas:" e "Requisitos Não-Funcionais e Observações:". Seja o mais específico possível.

    2.  **"prompt_lovable" (string, em inglês):**
        * Um prompt de UI detalhado para o Lovable.ai, baseado em todas as informações.
        * **Overview:** [Descrição da aplicação em 1 frase, mencionando o nome do cliente: {info_cliente.get('nome', 'N/A')}.]
        * **Style and Branding:**
            * The visual design must be clean, modern, and professional, reflecting the brand identity of '{info_cliente.get('nome', 'N/A')}'.
            * **Primary Colors:** Use these hex codes: {info_cliente.get('cores', '#007BFF, #FFFFFF')}.
            * **Header/Navbar:** The UI must have a main header. This header **MUST** include a dedicated space on the left for a **client logo** and should display the application's title.
        * **Main Components:** [Descrição detalhada dos componentes da UI, seguindo o branding definido acima.]
        * **UI Language:** All UI text must be in Portuguese.

    **--- DOCUMENTOS DE APOIO (TEXTO E ÁUDIOS TRANSCRITOS) ---**
    {contexto_documentos}
    **--- FIM DOS DOCUMENTOS ---**

    **--- TRANSCRIÇÃO DA REUNIÃO ---**
    {transcricao_completa}
    **--- FIM DA TRANSCRIÇÃO ---**

    Retorne APENAS o objeto JSON.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo", 
            messages=[
                {"role": "system", "content": "Você é uma IA especialista em análise de negócios e requisitos de software. Sua saída deve ser um objeto JSON estruturado."},
                {"role": "user", "content": prompt_mestre}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        resultado_json = json.loads(response.choices[0].message.content)
        return resultado_json
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI para análise: {e}")
        return {
            "pre_analise": "Ocorreu um erro ao gerar a análise.",
            "prompt_lovable": "Error generating prompt."
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
        print(f"-> [✅] Áudio transcrito com sucesso.")
        return transcription.text
    except Exception as e:
        print(f"❌ ERRO ao transcrever o áudio {os.path.basename(audio_file_path)}: {e}")
        return f"Erro ao processar o áudio {os.path.basename(audio_file_path)}."