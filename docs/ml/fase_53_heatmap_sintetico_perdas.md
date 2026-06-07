# Fase 53 - Heatmap Sintético de Perdas

## Objetivo

A Fase 53 adiciona a geração de heatmap sintético de perdas por transformador e alimentador.

O objetivo é transformar as tabelas sintéticas importadas na Fase 51 em relatórios auditáveis para visualização de áreas com maior e menor concentração de perdas.

## Contexto

Esta fase atende diretamente ao objetivo do projeto de criar um mapa de calor capaz de mostrar locais de maior e menor perda por transformador e alimentador.

A geração ainda é sintética, mas prepara a estrutura para substituição posterior por dados reais.

## Entradas

A fase depende das tabelas SQLite:

```text
synthetic_transformer_heatmap
synthetic_feeder_heatmap