# Contrato de Dados: Balanço Mensal de Geração Distribuída

## Objetivo

Definir o layout para integração dos dados de geração distribuída ao Area_51, permitindo ajustar a perda aparente por geração solar.

## Nome sugerido do arquivo

gd_monthly_balance_real.csv

## Granularidade esperada

Uma linha por área, transformador ou alimentador por mês.

## Campos obrigatórios

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| reference_month | texto | sim | Mês de referência no formato YYYY-MM |
| area_id | texto | sim | Área operacional associada |
| transformer_code | texto | sim | Código do transformador |
| feeder_code | texto | sim | Código do alimentador |
| gd_customer_count | inteiro | sim | Quantidade de clientes com GD na área |
| installed_capacity_kwp | decimal | sim | Potência instalada agregada em kWp |
| generated_energy_kwh | decimal | sim | Energia gerada estimada ou medida |
| consumed_energy_kwh | decimal | sim | Energia consumida pelo cliente/unidade ou grupo agregado |
| injected_to_grid_kwh | decimal | sim | Energia entregue à rede |
| received_from_grid_kwh | decimal | sim | Energia consumida da rede |
| compensated_energy_kwh | decimal | não | Energia compensada, se disponível |
| data_source | texto | sim | Origem do dado: api, csv, excel, database, estimated |

## Uso no Area_51

O dado de GD deve reduzir falso positivo de perda comercial/fraude.

Regra conceitual:

perda_ajustada = perda_estimada - geração_solar_relevante

A regra exata poderá variar conforme a qualidade do dado de GD.

## Exemplo

```csv
reference_month,area_id,transformer_code,feeder_code,gd_customer_count,installed_capacity_kwp,generated_energy_kwh,consumed_energy_kwh,injected_to_grid_kwh,received_from_grid_kwh,compensated_energy_kwh,data_source
2026-05,area-001,TR-001,AL-01,8,42.5,3200,2100,1100,900,700,api