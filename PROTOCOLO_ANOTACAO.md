# Protocolo de Anotação - Identificação Aérea

## Classe única: `telhado`

### Fase 1 - Classificação de tiles
- **POSITIVO**: tile com 1+ telhados visíveis (≥10% do tile)
- **NEGATIVO**: sem telhado ou fragmento mínimo (<10%)
- **INCERTO**: dúvida (sombra, resolução ruim)

### Fase 2 - Bounding Boxes (YOLOv8)
- Telhado 100% visível → anotar
- Telhado cortado ≥50% visível → anotar (box até a borda)
- Telhado cortado <50% visível → ignorar
- Telhado muito pequeno (<15x15 px) → ignorar

### Não anotar (é background)
Ruas, árvores, quintais, sombras, veículos, piscinas

### Regra de ouro
> Na dúvida, não anote. Consistência > Quantidade.
