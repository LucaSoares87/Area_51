# Dados Necessários da Concessionária - Area 51

## 1. Objetivo

Este documento lista os dados mínimos e desejáveis que devem ser solicitados à concessionária para execução de um piloto controlado do Area 51.

A finalidade é substituir dados simulados por dados reais auditáveis, permitindo validar a análise de perdas, geração distribuída, território, IBGE, CRAS, mapa operacional e priorização socioenergética.

## 2. Princípio geral

O sistema depende de vínculos consistentes entre:

- Unidade consumidora.
- Transformador.
- Alimentador.
- Subestação.
- Coordenadas.
- Histórico de consumo.
- Histórico de perdas.
- Geração distribuída.
- Território.
- Indicadores socioeconômicos.
- Evidências de campo.

Quanto melhor o vínculo entre esses dados, mais confiável será o resultado do piloto.

## 3. Dados cadastrais de unidades consumidoras

Solicitar base com uma linha por unidade consumidora ativa ou relevante para a área piloto.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| customer_id | Matrícula ou identificador da unidade consumidora | Sim |
| customer_status | Situação da unidade consumidora | Desejável |
| customer_class | Classe ou grupo de consumo | Desejável |
| city | Município | Sim |
| neighborhood | Bairro ou localidade | Sim |
| address_reference | Referência de endereço sem exposição excessiva de dado pessoal | Desejável |
| latitude | Latitude da unidade consumidora | Desejável |
| longitude | Longitude da unidade consumidora | Desejável |
| transformer_code | Código do transformador associado | Sim |
| feeder_code | Código do alimentador associado | Sim |
| substation_code | Código da subestação associada | Sim |

Observação: se houver restrição de privacidade, o endereço pode ser anonimizado ou substituído por referência operacional.

## 4. Dados de ativos elétricos

Solicitar base de ativos elétricos da área piloto.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| transformer_code | Código do transformador | Sim |
| feeder_code | Código do alimentador | Sim |
| substation_code | Código da subestação | Sim |
| area_id | Identificador da área operacional | Sim |
| latitude | Latitude do transformador | Sim |
| longitude | Longitude do transformador | Sim |
| city | Município | Sim |
| neighborhood | Bairro ou localidade | Sim |
| installed_capacity_kva | Potência instalada do transformador | Desejável |
| customer_count | Quantidade de clientes associados | Desejável |
| asset_status | Situação do ativo | Desejável |

## 5. Dados de perdas mensais

Solicitar histórico mensal de perdas por transformador, alimentador ou área operacional.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| reference_month | Mês de referência no formato AAAA-MM | Sim |
| transformer_code | Código do transformador | Desejável |
| feeder_code | Código do alimentador | Sim |
| substation_code | Código da subestação | Desejável |
| area_id | Área operacional | Sim |
| supplied_energy_kwh | Energia fornecida | Desejável |
| billed_energy_kwh | Energia faturada | Desejável |
| estimated_loss_kwh | Perda estimada em kWh | Sim |
| loss_percent | Percentual de perda | Sim |
| recurrence_count | Recorrência histórica de perda | Desejável |

Observação: se a perda for calculada em outro nível, como alimentador ou conjunto, informar a granularidade disponível.

## 6. Dados de inspeções e irregularidades

Solicitar base histórica de inspeções, quando disponível.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| inspection_id | Identificador da inspeção | Desejável |
| customer_id | Matrícula da unidade consumidora | Desejável |
| transformer_code | Transformador associado | Desejável |
| reference_date | Data da inspeção | Sim |
| result | Resultado da inspeção | Sim |
| irregularity_confirmed | Indica se houve irregularidade confirmada | Sim |
| irregularity_type | Tipo de irregularidade | Desejável |
| recovered_energy_kwh | Energia recuperada | Desejável |
| notes | Observações operacionais | Desejável |

Estes dados ajudam a validar se o ranking do sistema aponta áreas coerentes com ocorrências reais.

## 7. Dados de geração distribuída

Solicitar dados mensais de clientes com geração distribuída na área piloto.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| reference_month | Mês de referência no formato AAAA-MM | Sim |
| customer_id | Matrícula da unidade consumidora | Sim |
| transformer_code | Código do transformador associado | Desejável |
| feeder_code | Código do alimentador associado | Desejável |
| installed_power_kwp | Potência instalada do sistema | Desejável |
| generated_energy_kwh | Energia gerada no mês | Sim |
| consumed_energy_kwh | Energia consumida no mês | Sim |
| injected_energy_kwh | Energia injetada na rede | Sim |
| compensated_energy_kwh | Energia compensada | Desejável |
| net_balance_kwh | Saldo líquido entre geração e consumo | Desejável |

