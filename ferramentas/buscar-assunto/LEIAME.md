# buscar-assunto

Procura um assunto em todas as conversas com agentes de IA (Claude Code no
terminal e no VS Code, Claude Desktop, Hermes e sessões arquivadas) e mostra
em quais sessões ele apareceu, quem falou e o trecho. Das sessões do Claude
Desktop que só têm metadados, busca apenas no título.

**Problema:** depois de semanas usando vários agentes, a pergunta "em que
conversa a gente resolveu aquilo?" não tinha resposta rápida. As transcrições
somam centenas de megabytes, em formatos diferentes por aplicativo.

**Solução:** um script Python só com a biblioteca padrão, que não altera as
conversas (só grava o arquivo de pesquisa se você pedir), com menu numerado
para quem não quer decorar parâmetros.

## O que ele faz

- Lê as transcrições de cada aplicativo no formato próprio (`.jsonl` do
  Claude Code, metadados do Claude Desktop, `.md` arquivado, dumps do Hermes).
- Ignora o que não é conversa: lembretes do sistema, comandos internos,
  chamadas e resultados de ferramentas.
- Busca sem distinção de maiúsculas e acentos ("video" acha "vídeo").
- Junta a mesma sessão que aparece em duas pastas e marca a sessão retomada
  em outro aplicativo (ex.: `Terminal+VS Code`).
- Mostra uma barra de progresso, medida pelos bytes lidos.
- Mostra o resultado em tabela ajustada à largura do terminal.
- Salva a pesquisa, se você pedir, num **arquivo Markdown único e
  cumulativo**: cada pesquisa entra no fim com data e hora, filtros, id
  completo das sessões escolhidas e todos os trechos. Serve de contexto para
  a próxima conversa com um agente.

## Uso

```
python buscar_assunto.py                      # menu interativo
python buscar_assunto.py "placa de video"     # direto, saída em texto
python buscar_assunto.py RTX GTX --desde 2026-10-01 --so-usuario --json
```

Código de saída: 0 achou, 1 nada, 2 regex ou data inválida.

## Exemplo (dados fictícios dos testes)

```
Buscando [████████████░░░░░░░░░░░░░░░░░░]  40%

┌─────┬────────────┬──────────────────┬──────────┬──────┬──────┬───────────────────────────────┐
│  nº │ data       │ onde             │ id       │ você │   IA │ primeiro trecho               │
├─────┼────────────┼──────────────────┼──────────┼──────┼──────┼───────────────────────────────┤
│   1 │ 2026-03-02 │ PC arq.          │ abcd1234 │    1 │    1 │ comprar PLACA DE VIDEO nova   │
├─────┼────────────┼──────────────────┼──────────┼──────┼──────┼───────────────────────────────┤
│   2 │ 2026-05-03 │ Terminal         │ 11111111 │    1 │    0 │ qual a melhor placa de vídeo  │
│     │            │                  │          │      │      │ para o NAS?                   │
└─────┴────────────┴──────────────────┴──────────┴──────┴──────┴───────────────────────────────┘
2 sessões. "você" = suas mensagens que citam o assunto; "IA" = respostas.

E agora?
  1 - Buscar outro assunto
  2 - Mesmo assunto em outro lugar
  3 - Ver todos os trechos de uma sessão
  4 - Salvar pesquisa e resultado no arquivo de contexto
  0 - Sair
```

## Testes

```
python -m pytest test_buscar_assunto.py -q     # 23 testes, dados sintéticos
```

Os testes não leem nenhuma conversa real: montam transcrições falsas numa
pasta temporária e simulam as respostas do menu.

## Como foi feito

Escrito com Claude Code no papel de "Minion de Python", revisado por um
agente de QA e conferido pelo orquestrador (ver
[`projetos/04-servidor-caseiro-linux-ia.md`](../../projetos/04-servidor-caseiro-linux-ia.md)).
Cada mudança passou pelos testes antes de entrar no projeto.

*Gerado por: Claude Code — 2026-11-26 17:37 (LEIAME publico do buscar-assunto (aval do usuario))*
