# Simulação Realista - Fase 42

## Objetivo

Esta fase cria uma simulação mais próxima do fluxo real esperado para o Area 51.

O sistema passa a consultar um banco SQLite local que simula dados da concessionária, cruza informações com arquivos simulados de CRAS e IBGE, gera um mapa interativo por coordenadas e permite baixar um CSV com o resultado consolidado.

## Fluxo demonstrado

1. O usuário informa latitude e longitude.
2. O sistema consulta transformadores próximos no banco local.
3. O sistema identifica o transformador mais próximo.
4. O sistema consulta clientes vinculados ao transformador.
5. O sistema consulta energia medida, energia recebida de GD e energia injetada.
6. O sistema cruza dados de casas e pessoas do CRAS.
7. O sistema cruza dados de casas e pessoas do IBGE.
8. O sistema cruza estimativa de telhados, quando disponível.
9. O sistema calcula média estimada de casas.
10. O sistema estima perda e prioridade.
11. O sistema gera mapa interativo.
12. O sistema permite baixar CSV.

## Comandos

Criar banco realista:

```powershell
python -m scripts.seed_realistic_demo_db