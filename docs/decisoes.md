# Registro de decisões (ADR)

Formato: data · decisão · motivo · alternativas descartadas.

## 2026-11-12 · D1 · Módulos certificados soldados direto na PCB
- **Decisão:** ESP32-S3 e SX1262 como módulos com terminais castelados, SMD, sem barras de pinos ou soquetes.
- **Motivo:** aparência e realidade de produto; rádio já homologado reduz custo de certificação; evita projetar RF e circuitos internos de desacoplamento do zero.
- **Descartado:** placas de desenvolvimento em soquete (aparência de hobby); chips soltos (layout de RF arriscado sem protótipo).

## 2026-11-12 · D2 · LoRa ponto a ponto na demonstração
- **Decisão:** LoRa P2P estaca → gateway próprio; gateway publica em MQTT.
- **Motivo:** cabe em 48 h; mesmo hardware suporta LoRaWAN depois.
- **Roadmap:** LoRaWAN (AU915) para escala e redes públicas.

## 2026-11-12 · D3 · Bateria LiFePO4 18650 + painel de 1 W
- **Motivo:** tolera melhor calor e ciclos que Li-ion comum; mais segura em campo.

## 2026-11-12 · D4 · Umidade medida através da parede do tubo, com oscilador local (revisada)
- **Decisão:** dois pares de eletrodos interdigitados na PCB-sonda (~15 e ~40 cm), cobertos apenas por máscara de solda,
  dentro de tubo de parede fina (1–1,5 mm) na região dos eletrodos, com a PCB encostada na parede e o vão preenchido com resina (sem ar).
  Ao lado de cada eletrodo, um oscilador RC com inversor Schmitt (ex.: 74LVC1G14, SOT-23-5) gera frequência na faixa de MHz,
  contada pelo PCNT do ESP32-S3. Um NTC 0603 por profundidade para compensação e temperatura do solo.
  Osciladores alimentados só durante a leitura.
- **Motivo:** sem corrosão nem desgaste ao cravar; vedação simples; frequência atravessa 40 cm de trilha sem degradar;
  MHz reduz o efeito da salinidade frente ao touch (kHz). Mesmo princípio das sondas comerciais de perfil em tubo.
- **Calibração:** fábrica (ar e água, gravado no dispositivo) + por tipo de solo no backend.
- **Riscos:** sensibilidade através da parede é premissa sem protótipo; plano de teste = curva de frequência em Latossolo seco/úmido/saturado.
  Plano B: janelas no tubo, sem mudar a PCB.
- **Descartado:** resistiva (corrosão, adubo); touch direto com trilhas longas (trilha também sente umidade, kHz); eletrodos expostos (desgaste, borda do FR4).

## 2026-11-12 · D6 · Design base do produto
- **Decisão:** visual de `renders/design-base-v1.jpg` (ver `docs/design-produto.md`). A mecânica executa o que o hardware definir.

## 2026-11-12 · D5 · Roadmap de custo (v2)
- **Ideia:** migrar para SoC único MCU + LoRa (ex.: STM32WL) para reduzir custo e consumo. Citar no pitch.

## 2026-11-12 · D7 · Wi-Fi na demo, LoRa no produto
- A PCB mantém Wi-Fi (ESP32-S3) e LoRa (SX1262). Demo e bancada usam Wi-Fi; campo usa LoRa P2P → LoRaWAN no roadmap.

## 2026-11-12 · D8 · Bancada física para a demonstração
- ESP32 de desenvolvimento + sensores comprados, mesmo firmware e protocolo. Permite o roteiro de leitura real e queda de rede.
  A PCB-produto é apresentada em 3D, BOM, energia e simulação.

## 2026-11-12 · D9 · Duas interfaces
- WhatsApp (áudio/texto) + LEDs para o produtor; PWA para técnico, cooperativa e fazendas maiores.

## 2026-11-12 · D10 · Protocolo de dados alinhado ao esquema do time
- Um evento por profundidade no backend; pacote com 2 temperaturas de solo e idade da leitura (ver `protocolo-dados.md`).

