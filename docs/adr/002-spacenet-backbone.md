# ADR-002: SpaceNet como Backbone de Detecção

## Status

Aceito — 2026-04-19

## Contexto

O Stage 1 do pipeline precisa de um detector de construções pré-treinado capaz
de gerar candidatos (bounding boxes) a partir de imagens aéreas. O modelo deve
funcionar sem treinamento adicional e ser compatível com imagens de satélite.

Opções avaliadas:

| Modelo | Dataset de treino | Resolução | Licença | Peso |
|---|---|---|---|---|
| SpaceNet | SpaceNet 1-7 (satélite global) | 30-50 cm/px | Apache 2.0 | ~170 MB |
| YOLOv8 | COCO (objetos gerais) | Variável | AGPL 3.0 | ~25 MB |
| Mask R-CNN | COCO | Variável | BSD | ~180 MB |
| SAM (Meta) | SA-1B | Variável | Apache 2.0 | ~2500 MB |

## Decisão

SpaceNet como backbone do Stage 1.

Justificativas:

1. Treinado especificamente em imagens aéreas e de satélite.
2. Detecta footprints de construções, que é exatamente o domínio do projeto.
3. Licença Apache 2.0 permite uso governamental sem restrição.
4. Tamanho gerenciável (~170 MB) para infraestrutura municipal.
5. Comunidade ativa com modelos publicados por vencedores de competições.

Modelo específico utilizado:

- Backbone: ResNet-34 FPN (Feature Pyramid Network)
- Treinado em: SpaceNet 2 (Las Vegas) e SpaceNet 4 (multi-cidade)
- Output: bounding boxes e masks de construções
- Apenas bounding boxes são utilizados no pipeline (masks descartados)

Configuração de thresholds:

```python
SPACENET_CONFIDENCE_THRESHOLD = 0.3
SPACENET_NMS_THRESHOLD = 0.4
