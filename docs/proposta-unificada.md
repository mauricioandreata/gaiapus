# Proposta unificada · Gaiapus Field Shift

Junta a pesquisa do time de software/IA/agronomia (slides "Gaiapus · Field Shift") com a frente de hardware.

**Frase-guia:** planejar a próxima rotação sem deixar o solo descoberto — com dados da NASA para qualquer lugar
e uma estaca de baixo custo onde houver necessidade de precisão local.

## 1. Público e degraus
| Degrau | Público | Hardware | Interface |
|---|---|---|---|
| 0 · Regional | Qualquer produtor | Nenhum | WhatsApp (áudio/texto) e PWA |
| 1 · Estaca | Agricultura familiar | 1 estaca + gateway comunitário (cooperativa/assistência técnica) | WhatsApp + LEDs da estaca |
| 2 · Rede | Produção comercial | Estacas por zona de manejo | PWA por talhão |

Piloto: entorno de Uberlândia (1 produtor parceiro + 1 agrônomo). Generalidade: mesmo motor em outra região do mundo.

## 2. Dados
- **MVP:** NASA POWER (temperatura, radiação), GPM IMERG (chuva, 0,1°), **ZARC** (janela oficial por município/cultura/solo).
- **Extensão:** SMAP L4 (umidade superficial e zona radicular, 9 km), **HLS** (vegetação 30 m, solo nu), SRTM (declividade/erosão), SoilGrids (solo estimado).
- Origem, versão, resolução e datas preservadas; lacunas ≠ zero.

## 3. Motor de decisão
Filtrar (janela ZARC, solo, água, restrições) → gerar sequências (milho, soja, milheto, crotalária) → comparar por cenários
históricos e prioridades do produtor → explicar fonte e lacunas. A leitura calibrada da estaca atualiza o diagnóstico local.
IA (gradient boosting, previsão de umidade em 24 h) só após séries suficientes e teste contra persistência.

## 4. Dispositivo
- **Produto (Rev A, projeto completo):** estaca com PCB-sonda, umidade em 15 e 40 cm através da parede do tubo,
  2 NTC, ar (SHT40), pluviômetro, ESP32-S3 + LoRa SX1262 (Wi-Fi disponível), solar + LiFePO4, 3 LEDs + botão, fila offline.
  Entregáveis: esquemático, PCB 3D, BOM com custo, orçamento de energia, case, simulação Wokwi.
- **Bancada da demo (física):** ESP32 de desenvolvimento + sensores comprados, mesmo firmware e protocolo, via Wi-Fi.

## 5. Interfaces
- **Produtor:** WhatsApp com áudio e LEDs na estaca (idosos, baixa renda, celular simples).
- **Técnico/cooperativa/fazenda:** PWA em português, offline com data visível; cadastro, diagnóstico, comparação, detalhe do plano.

## 6. Roteiro da demonstração (≈ 5 min)
1. **Decisão:** cadastrar um talhão em Uberlândia; comparar até 3 sequências e mudar a prioridade (água × cobertura).
2. **Leitura real:** a bancada mede e a leitura chega ao talhão certo, com horário e profundidade.
3. **Falha de rede:** desligar o Wi-Fi, acumular, religar e reenviar sem duplicar.
4. **Produto:** estaca em 3D, PCB, custo e autonomia; simulação no Wokwi.
5. **Mundo:** trocar a coordenada para outra região e mostrar outras culturas e riscos.
6. **Impacto local:** feedback do produtor/agrônomo; limites declarados (ganhos exigem campo).

## 7. Frentes
| Frente | Responsável | Entrega |
|---|---|---|
| Hardware | Mauricio | Projeto da estaca + bancada da demo + firmware/protocolo |
| Mecânica | (definir) | Case, haste, pluviômetro, render e custo |
| Dados/IA | (definir) | Séries NASA, ZARC, catálogo, regras e API |
| App | (definir) | PWA + mensagem de WhatsApp simulada |
| Agronomia | (definir) | Validação de culturas, janelas e linguagem |

Critério de entrega comum: todas as frentes operam sobre o mesmo talhão e o mesmo contrato de dados (`protocolo-dados.md`).
