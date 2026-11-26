# -*- coding: utf-8 -*-
"""Testes do buscar_assunto.py (fixtures sinteticas; nao le sessoes reais).

Rodar: python -m pytest test_buscar_assunto.py -q
Assinado por: Claude Code (Minion de Python) — 2026-11-26 09:03
*Assinado por: Claude Code — 2026-11-26 17:18 (5 testes: tabela, escolha de numeros, arquivo unico acumulado, numero invalido, sem resultado)*
*Assinado por: Claude Code — 2026-11-26 17:23 (3 testes da barra de progresso)*
"""
import json
import sys
from pathlib import Path

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "buscar_assunto_sessoes", Path(__file__).resolve().parent / "buscar_assunto.py")
b = importlib.util.module_from_spec(_spec)
sys.modules["buscar_assunto_sessoes"] = b
_spec.loader.exec_module(b)

ID1 = "11111111-aaaa-bbbb-cccc-000000000001"
ID2 = "22222222-aaaa-bbbb-cccc-000000000002"


def ev(tipo, conteudo, ts="2026-05-03T10:00:00Z"):
    return json.dumps({"type": tipo, "timestamp": ts, "message": {"content": conteudo}})


def jsonl(pasta, ident, linhas):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / (ident + ".jsonl")).write_text("\n".join(linhas), encoding="utf-8")


def monta(tmp_path):
    home, raiz = tmp_path / "home", tmp_path / "proj"
    pr = home / ".claude" / "projects"
    a = [ev("user", "qual a melhor placa de vídeo para o NAS?"),
         ev("assistant", [{"type": "text", "text": "Uma RTX 3060 serve."}, {"type": "tool_use", "name": "x"}],
            "2026-05-03T10:01:00Z")]
    jsonl(pr / "-home-x", ID1, a)
    jsonl(pr / "-home-x-outra", ID1, a + [ev("user", "valeu")])  # duplicada, maior
    jsonl(pr / "-home-x", ID2, [
        ev("user", "<system-reminder>placa de video citada na memoria</system-reminder>", "2026-04-01T00:00:00Z"),
        ev("user", [{"type": "tool_result", "content": "placa de video"}]),
        ev("user", "oi")])
    md = raiz / "indices-e-backups/sessoes-pc/2026-03-02_abcd1234/sessoes/claude-code"
    md.mkdir(parents=True)
    (md / "conversa-legivel.md").write_text(
        "# Sessão do Claude Code (abcd1234-0000-0000-0000-000000000000)\n\n"
        "### Usuário — 02/03 10:00\n\ncomprar PLACA DE VIDEO nova\n\n"
        "### Claude Code — 02/03 10:01\n\nclaro, a placa de vídeo serve\n", encoding="utf-8")
    return home, raiz


def test_normalizar_acentos():
    rx = b.compilar(["video"])
    assert b.casa(rx, "Placa de VÍDEO") is not None
    assert b.casa(rx, "audio") is None


def test_filtra_ruido_e_deduplica(tmp_path):
    home, raiz = monta(tmp_path)
    res = b.varrer(b.compilar(["placa de v[ií]deo", "rtx ?3060"]), home=home, raiz=raiz)
    code = [r for r in res if r["app"] == b.TERMINAL]
    assert [r["id"] for r in code] == ["11111111"]  # ID2 so tem system-reminder
    assert code[0]["usuario"] == 1 and code[0]["respostas"] == 1
    assert "placa de vídeo" in code[0]["trechos"][0]


def test_md_arquivado_e_ordem(tmp_path):
    home, raiz = monta(tmp_path)
    res = b.varrer(b.compilar(["placa de video"]), home=home, raiz=raiz)
    assert [r["app"] for r in res] == [b.PC, b.TERMINAL]  # por data
    assert res[0]["data"] == "2026-03-02" and res[0]["id"] == "abcd1234"
    assert res[0]["usuario"] == 1 and res[0]["respostas"] == 1


def test_desde_e_so_usuario(tmp_path):
    home, raiz = monta(tmp_path)
    rx = b.compilar(["placa de video"])
    assert [r["app"] for r in b.varrer(rx, home=home, raiz=raiz, desde="2026-04-01")] == [b.TERMINAL]
    r = b.varrer(rx, home=home, raiz=raiz, so_usuario=True)
    assert all(x["respostas"] == 0 for x in r)


