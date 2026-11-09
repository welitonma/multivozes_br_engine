"""Caracterização de handle_text.preparar_texto_para_tts (comportamento atual)."""

from handle_text import preparar_texto_para_tts


def test_remove_emoji():
    assert preparar_texto_para_tts("Olá 🌎 mundo") == "Olá mundo"


def test_link_markdown_mantem_texto():
    assert preparar_texto_para_tts("[clique aqui](http://site.com)") == "clique aqui"


def test_imagem_markdown_mantem_alt_com_exclamacao():
    # caracteriza o comportamento atual: a regra de link roda antes da regra
    # de imagem, então a imagem vira "!alt" (o "!" sobra).
    assert preparar_texto_para_tts("![descrição da imagem](imagem.png)") == "!descrição da imagem"


def test_imagem_no_meio_de_frase():
    # caracteriza o comportamento atual (mesma ordem das regex acima).
    assert preparar_texto_para_tts("![alt](x.png) e [t](http://s)") == "!alt e t"


def test_negrito_e_italico_removidos():
    assert preparar_texto_para_tts("**negrito** e *itálico*") == "negrito e itálico"


def test_sublinhado_e_riscado_removidos():
    assert preparar_texto_para_tts("__u__ e _i_ e ~~riscado~~") == "u e i e riscado"


def test_codigo_inline_mantem_conteudo():
    assert preparar_texto_para_tts("Use `código` aqui") == "Use código aqui"


def test_bloco_de_codigo_removido():
    assert preparar_texto_para_tts("antes\n```python\nprint(1)\n```\ndepois") == "antes\n\ndepois"


def test_cabecalho_mantem_texto():
    assert preparar_texto_para_tts("### Título") == "Título"


def test_tag_html_removida():
    assert preparar_texto_para_tts("<b>oi</b> texto") == "oi texto"


def test_quebras_multiplas_normalizadas():
    assert preparar_texto_para_tts("a\n\n\nb") == "a\n\nb"


def test_espacos_multiplos_normalizados():
    assert preparar_texto_para_tts("a   b") == "a b"


def test_entrada_nao_string_devolve_vazio():
    assert preparar_texto_para_tts(123) == ""
