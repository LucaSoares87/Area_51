# Prontidão para Piloto - Area 51

## Objetivo

Este conjunto de documentos organiza a preparação do projeto Area 51 para execução de um piloto operacional em ambiente controlado.

O sistema tem como objetivo apoiar a análise de perdas, anomalias operacionais, geração distribuída, território, vulnerabilidade socioenergética e evidências por meio de dados elétricos, geográficos, cadastrais e imagens aéreas.

## Escopo do piloto

O piloto deve validar, em uma área limitada, a capacidade do sistema de:

- Consultar ativos por matrícula, transformador, alimentador, subestação e coordenadas.
- Cruzar perdas elétricas com ativos operacionais.
- Incorporar estimativas de geração distribuída e geração solar.
- Relacionar áreas operacionais com dados territoriais, IBGE e CRAS.
- Exibir ranking de prioridade socioenergética.
- Visualizar mapa operacional de transformadores.
- Receber imagem aérea para estimativa de telhados.
- Apoiar a decisão de inspeção, priorização e análise de campo.

## Premissas

- O piloto deve usar dados controlados, auditáveis e autorizados pela concessionária.
- Dados sensíveis devem ser tratados conforme política interna de segurança e privacidade.
- Os resultados do sistema devem ser considerados apoio à decisão, não decisão automática final.
- A validação deve ser feita com acompanhamento técnico de operação, perdas, medição, tecnologia e áreas de negócio.

## Documentos desta pasta

- `checklist_piloto.md`: lista de verificação antes da execução do piloto.
- `dados_necessarios_concessionaria.md`: dados que devem ser solicitados à concessionária.
- `guia_operacao_local.md`: instruções para execução local do sistema.
- `roteiro_demonstracao.md`: roteiro sugerido para apresentação do projeto.
- `riscos_e_proximas_fases.md`: riscos conhecidos e evolução após o piloto.

## Estado atual do projeto

O projeto encontra-se em nível de MVP técnico avançado, com APIs, testes automatizados, interface operacional, login integrado ao fluxo de autenticação existente, mapa operacional e camadas de análise territorial e socioenergética.

A próxima validação relevante é substituir dados simulados por dados reais controlados e executar um ciclo de análise com acompanhamento da concessionária.