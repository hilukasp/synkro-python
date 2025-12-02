import psutil
import asyncio
import time
from datetime import datetime
import pytz
import pyfiglet
import sys
import os
from uuid import getnode as get_mac
import getpass
import pandas as pd
import platform
import boto3
from io import StringIO



# ****************** CONFIG S3 *******************
horario_agora = datetime.now()
trata_data = horario_agora.strftime("%d%m%Y")
empresa = 1 
bucket_name = "synkro-raw" #alterar
prefix = str(empresa)+"/"+ str(get_mac()) + "/" + str(trata_data) + "/"
s3 = boto3.client("s3", region_name="us-east-1")
# ************************************************

fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
username = os.environ.get('USER') or getpass.getuser()
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
    "disco_latencia_ms": []
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
    cpu_iowait = getattr(cpu_dados, 'iowait', 0.0)
    return [cpu_dados.idle, cpu_dados.user, cpu_dados.system, cpu_iowait]

def uso_disco():
    return psutil.disk_usage('/').percent

async def pegar_processos_novo():
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    processos = []

    for proc in psutil.process_iter(["name"]):
        try:
            mem = proc.memory_percent()
            tempos_cpu = proc.cpu_times()
            total_cpu = tempos_cpu.user + tempos_cpu.system

            processos.append({
                "nome": proc.info["name"],
                "cpu_%": round(total_cpu, 2),
                "mem_%": round(mem, 2)
            })

        except Exception:
            continue

    processos.sort(key=lambda x: x["cpu_%"], reverse=True)
    top_processos = processos[:10]

    colunas = ["timestamp","macAdress","Identificação-Mainframe"]
    for i in range(1, 11):
        colunas += [f"nome{i}", f"cpu_%{i}", f"mem_%{i}"]

    linha = [ts, MacAdress, username]
    for p in top_processos:
        linha += [p["nome"], p["cpu_%"], p["mem_%"]]

    df_proc = pd.DataFrame([linha], columns=colunas)
    return df_proc

def montar_msg(dado, nomeDado, metrica, limite_barra, numDivisao):
    calculo = int(limite_barra * (dado / numDivisao))
    return f"{nomeDado} [{'■' * calculo}{' ' * (limite_barra - calculo)}] {dado}{metrica}"

def carregamento():
    for i in range(1, 101):
        sys.stdout.write(f"\rCarregando:  {i}%")
        sys.stdout.flush()
        time.sleep(0.05)
    print()

async def rodando():

    print(pyfiglet.figlet_format("INICIANDO..."))
    carregamento()

    while True:
        horario_agora = datetime.now()
        trata_data = horario_agora.strftime("%d-%m-%Y %H:%M:%S")

        # --- coleta ---
        dados_cpu = pegar_dados_cpu()
        uso_ram_porcentagem = uso_ram()
        swap_rate = pegar_swap_rate()
        uso_disco_porcentagem = uso_disco()
        dados_disco = pegar_iops_e_latencia()
        throughput = pegar_throughput()
        dados_disco.append(throughput)

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
        dados["macAdress"].append(MacAdress)

        print(f"\n--- COLETANDO DADOS {trata_data} ---\n")

        # =========================================================
      
        df = pd.DataFrame(dados)   # DataFrame mainframe
        df_proc = await pegar_processos_novo()   # DataFrame processos

        # Criar buffers CSV em memória
        csv_buffer_main = StringIO() 
        csv_buffer_proc = StringIO()

        df.to_csv(csv_buffer_main, index=False, sep=";")
        df_proc.to_csv(csv_buffer_proc, index=False, sep=";")

        # nomes
        nome_main = f"{prefix}dados-mainframe.csv"
        nome_proc = f"{prefix}processos.csv"

        # Upload direto
        s3.put_object(Bucket=bucket_name, Key=nome_main, Body=csv_buffer_main.getvalue())
        s3.put_object(Bucket=bucket_name, Key=nome_proc, Body=csv_buffer_proc.getvalue())

        print("Dados enviados ao S3")

# 
asyncio.run(rodando())
