# Fase 55 - API do Agente Sintético de Perdas

## Objetivo

A Fase 55 expõe via API o agente sintético de perdas do Area 51.

O objetivo é permitir que o ranking, as métricas, o heatmap e o mapa HTML do agente sintético sejam consultados pelo backend, facilitando testes via Swagger, Postman e futura integração com frontend.

## Contexto

Até a Fase 54, o agente sintético era executado por scripts locais.

A Fase 55 transforma esse fluxo em endpoints FastAPI, permitindo consultar os resultados por HTTP.

## Endpoints adicionados

```text
GET /synthetic-loss-agent/health
POST /synthetic-loss-agent/run
GET /synthetic-loss-agent/metrics
GET /synthetic-loss-agent/ranking
GET /synthetic-loss-agent/heatmap/transformers
GET /synthetic-loss-agent/heatmap/feeders
GET /synthetic-loss-agent/heatmap/summary
GET /synthetic-loss-agent/map