## 8. Regra de interpretação da GD

Para o piloto, é importante separar perda real de efeito de geração distribuída.

Exemplo:

- Cliente gerou 100 kWh.
- Cliente consumiu 80 kWh.
- Cliente injetou 20 kWh na rede.

Sem considerar esse balanço, parte da energia pode ser interpretada incorretamente como perda.

O sistema deve usar os dados de GD para ajustar a perda estimada por transformador, alimentador ou área operacional.

## 9. Dados territoriais

Solicitar tabela que relacione área elétrica com território.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| area_id | Área operacional | Sim |
| transformer_code | Transformador associado | Desejável |
| feeder_code | Alimentador associado | Desejável |
| ibge_sector_id | Código do setor censitário IBGE | Sim |
| cras_territory_id | Código ou nome do território CRAS | Sim |
| city | Município | Sim |
| neighborhood | Bairro ou localidade | Desejável |

## 10. Dados IBGE

Solicitar dados agregados por setor censitário ou usar fonte pública oficial, conforme disponibilidade.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| ibge_sector_id | Código do setor censitário | Sim |
| city | Município | Sim |
| population | População estimada | Sim |
| households | Quantidade de domicílios | Sim |
| average_income | Renda média ou indicador equivalente | Desejável |
| vulnerability_index | Indicador de vulnerabilidade, se houver | Desejável |

## 11. Dados CRAS

Solicitar dados de territórios CRAS ou referência territorial equivalente.

Campos mínimos:

| Campo | Descrição | Obrigatório |
|---|---|---|
| cras_territory_id | Identificador do território CRAS | Sim |
| cras_name | Nome do CRAS | Desejável |
| city | Município | Sim |
| neighborhood | Bairro ou área de abrangência | Desejável |
| vulnerability_level | Nível de vulnerabilidade | Desejável |
| families_assisted | Famílias acompanhadas | Desejável |
| notes | Observações territoriais | Desejável |

## 12. Imagens aéreas

Para análise de telhados, solicitar ou produzir imagens da área piloto.

Opções aceitáveis:

- Imagem do Google Earth.
- Print aéreo com boa resolução.
- Ortofoto.
- Imagem de drone.
- Imagem georreferenciada, quando disponível.

Informações desejáveis:

| Campo | Descrição |
|---|---|
| area_id | Área correspondente |
| reference_date | Data aproximada da imagem |
| source | Origem da imagem |
| resolution | Resolução aproximada |
| notes | Observações sobre qualidade |

## 13. Parâmetros mínimos para uma primeira validação

Para uma validação mínima, solicitar pelo menos:

- Uma área piloto.
- Lista de transformadores da área.
- Lista de clientes por transformador.
- Perdas mensais por transformador ou alimentador.
- Coordenadas dos transformadores.
- Dados de GD por cliente ou por transformador.
- Imagem aérea da área.
- Vínculo com setor IBGE ou território CRAS.

## 14. Consultas ao banco de dados

Quando os dados forem extraídos por query, pedir à concessionária:

- Nome da tabela de clientes.
- Nome da tabela de ativos.
- Nome da tabela de medição.
- Nome da tabela de perdas.
- Nome da tabela de geração distribuída.
- Nome da tabela de inspeções.
- Nome dos campos de matrícula, transformador, alimentador e subestação.
- Periodicidade de atualização.
- Filtros necessários para selecionar a área piloto.
- Regras de negócio usadas no cálculo de perdas.

## 15. Validação de qualidade dos dados

Antes de importar, validar:

- Se todas as matrículas têm transformador associado.
- Se todos os transformadores têm alimentador.
- Se todos os alimentadores têm subestação.
- Se há coordenadas válidas.
- Se o mês de referência está padronizado.
- Se os valores de energia estão em kWh.
- Se há duplicidade de registros.
- Se há valores negativos sem justificativa.
- Se os dados de GD têm a mesma referência temporal dos dados de perdas.

## 16. Cuidados com privacidade

Evitar carregar dados pessoais desnecessários.

Preferir:

- Matrícula técnica.
- Código de ativo.
- Área operacional.
- Coordenadas de ativo.
- Indicadores agregados.

Evitar, quando possível:

- CPF.
- Nome completo de cliente.
- Telefone.
- Endereço completo.
- Dados sensíveis não necessários ao piloto.

## 17. Entregável esperado da concessionária

A concessionária deve entregar, para o piloto:

- Arquivos CSV, Excel ou acesso controlado por query.
- Dicionário de campos.
- Mês de referência.
- Área piloto definida.
- Responsável técnico por cada base.
- Regras de cálculo usadas.
- Limitações conhecidas dos dados.