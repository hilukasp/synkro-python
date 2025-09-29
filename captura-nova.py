import psutil
import pandas as pd
import datetime
import threading 
import os

lista_captura = []

# Variáveis globais para cálculo de taxas
ultimo_swap_usado = None
ultimo_swap_time = None

def montar_msg(dado, nomeDado, metrica, limite_barra, numDivisao):
    calculo_total_barras = int(limite_barra * (dado / numDivisao))
    return f"{nomeDado} [{'■' * calculo_total_barras}{' ' * (limite_barra - calculo_total_barras)}] {dado}{metrica}"

def metricas():
    global ultimo_swap_usado, ultimo_swap_time

    conversor_gigabyte = 1024**3
    conversor_megabyte = 1024**2

    ram = psutil.virtual_memory()
    sensor = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}
    swap = psutil.swap_memory()
    time_now = datetime.datetime.now()
    hour = time_now.strftime("%d/%m/%y %H:%M:%S")

    # RAM
    ram_total = round(float(ram.total)/conversor_gigabyte, 2)
    ram_livre = round(float(ram.free)/conversor_gigabyte, 2)
    ram_usando = round(float(ram.used)/conversor_gigabyte, 2)

    # SWAP
    memoria_swap_total = round(swap.total/conversor_gigabyte, 2)
    memoria_swap_usando = round(swap.used/conversor_gigabyte, 2)
    memoria_swap_livre = round(swap.free/conversor_gigabyte, 2)

    # Calcular swap_rate_mbs
    swap_rate_mbs = 0
    now_timestamp = time_now.timestamp()
    if ultimo_swap_usado is not None and ultimo_swap_time is not None:
        delta_swap = swap.used - ultimo_swap_usado  # bytes
        delta_time = now_timestamp - ultimo_swap_time
        if delta_time > 0:
            swap_rate_mbs = round((delta_swap / delta_time) / (1024*1024), 2)
    ultimo_swap_usado = swap.used
    ultimo_swap_time = now_timestamp

    # CPU
    cpu_core = psutil.cpu_count(logical=False)
    cpu_core_logical = psutil.cpu_count()
    cpu_porcentagem_all = psutil.cpu_percent(interval=0.1)

    cpu_times = psutil.cpu_times()
    tempo_cpu_ociosa = getattr(cpu_times, 'idle', 0)
    cpu_io_wait = getattr(cpu_times, 'iowait', 0) if hasattr(cpu_times, 'iowait') else 0

    cpu_hotspot = sensor['coretemp'][0].critical if 'coretemp' in sensor else None
    cpu_temperature_atual = sensor['coretemp'][0].current if 'coretemp' in sensor else None

    # DISCO
    disc = psutil.disk_usage("/")
    disc_total = round(disc.total/conversor_gigabyte, 2)
    disc_usando = round(disc.used/conversor_gigabyte, 2)
    disc_livre = round(disc.free/conversor_gigabyte, 2)
    disc_porcentagem_usando = disc.percent

    disc_temp_atual = sensor['nvme'][0].current if 'nvme' in sensor else None
    disc_hotspot = sensor['nvme'][0].critical if 'nvme' in sensor else None

    # Métricas de disco adicionais
    io = psutil.disk_io_counters(perdisk=True)
    nome_disco = list(io.keys())[0] if io else None  # Pega o primeiro disco (ex: 'sda', 'C:', etc)

    if nome_disco:
        disco = io[nome_disco]
        disco_throughput_mbs = round((disco.read_bytes + disco.write_bytes) / conversor_megabyte, 2)
        disco_iops_total = disco.read_count + disco.write_count
        disco_read_count = disco.read_count
        disco_write_count = disco.write_count
        disco_latencia_ms = round((disco.read_time + disco.write_time) / max(disco_iops_total, 1), 2)
    else:
        disco_throughput_mbs = 0
        disco_iops_total = 0
        disco_read_count = 0
        disco_write_count = 0
        disco_latencia_ms = 0

    # Processos do usuário
    processos_usuario = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'username']):
        processos_usuario.append({
            "pid": proc.info['pid'],
            "nome": proc.info['name'],
            "usuario": proc.info['username']
        })

    captura = {
        "CPU": {
            "Uso": cpu_porcentagem_all,
            "Temperatura": cpu_temperature_atual,
            "Hotspot": cpu_hotspot,
            "Tempo_CPU_Ociosa": tempo_cpu_ociosa,
            "CPU_IO_Wait": cpu_io_wait,
        },
        "RAM": {
            "Total": ram_total,
            "Uso": ram_usando,
            "livre": ram_livre
        },
        "SWAP": {
            "Total": memoria_swap_total,
            "Uso": memoria_swap_usando,
            "livre": memoria_swap_livre,
            "Swap_Rate_MBs": swap_rate_mbs
        },
        "Disco": {
            "Total": disc_total,
            "Uso": disc_usando,
            "Livre": disc_livre,
            "Porcentagem_de_Uso": disc_porcentagem_usando,
            "Temperature": disc_temp_atual,
            "Hotspot": disc_hotspot,
            "Throughput_MB_s": disco_throughput_mbs,
            "IOPS_Total": disco_iops_total,
            "Read_Count": disco_read_count,
            "Write_Count": disco_write_count,
            "Latencia_ms": disco_latencia_ms
        },
        "Processos_Usuario": processos_usuario,
        "Data": hour
    }

    lista_captura.append(captura)
    salvar_csv(captura)

    print(f"""
+---------------------------------------------------+

CPU:
  Cores: {cpu_core}
  Virtual Core: {cpu_core_logical}
  {montar_msg(cpu_porcentagem_all, 'Consumo da CPU', '%', 20, 100)}
  Temperature: {cpu_temperature_atual} °C
  CPU Hotspot: {cpu_hotspot} °C
  Tempo CPU Ociosa: {tempo_cpu_ociosa}
  CPU IO Wait: {cpu_io_wait}

RAM:
  Total: {ram_total} GiB
  {montar_msg(ram_usando, 'Consumo da RAM', ' GiB', 20, ram_total)}
  Livre: {ram_livre} GiB

SWAP:
  Total: {memoria_swap_total} GiB
  {montar_msg(memoria_swap_usando, 'Uso da SWAP', ' GiB', 20, memoria_swap_total)}
  Livre: {memoria_swap_livre} GiB
  Swap Rate: {swap_rate_mbs} MB/s

DISCO:
  Total: {disc_total} GiB
  {montar_msg(disc_usando, 'Consumo do Disco', ' GiB', 20, disc_total)}
  Livre: {disc_livre} GiB
  {montar_msg(disc_porcentagem_usando, 'Porcentagem de Uso', '%', 20, 100)}
  Temperature: {disc_temp_atual} °C
  Hotspot: {disc_hotspot} °C
  Throughput: {disco_throughput_mbs} MB/s
  IOPS Total: {disco_iops_total}
  Read Count: {disco_read_count}
  Write Count: {disco_write_count}
  Latência: {disco_latencia_ms} ms

Processos do Usuário:
  Total: {len(processos_usuario)}

Data da Captura: {hour}
""")

def salvar_csv(captura):
    df = pd.json_normalize([captura])
    df.to_csv(
        "captura.csv",
        mode="a",
        header=not os.path.exists("captura.csv"),
        encoding="utf-8",
        index=False
    )

def iniciar_metricas():
    metricas()
    threading.Timer(3, iniciar_metricas).start()

iniciar_metricas()
