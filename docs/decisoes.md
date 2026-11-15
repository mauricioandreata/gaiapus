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

## 2026-11-14 · D22 · Correções do primeiro DRC da cabeça (233 erros → refeito)
- Curtos reais: U2 sobre Q1 e C12 sobre U5 (pads saindo do courtyard). U2/R3/C3 1,8 mm à esquerda, C12 girado e afastado. `check_placement.py` agora usa os pads reais e `verify_pcb.py` compara pads de componentes diferentes (os dois curtos antigos são detectados).
- Vias de GND a 0,1 mm entre si: o roteador mantém ≥ 0,8 mm entre centros de vias da mesma rede ou reaproveita a via vizinha.
- Furos de posicionamento do USB-C e do suporte 18650 viraram NPTH (footprint LCSC os marcava como PTH sem anel).
- Regras: VBAT/SW com mínimo 0,2 mm (pinos de 0,3 mm do TPS63802), isolamento de RF 0,2 mm, 0,09 mm só entre pads do próprio J5, ligação sólida ao pour em U4/J5.
- Pads custom: o traço de 0,05 mm do contorno entra na geometria.

## 2026-11-14 · D22 · Head case architecture (rev A)
- **Decision:** head PCB horizontal inside a 111 x 77 mm two-part case (lower shell + collar, lid); 18650 below the PCB; lid parting plane at z 33 with a D2 silicone cord; 4 M3 lid screws on heat-set inserts; PCB on 4 M3 standoffs. Solar panel (68 x 37) in a recess at the rear of the lid; button and LED bar in front of it.
- **Why the case is longer than the PCB:** the button (PCB y +2.6) has to stay in front of the panel, so the case extends 18.5 mm behind the PCB rear edge. The PCB antenna of the ESP32 ends up under the panel (Wi-Fi is demo only, D7).
- **Tube:** PVC D32 axis moved to y +4 so the cable slot (16 x 8) falls in front of the battery and inside the socket bore. Soil line = collar bottom (probe top 20 mm above it, D18).
- **Openings:** USB-C (front, silicone plug), PG7 gland for rain cable (front), SMA bulkhead for LoRa antenna (rear), 5 vent slots for the SHT40 with ePTFE patch (right), QR label (left).
- **Open:** tube wall (2.5 mm in D16 vs 1-1.5 mm in D4), switch and JST heights, real 18650 holder length (85.9 mm in the 3D model vs 90 mm board), 508 mm penetration depth. Details on sheet 1 of `mechanical/drawings`.
- **Files:** `mechanical/drawings/`, `mechanical/tools/case_params.py` (single source), `mechanical/cad/gaiapus_head_case.scad`.

## 2026-11-14 · D23 · Case rev B (replaces D22)
- **Why:** checking the exported boards (.glb/.step) showed the JST connectors J1, J3 and J4 plug in from the PCB front edge; rev A left only 2.8 mm to the wall. The USB-C 3D model is also 2.5 mm short of its footprint (the footprint is what gets built).
- **Decision:** 114 x 82 x 38.5 mm, two prints (base with collar, lid). Inside front wall 7 mm in front of the JSTs. Lid fixed by 4 x M3x30 **from below** into inserts (clean top, as in the design render). PCB on 4 standoffs with thread-forming screws. LEDs through 3 acrylic rods; TPU button cap. Tube centred under the head. Probe cable rises inside the tube through a floor slot; rain cable enters through a PG7 gland in the floor (drip-safe). SMA on the right wall, vent on the front next to the SHT40, QR on the left wall.
- **Checks:** 23/23 clearances OK (`mechanical/drawings/clearance-report-revB.md`).
- **Open:** real height of the 18650 holder with a cell (21 mm envelope assumed, model shows 14.9 without the cell); fix the USB-C 3D model offset in KiCad; first print to confirm button travel and lid fit.

