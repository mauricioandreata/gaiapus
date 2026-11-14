# Requisitos de hardware · Estaca Gaiapus (Rev A)

## Funcionais

| ID | Requisito |
|---|---|
| F1 | Medir umidade do solo em 2 profundidades (~15 cm e ~40 cm), através da parede do tubo (D4) |
| F2 | Medir temperatura do solo nas 2 profundidades |
| F3 | Medir temperatura e umidade do ar (risco de geada e calor) |
| F4 | Contar chuva com pluviômetro de báscula (pulsos, acorda o MCU) |
| F5 | Medir a tensão da bateria |
| F6 | Enviar os dados por LoRa a cada 30 min (configurável por downlink) |
| F7 | Receber o estado dos LEDs após cada envio |
| F8 | 3 LEDs (verde, amarelo, vermelho) e 1 botão |
| F9 | Guardar medições sem sinal e reenviar depois |
| F10 | Programação e atualização pelo USB-C nativo do ESP32-S3 |

## Não funcionais

| ID | Requisito | Meta |
|---|---|---|
| N1 | Autonomia sem sol | ≥ 14 dias (confirmar com `power/power_budget.py`) |
| N2 | Operação contínua com sol | Balanço diário positivo em dia nublado típico |
| N3 | Proteção | IP65 na parte eletrônica; eletrodos com revestimento conformal |
| N4 | Temperatura de operação | −5 °C a +60 °C (cobre geada e sol direto no case) |
| N5 | Montagem | 100% SMD, uma face se possível, montável na JLCPCB |
| N6 | Custo | Meta a definir após a BOM (estimar em 1 e 1.000 unidades) |
| N7 | Uso | Sem configuração pelo usuário: QR code liga a estaca ao produtor |
| N8 | Rádio | Módulos certificados; faixa AU915 no Brasil (915–928 MHz) |

## Fora do escopo da Rev A

GPS, tela, sensores de nutrientes (NPK), câmera, LoRaWAN completo.
