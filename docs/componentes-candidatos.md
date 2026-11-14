# Componentes candidatos (a confirmar na sexta)

Regra: SMD, modelo 3D disponível, código LCSC em estoque. Tudo abaixo é **candidato**:
conferir datasheet, estoque e preço antes de colocar no esquemático.

| Bloco | Função | Candidato | Encapsulamento | Verificar |
|---|---|---|---|---|
| MCU | Microcontrolador + USB nativo + touch | ESP32-S3-MINI-1 ou ESP32-S3-WROOM-1 | Módulo castelado | Área livre da antena; corrente em deep sleep |
| Rádio | LoRa SX1262 | Módulo SX1262 SMD (ex.: Ebyte E22-900M22S, Seeed Wio-SX1262) | Módulo castelado | Faixa 915 MHz, pinagem, certificações |
| Rádio | Antena | Conector U.FL ou SMA de borda SMD | SMD | Casamento 50 Ω até o módulo |
| Energia | Carregador LiFePO4 | CN3058E ou equivalente | SOP/ESOP-8 | Tensão de carga 3,6 V; entrada do painel |
| Energia | Regulador 3V3 | Buck-boost baixo Iq (ex.: TPS63802) | QFN/DFN | Iq, faixa 2,5–3,65 V de entrada |
| Energia | Porta-bateria 18650 | Suporte SMD (ex.: Keystone 1042) | SMD | Modelo 3D, fixação no case |
| Energia | Proteção | Proteção de inversão e fusível rearmável | SMD | — |
| Sensores | Umidade do solo | Eletrodos interdigitados na PCB (footprint próprio), 2 profundidades | Cobre + máscara | Ver D4 |
| Sensores | Oscilador da sonda (×2) | 74LVC1G14 (inversor Schmitt) + R + C | SOT-23-5, 0603 | Frequência na faixa de MHz, PCNT do ESP32-S3 |
| Sensores | Chave de alimentação da sonda | Load switch pequeno ou GPIO direto | SOT-23 | Corrente dos osciladores |
| Sensores | Temp. do solo (×2) | Termistor NTC 0603, um por profundidade | 0603 | Curva B, divisor chaveado |
| Sensores | Ar | SHT40 | DFN-4 | Posição ventilada no case |
| Sensores | Pluviômetro | Conector JST SMD de 2 vias | SMD | Debounce do reed switch |
| Interface | LEDs | 0603 verde, amarelo, vermelho | 0603 | Visível pelo case (guia de luz) |
| Interface | Botão | Tátil SMD | SMD | Acionamento pelo case |
| USB | Programação | USB-C 16 pinos SMD + ESD (ex.: USBLC6-2) | SMD | — |
| Teste | Depuração | Pads de teste (UART, 3V3, GND) | Pad | — |
