import psutil
import time
from datetime import datetime
import pytz
import pyfiglet
import sys
import os
from uuid import getnode as get_mac
import getpass
import pandas as pd
import boto3 
from io import StringIO
import requests

# ****************** CONFIG S3 *******************
horario_agora = datetime.now()
trata_data = horario_agora.strftime("%d%m%Y")
empresa = 1 
bucket_name = "synkro-raw"
prefix = str(empresa)+"/"+ str(get_mac()) + "/" + str(trata_data) + "/"
s3 = boto3.client("s3", region_name="us-east-1")
# ************************************************

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER') or getpass.getuser()

MacAdress = get_mac()
nucleo = psutil.cpu_percent(percpu=True)

#lista os processos comum
listar = {
    "Code.exe", "Taskmgr.exe", "chrome.exe",
    "svchost.exe", "python.exe", "mysqld.exe", "explorer.exe",
    "MsMpEng.exe", "AMDRSServ.exe", "System"
}

#captura os processos
def capturarprocesso(listar):
    grupos = {}
    linhas = []
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cpu_total=0.0
   
    ram_total = 0.0
 
    #para cada proc existente faça
    for proc in psutil.process_iter(["name"]):
        nome = proc.info.get("name", "")

        if nome not in listar:
            continue

        try:
            cpu = proc.cpu_percent(interval=0.1) / len(nucleo)
            mem = proc.memory_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        #inicializa valores se o processo ainda não estiver no dicionário
        if nome not in grupos:
            grupos[nome] = {"cpu": 0.0, "mem": 0.0}

        grupos[nome]["cpu"] += cpu
        grupos[nome]["mem"] += mem

    for nome in grupos:
        grupos[nome]["cpu"] *= 3.5
        cpu_total+=grupos[nome]["cpu"]
        ram_total+=grupos[nome]["mem"]


    #cria colunas 
    col_n = 10
    linha = [ts, MacAdress, username, cpu_total,ram_total]
    for nome in listar:
        dados = grupos.get(nome, {"cpu": 0.0, "mem": 0.0})
        linha.append(nome)
        linha.append(round(dados["cpu"], 2))
        linha.append(round(dados["mem"], 2))

 

    faltam = col_n - len(listar)
    for _ in range(faltam):
        linha += ["", "", ""]

    linhas.append(linha)

    processo = "processos.csv"

    # Criar CSV se não existir
    if not os.path.exists(processo):
        colunas = ["timestamp", "macAdress", "Identificação-Mainframe", "cpu_total", "ram_total"]
        for i in range(1, col_n + 1):
            colunas += [f"nome{i}", f"cpu_perc{i}", f"mem_perc{i}"]
        pd.DataFrame(columns=colunas).to_csv(processo, index=False, sep=";")

    #importando csv
    colunas = ["timestamp", "macAdress", "Identificação-Mainframe", "cpu_total", "ram_total"]
    for i in range(1, col_n + 1):
        colunas += [f"nome{i}", f"cpu_perc{i}", f"mem_perc{i}"]

    df = pd.DataFrame(linhas, columns=colunas)
    df.to_csv(processo, index=False, sep=";", mode='a', header=False)
    return df


def carregamento():
    for i in range(1, 101):
        sys.stdout.write(f"\rCarregando:  {i}%")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\n")


print(f"HORÁRIO AGORA = {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(pyfiglet.figlet_format("INICIANDO..."))
carregamento()

while True:
    capturarprocesso(listar)



    
    #aws
    # =========================================================
      
    df_proc = pd.read_csv("processos.csv", sep=";")

    # Criar buffers CSV em memória 
    csv_buffer_proc = StringIO()
 
    df_proc.to_csv(csv_buffer_proc, index=False, sep=";")




     # Enviar via HTTP POST
    csv_buffer_proc.seek(0) 
    url = "http://44.195.183.193:5000/upload"

    # Incluindo a estrutura de pastas no nome do arquivo
    nome_arquivo_s3 = f"{prefix}processos.csv"
    files = {"file": (nome_arquivo_s3, csv_buffer_proc)}

    r = requests.post(url, files=files)
    print(r.text)
    print("Dados enviados ao S3 com role da EC2")
    print("Dados enviados ao S3")
    time.sleep(5)  # intervalo entre envios