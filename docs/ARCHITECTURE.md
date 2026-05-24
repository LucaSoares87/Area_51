# Arquitetura do Projeto

## Visão geral

O projeto Area 51 - Aerial Housing Detection é um backend Python para estimar residências em áreas de risco a partir de imagens aéreas.

A arquitetura foi organizada para separar responsabilidades entre domínio, API, pipeline, detecção, relatórios e scripts operacionais.

## Objetivo arquitetural

O objetivo principal é manter um core simples, testável e preparado para evolução futura com modelos de visão computacional.

Nesta fase, o detector usa uma abordagem determinística inicial. A arquitetura já está preparada para receber modelos treinados, filtros auxiliares e integrações externas.

## Camadas principais do projeto

```text
config/
src/aerial_housing_detection/
scripts/
tests/
reports/
data/
models/