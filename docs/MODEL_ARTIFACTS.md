# Model Artifacts

## Objetivo

Este documento define como o projeto Area 51 - Aerial Housing Detection deve tratar artefatos de modelos de machine learning.

## Contexto

O treinamento YOLO gera arquivos locais como pesos, métricas, gráficos, logs e caches.

Esses artefatos são importantes para análise técnica, mas não devem ser commitados diretamente no Git comum quando forem pesados, temporários ou dependentes da máquina local.

## Artefatos gerados pelo treino

O script principal de treinamento é:

```powershell
python -m scripts.train_yolo --dataset data\yolo\dataset.yaml --model yolov8n.pt --epochs 1 --batch 1 --imgsz 416 --device cpu --quick