# ADR-001: Arquitetura Bootstrap para Detecção de Habitações

## Status
**Aceito** — 2026-04-19

## Contexto

O município de Paulista-PE precisa identificar habitações (formais e informais)
em imagens aéreas para subsidiar políticas habitacionais e cruzar com dados do
CadÚnico. O desafio central é: **não existe dataset rotulado específico para a
região**. Modelos pré-treinados (SpaceNet, etc.) detectam construções genéricas
mas geram muitos falsos positivos no contexto local (galpões, quadras, igrejas).

## Decisão

Adotamos uma **arquitetura de 2 estágios com bootstrap iterativo**:

### Stage 1 — SpaceNet (Detector genérico)
- Usa modelo pré-treinado no dataset SpaceNet (satélite global).
- Gera **candidatos** (bounding boxes de possíveis construções).
- Threshold baixo (0.3) para maximizar recall — queremos pegar tudo.
- Saída: lista de recortes (crops) com coordenadas.

### Stage 2 — Bootstrap Classifier (Filtro local)
- Classificador binário treinado **com imagens locais de Paulista-PE**.
- Entrada: crops do Stage 1.
- Saída: "é habitação" ou "não é habitação".
- Threshold alto (0.7) para maximizar precision — queremos certeza.

### Ciclo Bootstrap
```text
1. SpaceNet gera candidatos em imagens de Paulista
2. Humano revisa amostra → rotula positivos e negativos
3. Treina Bootstrap Classifier com esses rótulos
4. Classifier filtra próxima rodada de candidatos
5. Humano revisa apenas os duvidosos → refina dataset
6. Retreina → melhora → repete
