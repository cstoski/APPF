from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

from app.services.seguranca_service import normalizar_cpf

_MESES_PT = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def _formatar_valor_br(valor: float) -> str:
    q = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    partes = f"{q:.2f}".split(".")
    inteiro = int(partes[0])
    centavos = partes[1]
    inteiro_fmt = f"{inteiro:,}".replace(",", ".")
    return f"R$ {inteiro_fmt},{centavos}"


def formatar_cpf_recibo(cpf: Optional[str]) -> str:
    d = normalizar_cpf(cpf or "")
    if len(d) != 11:
        return "não informado"
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def _centenas_por_extenso(n: int) -> str:
    centenas = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]
    dezenas = [
        "",
        "",
        "vinte",
        "trinta",
        "quarenta",
        "cinquenta",
        "sessenta",
        "setenta",
        "oitenta",
        "noventa",
    ]
    especiais = [
        "dez",
        "onze",
        "doze",
        "treze",
        "quatorze",
        "quinze",
        "dezesseis",
        "dezessete",
        "dezoito",
        "dezenove",
    ]
    unidades = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]

    if n == 0:
        return ""
    if n == 100:
        return "cem"
    if n < 10:
        return unidades[n]
    if n < 20:
        return especiais[n - 10]
    if n < 100:
        d, u = divmod(n, 10)
        parte = dezenas[d]
        if u:
            parte = f"{parte} e {unidades[u]}" if parte else unidades[u]
        return parte
    c, resto = divmod(n, 100)
    prefixo = centenas[c]
    sufixo = _centenas_por_extenso(resto)
    if sufixo:
        if resto < 100 or (resto % 100) < 10:
            return f"{prefixo} e {sufixo}"
        return f"{prefixo} e {sufixo}"
    return prefixo


def _bloco_por_extenso(n: int, escala_singular: str, escala_plural: str) -> str:
    if n == 0:
        return ""
    texto = _centenas_por_extenso(n)
    escala = escala_singular if n == 1 else escala_plural
    return f"{texto} {escala}".strip()


def valor_por_extenso(valor: float) -> str:
    q = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if q < 0:
        q = -q
    reais = int(q)
    centavos = int((q - Decimal(reais)) * 100)

    if reais == 0 and centavos == 0:
        return "zero real"

    partes: list[str] = []
    if reais > 0:
        milhoes, resto = divmod(reais, 1_000_000)
        milhares, resto = divmod(resto, 1_000)
        if milhoes:
            partes.append(_bloco_por_extenso(milhoes, "milhão", "milhões"))
        if milhares:
            bloco = _centenas_por_extenso(milhares)
            partes.append(f"{bloco} mil".strip())
        if resto:
            partes.append(_centenas_por_extenso(resto))
        texto_reais = " e ".join(p for p in partes if p)
        partes_valor = [f"{texto_reais} {'real' if reais == 1 else 'reais'}".strip()]
    else:
        partes_valor = []

    if centavos > 0:
        texto_cent = _centenas_por_extenso(centavos)
        sufixo_cent = "centavo" if centavos == 1 else "centavos"
        if partes_valor:
            partes_valor.append(f"{texto_cent} {sufixo_cent}")
        else:
            partes_valor.append(f"{texto_cent} {sufixo_cent}")

    return " e ".join(partes_valor)


def formatar_data_recibo(data: Union[datetime, None]) -> str:
    if data is None:
        data = datetime.utcnow()
    return f"{data.day} de {_MESES_PT[data.month - 1]} de {data.year}"


def gerar_texto_corpo_recibo(
    nome: str,
    cpf: Optional[str],
    valor: float,
    data: Optional[datetime] = None,
) -> str:
    nome_fmt = " ".join((nome or "").strip().split()) or "—"
    cpf_fmt = formatar_cpf_recibo(cpf)
    valor_num = _formatar_valor_br(valor)
    valor_ext = valor_por_extenso(valor)
    data_fmt = formatar_data_recibo(data)
    return (
        f"Recebemos de {nome_fmt}, inscrito(a) no CPF sob o nº {cpf_fmt}, "
        f"a importância de {valor_num} ({valor_ext}) em {data_fmt}, "
        f"a título de contribuição social voluntária destinada à Associação de Pais, "
        f"Professores e Funcionários (APPF) deste estabelecimento de ensino."
    )
