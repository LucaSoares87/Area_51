# Contrato de Dados: Perdas Mensais Reais

## Objetivo

Definir o layout mínimo necessário para alimentar o Area_51 com dados reais agregados por área operacional, transformador, alimentador ou subestação.

Este contrato deve ser usado para extração mensal de dados da concessionária.

## Nome sugerido do arquivo

monthly_losses_real.csv

## Granularidade esperada

Uma linha por área operacional ou transformador por mês.

## Campos obrigatórios

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| area_id | texto | sim | Identificador interno da área operacional usada pelo Area_51 |
| transformer_code | texto | sim | Código do transformador |
| latitude | decimal | sim | Latitude do transformador ou ponto central da área |
| longitude | decimal | sim | Longitude do transformador ou ponto central da área |
| neighborhood | texto | sim | Bairro/localidade |
| city | texto | sim | Município |
| feeder | texto | sim | Código do alimentador |
| customer_count | inteiro | sim | Quantidade de clientes vinculados ao transformador ou área |
| reference_month | texto | sim | Mês de referência no formato YYYY-MM |
| injected_energy_kwh | decimal | sim | Energia injetada, medida, estimada ou alocada para a área/trafo |
| billed_consumption_kwh | decimal | sim | Consumo faturado agregado dos clientes vinculados |

## Campos recomendados

| Campo | Tipo | Descrição |
|---|---|---|
| substation_code | texto | Código da subestação |
| installed_power_kva | decimal | Potência instalada do transformador |
| measurement_source | texto | measured, estimated, allocated ou unknown |
| measurement_quality_flag | texto | Indicador de qualidade da medição |
| technical_loss_estimate_kwh | decimal | Estimativa de perda técnica, se disponível |
| active_customers_count | inteiro | Clientes ativos no período |
| consumer_class_summary | texto/json | Resumo agregado por classe de consumo |

## Regra de cálculo inicial

perda_estimada_kwh = injected_energy_kwh - billed_consumption_kwh

perda_percentual = perda_estimada_kwh / injected_energy_kwh

## Restrições

Não incluir dados pessoais, como:

- nome de cliente
- CPF
- RG
- telefone
- endereço individual completo
- NIS
- dados sensíveis individuais

## Exemplo

```csv
area_id,transformer_code,latitude,longitude,neighborhood,city,feeder,customer_count,reference_month,injected_energy_kwh,billed_consumption_kwh
area-001,TR-001,-7.9401,-34.8734,Maranguape I,Paulista,AL-01,120,2026-05,12000,8300