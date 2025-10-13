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
    "identificao-mainframe": [],
    "uso_cpu_total_%": [],
    "uso_ram_total_%": [],
    "swap_rate_mbs": [],
    "tempo_cpu_ociosa": [],
    "cpu_io_wait": [],
    "uso_disco_total_%": [],
    "disco_throughput_mbs": [],
    "disco_iops_total": [],
    "disco_read_count": [],
    "disco_write_count": [],
    "disco_latencia_ms": [],
    "processos": []
}

def to_mb(x):
    return round((x / (1024 ** 2)), 2)

def uso_ram():
    return psutil.virtual_memory().percent

def pegar_swap_rate():
    swap_rate = [psutil.swap_memory()]
    time.sleep(1)
    swap_rate.append(psutil.swap_memory())
    sout_rate = swap_rate[1].sout - swap_rate[0].sout
    sin_rate = swap_rate[1].sin - swap_rate[0].sin
    return [to_mb(sout_rate), to_mb(sin_rate), to_mb(sout_rate + sin_rate)]

def pegar_throughput():
    data = [psutil.disk_io_counters()]
    time.sleep(1)
    data.append(psutil.disk_io_counters())
    read_per_sec = data[1].read_bytes - data[0].read_bytes
    write_per_sec = data[1].write_bytes - data[0].write_bytes
    return to_mb(read_per_sec + write_per_sec)

def pegar_iops_e_latencia():
    inicio = time.perf_counter()
    io1 = psutil.disk_io_counters()
    time.sleep(1)
    fim = time.perf_counter()
    io2 = psutil.disk_io_counters()
    
    read_iops = io2.read_count - io1.read_count
    write_iops = io2.write_count - io1.write_count
    total_iops = read_iops + write_iops
    
    total_ms = (fim - inicio) * 1000
    latencia_ms = round(total_ms / total_iops, 2) if total_iops > 0 else 0
    return [total_iops, read_iops, write_iops, latencia_ms]

def pegar_dados_cpu():
    cpu_dados = psutil.cpu_times_percent(interval=0.1)
    cpu_iowait = getattr(cpu_dados, 'iowait', 0.0)  # Linux tem iowait, Windows não
    return [cpu_dados.idle, cpu_dados.user, cpu_dados.system, cpu_iowait]

def uso_disco():
    return psutil.disk_usage('/').percent

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

    dados_cpu = pegar_dados_cpu()
    uso_ram_porcentagem = uso_ram()
    swap_rate = pegar_swap_rate()
    uso_disco_porcentagem = uso_disco()
    dados_disco = pegar_iops_e_latencia()
    throughput = pegar_throughput()
    dados_disco.append(throughput)
    
    user_processos = pegar_processos()
    #user_processos = pegar_processos_top10()

    dados["timestamp"].append(trata_data)
    dados["identificao-mainframe"].append(username)
    dados["uso_cpu_total_%"].append(dados_cpu[2])
    dados["uso_ram_total_%"].append(uso_ram_porcentagem)
    dados["swap_rate_mbs"].append(swap_rate[2])
    dados["tempo_cpu_ociosa"].append(dados_cpu[0])
    dados["cpu_io_wait"].append(dados_cpu[3])
    dados["uso_disco_total_%"].append(uso_disco_porcentagem)
    dados["disco_iops_total"].append(dados_disco[0])
    dados["disco_throughput_mbs"].append(dados_disco[-1])
    dados["disco_read_count"].append(dados_disco[1])
    dados["disco_write_count"].append(dados_disco[2])
    dados["disco_latencia_ms"].append(dados_disco[3])
    dados["processos"].append(user_processos)
    
    dados["macAdress"].append(MacAdress)

    print(f"""
+------------------------------------------------------------------------------+

!--------IDENTIFICAÇÃO DO MAINFRAME---------!
    User: {dados["identificao-mainframe"][-1]}
    Mac Adress: {MacAdress}

!---------------PROCESSOS-------------------!
  Total de processos: {len(dados["processos"][-1])}

!---------------DADOS DA CPU----------------!
    {montar_msg(dados["uso_cpu_total_%"][-1], "Consumo da CPU", "%", 10, 100)}
    {montar_msg(dados["tempo_cpu_ociosa"][-1], "Tempo de CPU Ociosa", "s", 10, 100)}
    {montar_msg(dados["cpu_io_wait"][-1], "Tempo de CPU I/O Wait", "s", 10, 100)}

!---------------DADOS DA RAM----------------!
    {montar_msg(dados["uso_ram_total_%"][-1], "Consumo da RAM", "%", 10, 100)}
    {montar_msg(dados["swap_rate_mbs"][-1], "Dados indo para memória SWAP", "MB/s", 10, 100)}

!---------------DADOS DO DASD---------------!
    {montar_msg(dados["uso_disco_total_%"][-1], "Consumo do DASD", "%", 10, 100)}
    {montar_msg(dados["disco_throughput_mbs"][-1], "Throughput do DASD", "MB/s", 10, 100)}
    {montar_msg(dados["disco_iops_total"][-1], "IOPS no Disco", "qtd", 10, 100)}
    {montar_msg(dados["disco_read_count"][-1], "Dados lidos no DASD", "qtd", 10, 100)}
    {montar_msg(dados["disco_write_count"][-1], "Dados escritos no DASD", "qtd", 10, 100)}
    {montar_msg(dados["disco_latencia_ms"][-1], "Latência do DASD", "ms", 10, 1000)}
""")

    df = pd.DataFrame(dados)
    df.to_csv("dados-mainframe2.csv", encoding="utf-8", sep=";", index=False)
    
    #comando AWS
    # csv_buffer = StringIO() #dependencia, em vez do csv carregar na máquina ele armazena temporariamente na pasta do projeto
    # df.to_csv(csv_buffer, index=False)

    # s3 = boto3.client('s3') #importa o s3
    # s3.put_object( #coloca o arquivo
    #     Bucket='nome-do-bucket',
    #     Key='arquivo.csv',  # caminho dentro do bucket
    #     Body=csv_buffer.getvalue()
    # )
