import psutil
import time
from datetime import datetime
import pytz  # ajusta fuso horário
import pyfiglet
import sys
import os
from uuid import getnode as get_mac
import getpass
import pandas as pd 

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER') or getpass.getuser()  # Linux

MacAdress = get_mac()
  
 
def pegar_processos_novo():
    linhas = []
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
     
    processos = []
    for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"]):
        try:
            processos.append({
                "pid": proc.info["pid"],
                "nome": proc.info["name"],
                "usuario": proc.info["username"],
                "cpu_%": round(proc.info["cpu_percent"], 2),
                "mem_%": round(proc.info["memory_percent"], 2)
            }) 
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    #ordena pelo uso de memória descrescente
    processos.sort(key=lambda x: x["mem_%"], reverse=True)

    col_n = 10
    
    #filtra os processos,pega até 10 processos
    # processos[inicio:fim]
    top_processos = processos[:col_n]

    #cria colunas
    colunas = ["timestamp","macAdress","Identificação-Mainframe"]
    #for de 1 até 10'
    for i in range(1, col_n + 1):
        colunas.append(f"pid{i}")
        colunas.append(f"nome{i}")
        colunas.append(f"usuario{i}")
        colunas.append(f"cpu_%{i}")
        colunas.append(f"mem_%{i}")
    
    #cria linhas
    linha = [ts,MacAdress,username]
    for proc in top_processos:
        linha.append(proc["pid"])
        linha.append(proc["nome"])
        linha.append(proc["usuario"])
        linha.append(proc["cpu_%"])
        linha.append(proc["mem_%"])

    linhas.append(linha)

    processo = "processos.csv"
    
    #cria o cabeçalho se o processo não existir
    if not os.path.exists(processo):
        colunas = ["timestamp", "macAdress", "Identificação-Mainframe"]
        col_n = 10
        for i in range(1, col_n + 1):
            colunas += [f"pid{i}", f"nome{i}", f"usuario{i}", f"cpu_%{i}", f"mem_%{i}"]
        pd.DataFrame(columns=colunas).to_csv(processo, index=False, encoding="utf-8", sep=";")

    df = pd.DataFrame(linhas, columns=colunas)
    df.to_csv(processo, index=False, encoding="utf-8",sep=";",mode='a',header=False )
    print(df)

 

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
    horario_agora = datetime.now()
    trata_data = horario_agora.strftime("%d-%m-%Y %H:%M:%S")
  
    pegar_processos_novo() 
    # user_processos = pegar_processos_top10()

 