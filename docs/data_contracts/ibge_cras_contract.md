# Contrato de Dados: IBGE e CRAS Agregados

## Objetivo

Definir os dados territoriais e sociais necessários para cruzamento socioenergético no Area_51.

## IBGE

### Nome sugerido

ibge_sectors_real.csv

### Campos obrigatórios

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| sector_id | texto | sim | Código do setor censitário ou identificador territorial |
| city | texto | sim | Município |
| state | texto | sim | UF |
| neighborhood | texto | sim | Bairro/localidade |
| population | inteiro | sim | População agregada |
| households | inteiro | sim | Quantidade de domicílios |
| average_residents_per_household | decimal | sim | Média de residentes por domicílio |

### Campos recomendados

| Campo | Tipo | Descrição |
|---|---|---|
| centroid_lat | decimal | Latitude do centroide |
| centroid_lon | decimal | Longitude do centroide |
| geometry_wkt | texto | Polígono em WKT, se disponível |
| average_income | decimal | Renda média agregada, se disponível |

## CRAS/CadÚnico agregado

### Nome sugerido

cras_territories_real.csv

### Campos obrigatórios

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| territory_id | texto | sim | Identificador do território CRAS |
| cras_code | texto | sim | Código do CRAS |
| cras_name | texto | sim | Nome do CRAS |
| city | texto | sim | Município |
| state | texto | sim | UF |
| neighborhood | texto | sim | Bairro/localidade |
| assisted_families | inteiro | sim | Famílias acompanhadas/assistidas |
| vulnerable_families | inteiro | sim | Famílias vulneráveis agregadas |

### Campos recomendados

| Campo | Tipo | Descrição |
|---|---|---|
| extreme_poverty_families | inteiro | Famílias em extrema pobreza, agregado |
| centroid_lat | decimal | Latitude do centroide |
| centroid_lon | decimal | Longitude do centroide |
| geometry_wkt | texto | Polígono do território, se disponível |

## Restrições

Não incluir:

- CPF
- NIS
- nome de beneficiário
- endereço individual
- telefone
- qualquer identificador pessoal

## Vínculo territorial

Arquivo recomendado:

territory_links_real.csv

Campos:

```csv
area_id,sector_id,territory_id
area-001,sector-001,cras-territory-001