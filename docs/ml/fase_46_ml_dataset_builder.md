# Fase 46 - ML Dataset Builder

## Objetivo

A Fase 46 cria o primeiro dataset tabular preparado para Machine Learning no Area 51.

Essa fase usa como entrada a Feature Store Operacional criada na Fase 45 e gera um arquivo CSV consolidado com variáveis explicativas e um alvo inicial.

## Pré-requisitos

Antes de executar esta fase, rode:

```powershell
python -m scripts.import_concessionaria_csvs
python -m scripts.build_operational_feature_store