import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

def criar_prototipo_lovable(prompt: str, logo_path: str = None, progress_callback=None) -> str:
    def report_progress(message):
        print(message)
        if progress_callback:
            progress_callback(message)

    link_prototipo = "Erro ao gerar protótipo."
    lovable_url = os.getenv("LOVABLE_URL")
    if not lovable_url:
        return "Erro: LOVABLE_URL não definida."

    driver = None
    try:
        report_progress("-> [⚙️] Iniciando serviço do WebDriver (Selenium)...")
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")

        report_progress("-> [⚙️] Iniciando navegador (RPA)...")
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 45)

        report_progress(f"-> [⚙️] Navegando para a plataforma Lovable...")
        driver.get(lovable_url)

        report_progress("-> [⚙️] Verificando e realizando login...")
        try:
            # Tenta encontrar o botão de login principal. Se não encontrar em 5 segundos, pula.
            login_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "login-link")))
            login_button.click()
            
            # Fluxo de login detalhado
            wait.until(EC.element_to_be_clickable((By.ID, "email-login-button"))).click()
            email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
            email_input.send_keys(os.getenv("LOVABLE_EMAIL"))
            
            continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continuar']")))
            continue_button.click()

            password_input = wait.until(EC.visibility_of_element_located((By.ID, "password")))
            password_input.send_keys(os.getenv("LOVABLE_PASSWORD"))
            driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
            report_progress("-> [✅] Login enviado. Aguardando carregamento da página principal...")

        except Exception:
            report_progress("-> [✅] Sessão de login provavelmente já estava ativa.")

        # --- PONTO CRÍTICO 1: VERIFICAÇÃO PÓS-LOGIN ---
        # Esperamos explicitamente pelo campo de texto que SÓ EXISTE na página principal.
        # Se isso falhar, o login não funcionou e o script vai parar aqui com um erro claro.
        report_progress("-> [⚙️] Verificando se o login foi bem-sucedido e a página principal carregou...")
        wait.until(EC.visibility_of_element_located((By.ID, "chatinput")))
        # Adicionamos uma pausa generosa para garantir que TUDO na página termine de carregar.
        time.sleep(3)
        report_progress("-> [✅] Interface principal carregada com sucesso.")

        # Agora que temos certeza de que estamos na página certa, podemos interagir.
        chat_input = driver.find_element(By.ID, "chatinput")
        chat_input.send_keys(prompt)
        report_progress("-> [✅] Prompt inserido.")

        # Anexo de logo (se houver)
        if logo_path and os.path.exists(logo_path):
            try:
                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                file_input.send_keys(os.path.abspath(logo_path))
                time.sleep(2)
                report_progress("-> [✅] Logo anexado.")
            except Exception as e:
                report_progress(f"-> [⚠️] Não foi possível anexar o logo: {e}")

        # --- PONTO CRÍTICO 2: CLIQUE FINAL NO BOTÃO DE ENVIO ---
        # Esperamos o botão estar clicável.
        send_button = wait.until(EC.element_to_be_clickable((By.ID, 'chatinput-send-message-button')))
        # E usamos JavaScript para o clique mais robusto.
        driver.execute_script("arguments[0].click();", send_button)
        report_progress("-> [✅] Prompt enviado para geração.")
        
        report_progress("-> [⏳] Aguardando geração do Lovable... (Este passo pode levar até 8 minutos)")
        preview_link_element = WebDriverWait(driver, 480).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="preview--"]'))
        )
        
        report_progress("-> [⚙️] Protótipo gerado! Extraindo link...")
        link_prototipo = preview_link_element.get_attribute('href')
        report_progress(f"-> [✅] Sucesso! Link do protótipo extraído.")

    except Exception as e:
        error_message = f"-> [❌] Erro fatal na automação com Selenium: {e}"
        report_progress(error_message)
        link_prototipo = error_message
    finally:
        if driver:
            driver.quit()

    return link_prototipo