# Contrato de Dados: Busca Operacional

## Objetivo

Definir os dados necessários para que um usuário busque uma matrícula, transformador, alimentador, subestação ou coordenada e o sistema encontre o território elétrico correspondente.

## Casos de busca

O sistema deve aceitar:

- matrícula ou identificador operacional da unidade consumidora
- código do transformador
- código do alimentador
- código da subestação
- coordenadas latitude/longitude

## Consulta por matrícula

Campos mínimos esperados:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| customer_id | texto | sim | Identificador operacional da unidade consumidora |
| transformer_code | texto | sim | Código do transformador associado |
| feeder_code | texto | sim | Código do alimentador |
| substation_code | texto | sim | Código da subestação |
| reference_month | texto | sim | Mês de referência |
| customer_status | texto | não | Status operacional |
| consumer_class | texto | não | Classe de consumo agregável |

## Consulta por transformador

Campos mínimos:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| transformer_code | texto | sim | Código do transformador |
| feeder_code | texto | sim | Código do alimentador |
| substation_code | texto | sim | Código da subestação |
| latitude | decimal | sim | Latitude |
| longitude | decimal | sim | Longitude |
| city | texto | sim | Município |
| neighborhood | texto | sim | Bairro/localidade |
| customer_count | inteiro | sim | Total de clientes vinculados |

## Consulta por alimentador

Campos mínimos:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| feeder_code | texto | sim | Código do alimentador |
| substation_code | texto | sim | Código da subestação |
| transformer_count | inteiro | sim | Quantidade de transformadores |
| customer_count | inteiro | sim | Quantidade de clientes |
| city | texto | sim | Município principal ou área atendida |

## Consulta por subestação

Campos mínimos:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| substation_code | texto | sim | Código da subestação |
| substation_name | texto | não | Nome da subestação |
| latitude | decimal | sim | Latitude |
| longitude | decimal | sim | Longitude |
| feeder_count | inteiro | sim | Quantidade de alimentadores |
| transformer_count | inteiro | sim | Quantidade de transformadores |

## Consulta por coordenadas

Entrada:

```json
{
  "latitude": -7.9401,
  "longitude": -34.8734
}