## 2026-11-12 · D11 · Uma submissão para as etapas local e mundial, em inglês
- A documentação enviada na etapa local não muda para a mundial. Toda documentação final em inglês.
- Narrativa: Uberlândia como caso principal (melhores dados e validação local) + prova curta de generalidade global.
- Novos artefatos de hardware (README, BOM, notas do esquemático) passam a ser escritos em inglês a partir de sexta.
- Demo: vídeo de até 30 s (guia de submissão 2025; confirmar 2026), com legendas em inglês se a narração for em outra língua.

## 2026-11-12 · D12 · Componentes principais (ver `component-selection.md`)
- ESP32-S3-MINI-1-N8 (menor e mais barato que o WROOM) · E22-900MM22S (SX1262, 10×10 mm, antena pelo IPEX do próprio módulo)
  · CN3058E + HY2112-BB (carga e proteção LiFePO4) · TPS63802 (3V3 buck-boost, 11 µA) · SHT40 · 74LVC1G14 ×2 · NTC 0603 ×2 · USB-C HRO + USBLC6.
- Sem load switch: osciladores e NTC alimentados por GPIO só durante a leitura.

## 2026-11-14 · D13 · Esquemático gerado por script
O esquemático KiCad é gerado por `hardware/tools/gen_kicad.py` a partir de uma descrição de nets em Python, e validado por `check_kicad.py`. Motivo: tempo de hackathon e reprodutibilidade (mesma entrada, mesma saída, diffs legíveis no git). Regra: ou se edita o script, ou se edita no KiCad e para de regenerar.

## 2026-11-14 · D14 · Antena do LoRa: pad + U.FL na placa
O E22-900MM22S só tem pad de antena (pino 6). Caminho: pad → resistor 0 Ω (casamento em pi, capacitores shunt DNP) → U.FL-R-SMT-1(80) na placa, trilha curta (<5 mm) de 50 Ω. Isso corrige a ideia anterior de usar o conector IPEX do módulo.

## 2026-11-14 · D15 · Um só codificador do pacote, testado
O formato de 25 bytes vive em `firmware/include/gaiapus_protocol.h` (C puro), usado por estaca, bancada, Wokwi e testes; o lado do gateway/backend é `firmware/tools/gaiapus_decode.py`. O firmware da bancada é executado no PC com mocks do Arduino e cada JSON publicado é conferido contra o decodificador. `device_id` = últimos 4 octetos do MAC em hex. `idade_min` em minutos reais.

## 2026-11-14 · D16 · Duas placas: cabeça + sonda
- **Cabeça** (`hardware/gaiapus-node`): ESP32-S3, LoRa, energia, SHT40, pluviômetro, LEDs, USB.
- **Sonda** (`hardware/gaiapus-probe`): tira de 22 × ~460 mm dentro do tubo de PVC 32 mm (DI ~27 mm), com resina. Eletrodos interdigitados a 15 e 40 cm, e o oscilador 74LVC1G14 + NTC colados a cada eletrodo.
- Motivo: o oscilador tem de ficar junto do eletrodo (fio longo soma capacitância parasita e degrada a medida); placa longa única seria cara e frágil.
- Ligação: JST-SH 10P SMD (SM10B-SRSS-TB, LCSC C160409) nas duas placas + cabo 1:1. Pinagem: 1 GND, 2 OSC15_FREQ, 3 GND, 4 OSC40_FREQ, 5 GND, 6 PWR_OSC15, 7 PWR_OSC40, 8 PWR_NTC, 9 NTC15_ADC, 10 NTC40_ADC (GND entre as linhas de frequência).
- Na sonda: resistor série de 100 Ω na saída de cada oscilador e ponto de teste da frequência.

