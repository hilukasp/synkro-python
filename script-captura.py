import pandas as pd
import psutil
import time
from datetime import datetime
import pytz #ajusta fuso horário
import pyfiglet
import sys
import os

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER')

dados = {
    "timestamp": [],
    "identificao-mainframe":[],
    "uso_cpu_total_%":[], #dados_cpu
    "uso_ram_total_%":[], #uso_ram
    "swap_rate_mbs": [], #pegar_swap_rate
    "tempo_cpu_ociosa": [], #dados_cpu
    "cpu_io_wait":[],#dados_cpu
    "uso_disco_total_%":[], #uso_disco
    "disco_throughput_mbs": [], #pegar_throughput
    "disco_iops_total": [], #pegar_iops_e_latencia
    "disco_read_count":[], #pegar_iops_e_latencia
    "disco_write_count":[], #pegar_iops_e_latencia
    "disco_latencia_ms": [], #pegar_iops_e_latencia
    "processos":[]
}

#Throughput de um disco só
def to_mb(x): #funcao para transformar em mb
    return round((x / (1024**2)),2)

def uso_ram():
    uso_ram = psutil.virtual_memory().percent
    return uso_ram

def pegar_swap_rate():
    swap_rate = []
    swap_rate.append(psutil.swap_memory())
    time.sleep(1)
    swap_rate.append(psutil.swap_memory())

    sout_rate = (swap_rate[1].sout - swap_rate[0].sout)
    sin_rate = (swap_rate[1].sin - swap_rate[0].sin)
    return [to_mb(sout_rate), to_mb(sin_rate), (to_mb(sout_rate) + to_mb(sin_rate))]

def pegar_throughput():
    data = []
    data.append(psutil.disk_io_counters())
    time.sleep(1)
    data.append(psutil.disk_io_counters())

    readPerSecond = data[1].read_bytes - data[0].read_bytes
    writePerSecond = data[1].write_bytes - data[0].write_bytes
    return (to_mb(readPerSecond+writePerSecond))

def pegar_iops_e_latencia():
    tempo_inicio = time.perf_counter()
    io1 = psutil.disk_io_counters()
    time.sleep(1)
    tempo_final = time.perf_counter()
    io2 = psutil.disk_io_counters()

    readIOPS = io2.read_count - io1.read_count
    writeIOPS = io2.write_count - io1.write_count
    iops = readIOPS+writeIOPS

    total_ms = (tempo_final - tempo_inicio) *1000
    latencia_ms = 0
    if iops > 0:
        latencia_ms = round(total_ms / iops,2)
    return [iops, readIOPS, writeIOPS, latencia_ms]

def pegar_dados_cpu():
    # só com linux o io_wait
    cpu_dados = psutil.cpu_times_percent(interval=0.1)
    cpu_iowait = cpu_dados.iowait
    cpu_idle = cpu_dados.idle
    cpu_uso_usuarios = cpu_dados.user
    cpu_uso_sistema = cpu_dados.system
    return [cpu_idle, cpu_uso_usuarios, cpu_uso_sistema, cpu_iowait]

def uso_disco():
    dados_disco = psutil.disk_usage('/').percent
    return dados_disco    

# FUNÇÃO MODIFICADA
def pegar_processos():
    processos_agrupados = {}

    for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"]):
        if proc.info["username"] != username:
            continue 
        if proc.info["cpu_percent"] <= 0 and proc.info["memory_percent"] <= 0:
            continue

        chave = (proc.info['name'], proc.info['username'])

        if chave not in processos_agrupados:
            processos_agrupados[chave] = {
                "nome": proc.info['name'],
                "usuario": proc.info['username'],
                "cpu_%": proc.info['cpu_percent'],
                "Mem_%": proc.info['memory_percent']
            }
        else:
            processos_agrupados[chave]["cpu_%"] += proc.info['cpu_percent']
            processos_agrupados[chave]["Mem_%"] += proc.info['memory_percent']

    return list(processos_agrupados.values())

def montar_msg(dado, nomeDado, metrica, limite_barra, numDivisao):
    calculo_total_barras = int(limite_barra * (dado/numDivisao))
    return f"{nomeDado} [{'■'* calculo_total_barras}{" "*(limite_barra - calculo_total_barras)}] {dado}{metrica}"

