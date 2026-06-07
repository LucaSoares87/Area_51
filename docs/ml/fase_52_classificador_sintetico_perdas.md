# Fase 52 - Classificador Sintético de Perdas

## Objetivo

A Fase 52 adiciona um classificador sintético para o agente identificador de perdas do Area 51.

O objetivo é simular um modelo supervisionado capaz de priorizar transformadores e meses com maior probabilidade de perda ou irregularidade, usando dados sintéticos e sem exposição de dados reais protegidos por LGPD.

## Contexto

O objetivo final do projeto é construir um agente capaz de:

- identificar perdas e suspeitas de irregularidade;
- usar dados operacionais por transformador e alimentador;
- considerar estimativa de casas por CRAS, IBGE e imagem;
- apoiar a criação de mapa de calor de perdas;
- priorizar inspeções de campo.

Esta fase atende a primeira camada desse objetivo: classificação e priorização supervisionada em ambiente sintético.

## Entrada

A fase depende da tabela SQLite:

```text
synthetic_loss_agent_dataset