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
import platform
#import boto3 
#from io import StringIO

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER') or getpass.getuser()  # Linux

MacAdress = get_mac()

dados = {
    "macAdress": [],
    "timestamp": [], 
    "processos": []
}
 

def pegar_processos():
    usuario_atual = getpass.getuser()
    processos_usuario = []
    agrupado = {}

    for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"]):
        try:
             
            usuario_proc = proc.info.get('username')
            if not usuario_proc:
                continue

            # Linux: username já é só o usuário
            if platform.system() == "Windows":
                usuario_proc = usuario_proc.split("\\")[-1]

            if usuario_proc != usuario_atual:
                continue

            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_percent()
            if cpu <= 0.01 and mem <= 0.01:#se for menor que 0.01%
                continue
            
            nome = proc.info['name']
 
            if nome not in agrupado: #agrupa os processos de mesmo nome
                agrupado[nome] = {
                    "pid": proc.info["pid"],
                    "nome": nome,
                    "usuario": usuario_proc,
                    "cpu_%": cpu,
                    "mem_%": mem,
                }
            else:
                agrupado[nome]["cpu_%"] += cpu
                agrupado[nome]["mem_%"] += mem  

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        
        for dados in agrupado.values(): #adiciona os valores agrupados na lista
            processos_usuario.append({
                "pid": dados["pid"],
                "nome": dados["nome"],
                "usuario": dados["usuario"],
                "cpu_%": round(dados["cpu_%"], 2),
                "Mem_%": round(dados["mem_%"], 2)
            })
    
    return processos_usuario

def pegar_processos_top10():
    usuario_atual = getpass.getuser()
    processos_usuario = []
    processos_usuario_filtrado = []
    agrupado = {}

    for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"]):
        try:
             
            usuario_proc = proc.info.get('username')
            if not usuario_proc:
                continue

            # Linux: username já é só o usuário
            if platform.system() == "Windows":
                usuario_proc = usuario_proc.split("\\")[-1]

            if usuario_proc != usuario_atual:
                continue

            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_percent()
            if cpu <= 0.01 and mem <= 0.01:
                continue
            
            nome = proc.info['name']
 
            if nome not in agrupado: 
                agrupado[nome] = {
                    "pid": proc.info["pid"],
                    "nome": nome,
                    "usuario": usuario_proc,
                    "cpu_%": cpu,
                    "mem_%": mem,
                }
            else:
                agrupado[nome]["cpu_%"] += cpu
                agrupado[nome]["mem_%"] += mem  

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        
        for dados in agrupado.values():
            processos_usuario.append({
                "pid": dados["pid"],
                "nome": dados["nome"],
                "usuario": dados["usuario"],
                "cpu_%": round(dados["cpu_%"], 2),
                "Mem_%": round(dados["mem_%"], 2)
            })

        processos_usuario = sorted(processos_usuario, key=lambda x: x['cpu_%'], reverse=True) #ordena o dicionario pelo processo
        #x é um valor empírico
        print(processos_usuario)
        # for i in range(10):
            
        #     dados = processos_usuario[i]
        #     processos_usuario_filtrado.append({
        #         "pid": dados["pid"],
        #         "nome": dados["nome"],
        #         "usuario": dados["usuario"],
        #         "cpu_%": round(dados["cpu_%"], 2),
        #         "Mem_%": round(dados["Mem_%"], 2)
        #     })
            
    
    return processos_usuario

def montar_msg(dado, nomeDado, metrica, limite_barra, numDivisao):
    calculo_total_barras = int(limite_barra * (dado / numDivisao))
    return f"{nomeDado} [{'■' * calculo_total_barras}{' ' * (limite_barra - calculo_total_barras)}] {dado}{metrica}"

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
  
    
    #user_processos = pegar_processos()
    user_processos = pegar_processos_top10()

    dados["timestamp"].append(trata_data)
    dados["identificao-mainframe"].append(username) 
    #dados["processos"].append(user_processos)
    dados["processos"].append(user_processos)
    
    dados["macAdress"].append(MacAdress)

    print(f"""
+------------------------------------------------------------------------------+

!--------IDENTIFICAÇÃO DO MAINFRAME---------!
    User: {dados["identificao-mainframe"][-1]}
    Mac Adress: {MacAdress}

!---------------PROCESSOS-------------------!
  Total de processos: {len(dados["processos"][-1])}

 
""")

    df = pd.DataFrame(dados)
    df.to_csv("dados-processo.csv", encoding="utf-8", sep=";", index=False)
    
    #comando AWS
    # csv_buffer = StringIO() #dependencia, em vez do csv carregar na máquina ele armazena temporariamente na pasta do projeto
    # df.to_csv(csv_buffer, index=False)

    # s3 = boto3.client('s3') #importa o s3
    # s3.put_object( #coloca o arquivo
    #     Bucket='nome-do-bucket',
    #     Key='arquivo.csv',  # caminho dentro do bucket
    #     Body=csv_buffer.getvalue()
    # )