def carregamento():
    for i in range(1,101):
        sys.stdout.write("\r"+f"Carregando:  {i}%") #volta sempre pro começo da linha e fica sobrescrevendo
        sys.stdout.flush() #nao espera buffer encher
        time.sleep(0.05)
    sys.stdout.write("\n")

print(f"HORÁRIO AGORA = {datetime.now().strftime("%d/%m/%Y %H:%M")}")
print(pyfiglet.figlet_format("INICIANDO..."))
print(carregamento())
while True:
    horario_agora = datetime.now()
    trata_data = datetime.strftime(horario_agora, "%d-%m-%Y %H:%M:%S")
    dados_cpu = pegar_dados_cpu()
    uso_ram_porcentagem = uso_ram()
    swap_rate = pegar_swap_rate()
    uso_disco_porcentagem = uso_disco()
    dados_disco = pegar_iops_e_latencia()
    throughput = pegar_throughput()
    dados_disco.append(throughput)
    user_processos = pegar_processos()

    dados["timestamp"].append(trata_data)
    dados["identificao-mainframe"].append(username)
    dados["uso_cpu_total_%"].append(dados_cpu[2])
    dados["uso_ram_total_%"].append(uso_ram_porcentagem)
    dados["swap_rate_mbs"].append(swap_rate[2])
    dados["tempo_cpu_ociosa"].append(dados_cpu[0])
    dados["cpu_io_wait"].append(dados_cpu[3])
    dados["uso_disco_total_%"].append(uso_disco_porcentagem)
    dados["disco_iops_total"].append(dados_disco[0])
    dados["disco_throughput_mbs"].append(dados_disco[len(dados_disco)-1])
    dados["disco_read_count"].append(dados_disco[1])
    dados["disco_write_count"].append(dados_disco[2])
    dados["disco_latencia_ms"].append(dados_disco[3])
    dados["processos"].append(user_processos)

    print(f"""
        +------------------------------------------------------------------------------+

        !--------IDENTIFICAÇÃO DO MAINFRAME---------!
            {dados["identificao-mainframe"][len(dados["identificao-mainframe"])-1]}
        
        !---------------PROCESSOS-------------------!
            {dados["processos"][len(dados["processos"])-1]}
        !---------------DADOS DA CPU----------------!
            
            {montar_msg(dados["uso_cpu_total_%"][len(dados["uso_cpu_total_%"])-1], "Consumo da CPU", "%", 10, 100)}
            {montar_msg(dados["tempo_cpu_ociosa"][len(dados["tempo_cpu_ociosa"])-1], "Tempo de CPU Ociosa", "s", 10, 100)}
            {montar_msg(dados["cpu_io_wait"][len(dados["cpu_io_wait"])-1], "Tempo de CPU I/O Wait","s",10,100)}

        !---------------DADOS DA RAM----------------!

            {montar_msg(dados["uso_ram_total_%"][len(dados["uso_ram_total_%"])-1], "Consumo da RAM", "%", 10, 100)}
            {montar_msg(dados["swap_rate_mbs"][len(dados["swap_rate_mbs"])-1], "Dados indo para memória SWAP", "MB/s", 10, 100)}

        !---------------DADOS DO DASD---------------!
            {montar_msg(dados["uso_disco_total_%"][len(dados["uso_disco_total_%"])-1], "Consumo do DASD", "%", 10, 100)}
            {montar_msg(dados["disco_throughput_mbs"][len(dados["disco_throughput_mbs"])-1], "Throughput do DASD", "MB/s", 10, 100)}
            {montar_msg(dados["disco_iops_total"][len(dados["disco_iops_total"])-1], "IOPS no Disco", "qtd", 10, 100)}
            {montar_msg(dados["disco_read_count"][len(dados["disco_read_count"])-1], "Dados lidos no DASD", "qtd", 10, 100)}
            {montar_msg(dados["disco_write_count"][len(dados["disco_write_count"])-1], "Dados escritos no DASD", "qtd", 10, 100)}
            {montar_msg(dados["disco_latencia_ms"][len(dados["disco_latencia_ms"])-1], "Latência do DASD", "ms",10, 1000)}
    """)
    df = pd.DataFrame(dados)
    df.to_csv("dados-mainframe.csv", encoding="utf-8", sep=";", index=False)
