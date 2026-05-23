# ADR-005: Monitoramento de Modelo em Produção

## Status
**Aceito** — 2026-04-19

## Contexto

Modelos de ML degradam silenciosamente ao longo do tempo. Causas comuns:
- **Data drift**: imagens de novas áreas têm características diferentes.
- **Concept drift**: novos tipos de construção que o modelo não conhece.
- **Degradação técnica**: mudança de resolução/provedor de imagens.

Sem monitoramento, o modelo pode estar errando 40% e ninguém percebe.

## Decisão

### Três pilares de monitoramento

#### 1. Prediction Logger
Registra **toda** inferência com:
- Timestamp, user, request_id.
- Confidence scores de cada detecção.
- Classes detectadas e quantidades.
- Latência (total, SpaceNet, Bootstrap).
- Dimensões da imagem, região, GPU utilizada.

#### 2. Drift Detector (PSI — Population Stability Index)

Compara a distribuição de confidence scores entre:
- **Referência**: distribuição do período de treino/validação.
- **Atual**: distribuição das últimas N predições.

