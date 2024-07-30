from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import os
import pandas as pd
import time
import zipfile
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import shutil
import random


# Carregar variáveis de ambiente
load_dotenv()

LOGIN = os.getenv('LOGIN')
SENHA = os.getenv('SENHA')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")  # Configura o SocketIO com suporte a CORS

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

associacoes = {}
tickets_baixados = []

# Configurações globais do Selenium
options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--start-maximized")
options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(OUTPUT_FOLDER),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver_instance = None

def get_driver():
    global driver_instance
    if driver_instance is None:
        driver_instance = webdriver.Chrome(options=options)
    return driver_instance

def descompactar_arquivo_zip(caminho_zip, pasta_destino):
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    with zipfile.ZipFile(caminho_zip, 'r') as arquivo_zip:
        for member in arquivo_zip.namelist():
            nome_corrigido = member.replace('Ticket - ', '', 1)
            destino_corrigido = os.path.join(pasta_destino, nome_corrigido)

            if member.endswith('/'):
                os.makedirs(destino_corrigido, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(destino_corrigido), exist_ok=True)
                with arquivo_zip.open(member) as source, open(destino_corrigido, "wb") as target:
                    shutil.copyfileobj(source, target)
        print("Arquivo descompactado e nomes de pasta ajustados com sucesso!")

def obter_ultimo_arquivo_diretorio(diretorio):
    arquivos = os.listdir(diretorio)
    caminhos_completos = [os.path.join(diretorio, nome) for nome in arquivos]
    arquivo_mais_recente = max(caminhos_completos, key=os.path.getctime)
    return os.path.basename(arquivo_mais_recente)

def mover_arquivo_para_pasta_ticket(nome_arquivo, numero_ticket, pasta_destino_base):
    numero_ticket = str(int(float(numero_ticket)))
    pasta_ticket = os.path.join(pasta_destino_base, numero_ticket)
    if not os.path.exists(pasta_ticket):
        os.makedirs(pasta_ticket)
    
    caminho_arquivo_atual = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    
    nome, extensao = os.path.splitext(nome_arquivo)
    nome_arquivo_novo = nome_arquivo
    caminho_novo_arquivo = os.path.join(pasta_ticket, nome_arquivo_novo)
    while os.path.exists(caminho_novo_arquivo):
        numero_aleatorio = random.randint(10, 99)
        nome_arquivo_novo = f"{nome}_{numero_aleatorio}{extensao}"
        caminho_novo_arquivo = os.path.join(pasta_ticket, nome_arquivo_novo)
    
    os.rename(caminho_arquivo_atual, caminho_novo_arquivo)
    print(f"Arquivo {nome_arquivo} movido para a pasta {pasta_ticket} como {nome_arquivo_novo}")


def wait_for_downloads(download_folder, timeout=5):
    seconds = 0
    while not any(fname.endswith('.crdownload') for fname in os.listdir(download_folder)):
        time.sleep(1)
        seconds += 3
        if seconds > timeout:
            break


csv_file_path = 'uploads/anexos.csv'  # Substitua pelo nome correto do seu arquivo CSV
output_folder = "downloads" 
pasta_de_destino = 'pastas' 

    # Configurações do Selenium
options = Options()
options.add_argument("--headless")  # Adiciona o modo headless
options.add_argument("--log-level=3") 
options.add_argument("--window-size=1920,1080")
options.add_argument("--start-maximized")  # Inicia o navegador maximizado
options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath("downloads"),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver = webdriver.Chrome(options=options)



@app.route('/process', methods=['POST'])
def run_selenium():
    global tickets_baixados
    tickets_baixados = []  # Reiniciar a lista de tickets para esta execução
    driver = get_driver()
    try:
        driver.get("https://tracbel.centralitcloud.com.br/citsmart/webmvc/login")
        driver.find_element(By.XPATH, '//*[@id="user_login"]').send_keys(LOGIN)
        driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(SENHA)
        driver.find_element(By.XPATH, '//*[@id="btnEntrar"]').click()

        time.sleep(10)

        if os.path.exists(csv_file_path):
            df = pd.read_csv(csv_file_path, delimiter=';')
            df.columns = df.columns.str.strip()

            if "Link do(s) Anexo(s)" in df.columns and "Ticket" in df.columns:
                for index, row in df.iterrows():
                    links = row["Link do(s) Anexo(s)"]
                    ticket_number = row["Ticket"]
                    if pd.notna(links) and links != '-':
                        for link in links.split(' || '):
                            print(f"Baixando: {link}")
                            driver.get(link)
                            wait_for_downloads(output_folder)
                            nome_arquivo = obter_ultimo_arquivo_diretorio(output_folder)

                            if nome_arquivo.endswith('.crdownload'):
                                nome_arquivo = nome_arquivo.replace('.crdownload', '')

                            associacoes[nome_arquivo] = ticket_number
                            print(f"Download concluído com sucesso para o arquivo '{nome_arquivo}' associado ao ticket '{ticket_number}'.")

                            tickets_baixados.append(ticket_number)
                            socketio.emit('ticket_updated', {'ticket_number': ticket_number})

            else:
                print('Coluna "Link do(s) Anexo(s)" ou "Ticket" não encontrada no CSV.')
        else:
            print(f'Arquivo CSV "{csv_file_path}" não encontrado.')

        for arquivo, ticket in associacoes.items():
            mover_arquivo_para_pasta_ticket(arquivo, ticket, pasta_de_destino)

        print("Process completed.")
        print(f"Tickets baixados: {tickets_baixados}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        return jsonify({"status": "success", "tickets": tickets_baixados}), 200
@app.route('/close', methods=['POST'])
def close():
     driver = webdriver.Chrome(options=options)
     driver.quit()  

     return jsonify({"status": "success"}), 200

@app.route('/upload', methods=['POST'])
def handle_upload():
    print("Requisição recebida!")
    
    # Verificar e limpar a pasta de uploads antes de salvar novos arquivos
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    if 'csv' not in request.files or 'zip' not in request.files:
        print("Arquivos CSV ou ZIP não encontrados na requisição.")
        return jsonify({'error': 'Arquivos .csv e .zip são necessários'}), 400

    csv_file = request.files['csv']
    zip_file = request.files['zip']
    print(f"Arquivos recebidos: {csv_file.filename}, {zip_file.filename}")

    if csv_file.filename == '' or zip_file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    # Renomear os arquivos
    csv_filename = 'anexos.csv'
    zip_filename = 'pastas-arquivos.zip'

    csv_path = os.path.join(UPLOAD_FOLDER, secure_filename(csv_filename))
    zip_path = os.path.join(UPLOAD_FOLDER, secure_filename(zip_filename))

    csv_file.save(csv_path)
    zip_file.save(zip_path)
    print("Arquivos salvos")

    descompactar_arquivo_zip(zip_path, os.path.join(UPLOAD_FOLDER, '../pastas'))

    return jsonify({'message': 'Arquivos recebidos e descompactados com sucesso'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# if __name__ == '__main__':
#     app.run(debug=True, use_reloader=False, port=5000)
