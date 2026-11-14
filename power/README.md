# Orçamento de energia

```bash
python power/power_budget.py --help
python power/power_budget.py
```

Os padrões são estimativas. Ao escolher cada componente, troque o valor e registre a fonte:

| Parâmetro | Valor usado | Fonte (datasheet, página) |
|---|---|---|
| Sono profundo total | 25 µA | estimativa |
| MCU ativo | 35 mA | estimativa |
| SX1262 TX | 45 mA | estimativa |
| SX1262 RX | 5 mA | estimativa |
| Horas de sol pleno (Uberlândia) | 4,5 h | estimativa — calcular com NASA POWER |

O pior caso de geração solar deve vir do NASA POWER (radiação diária mínima histórica),
o que liga o hardware aos dados da NASA no pitch.
