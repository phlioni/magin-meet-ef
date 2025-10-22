# ✨ Business Analyst Copilot ✨

O **Business Analyst Copilot** é uma ferramenta inteligente projetada para apoiar analistas de negócio e gerentes de produto, transformando transcrições de reuniões e documentos de apoio em artefatos de projeto claros e estruturados.

Utilizando transcrição em tempo real e análise por IA (GPT-4o), esta aplicação gera um **Mapa Mental** interativo para visualização de alto nível e uma **Especificação Funcional** detalhada, acelerando o processo de descoberta e documentação de requisitos.

---

### 🚀 Principais Funcionalidades

* **Transcrição em Tempo Real:** Captura o áudio do microfone e o transcreve, criando um registro da reunião.
* **Contexto Aumentado:** Permite o upload de múltiplos documentos (.pdf, .txt) e áudios (.mp3, .wav) para enriquecer o contexto da análise.
* **Análise de Requisitos com IA:** Utiliza GPT-4o para analisar a transcrição e os documentos, extraindo requisitos, fluxos, stakeholders e regras de negócio.
* **Geração de Mapa Mental:** Cria automaticamente um mapa mental em formato Markdown a partir da análise.
* **Visualizador e Editor de Mapa Mental:** Permite visualizar o mapa mental gerado, editar o código Markdown em tempo real e salvar o resultado como um arquivo HTML interativo.
* **Geração de Especificação Funcional:** Preenche um template de especificação funcional com os dados extraídos, criando um documento robusto e pronto para ser refinado.

### 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface Gráfica:** CustomTkinter
* **Orquestração de IA:** OpenAI API (GPT-4o)
* **Transcrição de Áudio:** Google Cloud Speech-to-Text API
* **Captura de Áudio:** Sounddevice
* **Visualização de Mapa Mental:** Markmap.js (via TkinterWeb)

---

### 🏁 Como Usar a Aplicação

1.  **Execute a Aplicação:** Use o script `run.bat`.
2.  **Prepare a Reunião:** Preencha o nome do cliente e adicione documentos de apoio relevantes (editais, briefings, áudios, etc.).
3.  **Transcreva:** Use os botões "Iniciar/Parar Transcrição". Lembre-se de ouvir o cliente e repetir/resumir os pontos importantes em voz alta para que a IA capture com clareza.
4.  **Gere a Análise:** Ao final, clique em **"Gerar Análise e Artefatos"**. O sistema irá processar todo o conteúdo.
5.  **Explore os Resultados:**
    * Navegue até a aba **"Mapa Mental"**. Visualize o mapa, faça ajustes no editor de Markdown à esquerda e veja a mágica acontecer. Salve-o como HTML.
    * Vá para a aba **"Especificação Funcional"** para ver o documento detalhado. Salve-o como TXT.