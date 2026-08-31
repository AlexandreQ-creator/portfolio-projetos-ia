## Ecossistema de Assistentes de IA Generativa (GenAI)

Período: out/2023 – jul/2026 · Contexto: Procter & Gamble

### Visão geral

Idealização e desenvolvimento de um ecossistema integrado de assistentes de IA (Large Language Models via ChatGPT e Gemini) para eliminar gargalos de tarefas manuais e responder dúvidas técnicas operacionais, usando Context Engineering alimentado por bases de conhecimento próprias, consultadas via RAG (Retrieval-Augmented Generation).

Nível de detalhe: apenas arquitetura e metodologia. Nenhum prompt de produção, dado sensível ou processo interno de empregador é reproduzido aqui.

### Arquitetura

O ecossistema é composto por 4 assistentes, cada um estruturado como um agente com persona, tom e escopo definidos, seguindo a técnica de prompt Persona, Tom, Especificidades e Contexto.

Py. Assistente técnico dedicado a consultas rápidas e tratamento de erros em Excel, Power Query, Macros, SAP, Salesforce, KNIME e Blue Yonder TMS, com aprendizado incremental a partir do uso.

Assistente de Avaliação de Desempenho. Apoio à redação de planos de desenvolvimento individual e autoavaliações de performance, com busca de referências em repositório de conhecimento dedicado.

Redator de Texto. Sumarização e resposta objetiva de e-mails, conversas do Teams e transcrições de reuniões.

Prompt Master. Meta-prompt de engenharia recursiva, que estrutura a criação de novos assistentes seguindo o mesmo framework (Persona, Tom, Especialidades, Especificidades, Contexto e Critérios), reduzindo alucinações e inconsistências.

### Evolução

A prática evoluiu de prompts avulsos para skills estruturadas — instruction sets reutilizáveis em formato Markdown/YAML — indo além do prompt único para sistemas de comportamento versionáveis, com regras de negócio, persona e lógica condicional bem definidas.

### Impacto

Ganho estimado de 30% de produtividade do time em rotinas administrativas repetitivas. Ferramentas disponibilizadas em regime de self-service para os usuários finais, em uso ativo até hoje.

### Competências aplicadas

RAG (Retrieval-Augmented Generation) · Inteligência Artificial · Context Engineering · Prompt Engineering

Voltar ao índice: ../README.md
