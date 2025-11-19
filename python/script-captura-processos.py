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
from collections import defaultdict


# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER') or getpass.getuser()  # Linux

MacAdress = get_mac()
nucleo=psutil.cpu_percent(percpu=True)
  
 
def pegar_processos_comeco():
    processos = []
    #agrupa por nome
    for proc in psutil.process_iter(["name"]):
        try:  
            mem = proc.memory_percent()
            tempos_cpu = proc.cpu_times() 
            #total_cpu = tempos_cpu.user + tempos_cpu.system
            total_cpu= proc.cpu_percent(interval=0.1)

            processos.append({ 
                "obj": proc, 
                "nome": proc.info["name"],
                "cpu_perc": round(total_cpu, 2), 
                "mem_perc": round(mem, 2)
            })  
             
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    #ordena pelo uso de memória descrescente
    processos.sort(key=lambda x: x["mem_perc"], reverse=True)

    col_n = 10
    
    #filtra os processos,pega até 10 processos
    # processos[inicio:fim]
    top_processos = processos[:col_n]

    return top_processos

    

def capturarprocesso(top_processos):  
    col_n = 10
    linhas = []
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S") 
    
    for proc_info in top_processos: 
        proc = proc_info["obj"]  
   
        try:
            cpu = proc.cpu_percent(interval=0.1)
            mem=proc.memory_percent()

            proc.info["name"]
            proc_info["cpu_perc"] = round(cpu, 2)
            proc_info["mem_perc"] = round(mem, 2)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            proc_info["cpu_perc"] = 0.0
            print("erro")

    #cria colunas
    colunas = ["timestamp","macAdress","Identificação-Mainframe"]
    #for de 1 até 10'
    for i in range(1, col_n + 1):
        # colunas.append(f"pid{i}")
        colunas.append(f"nome{i}")
        # colunas.append(f"usuario{i}")
        colunas.append(f"cpu_perc{i}")
        colunas.append(f"mem_perc{i}")
    
    #cria linhas
    linha = [ts,MacAdress,username]
    for proc in top_processos: 
        # linha.append(proc["pid"])
        linha.append(proc["nome"])
        # linha.append(proc["usuario"])
        linha.append(proc["cpu_perc"])
        linha.append(proc["mem_perc"])

    linhas.append(linha)

    processo = "processos.csv"
    
    #cria o cabeçalho se o processo não existir
    if not os.path.exists(processo):
        colunas = ["timestamp", "macAdress", "Identificação-Mainframe"]
        col_n = 10
        for i in range(1, col_n + 1):
            colunas += [ f"nome{i}", f"cpu_perc{i}", f"mem_perc{i}"]
        pd.DataFrame(columns=colunas).to_csv(processo, index=False, encoding="utf-8", sep=";")
    
    
    df = pd.DataFrame(linhas, columns=colunas)
    df.to_csv(processo, index=False, encoding="utf-8",sep=";",mode='a',header=False )
 


def carregamento():
    for i in range(1, 101):
        sys.stdout.write(f"\rCarregando:  {i}%")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\n")

print(f"HORÁRIO AGORA = {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(pyfiglet.figlet_format("INICIANDO..."))
carregamento()

top_processos=[]
top_processos=pegar_processos_comeco()
while True:  
        capturarprocesso(top_processos)