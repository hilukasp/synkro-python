import pandas as pd
import psutil
import time
from datetime import datetime
import pytz  # ajusta fuso horário
import pyfiglet
import sys

# Definir o fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')

dados = {
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
    "disco_latencia_ms": []
}

# Função para converter bytes para MB
def to_mb(x):
    return round(x / (1024**2), 2)

# Uso de RAM
def uso_ram():
    return psutil.virtual_memory().percent

# Swap rate
def pegar_swap_rate():
    swap_rate = [psutil.swap_memory()]
    time.sleep(1)
    swap_rate.append(psutil.swap_memory())
    sout_rate = getattr(swap_rate[1], "sin", 0)  # tratamento seguro
    sin_rate = getattr(swap_rate[1], "sin", 0)
    return [to_mb(sout_rate), to_mb(sin_rate), (to_mb(sout_rate) + to_mb(sin_rate))]

# Throughput de disco
def pegar_throughput():
    data = [psutil.disk_io_counters()]
    time.sleep(1)
    data.append(psutil.disk_io_counters())
    readPerSecond = data[1].read_bytes - data[0].read_bytes
    writePerSecond = data[1].write_bytes - data[0].write_bytes
    return to_mb(readPerSecond + writePerSecond)

# IOPS e latência
def pegar_iops_e_latencia():
    tempo_inicio = time.perf_counter()
    io1 = psutil.disk_io_counters()
    time.sleep(1)
    tempo_final = time.perf_counter()
    io2 = psutil.disk_io_counters()
    readIOPS = io2.read_count - io1.read_count
    writeIOPS = io2.write_count - io1.write_count
    iops = readIOPS + writeIOPS
    total_ms = (tempo_final - tempo_inicio) * 1000
    latencia_ms = round(total_ms / iops, 2) if iops > 0 else 0
    return [iops, readIOPS, writeIOPS, latencia_ms]

# Dados CPU (Linux e Windows)
def pegar_dados_cpu():
    cpu_dados = psutil.cpu_times_percent(interval=0.1)
    cpu_idle = cpu_dados.idle
    cpu_uso_usuarios = cpu_dados.user
    cpu_uso_sistema = cpu_dados.system
    cpu_iowait = getattr(cpu_dados, "iowait", 0.0)
    return [cpu_idle, cpu_uso_usuarios, cpu_uso_sistema, cpu_iowait]

# Uso de disco
def uso_disco():
    return psutil.disk_usage('/').percent

# Montar barra visual
def montar_msg(dado, nomeDado, metrica, limite_barra, numDivisao):
    calculo_total_barras = int(limite_barra * (dado / numDivisao))
    return f"{nomeDado} [{'■' * calculo_total_barras}{' ' * (limite_barra - calculo_total_barras)}] {dado}{metrica}"

# Carregamento
def carregamento():
    for i in range(1, 101):
        sys.stdout.write("\r" + f"Carregando:  {i}%")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\n")

print(f"HORÁRIO AGORA = {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(pyfiglet.figlet_format("INICIANDO..."))
print(carregamento())

while True:
    horario_agora = datetime.now()
    trata_data = horario_agora.strftime("%d-%m-%Y %H:%M:%S")

    # Captura de CPU, RAM, SWAP, Disco
    dados_cpu = pegar_dados_cpu()
    uso_ram_porcentagem = uso_ram()
    swap_rate = pegar_swap_rate()
    uso_disco_porcentagem = uso_disco()
    dados_disco = pegar_iops_e_latencia()
    throughput = pegar_throughput()
    dados_disco.append(throughput)

    # Temperaturas e hotspot (tratamento seguro)
    cpu_temperature_atual = None
    cpu_hotspot = None
    disc_temp_atual = None
    disc_hotspot = None
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures(fahrenheit=False)
        if "coretemp" in temps:
            cpu_temperature_atual = temps["coretemp"][0].current
            cpu_hotspot = max(t.current for t in temps["coretemp"])
        if "nvme" in temps:
            disc_temp_atual = temps["nvme"][0].current
            disc_hotspot = max(t.current for t in temps["nvme"])

    # Monta dicionário de captura completo
    captura = {
        "CPU": {
            "Uso": dados_cpu[1],
            "Temperatura": cpu_temperature_atual,
            "Hotspot": cpu_hotspot
        },
        "RAM": {
            "Total": psutil.virtual_memory().total,
            "Uso": psutil.virtual_memory().used,
            "Livre": psutil.virtual_memory().available
        },
        "SWAP": {
            "Total": psutil.swap_memory().total,
            "Uso": psutil.swap_memory().used,
            "Livre": psutil.swap_memory().free
        },
        "Disco": {
            "Total": psutil.disk_usage('/').total,
            "Uso": psutil.disk_usage('/').used,
            "Livre": psutil.disk_usage('/').free,
            "Porcentagem de Uso": uso_disco_porcentagem,
            "Temperatura": disc_temp_atual,
            "Hotspot": disc_hotspot
        },
        "Data": trata_data
    }

    # Armazena nos dados para CSV
    dados["timestamp"].append(trata_data)
    dados["identificao-mainframe"].append(psutil.users()[0].name)
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

    # Impressão visual
    print(f"""
+------------------------------------------------------------------------------+

!--------IDENTIFICAÇÃO DO MAINFRAME---------!
    {dados['identificao-mainframe'][-1]}

!---------------DADOS DA CPU----------------!
    {montar_msg(dados['uso_cpu_total_%'][-1], 'Consumo da CPU', '%', 10, 100)}
    {montar_msg(dados['tempo_cpu_ociosa'][-1], 'Tempo de CPU Ociosa', 's', 10, 100)}
    {montar_msg(dados['cpu_io_wait'][-1], 'Tempo de CPU I/O Wait', 's', 10, 100)}

!---------------DADOS DA RAM----------------!
    {montar_msg(dados['uso_ram_total_%'][-1], 'Consumo da RAM', '%', 10, 100)}
    {montar_msg(dados['swap_rate_mbs'][-1], 'Dados indo para memória SWAP', 'MB/s', 10, 100)}

!---------------DADOS DO DASD---------------!
    {montar_msg(dados['uso_disco_total_%'][-1], 'Consumo do DASD', '%', 10, 100)}
    {montar_msg(dados['disco_throughput_mbs'][-1], 'Throughput do DASD', 'MB/s', 10, 100)}
    {montar_msg(dados['disco_iops_total'][-1], 'IOPS no Disco', 'qtd', 10, 100)}
    {montar_msg(dados['disco_read_count'][-1], 'Dados lidos no DASD', 'qtd', 10, 100)}
    {montar_msg(dados['disco_write_count'][-1], 'Dados escritos no DASD', 'qtd', 10, 100)}
    {montar_msg(dados['disco_latencia_ms'][-1], 'Latência do DASD', 'ms', 10, 1000)}
""")

    # Salva CSV
    df = pd.DataFrame(dados)
    df.to_csv("dados-mainframe.csv", encoding="utf-8", sep=";", index=False)

    # Pequena pausa entre iterações
    time.sleep(1)
