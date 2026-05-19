from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional, List, Dict

from fastapi import BackgroundTasks


def construir_tabela_html(razao_social: str, cnpj: str, contribuinte_nome: str, linhas: List[Dict[str, str]]) -> str:
    """
    Gera HTML elegante e simples (offline-friendly).
    """
    style = """
    <style>
      body { font-family: Arial, sans-serif; color: #222; }
      .header { margin-bottom: 12px; }
      .badge { display:inline-block; padding:6px 10px; background:#0b5; color:#fff; border-radius:6px; font-size:12px; }
      table { border-collapse: collapse; width: 100%; margin-top: 12px; }
      th, td { border: 1px solid #ddd; padding: 8px; }
      th { background: #f4f6f8; text-align: left; }
      .footer { margin-top: 14px; font-size: 12px; color: #555; }
    </style>
    """
    header = f"""
    <div class="header">
      <div class="badge">Relatório Offline - APPF</div>
      <h2>Histórico de Contribuições Voluntárias</h2>
      <p><strong>Instituição:</strong> {razao_social} &nbsp; | &nbsp; <strong>CNPJ:</strong> {cnpj}</p>
      <p><strong>Contribuinte:</strong> {contribuinte_nome}</p>
    </div>
    """

    rows = ""
    for r in linhas:
        rows += f"<tr><td>{r.get('numero','')}</td><td>{r.get('data','')}</td><td>{r.get('valor','')}</td><td>{r.get('descricao','')}</td></tr>"

    table = f"""
    <table>
      <thead>
        <tr>
          <th>Nº Recibo</th>
          <th>Data</th>
          <th>Valor</th>
          <th>Descrição</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """

    footer = """
    <div class="footer">
      <p>Este e-mail contém informações emitidas por sistema local da APPF, com rastreabilidade temporal.</p>
    </div>
    """

    return f"<!doctype html><html><head>{style}</head><body>{header}{table}{footer}</body></html>"


def enviar_email_smtp(
    host: str,
    porta: int,
    usuario: Optional[str],
    senha: Optional[str],
    usar_starttls: bool,
    remetente: str,
    destinatario: str,
    assunto: str,
    html: str,
) -> None:
    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content("Seu cliente de e-mail não suporta HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(host, porta, timeout=25) as server:
        server.ehlo()
        if usar_starttls:
            server.starttls()
            server.ehlo()
        if usuario and senha:
            server.login(usuario, senha)
        server.send_message(msg)


def disparar_email_background(
    bg: BackgroundTasks,
    *,
    host: str,
    porta: int,
    usuario: Optional[str],
    senha: Optional[str],
    usar_starttls: bool,
    remetente: str,
    destinatario: str,
    assunto: str,
    html: str,
) -> None:
    bg.add_task(
        enviar_email_smtp,
        host,
        porta,
        usuario,
        senha,
        usar_starttls,
        remetente,
        destinatario,
        assunto,
        html,
    )