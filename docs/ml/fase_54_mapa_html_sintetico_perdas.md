# Fase 54 - Mapa HTML Sintético de Perdas

## Objetivo

A Fase 54 adiciona uma visualização HTML sintética para o mapa de perdas do Area 51.

O objetivo é transformar as camadas sintéticas de transformadores e alimentadores em um mapa visual navegável, permitindo observar áreas de maior e menor criticidade operacional.

## Contexto

Esta fase atende diretamente ao objetivo do projeto de criar um mapa de calor para perdas por transformador e alimentador.

A visualização ainda usa dados sintéticos, sem exposição de dados reais protegidos por LGPD.

## Entradas

A fase depende das tabelas SQLite:

```text
synthetic_transformer_heatmap
synthetic_feeder_heatmap