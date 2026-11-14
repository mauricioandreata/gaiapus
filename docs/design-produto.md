# Design base do produto (v1)

Referência visual: `renders/design-base-v1.jpg` (imagem gerada por IA, aprovada pela equipe em 12/11/2026).
Serve como guia de estilo e de layout; as cotas reais vêm do CAD da mecânica.

## Linguagem visual
- Cor principal: **verde-oliva escuro fosco** em toda a peça (cabeça, haste, suportes).
- Acabamento plástico fosco, cantos arredondados, aparência robusta e "de campo".
- Detalhes em preto: antena, botão, cabo, grelhas.
- Etiqueta branca com QR code e o nome **Gaiapus**.

## Elementos e onde ficam

| Elemento | Posição no design | Impacto no hardware/mecânica |
|---|---|---|
| Painel solar | Topo da cabeça, retangular, levemente inclinado | Painel pequeno (cálculo mostra que < 1 W basta); conector SMD na PCB |
| Botão | Topo, à frente do painel, grande e redondo, ícone de liga | Botão tátil SMD sob membrana/atuador do case |
| Barra de LEDs | Face frontal, faixa translúcida horizontal: verde, amarelo, vermelho | 3 LEDs 0603 alinhados na borda da PCB + guia de luz |
| Antena | Externa, preta, lateral traseira, articulada | Conector SMA/U.FL na PCB + cabo curto até a carcaça |
| Ventilação | Grelha vertical na frente/lateral inferior da cabeça, com aba gota | Posição do SHT40, isolado termicamente do resto da placa |
| QR code | Lateral da cabeça | Etiqueta; nenhum impacto elétrico |
| Divisão da cabeça | Tampa superior + corpo inferior (linha de junta visível) | Junta com vedação (anel/gaxeta) para IP65 |
| Colar | Transição cabeça → haste | Ponto de vedação e de alívio de esforço da PCB |
| Haste | Tubo cilíndrico com ponta cônica | PCB-sonda corre dentro do tubo: largura da placa limitada pelo diâmetro interno |
| Pluviômetro | Copo com funil preso à haste por braçadeira, cabo preto até a cabeça | Conector SMD de 2 vias; cabo com prensa-cabo |

## Pontos a resolver (hardware + mecânica)
1. **Eletrodos dentro do tubo:** o sensor capacitivo mede através da parede do tubo? Opções: parede fina no trecho dos eletrodos, ou janelas com a PCB revestida em contato com o solo. Testar/decidir.
2. **Largura da PCB-sonda** = diâmetro interno do tubo menos folga. Definir diâmetro do tubo primeiro.
3. **Bateria 18650 (65 × 18 mm)** precisa caber na cabeça junto com a PCB principal.
4. **Pluviômetro na haste, perto do solo**, sofre respingo e sombra das plantas. Avaliar subir o copo ou fixá-lo no topo/estaca própria. O copo do render é pequeno para uma báscula: rever tamanho.
5. **Antena externa** aumenta alcance, mas é ponto frágil: avaliar antena interna na v2.
6. **Painel e LEDs no sol:** garantir contraste dos LEDs sob luz forte (guia de luz recuado).