def test_caminhos_inexistentes_e_exit(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(b, "HOME", tmp_path / "vazio")
    monkeypatch.setattr(b, "RAIZ", tmp_path / "vazio")
    assert b.varrer(b.compilar(["x"]), home=tmp_path / "vazio", raiz=tmp_path / "vazio") == []
    monkeypatch.setattr(b, "varrer", lambda *a, **k: [])
    assert b.main(["zzz"]) == 1
    assert "Nada" in capsys.readouterr().out


def test_help_nao_executa(capsys):
    try:
        b.main(["--help"])
    except SystemExit as e:
        assert e.code == 0


def test_escapes_em_maiuscula_mantem_o_sentido():
    import buscar_assunto_sessoes as b
    assert b.casa(b.compilar([r"a\Sb"]), "axb")
    assert not b.casa(b.compilar([r"a\Sb"]), "a b")
    assert b.casa(b.compilar([r"RTX\s\D+"]), "rtx super")
    assert not b.casa(b.compilar([r"RTX\s\D+"]), "rtx 3060")
    assert b.casa(b.compilar(["VÍDEO"]), "placa de video")


def test_regex_invalida_e_data_invalida_saem_com_2(capsys):
    import buscar_assunto_sessoes as b
    assert b.main(["("]) == 2
    assert b.main(["x", "--desde", "2026-13-45"]) == 2


def test_app_vem_do_entrypoint_da_transcricao():
    assert b.app_do_entrypoint("cli") == b.TERMINAL
    assert b.app_do_entrypoint("sdk-cli") == b.TERMINAL
    assert b.app_do_entrypoint("claude-vscode") == b.VSCODE
    assert b.app_do_entrypoint("claude-desktop") == b.DESKTOP
    assert b.app_do_entrypoint("") == b.TERMINAL


def test_varrer_filtra_por_app_e_separa_vscode(tmp_path):
    home, raiz = monta(tmp_path)
    linhas = [json.dumps({"type": "user", "timestamp": "2026-06-01T09:00:00Z", "entrypoint": "claude-vscode",
                          "message": {"content": "placa de video no vscode"}})]
    jsonl(home / ".claude" / "projects" / "-home-x", "33333333-aaaa-bbbb-cccc-000000000003", linhas)
    rx = b.compilar(["placa de video"])
    todos = b.varrer(rx, home=home, raiz=raiz)
    assert {r["app"] for r in todos} == {b.TERMINAL, b.VSCODE, b.PC}
    so_vscode = b.varrer(rx, home=home, raiz=raiz, apps={b.VSCODE})
    assert [r["app"] for r in so_vscode] == [b.VSCODE]
    assert so_vscode[0]["trechos_usuario"] and so_vscode[0]["trechos_ia"] == []


def test_assunto_digitado_vira_padrao_literal():
    pads = b.padroes_do_assunto("placa de vídeo, RTX 3060 (12GB)")
    assert pads == [b.re.escape("placa de vídeo"), b.re.escape("RTX 3060 (12GB)")]
    assert b.padroes_do_assunto("  ,  ") == []


def test_menu_fluxo_completo_com_respostas_simuladas(tmp_path):
    home, raiz = monta(tmp_path)
    respostas = iter(["placa de video", "5", "1", "3", "1", "0"])
    saida = []

    def entrada(prompt):
        saida.append(prompt)
        return next(respostas)

    b.menu(entrada=entrada, saida=saida.append, home=home, raiz=raiz)
    texto = "\n".join(saida)
    assert "Qual assunto" in texto and "Onde procurar" in texto and "Quem falou" in texto
    assert "comprar PLACA DE VIDEO nova" in texto          # achou a sessão do PC, só fala do usuário
    assert "a placa de vídeo serve" not in texto           # resposta da IA ficou de fora (opção 1)
    assert "Até a próxima" in texto


def test_menu_enter_vazio_sai(tmp_path):
    saida = []
    b.menu(entrada=lambda _: "", saida=saida.append, home=tmp_path, raiz=tmp_path)
    assert "Até a próxima" in "\n".join(saida)


def test_sessao_retomada_no_vscode_aparece_nos_dois_filtros(tmp_path):
    home, raiz = monta(tmp_path)
    ev2 = lambda ep, txt: json.dumps({"type": "user", "timestamp": "2026-06-02T09:00:00Z", "entrypoint": ep,
                                      "message": {"content": txt}})
    jsonl(home / ".claude" / "projects" / "-home-x", "44444444-aaaa-bbbb-cccc-000000000004",
          [ev2("cli", "placa de video no terminal"), ev2("claude-vscode", "continuei no vscode")])
    rx = b.compilar(["placa de video"])
    so_vscode = b.varrer(rx, home=home, raiz=raiz, apps={b.VSCODE})
    assert [r["app"] for r in so_vscode] == [b.TERMINAL + "+" + b.VSCODE]
    so_terminal = b.varrer(rx, home=home, raiz=raiz, apps={b.TERMINAL})
    assert "44444444" in {r["id"] for r in so_terminal}


def test_ctrl_c_na_busca_volta_ao_menu(tmp_path, monkeypatch):
    home, raiz = monta(tmp_path)

    def interrompe(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(b, "varrer", interrompe)
    respostas = iter(["placa", "1", "1", ""])
    saida = []
    assert b.menu(entrada=lambda _: next(respostas), saida=saida.append, home=home, raiz=raiz) == 0
    assert "Busca interrompida" in "\n".join(saida)


def test_tabela_caixa_cabe_na_largura_e_tem_bordas(tmp_path):
    home, raiz = monta(tmp_path)
    res = b.varrer(b.compilar(["placa de video"]), home=home, raiz=raiz)
    t = b.tabela_caixa(res, largura=90)
    linhas = t.splitlines()
    assert linhas[0].startswith("┌") and linhas[-1].startswith("└")
    assert all(len(l) == len(linhas[0]) for l in linhas)  # todas as linhas alinhadas
    assert len(linhas[0]) <= 90
    assert "primeiro trecho" in t and "PC arq." in t


def test_escolher_numeros():
    assert b.escolher_numeros("", 3) == [1, 2, 3]
    assert b.escolher_numeros("t", 2) == [1, 2]
    assert b.escolher_numeros("1, 3-4", 5) == [1, 3, 4]
    assert b.escolher_numeros("6", 5) is None
    assert b.escolher_numeros("abc", 5) is None


def test_menu_salva_e_acumula_no_arquivo_unico(tmp_path):
    home, raiz = monta(tmp_path)
    # 1ª pesquisa: salva só a nº 1; 2ª pesquisa (outro assunto): salva todas
    respostas = iter(["placa de video", "1", "2", "4", "1", "1",
                      "RTX", "1", "2", "4", "", "0"])
    saida = []
    assert b.menu(entrada=lambda _: next(respostas), saida=saida.append, home=home, raiz=raiz) == 0
    arq = raiz / b.ARQUIVO_PESQUISAS
    txt = arq.read_text(encoding="utf-8")
    assert txt.count("# Pesquisas de assunto") == 1            # cabeçalho uma vez só
    assert txt.count("- **Dia da pesquisa:**") == 2             # duas pesquisas acumuladas
    assert '"placa de video"' in txt and '"RTX"' in txt
    assert "- **Onde:** Em todos os lugares" in txt and "- **Quem falou:** Você e a IA" in txt
    assert ID1 in txt and "**[IA]** Uma RTX 3060 serve." in txt
    assert "Salvo:" in "\n".join(saida)


def test_salvar_numero_invalido_nao_grava(tmp_path):
    home, raiz = monta(tmp_path)
    respostas = iter(["placa de video", "1", "2", "4", "99", "0"])
    saida = []
    b.menu(entrada=lambda _: next(respostas), saida=saida.append, home=home, raiz=raiz)
    assert not (raiz / b.ARQUIVO_PESQUISAS).exists()
    assert "Nada foi salvo" in "\n".join(saida)


def test_sem_resultado_nao_oferece_salvar(tmp_path):
    home, raiz = monta(tmp_path)
    respostas = iter(["xyzzy-nada", "1", "2", "0"])
    saida = []
    b.menu(entrada=lambda _: next(respostas), saida=saida.append, home=home, raiz=raiz)
    assert "Salvar pesquisa" not in "\n".join(saida)


def test_barra_de_progresso():
    assert b.barra(0, 10, largura=10) == "Buscando [░░░░░░░░░░]   0%"
    assert b.barra(5, 10, largura=10) == "Buscando [█████░░░░░]  50%"
    assert b.barra(10, 10, largura=10) == "Buscando [██████████] 100%"


def test_varrer_avisa_progresso_ate_100(tmp_path):
    home, raiz = monta(tmp_path)
    chamadas = []
    b.varrer(b.compilar(["placa"]), home=home, raiz=raiz, progresso=lambda f, t: chamadas.append((f, t)))
    assert chamadas and chamadas[-1][0] == chamadas[-1][1]          # termina em 100%
    assert all(a[0] <= c[0] for a, c in zip(chamadas, chamadas[1:]))  # nunca volta


def test_menu_usa_o_progresso_e_fora_do_terminal_nao_desenha(tmp_path):
    import io
    assert b.progresso_terminal(io.StringIO()) is None   # saída redirecionada: sem barra
    home, raiz = monta(tmp_path)
    vistos = []
    respostas = iter(["placa", "1", "2", "0"])
    b.menu(entrada=lambda _: next(respostas), saida=lambda *_: None, home=home, raiz=raiz,
           progresso=lambda f, t: vistos.append(f * 100 // t))
    assert vistos[-1] == 100
