#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Procura um assunto em todas as sessoes de agentes de IA do usuario (so le as sessoes;
grava apenas o arquivo de pesquisa, se pedido na opcao 4 do menu).

Fontes (caminho inexistente e ignorado em silencio):
  - Claude Code (CLI/VS Code): ~/.claude/projects/*/*.jsonl, deduplicado pelo id
    (mesmo id em duas pastas de projeto conta uma vez; vale o arquivo maior).
  - Claude Desktop: ~/.config/Claude/claude-code-sessions/**/*.json. O arquivo so tem
    metadados (titulo, cliSessionId), sem as falas: busca so no titulo, marcado
    "estrutura nao lida"; some se o cliSessionId ja apareceu como Claude Code.
  - PC arquivado: <raiz>/indices-e-backups/sessoes-pc/*/sessoes/*/conversa-legivel.md
  - NAS arquivado: <raiz>/Projetos/mestre-linux/sessoes/**/conversa-legivel.md
    (id ja visto no Claude Code e omitido).
  - Hermes: ~/.hermes/sessions/*.json (dumps de requisicao; usa request.body.messages).

PADRAO e regex sem distincao de maiusculas e acentos. A sessao so aparece se tiver
fala REAL que case (system-reminder, <command-*>, tool_use/tool_result nao contam).
Data = primeiro "timestamp" do .jsonl (nao o mtime). Saida ordenada por data.
Codigo de saida: 0 achou, 1 nada, 2 regex ou data invalida.

Uso:
    buscar-assunto  (menu)  |  python buscar_assunto.py PADRAO [PADRAO...] [--desde AAAA-MM-DD]
        [--so-usuario] [--trechos N] [--json]
    (varios PADRAO = qualquer um deles casa)

Assinado por: Claude Code (Minion de Python) — 2026-11-26 09:03
*Assinado por: Claude Code — 2026-11-26 09:46 (menu interativo, separacao Terminal/VS Code/Desktop por entrypoint, regex so sem acento, --raiz; QA do Dru 3 rodadas; aval do usuario)*
*Assinado por: Claude Code — 2026-11-26 17:18 (menu: resultado em tabela com bordas e opcao 4 salvar pesquisa em indices-e-backups/pesquisas-assunto.md (aval do usuario))*
*Assinado por: Claude Code — 2026-11-26 17:23 (barra de progresso Buscando [###] NN% por bytes lidos, so em terminal (pedido do usuario))*
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOME = Path.home()
# Nomes dos lugares onde as sessões ficam (aparecem no menu e na coluna "app").
TERMINAL = "Terminal"
VSCODE = "VS Code"
DESKTOP = "Claude Desktop"
PC = "PC arquivado"
NAS = "NAS arquivado"
HERMES = "Hermes"
TODOS_OS_APPS = (TERMINAL, VSCODE, DESKTOP, PC, NAS, HERMES)


def app_do_entrypoint(entrypoint):
    """Campo "entrypoint" da transcrição do Claude Code -> app. Sem o campo: Terminal."""
    if entrypoint == "claude-vscode":
        return VSCODE
    if entrypoint == "claude-desktop":
        return DESKTOP
    return TERMINAL


MARCAS_RUIDO = ("<system-reminder>", "<command-", "<local-command")
CAB_MD = re.compile(r"^### (Usuário|Usuario|.+?) — (\d{2})/(\d{2}) (\d{2}:\d{2})\s*$", re.M)


def normalizar(txt):
    """Minusculas e sem acentos, caractere a caractere."""
    saida = []
    for c in txt:
        d = unicodedata.normalize("NFD", c)
        saida.append("".join(x for x in d if not unicodedata.combining(x)).lower())
    return "".join(saida)


def sem_acento(txt):
    """Tira so os acentos, sem mexer em maiusculas (\\S, \\D, \\W, \\B mantem o sentido)."""
    d = unicodedata.normalize("NFD", txt)
    return unicodedata.normalize("NFC", "".join(x for x in d if not unicodedata.combining(x)))


def compilar(padroes):
    return re.compile("|".join("(?:%s)" % sem_acento(p) for p in padroes), re.IGNORECASE)


def casa(rx, texto):
    """Devolve o trecho (ate 160 car.) se casar, senao None."""
    n = normalizar(texto)
    m = rx.search(n)
    if not m:
        return None
    base = texto if len(n) == len(texto) else n
    ini = max(0, m.start() - 60)
    t = re.sub(r"\s+", " ", base[ini:ini + 160]).strip()
    return t


def texto_real(msg):
    """Texto de uma fala real de um evento .jsonl, ou '' se for ruido."""
    if msg.get("isMeta"):
        return ""
    c = (msg.get("message") or {}).get("content")
    if isinstance(c, str):
        partes = [c]
    elif isinstance(c, list):
        partes = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return ""
    partes = [p for p in partes if p and not any(k in p for k in MARCAS_RUIDO)]
    return "\n".join(partes)


def ler_jsonl(caminho):
    """-> (id, data 'AAAA-MM-DD' ou '', [(papel, texto)], nlinhas, [entrypoints em ordem])."""
    falas, data, n, entrada = [], "", 0, []
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for linha in f:
            n += 1
            try:
                ev = json.loads(linha)
            except ValueError:
                continue
            if not isinstance(ev, dict):
                continue
            ep = ev.get("entrypoint")
            if isinstance(ep, str) and ep not in entrada:
                entrada.append(ep)  # sessão retomada em outro app acrescenta o segundo
            if not data and isinstance(ev.get("timestamp"), str):
                data = ev["timestamp"][:10]
            if ev.get("type") in ("user", "assistant"):
                t = texto_real(ev)
                if t:
                    falas.append((ev["type"], t))
    return Path(caminho).stem, data, falas, n, entrada


def ler_md(caminho):
    """conversa-legivel.md -> (id, data, [(papel, texto)])."""
    txt = Path(caminho).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\(([0-9a-f]{8}-[0-9a-f-]{27})\)", txt[:300])
    ident = m.group(1) if m else ""
    data = ""
    for parte in Path(caminho).parts:
        d = re.match(r"(\d{4}-\d{2}-\d{2})_", parte)
        if d:
            data = d.group(1)
    if not ident:
        for parte in Path(caminho).parts:
            d = re.match(r"\d{4}-\d{2}-\d{2}_([0-9a-f]{8})", parte)
            if d:
                ident = d.group(1)
    cabs = list(CAB_MD.finditer(txt))
    falas = []
    for i, c in enumerate(cabs):
        fim = cabs[i + 1].start() if i + 1 < len(cabs) else len(txt)
        corpo = txt[c.end():fim].strip()
        falas.append(("user" if c.group(1).startswith("Usu") else "assistant", corpo))
    return ident, data, falas


def ler_hermes(arquivos):
    """Agrupa dumps por session_id -> {id: (data, [(papel, texto)])}."""
    sess = {}
    for a in arquivos:
        try:
            d = json.loads(Path(a).read_text(encoding="utf-8", errors="replace"))
            sid = d["session_id"]
            msgs = d["request"]["body"]["messages"]
        except (ValueError, KeyError, TypeError, OSError):
            continue
        data, falas = sess.setdefault(sid, ((d.get("timestamp") or "")[:10], []))
        for m in msgs:
            if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
                par = (m["role"], m["content"])
                if par not in falas and not any(k in par[1] for k in MARCAS_RUIDO):
                    falas.append(par)
    return sess


def avaliar(rx, falas, so_usuario):
    nu = na = 0
    tu, ta = [], []
    for papel, t in falas:
        r = casa(rx, t)
        if r is None:
            continue
        if papel == "user":
            nu += 1
            tu.append(r)
        elif not so_usuario:
            na += 1
            ta.append(r)
    return nu, na, tu, ta


def _tamanho(p):
    try:
        return Path(p).stat().st_size
    except OSError:
        return 0


def varrer(rx, home=HOME, raiz=RAIZ, desde="", so_usuario=False, apps=None, progresso=None):
    """Devolve lista de dicts (data, app, id, usuario, respostas, trechos, obs).

    progresso(feito, total): chamado após cada arquivo lido; feito/total em bytes.
    """
    res = []
    vistos_code = set()
    arq_code = list((home / ".claude" / "projects").glob("*/*.jsonl"))
    arq_desk = list((home / ".config" / "Claude" / "claude-code-sessions").glob("**/*.json"))
    fontes_md = [(app, sorted(raiz.glob(padrao))) for app, padrao in (
        (PC, "indices-e-backups/sessoes-pc/*/sessoes/*/conversa-legivel.md"),
        (NAS, "Projetos/mestre-linux/sessoes/**/conversa-legivel.md"))]
    herm = sorted((home / ".hermes" / "sessions").glob("*.json"))
    todos = arq_code + arq_desk + [p for _, ps in fontes_md for p in ps] + herm
    total = sum(_tamanho(p) for p in todos) or 1
    feito = [0]

    def avancar(*arquivos):
        feito[0] += sum(_tamanho(p) for p in arquivos)
        if progresso:
            progresso(min(feito[0], total), total)

    def somar(app, data, ident, falas, obs=""):
        # app pode ser "Terminal+VS Code" (sessão usada nos dois): entra se algum casar
        if apps and not apps & set(app.split("+")):
            return
        nu, na, tu, ta = avaliar(rx, falas, so_usuario)
        if nu + na == 0 or (desde and data and data < desde):
            return
        res.append({"data": data, "app": app, "id": ident[:8], "id_completo": ident,
                    "usuario": nu, "respostas": na, "trechos": tu or ["[A] " + t for t in ta],
                    "trechos_usuario": tu, "trechos_ia": ta, "obs": obs})

    melhor = {}
    for p in arq_code:
        ident, data, falas, n, entrada = ler_jsonl(p)
        if ident not in melhor or n > melhor[ident][3]:
            melhor[ident] = (ident, data, falas, n, entrada)
        avancar(p)
    for ident, data, falas, _, entrada in melhor.values():
        vistos_code.add(ident)
        nomes = []
        for ep in entrada or [""]:
            nome = app_do_entrypoint(ep)
            if nome not in nomes:
                nomes.append(nome)
        somar("+".join(nomes), data, ident, falas)

    ja = {r["id_completo"] for r in res}
    for p in arq_desk:
        avancar(p)
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (ValueError, OSError):
            continue
        titulo = d.get("title") if isinstance(d, dict) else None
        cli = str(d.get("cliSessionId") or d.get("sessionId") or "") if titulo is not None else ""
        if not titulo or cli in ja or (apps and DESKTOP not in apps):
            continue
        r = casa(rx, titulo)
        if r:
            ms = d.get("createdAt")
            try:
                from datetime import datetime
                data = datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                data = ""
            if desde and data and data < desde:
                continue
            res.append({"data": data, "app": DESKTOP, "id": cli[:8], "id_completo": cli,
                        "usuario": 1, "respostas": 0, "trechos": [r],
                        "trechos_usuario": [r], "trechos_ia": [],
                        "obs": "estrutura nao lida (so titulo)"})

    for app, ps in fontes_md:
        for p in ps:
            avancar(p)
            ident, data, falas = ler_md(p)
            if app == NAS and ident in vistos_code:
                continue
            somar(app, data, ident or p.parent.parent.parent.name, falas)

    for sid, (data, falas) in ler_hermes(herm).items():
        somar(HERMES, data, sid, falas)
    avancar(*herm)

    res.sort(key=lambda r: (r["data"] or "9999", r["app"], r["id"]))
    return res


