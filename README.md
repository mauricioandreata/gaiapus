# Gaiapus · Field Shift (NASA Space Apps 2026)

Equipe **Gaiapus** · Desafio *Field Shift: Adapting Farms with NASA Data*.

Ferramenta de apoio à decisão de rotação de culturas que funde dados de satélite da NASA
(POWER, GPM, SMAP, MODIS/Landsat, SRTM) com uma **estaca de solo** IoT de baixo custo.

> A ferramenta sugere e explica; a decisão final é sempre do agricultor e do agrônomo local.

## Os três degraus do produto

| Degrau | Quem | No campo |
|---|---|---|
| 0 · Satélite | Qualquer produtor, custo zero | Nada, só a localização |
| 1 · Estaca | Pequena propriedade | 1 estaca solar + gateway comunitário |
| 2 · Rede | Médias e grandes | Várias estacas por zona de manejo |

## Estrutura deste repositório

| Pasta | Conteúdo | Dono |
|---|---|---|
| `docs/` | Requisitos, decisões (ADR), componentes, protocolo de dados | Hardware |
| `hardware/gaiapus-node/` | Projeto KiCad 8 da estaca (esquemático + PCB) | Hardware |
| `hardware/lib/` | Símbolos, footprints e modelos 3D próprios do projeto | Hardware |
| `hardware/datasheets/` | PDFs dos componentes escolhidos | Hardware |
| `power/` | Orçamento de energia (`power_budget.py`) | Hardware |
| `bom/` | Lista de materiais com custos (1 un. e 1.000 un.) | Hardware |
| `firmware/` | Firmware ESP32-S3 | Hardware / Software |
| `sim/wokwi/` | Simulação do nó no Wokwi | Hardware |
| `mechanical/` | Estaca, case IP65, pluviômetro (CAD, STEP, renders) | Mecânica |
| `renders/` | Imagens finais para o pitch | Todos |

## Regras de projeto de hardware

1. **Tudo SMD direto na placa.** Módulos certificados (ESP32-S3, LoRa SX1262) com terminais
   castelados soldados na PCB. Sem barra de pinos, sem soquetes, sem placas de desenvolvimento.
2. Conectores externos (painel, pluviômetro, antena, USB-C) também SMD.
3. Todo componente precisa de: footprint, modelo 3D e código LCSC (para custo e montagem JLCPCB).
4. Toda escolha relevante vai para `docs/decisoes.md` com o motivo.

## Calendário

| Dia | Hardware |
|---|---|
| Qui 12 (noite) | Repositório, decisões de arquitetura |
| Sex 13 | Datasheets, componentes, símbolos/footprints, energia preliminar |
| Sáb 14 | Esquemático completo; firmware simulado no Wokwi enviando dados |
| Dom 15 | PCB + render 3D, BOM com custos, encaixe no case, autonomia final |

## Primeiros passos

```bash
cd Documents/gaiapus
git init
git add .
git commit -m "Estrutura inicial"
```

Depois crie o repositório no GitHub (ou pelo GitHub Desktop) e faça o push.
