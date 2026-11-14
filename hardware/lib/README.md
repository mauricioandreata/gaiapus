# Bibliotecas do projeto

Tudo que não vem da biblioteca padrão do KiCad 8 fica aqui, para o projeto abrir igual em qualquer computador.

- `symbols/gaiapus.kicad_sym`: símbolos próprios (módulo LoRa, carregador etc.)
- `footprints/gaiapus.pretty/`: footprints próprios (eletrodos da sonda, módulos)
- `3dmodels/`: arquivos STEP. No footprint, referencie com `${KIPRJMOD}/../lib/3dmodels/<arquivo>.step`

Ao importar do LCSC/EasyEDA (por exemplo com `easyeda2kicad`), salve o resultado aqui e anote o código LCSC no campo `LCSC` do símbolo.