## 2026-11-14 · D24 · Firmware da estaca (`firmware/src/stake/`)
- **Decisão:** firmware próprio da PCB, separado do da bancada, com o mesmo pacote. Três alvos no PlatformIO: `stake-lora` (produto), `stake-wifi` (demo com a placa real sem gateway) e `stake-wifi-demo` (ciclo de 30 min comprimido em 1 min para o vídeo).
- **Ciclo:** MCU sempre em deep sleep; acorda por timer (medição), reed do pluviômetro (conta pulso e volta a dormir) ou botão (mostra o LED por 8 s e mede/envia na hora; segurar 3 s = modo diagnóstico na USB, usado para a calibração de fábrica ar/água). Estado, fila e contadores na RAM RTC.
- **Downlink endereçado:** no ar o downlink vira `node_id + 2 bytes` (6 bytes), porque todas as estacas ouvem o gateway. O quadro funciona como ACK; sem ele a medição fica na fila (48 posições = 24 h) e é reenviada com `idade_min`. Bit3 de `flags` = carregando (informativo, compatível com o backend atual).
- **Umidade:** um oscilador ligado por vez (sem acoplamento entre eletrodos), PCNT por 10 ms normalizado, `raw = f/100`; `raw = 0` indica sonda desconectada.
- **LEDs:** acesos só após o botão e um flash curto no fim de cada ciclo. Piscar a cada 4 s exigiria acordar a cada 4 s e quase dobraria o consumo diário.
- **Testado no PC** com mocks (LoRa e Wi-Fi, drivers PCNT do IDF 4.4 e 5.x): 9 h simuladas com queda do gateway, chuva, botão, troca de intervalo, sonda desconectada, quadro de outra estaca, bateria fraca e reed preso. Falta validar na placa: RF, TCXO do E22, PCNT nos pads reais, corrente de sono.
- **Gateway:** ver D25.

## 2026-11-15 · D25 · Firmware do gateway comunitário (`firmware/src/gateway/`)
- **Hardware:** a própria placa-cabeça da estaca, alimentada pela USB-C (já tem ESP32-S3 com Wi-Fi e o E22-900MM22S): nenhuma placa nova. Alternativa de prateleira: Heltec WiFi LoRa 32 V3 (`gateway-heltec-v3`), só troca de pinos.
- **ACK só depois de publicar:** o gateway publica o JSON no MQTT e só então responde com o quadro de 6 bytes. Sem internet não há ACK e a medição fica na fila de 24 h da estaca. O gateway não precisa de armazenamento e não perde dado em queda de rede.
- **Comandos:** assina `gaiapus/devices/+/down` (retido), guarda até 64 estacas; estaca sem comando recebe LED apagado e 30 min.
- **Um só gerador de JSON** (`include/gaiapus_json.h`) para gateway e estaca Wi-Fi; mesmas configurações de rádio da estaca (`src/stake/config.h`).
- **Saúde:** `gaiapus/gateways/{id}/status` a cada 5 min; LEDs verde/amarelo/vermelho; reinicia após 30 min sem Wi-Fi e reinicializa o rádio após 15 min sem pacotes.
- **Testado no PC** contra o decodificador Python: comando retido, ao vivo, parcial e apagado, estaca desconhecida, ruído (quadro de outro gateway, versão errada, CRC), queda e volta da internet com reenvio.

## 2026-11-15 · D26 · Identificação e localização das estacas
- **Identidade:** `device_id` fixo (4 últimos bytes do MAC), em todo pacote, tópico e `event_id`.
- **Localização:** sem GPS na Rev A. A posição vem do celular na instalação, ao escanear o QR do case, e fica no backend (registro de instalação). Medição pertence à instalação ativa em `observed_at`. Detalhes em `protocolo-dados.md`.
- **QR com código de posse** gerado pelo backend: o número impresso sozinho não basta para cadastrar a estaca de outra pessoa.
- **`gateway_id` em cada uplink:** dá a área aproximada (raio do gateway comunitário) e permite alertar estaca ouvida por gateway inesperado (movida/furtada). Rádio não dá posição: RSSI/SNR só indicam qualidade do enlace e P2P não permite triangular.
- **Botão na instalação:** envia na hora e o app confirma "conectada via gateway X". Teste de campo no próprio ato de instalar.
- **Rev B:** GPS ou acelerômetro se for preciso detectar movimento sem depender do gateway.