## 2026-11-14 · D17 · Footprints: LCSC importado + eletrodo paramétrico
Componentes com código LCSC recebem footprint e modelo 3D do próprio LCSC via `easyeda2kicad` (`hardware/tools/import_lcsc.cmd`), conferidos por `apply_lcsc.py` (número de cada pino do símbolo precisa existir no footprint). O eletrodo é cobre nosso: `gen_footprints.py` gera `ELECTRODE_IDC_18x40` (9 dedos de 2 mm, folga 2,5 mm, cobre sob máscara, sem cobre no verso). MOSFET da proteção trocado para HXY 8205A (C5148694): o Fortune FS8205A saiu de linha no LCSC.

## 2026-11-14 · D18 · Contornos das placas (proposta, mecânica confirma)
- **Cabeça:** 90 × 50 mm, cantos r4, 4 furos M3; suporte da 18650 (77 × 21 mm) no **lado de baixo**; ESP32 com antena na borda (sem cobre embaixo), LoRa + U.FL no canto oposto; LEDs na borda frontal; SHT40 numa ilha isolada por rasgo de 1 mm em L.
- **Sonda:** 22 × 450 mm (JLCPCB aceita placa única até 400 × 500 mm). Superfície do solo assumida 20 mm abaixo da borda superior; eletrodos centrados a 170 e 420 mm da borda (15 e 40 cm de profundidade).
- Tudo parametrizado em `hardware/tools/gen_pcb_outline.py`.

## 2026-11-14 · D19 · Roteamento
- **Sonda:** roteada por `route.py` (12/12 redes, 0 violações no `verify_pcb.py`). Pour de GND nas duas faces, sem pour a 2 mm dos eletrodos; linhas de 40 cm passam pelo verso atrás do eletrodo de 15 cm.
- **Cabeça:** posicionamento corrigido (BT1 colidia com a perna PTH do USB-C = curto VBAT-GND; L1 do lado errado do TPS63802). Roteadas por script só as redes críticas (antena, laço do conversor, VBAT, +3V3); o resto fica para o Freerouting (plugin do KiCad), que tem rip-up. Área sem cobre sob a antena do ESP32.
- Largura limitada pela menor ilha: VBAT/+3V3 a 0,3 mm e SW_L1/SW_L2 a 0,2 mm nos pinos de 0,5 mm do TPS63802 — alargar depois de sair dos pinos.

## 2026-11-14 · D20 · Cabeça: novo posicionamento e roteamento
- Planta guiada pelas conexões (`hardware/tools/place_head.py`): ESP32 no canto superior esquerdo (antena na borda), conversor no centro superior (inalterado), LoRa no canto superior direito com caminho de RF U5.6 → R10 → J2 reto (~4 mm), proteção da bateria à direita junto do pad negativo do BT1, borda inferior com sonda, USB-C, LEDs, solar e chuva, SHT40 na ilha.
- Roteado por `route.py` com rip-up: 50 de 52 redes, 0 violações no `verify_pcb.py`. Faltam PWR_OSC40 e CHG_DONE_N (sinais curtos, terminar no roteador interativo do KiCad). GND por vias de costura + pours nas duas faces.

## 2026-11-14 · D21 · Cabeça em 4 camadas
- Pilha: F.Cu (sinais) / In1.Cu (plano de GND inteiro) / In2.Cu (plano +3V3, usado também por 10 sinais, 231 mm) / B.Cu (sinais). JLCPCB JLC04161H-7628, 1,6 mm.
- Motivo: em 2 camadas o roteamento parava em 50/52 com 188 vias, GND picotado e sem plano de referência para a antena. Em 4 camadas: 51/51 redes roteadas (GND e +3V3 pelos planos), 0 violações no `verify_pcb.py`, todos os pinos de GND/+3V3 com via ao plano, plano +3V3 contínuo (16 vias numa só região, 85 % da placa).
- Trilha de RF 0,35 mm sobre o plano de GND (estimativa de 50 Ω, confirmar na calculadora da JLCPCB). Área sem cobre sob a antena do ESP32 nas 4 camadas.
- A sonda continua em 2 camadas (um plano atrás dos eletrodos roubaria sensibilidade).
