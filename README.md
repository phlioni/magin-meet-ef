# ✨ Magic Meet Copilot Pro ✨

**Magic Meet Copilot Pro** é uma plataforma de inteligência de vendas projetada para transformar o ciclo de criação de propostas, indo da conversa inicial a uma proposta comercial contextualizada em questão de minutos.

Utilizando transcrição em tempo real, upload de documentos, análise por IA, automação RPA e uma base de conhecimento de propostas anteriores (RAG), esta aplicação gera um pacote completo de artefatos de venda (pré-análise, protótipo funcional e pré-proposta comercial) para acelerar negócios e encantar clientes.

---

### 🚀 Principais Funcionalidades

* **Transcrição Direta do Microfone:** Captura o áudio diretamente do microfone padrão do usuário.
* **Contexto Aumentado:** Permite o upload de múltiplos documentos (.pdf, .txt) para enriquecer o contexto da análise.
* **Análise de Negócios com IA:** Utiliza GPT-4 para analisar a transcrição e os documentos, extraindo requisitos para um documento de pré-análise editável.
* **Criação de Protótipo (Opcional):** Usa Playwright para automatizar a criação de um protótipo funcional na plataforma Lovable.
* **Geração de Proposta com RAG:** Integra uma base de conhecimento vetorial (ChromaDB) de propostas anteriores para gerar uma pré-proposta comercial robusta e contextualizada.
* **Fluxo de Trabalho Flexível:** A interface permite gerar a análise, o protótipo e a proposta de forma independente, adaptando-se à necessidade de cada reunião.

### 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11
* **Interface Gráfica:** CustomTkinter
* **Orquestração de IA:** OpenAI API (GPT-4 Turbo)
* **Transcrição de Áudio:** Google Cloud Speech-to-Text API
* **Captura de Áudio:** Sounddevice
* **Automação Web (RPA):** Playwright
* **RAG (Retrieval-Augmented Generation):** LangChain
* **Banco de Dados Vetorial:** ChromaDB
* **Leitura de Documentos:** Unstructured, PyPDF

---

### 🏁 Começando (Para Desenvolvedores)

#### Pré-requisitos
* Python 3.11
* Um microfone funcional configurado como padrão.

#### Instalação
1.  Clone o repositório.
2.  Crie e ative um ambiente virtual (ex: `py -3.11 -m venv venv`).
3.  Instale as dependências unificadas: `pip install -r requirements.txt`.
4.  Instale os navegadores do Playwright: `playwright install`.

#### Configuração
O projeto requer os seguintes arquivos e pastas na raiz:
1.  **`.env`**: Para as chaves de API e credenciais (OPENAI_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, LOVABLE_*).
2.  **`google_credentials.json`**: Chave da conta de serviço do Google Cloud.
3.  **`templates/`**: Pasta contendo o `proposal_template.txt`.
4.  **`hot_folder_for_rag/`**: Pasta para adicionar novos documentos à base de conhecimento.

#### Setup da Base de Conhecimento (RAG) - Passo Obrigatório
Para que a geração de propostas funcione, a base de conhecimento precisa ser criada.
1.  Coloque seus arquivos de propostas antigas (.pdf, .txt) em uma pasta.
2.  Execute o script de ingestão em massa, apontando para essa pasta:
    ```bash
    .\venv\Scripts\python.exe ingest_data.py "C:\Caminho\Para\Suas\Propostas"
    ```
    Isso criará e populará a pasta `chroma_db`.

### 🎈 Como Usar a Aplicação

1.  **Execute a Aplicação:** Use o script `run.bat`.
2.  **Prepare a Reunião:** Preencha as informações do cliente e adicione documentos de apoio relevantes.
3.  [cite_start]**Transcreva:** Use os botões "Iniciar/Parar Transcrição" e a "Técnica do Espelho". [cite: 16]
4.  **Gere a Análise:** Clique em **"1. Gerar Análise"**. O sistema irá processar a transcrição e os documentos. A pré-análise aparecerá na aba correspondente e se tornará editável.
5.  **Refine e Gere (Opcional):**
    * Edite o texto da pré-análise para garantir a precisão.
    * Se necessário, clique em **"2. Gerar Protótipo (RPA)"**.
    * Clique em **"3. Gerar Pré-Proposta (RAG)"** para criar a proposta com base na sua análise refinada.