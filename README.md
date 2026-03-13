# ✨ Business Analyst Copilot ✨

O **Business Analyst Copilot** é uma ferramenta inteligente projetada para apoiar analistas de negócio e gerentes de produto, transformando transcrições de reuniões e documentos de apoio em artefatos de projeto claros e estruturados.

Utilizando transcrição em tempo real e análise por IA (GPT-4o), esta aplicação gera um **Mapa Mental** interativo para visualização de alto nível e uma **Especificação Funcional** detalhada, acelerando o processo de descoberta e documentação de requisitos.

---

### 🚀 Principais Funcionalidades

* **Transcrição em Tempo Real:** Captura o áudio do microfone e, opcionalmente, o áudio do sistema (saída dos alto-falantes), permitindo transcrever reuniões do Teams, Meet, Zoom etc. com a sua voz e a dos participantes remotos.
* **Contexto Aumentado:** Permite o upload de múltiplos documentos (.pdf, .txt) e áudios (.mp3, .wav) para enriquecer o contexto da análise.
* **Análise de Requisitos com IA:** Utiliza GPT-4o para analisar a transcrição e os documentos, extraindo requisitos, fluxos, stakeholders e regras de negócio.
* **Geração de Especificação Funcional:** Preenche um template de especificação funcional com os dados extraídos, criando um documento robusto e pronto para ser refinado.

### 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface Gráfica:** CustomTkinter
* **Orquestração de IA:** OpenAI API (GPT-4o)
* **Transcrição de Áudio:** Google Cloud Speech-to-Text API
* **Captura de Áudio:** Sounddevice (microfone) e PyAudioWPatch (áudio do sistema via WASAPI loopback no Windows)

---

### Captura de áudio do sistema (microfone + speaker)

Para transcrever reuniões com a sua voz e a dos participantes remotos (Teams, Meet, Zoom):

1. **No Windows:** A captura do áudio do sistema usa WASAPI (loopback). Não é necessário configurar "Stereo Mix" manualmente; a aplicação usa o dispositivo de saída padrão.
2. **Na interface:** Em "Entrada de Áudio", selecione o **Microfone** desejado e marque **"Capturar áudio do sistema (Teams/Meet/Zoom)"**. Opcionalmente, escolha qual saída de áudio capturar em "Áudio do sistema" (o padrão é a saída principal).
3. **Limitações:** A captura de áudio do sistema está disponível apenas no Windows (PyAudioWPatch/WASAPI). Em caso de falha (driver ou permissões), a transcrição continua apenas com o microfone.

---

### 🏁 Como Usar a Aplicação

1.  **Execute a Aplicação:** Use o script `run.bat`.
2.  **Prepare a Reunião:** Preencha o nome do cliente e adicione documentos de apoio relevantes (editais, briefings, áudios, etc.).
3.  **Transcreva:** Selecione o microfone e, se quiser incluir a voz dos participantes remotos, marque **"Capturar áudio do sistema (Teams/Meet/Zoom)"**. Use os botões "Iniciar Reunião" / "Parar Reunião".
4.  **Gere a Análise:** Ao final, clique em **"Gerar Documentação"**. O sistema irá processar todo o conteúdo.
5.  **Explore os Resultados:**
    * Navegue até a aba **"BPMN"** para visualizar e salvar o diagrama de processo.
    * Vá para a aba **"Especificação Funcional"** para ver o documento detalhado. Salve-o como TXT ou Word.