def tabela(res, trechos):
    linhas = ["%-10s %-14s %-8s %4s %4s  %s" % ("data", "app", "id", "usu", "resp", "trechos")]
    for r in res:
        tr = " | ".join(t[:160] for t in r["trechos"][:trechos])
        if r["obs"]:
            tr = "(%s) %s" % (r["obs"], tr)
        linhas.append("%-10s %-14s %-8s %4d %4d  %s" % (r["data"] or "?", r["app"], r["id"],
                                                         r["usuario"], r["respostas"], tr))
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Menu (comando buscar-assunto sem argumentos)
# ---------------------------------------------------------------------------

MENU_ONDE = (
    ("1", "Em todos os lugares", None),
    ("2", "Terminal (Claude Code)", {TERMINAL}),
    ("3", "VS Code", {VSCODE}),
    ("4", "Claude Desktop", {DESKTOP}),
    ("5", "Sessões arquivadas do PC", {PC}),
    ("6", "Sessões arquivadas do NAS", {NAS}),
    ("7", "Hermes", {HERMES}),
)


def padroes_do_assunto(texto):
    """Assunto digitado -> padrões literais; vírgula separa alternativas."""
    return [re.escape(t.strip()) for t in texto.split(",") if t.strip()]


def _escolher(titulo, opcoes, entrada, saida):
    """Mostra o menu e devolve a chave escolhida ("0" = voltar). Ctrl+D/Ctrl+C = "0"."""
    saida("\n" + titulo)
    for chave, rotulo in opcoes:
        saida("  %s - %s" % (chave, rotulo))
    validas = {c for c, _ in opcoes}
    while True:
        try:
            r = entrada("Escolha: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "0"
        if r in validas:
            return r
        saida("Opção inválida. Digite um destes números: " + ", ".join(sorted(validas)))


ARQUIVO_PESQUISAS = Path("indices-e-backups") / "pesquisas-assunto.md"
CAB_ARQUIVO = ("# Pesquisas de assunto nas sessões de IA\n\n"
               "Arquivo único, gerado pelo `buscar-assunto` (buscar_assunto.py).\n"
               "Cada pesquisa salva entra no fim, com a data. Serve de contexto para agentes.\n")


def _largura_terminal():
    import shutil
    return max(70, shutil.get_terminal_size((100, 24)).columns)


def _quebrar(texto, largura, max_linhas=2):
    """Quebra o texto em até max_linhas de 'largura' caracteres; corta com '…'."""
    import textwrap
    linhas = textwrap.wrap(texto, largura) or [""]
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = linhas[-1][:largura - 1].rstrip() + "…"
    return linhas


def _onde_curto(app):
    return app.replace("arquivado", "arq.").replace("Claude Desktop", "Desktop")


def tabela_caixa(res, largura=None):
    """Resultado em tabela com bordas; o trecho ocupa o que sobra da largura do terminal."""
    largura = largura or _largura_terminal()
    cols = [("nº", 3, ">"), ("data", 10, "<"), ("onde", 16, "<"), ("id", 8, "<"),
            ("você", 4, ">"), ("IA", 4, ">")]
    fixas = sum(w for _, w, _ in cols) + 3 * (len(cols) + 1) + 1
    wt = max(20, largura - fixas)
    larg = [w for _, w, _ in cols] + [wt]

    def borda(e, m, d):
        return e + m.join("─" * (w + 2) for w in larg) + d

    def linha(celulas, alinh):
        return "│" + "│".join(" %s " % (c[:w].ljust(w) if a == "<" else c[:w].rjust(w))
                              for c, w, a in zip(celulas, larg, alinh)) + "│"

    alinh = [a for _, _, a in cols] + ["<"]
    out = [borda("┌", "┬", "┐"), linha([n for n, _, _ in cols] + ["primeiro trecho"], alinh),
           borda("├", "┼", "┤")]
    for i, r in enumerate(res, 1):
        tr = (r["trechos"] or [""])[0]
        if r["obs"]:
            tr = "(%s) %s" % (r["obs"], tr)
        pedacos = _quebrar(tr, wt)
        out.append(linha([str(i), r["data"] or "?", _onde_curto(r["app"]), r["id"],
                          str(r["usuario"]), str(r["respostas"]), pedacos[0]], alinh))
        for p in pedacos[1:]:
            out.append(linha(["", "", "", "", "", "", p], alinh))
        if i < len(res):
            out.append(borda("├", "┼", "┤"))
    out.append(borda("└", "┴", "┘"))
    return "\n".join(out)


def barra(feito, total, largura=30):
    """Linha de progresso: 'Buscando [█████░░░░░]  50%'."""
    frac = feito / total if total else 1.0
    cheio = int(round(frac * largura))
    return "Buscando [%s%s] %3d%%" % ("█" * cheio, "░" * (largura - cheio), int(frac * 100))


def progresso_terminal(stream=None):
    """Função de progresso que redesenha a barra na mesma linha (só em terminal)."""
    stream = stream or sys.stdout
    if not stream.isatty():
        return None
    ultimo = [-1]

    def mostrar(feito, total):
        pct = int(feito * 100 / total) if total else 100
        if pct == ultimo[0]:
            return
        ultimo[0] = pct
        stream.write("\r" + barra(feito, total))
        if pct >= 100:
            stream.write("\r" + " " * 50 + "\r")  # apaga a barra antes da tabela
        stream.flush()
    return mostrar


def _mostrar(res, saida):
    if not res:
        saida("\nNada encontrado.")
        return
    saida("\n" + tabela_caixa(res))
    saida("%d sessões. \"você\" = suas mensagens que citam o assunto; \"IA\" = respostas." % len(res))


def escolher_numeros(texto, total):
    """'1, 3-5' -> [1, 3, 4, 5]; vazio ou 't' -> todos; inválido -> None."""
    texto = texto.strip().lower()
    if texto in ("", "t", "todos", "todas"):
        return list(range(1, total + 1))
    nums = []
    for parte in texto.replace(" ", "").split(","):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", parte)
        if not m:
            return None
        a, z = int(m.group(1)), int(m.group(2) or m.group(1))
        if not 1 <= a <= z <= total:
            return None
        nums.extend(n for n in range(a, z + 1) if n not in nums)
    return nums


def bloco_pesquisa(assunto, onde, quem, res, escolhidos, agora):
    """Seção Markdown de uma pesquisa salva (data, filtros, tabela e trechos completos)."""
    sel = [res[n - 1] for n in escolhidos]
    out = ["", "## %s — \"%s\"" % (agora.strftime("%Y-%m-%d %H:%M"), assunto), "",
           "- **Dia da pesquisa:** %s" % agora.strftime("%d/%m/%Y às %H:%M"),
           "- **Assunto:** %s" % assunto,
           "- **Onde:** %s" % onde,
           "- **Quem falou:** %s" % quem,
           "- **Sessões achadas:** %d; **salvas aqui:** %d (nº %s)" % (
               len(res), len(sel), ", ".join(map(str, escolhidos))),
           "", "| nº | data | onde | sessão (id completo) | você | IA |",
           "|---:|---|---|---|---:|---:|"]
    for n, r in zip(escolhidos, sel):
        out.append("| %d | %s | %s | `%s` | %d | %d |" % (n, r["data"] or "?", r["app"],
                                                         r["id_completo"], r["usuario"], r["respostas"]))
    for n, r in zip(escolhidos, sel):
        out += ["", "### nº %d · %s · %s · `%s`" % (n, r["data"] or "?", r["app"], r["id_completo"])]
        if r["obs"]:
            out.append("_%s_" % r["obs"])
        out += ["- **[você]** " + t.replace("|", "\\|") for t in r.get("trechos_usuario", [])]
        out += ["- **[IA]** " + t.replace("|", "\\|") for t in r.get("trechos_ia", [])]
    out.append("\n*Gerado por: buscar-assunto — %s*" % agora.strftime("%Y-%m-%d %H:%M"))
    return "\n".join(out) + "\n"


def salvar_pesquisa(arquivo, bloco):
    """Acrescenta o bloco no fim do arquivo único (cria com cabeçalho na 1ª vez)."""
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    novo = not arquivo.exists()
    with open(arquivo, "a", encoding="utf-8") as f:
        if novo:
            f.write(CAB_ARQUIVO)
        f.write(bloco)


def _salvar(res, assunto, onde, quem, raiz, entrada, saida, agora=None):
    from datetime import datetime
    try:
        t = entrada("Quais sessões salvar? (nº separados por vírgula, ex. 1,3-5; Enter = todas): ")
    except (EOFError, KeyboardInterrupt):
        return
    nums = escolher_numeros(t, len(res))
    if not nums:
        saida("Número fora da lista. Nada foi salvo.")
        return
    arq = raiz / ARQUIVO_PESQUISAS
    salvar_pesquisa(arq, bloco_pesquisa(assunto, onde, quem, res, nums, agora or datetime.now()))
    saida("Salvo: %d sessão(ões) acrescentadas em %s" % (len(nums), arq))


def _ver_sessao(res, entrada, saida):
    try:
        n = entrada("Número da sessão (coluna nº): ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not n.isdigit() or not 1 <= int(n) <= len(res):
        saida("Número fora da lista.")
        return
    r = res[int(n) - 1]
    saida("\n== %s · %s · sessão %s ==" % (r["data"], r["app"], r["id_completo"]))
    for t in r.get("trechos_usuario", []):
        saida("  [você] " + t)
    for t in r.get("trechos_ia", []):
        saida("  [IA]   " + t)


def menu(entrada=input, saida=print, home=HOME, raiz=RAIZ, progresso=None):
    saida("=" * 50 + "\n   BUSCAR ASSUNTO NAS SESSÕES DE IA\n" + "=" * 50)
    assunto = ""
    while True:
        if not assunto:
            try:
                texto = entrada("\nQual assunto? (vírgula separa alternativas; Enter vazio sai): ")
            except (EOFError, KeyboardInterrupt):
                texto = ""
            pads = padroes_do_assunto(texto)
            if not pads:
                saida("Até a próxima!")
                return 0
            assunto = texto.strip()
        onde = _escolher("Onde procurar \"%s\"?" % assunto,
                         [(c, r) for c, r, _ in MENU_ONDE] + [("0", "Voltar (outro assunto)")], entrada, saida)
        if onde == "0":
            assunto = ""
            continue
        quem = _escolher("Quem falou?", [("1", "Só você (suas mensagens)"),
                                          ("2", "Você e as respostas da IA"), ("0", "Voltar")], entrada, saida)
        if quem == "0":
            continue
        apps = dict((c, a) for c, _, a in MENU_ONDE)[onde]
        try:
            res = varrer(compilar(padroes_do_assunto(assunto)), home=home, raiz=raiz,
                         so_usuario=(quem == "1"), apps=apps,
                         progresso=progresso or progresso_terminal())
        except KeyboardInterrupt:
            saida("\nBusca interrompida (Ctrl+C).")
            assunto = ""
            continue
        _mostrar(res, saida)
        rotulo_onde = dict((c, r) for c, r, _ in MENU_ONDE)[onde]
        rotulo_quem = "Só você" if quem == "1" else "Você e a IA"
        opcoes = [("1", "Buscar outro assunto"), ("2", "Mesmo assunto em outro lugar"),
                  ("3", "Ver todos os trechos de uma sessão")]
        if res:
            opcoes.append(("4", "Salvar pesquisa e resultado no arquivo de contexto"))
        opcoes.append(("0", "Sair"))
        while True:
            depois = _escolher("E agora?", opcoes, entrada, saida)
            if depois == "3":
                _ver_sessao(res, entrada, saida)
                continue
            if depois == "4":
                _salvar(res, assunto, rotulo_onde, rotulo_quem, raiz, entrada, saida)
                continue
            break
        if depois == "0":
            saida("Até a próxima!")
            return 0
        if depois == "1":
            assunto = ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Busca um assunto nas sessoes de agentes de IA (so le as sessoes; o menu grava o arquivo de pesquisa so na opcao 4).")
    ap.add_argument("padrao", nargs="*",
                    help="regex sem distincao de maiusculas/acentos; sem padrao, abre o menu")
    ap.add_argument("--desde", default="", help="AAAA-MM-DD")
    ap.add_argument("--so-usuario", action="store_true", help="ignora respostas do assistente")
    ap.add_argument("--trechos", type=int, default=2, help="trechos por sessao (padrao 2)")
    ap.add_argument("--json", action="store_true", help="saida em JSON")
    ap.add_argument("--raiz", type=Path, default=RAIZ,
                    help="pasta do projeto com as sessoes arquivadas (padrao: a pasta acima deste script)")
    a = ap.parse_args(argv)
    if not a.padrao:
        return menu(raiz=a.raiz)
    if a.desde:
        from datetime import date
        try:
            date.fromisoformat(a.desde)
        except ValueError:
            print("data invalida em --desde: %s (use AAAA-MM-DD)" % a.desde, file=sys.stderr)
            return 2
    try:
        rx = compilar(a.padrao)
    except re.error as e:
        print("regex invalida: %s" % e, file=sys.stderr)
        return 2
    if not (a.raiz / "indices-e-backups" / "sessoes-pc").is_dir():
        print("aviso: %s nao tem indices-e-backups/sessoes-pc; sessoes arquivadas ficam de fora "
              "(use --raiz)" % a.raiz, file=sys.stderr)
    res = varrer(rx, raiz=a.raiz, desde=a.desde, so_usuario=a.so_usuario)
    if a.json:
        print(json.dumps([{k: v[:a.trechos] if k == "trechos" else v for k, v in r.items()}
                          for r in res], ensure_ascii=False, indent=2))
    elif res:
        print(tabela(res, a.trechos))
        print("\n%d sessoes." % len(res))
    else:
        print("Nada encontrado.")
    return 0 if res else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
