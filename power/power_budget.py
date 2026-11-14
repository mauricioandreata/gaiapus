#!/usr/bin/env python3
"""Orçamento de energia da estaca Gaiapus.

Todos os valores padrão são ESTIMATIVAS iniciais. Substitua pelos números dos datasheets
dos componentes escolhidos (anote a fonte em power/README.md).

Uso:
    python power_budget.py
    python power_budget.py --intervalo 15 --sf 10 --tx-ma 118
"""
import argparse
import math


def lora_airtime_s(payload_bytes, sf, bw_hz=125_000, cr=1, preamble=8, crc=True, header=True):
    """Tempo no ar de um pacote LoRa (fórmula do datasheet Semtech SX126x)."""
    t_sym = (2 ** sf) / bw_hz
    de = 1 if t_sym > 0.016 else 0  # otimização de baixa taxa
    ih = 0 if header else 1
    num = 8 * payload_bytes - 4 * sf + 28 + 16 * int(crc) - 20 * ih
    n_payload = 8 + max(math.ceil(num / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return (preamble + 4.25) * t_sym + n_payload * t_sym


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a = p.add_argument
    # Ciclo
    a("--intervalo", type=float, default=30, help="minutos entre medições")
    a("--payload", type=int, default=25, help="bytes do uplink (protocolo de dados)")
    a("--sf", type=int, default=9, help="spreading factor LoRa")
    # Correntes (mA) e tempos (s) — ESTIMATIVAS
    a("--sleep-ua", type=float, default=25, help="corrente total em sono profundo (µA): MCU + rádio + regulador + sensores")
    a("--mcu-ma", type=float, default=35, help="MCU ativo, sem Wi-Fi")
    a("--medir-s", type=float, default=0.4, help="tempo acordado medindo sensores")
    a("--tx-ma", type=float, default=45, help="rádio transmitindo (SX1262 ~14 dBm)")
    a("--rx-ma", type=float, default=5, help="rádio recebendo")
    a("--rx-s", type=float, default=1.0, help="janela de recepção do downlink")
    # Bateria e sol
    a("--bat-mah", type=float, default=1500, help="capacidade LiFePO4 18650")
    a("--bat-util", type=float, default=0.8, help="fração utilizável da bateria")
    a("--painel-w", type=float, default=1.0)
    a("--hsp", type=float, default=4.5, help="horas de sol pleno por dia (estimativa, confirmar com NASA POWER)")
    a("--efic", type=float, default=0.5, help="eficiência total painel→bateria (carregador linear)")
    a("--nublado", type=float, default=0.25, help="fração da geração em dia nublado")
    a("--v-bat", type=float, default=3.2, help="tensão nominal da bateria")
    a("--autodesc", type=float, default=3.0, help="autodescarga da bateria (%% por mês)")
    args = p.parse_args()

    ciclos_dia = 24 * 60 / args.intervalo
    t_air = lora_airtime_s(args.payload, args.sf)

    # Carga por ciclo em mA·s
    q_medir = args.mcu_ma * args.medir_s
    q_tx = (args.mcu_ma + args.tx_ma) * t_air
    q_rx = (args.mcu_ma + args.rx_ma) * args.rx_s
    t_ativo = args.medir_s + t_air + args.rx_s
    q_ciclo = q_medir + q_tx + q_rx

    mah_ativo_dia = q_ciclo * ciclos_dia / 3600
    horas_sono = 24 - t_ativo * ciclos_dia / 3600
    mah_sono_dia = args.sleep_ua / 1000 * horas_sono
    mah_dia = mah_ativo_dia + mah_sono_dia
    i_media_ua = mah_dia / 24 * 1000

    mah_autodesc = args.bat_mah * args.autodesc / 100 / 30
    autonomia = args.bat_mah * args.bat_util / (mah_dia + mah_autodesc)
    gera_sol = args.painel_w * args.hsp * args.efic / args.v_bat * 1000
    gera_nub = gera_sol * args.nublado

    print("=== Orçamento de energia · Estaca Gaiapus (ESTIMATIVA) ===")
    print(f"Ciclos por dia:               {ciclos_dia:8.0f}")
    print(f"Tempo no ar LoRa (SF{args.sf}):     {t_air*1000:8.1f} ms")
    print(f"Tempo ativo por ciclo:        {t_ativo:8.2f} s")
    print(f"Carga por ciclo:              {q_ciclo/3.6:8.2f} µAh  (medir {q_medir/3.6:.1f} | TX {q_tx/3.6:.1f} | RX {q_rx/3.6:.1f})")
    print(f"Consumo ativo por dia:        {mah_ativo_dia:8.2f} mAh")
    print(f"Consumo em sono por dia:      {mah_sono_dia:8.2f} mAh")
    print(f"Consumo total por dia:        {mah_dia:8.2f} mAh  (média {i_media_ua:.0f} µA)")
    print(f"Autodescarga da bateria:      {mah_autodesc:8.2f} mAh/dia")
    print(f"Autonomia sem sol:            {autonomia:8.0f} dias")
    print(f"Geração em dia de sol:        {gera_sol:8.0f} mAh/dia")
    print(f"Geração em dia nublado:       {gera_nub:8.0f} mAh/dia")
    print(f"Saldo em dia nublado:         {gera_nub - mah_dia:+8.0f} mAh/dia")
    print("Meta N1 (≥14 dias sem sol):  ", "OK" if autonomia >= 14 else "NÃO ATENDE")


if __name__ == "__main__":
    main()
