# Servidor caseiro em Linux operado com agentes de IA

Um PC antigo virou o servidor da casa: guarda as memórias da família, serve
filmes e fotos para a TV e o celular, e roda modelos de linguagem localmente.
Toda a operação foi conduzida em conversa com agentes de IA, por alguém que
não era administrador Linux, com regras que obrigam a IA a mostrar fontes e
conferir o que afirma.

## O problema

- Fotos, vídeos e documentos da família espalhados em HDs antigos, alguns
  falhando, sem saber o que era cópia de quê.
- DVDs e músicas sem um lugar único para assistir e ouvir em casa.
- O risco real de usar IA para administrar uma máquina: um comando
  inventado num disco errado apaga anos de fotos.

## A solução

**Máquina:** Intel Core i7-3770 de 3ª geração, GeForce GTX 1050 Ti,
Debian 12, HDs reaproveitados com uma cópia espelhada.

**Serviços:**

| Serviço | Para quê |
|---|---|
| Jellyfin | Filmes, séries, músicas e livros na TV e no celular |
| Immich | Fotos do celular, com reconhecimento de rosto na GPU |
| Ollama com CUDA | Modelos de linguagem locais, na placa de vídeo |
| Cópia noturna medida | Espelho do acervo, conferido antes e depois |
| Syncthing | Projeto sincronizado entre o PC e o servidor |

## Como a IA foi usada (o método)

O trabalho é coordenado por um agente orquestrador ("Dru"), uma skill do
Claude Code, com especialistas por área: discos, rede, GPU e LLM, Python,
Bash, QA e auditoria.

1. **A ficha é a verdade.** Hardware, distribuição e discos vêm de uma ficha
   gerada por script na própria máquina. O que a ficha não cobre vira "não
   sei, rode X para descobrir", nunca uma suposição.
2. **Base de conhecimento antes da web.** Fato pesquisado entra numa base
   própria, com fonte oficial e data de conferência. Número sem fonte é
   tratado como "não sabemos".
3. **Todo comando traz risco e fonte.** Cada comando entregue leva uma linha
   `RISCO: leitura | altera configuração | destrutivo` e uma linha `Fonte:`.
   Comando destrutivo diz em português o que apaga e espera o "sim".
4. **Disco de origem fica intacto** até os arquivos existirem em dois lugares,
   conferidos por hash (SHA-256).
5. **Especialista também inventa.** Toda afirmação de um subagente é
   conferida com ferramenta antes de chegar ao usuário.
6. **Tarefa repetida vira script com teste.** Os scripts nascem em rascunho,
   passam por um agente de QA e só entram no projeto com aval.
7. **Toda sessão é auditada.** Um script confere, na transcrição, se os
   marcadores de risco e fonte estavam lá, e um diário registra o que mudou.

## Processos que viraram ferramenta

| Processo | Em uma linha |
|---|---|
| HD antigo na dock | Identificar, calcular hashes, achar repetidos e copiar para o acervo só com conferência |
| Mídia para o acervo | Planejar, copiar, conferir e espelhar por SHA-256. A pergunta "posso apagar a origem?" é respondida por hash |
| DVD para o Jellyfin | Preset do HandBrake, nome "Título (Ano)" e conferência de duração disco × capa |
| Catálogo de DVDs pela foto | Código de barras, OCR do verso e comparação da capa com pôsteres, sem IA generativa |
| Celular para o acervo | Rotina semanal leva as fotos do Immich ao acervo, conferidas por hash, sem apagar nada |
| Buscar assunto nas conversas | Acha em que sessão de IA um assunto foi tratado e salva o resultado como contexto ([código](../ferramentas/buscar-assunto/)) |

## Resultado

- Acervo da família consolidado em um lugar, com cópia espelhada e conferida.
- Biblioteca de filmes, séries e músicas organizada para o Jellyfin.
- Um jeito reproduzível de usar IA em infraestrutura: o agente propõe, a
  ferramenta confere e o humano aprova o que é destrutivo.

## Stack

Debian 12 · Python 3 (biblioteca padrão + pytest) · Bash · systemd ·
Jellyfin · Immich · Ollama/CUDA · Syncthing · HandBrake · Claude Code
(skills, subagentes, hooks)

*Gerado por: Claude Code — 2026-11-26 17:37 (pagina 04 do portfolio (aval do usuario))*
