# Divergências entre a pesquisa do time (slides) e a frente de hardware

| # | Tema | Time (slides) | Hardware | Proposta de consenso |
|---|---|---|---|---|
| 1 | Alcance geográfico | Foco em Uberlândia e categoria Local Impact (categoria de 2026 a confirmar) | Motor genérico, Uberlândia como exemplo, demo em 2ª região para a fase mundial | Piloto em Uberlândia na etapa local; motor parametrizado por região e demo em outra região do mundo para a final |
| 2 | Interface | App web instalável (PWA) | WhatsApp com áudio + LEDs na estaca | Ambos: WhatsApp/LEDs para o produtor, PWA para técnico e fazenda maior |
| 3 | Papel do hardware | Opcional, 1 ponto e 1 profundidade, ESP32 genérico | Produto completo e diferencial: estaca, PCB, case, BOM, energia | Hardware opcional para o usuário, mas central no pitch como produto |
| 4 | Variáveis medidas | Umidade e temperatura do solo em 1 profundidade | Umidade e temperatura em 2 profundidades, chuva, temperatura e umidade do ar | Adotar as variáveis do hardware no esquema de dados |
| 5 | Conectividade | Wi-Fi na demo, LoRaWAN a avaliar | LoRa ponto a ponto + gateway comunitário | Wi-Fi na demo, LoRa no produto (a placa tem os dois) |
| 6 | Demo do dispositivo | Leitura física real e teste de queda de Wi-Fi | Protótipo virtual: 3D, simulação, sem placa física | Bancada física com ESP32 de desenvolvimento + estaca em 3D |
| 7 | Energia | Painel "eventual", após medir consumo | Solar + LiFePO4 dimensionado desde já | Usar o orçamento de energia; radiação da NASA POWER dimensiona o painel |
| 8 | Motor de decisão | Regras explicáveis + cenários históricos | Regras + balanço hídrico diário (chuva − evapotranspiração) corrigido pela estaca | Regras como base; balanço hídrico como evidência do risco de água |
| 9 | Dados NASA | POWER e IMERG; SMAP L4 e HLS como extensão | Inclui SRTM (declividade e erosão) e GRACE (contexto) | Incluir SRTM: o desafio pede redução de erosão |
| 10 | Calendário oficial | ZARC por município, cultura e solo | Não previa | Adotar o ZARC (ganho do time) |
| 11 | Estratégias comparadas | Até 3 sequências; tela mostra Plano A e B | 3 estratégias incluindo a rotação atual | Rotação atual sempre como referência + 2 alternativas (o desafio pede) |
| 12 | Como provar valor | Compreensão do produtor e coerência agronômica | Teste numa safra passada difícil + métricas (dias de solo nu, mm de água, risco de déficit) | Ambos, declarando que ganhos reais exigem campo |
| 13 | Público | Agricultura familiar e produção comercial em Uberlândia | Inclui idosos, baixa renda e outros países, custo mínimo | Mesmos degraus para todos; acessibilidade como critério de design |
