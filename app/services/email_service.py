from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any, Optional, List, Dict

from fastapi import BackgroundTasks

from app.services.email_log_service import log_email_aceito_smtp, log_email_falha


def abrir_conexao_smtp(
    host: str,
    porta: int,
    usar_starttls: bool,
    *,
    timeout: int = 25,
) -> smtplib.SMTP:
    """Abre SMTP (porta 465 = SSL implícito; demais portas = SMTP + STARTTLS opcional)."""
    porta_int = int(porta)
    if porta_int == 465:
        server = smtplib.SMTP_SSL(host, porta_int, timeout=timeout)
        server.ehlo()
        return server

    server = smtplib.SMTP(host, porta_int, timeout=timeout)
    code, _ = server.ehlo()
    if code >= 400:
        server.helo()

    if usar_starttls:
        if not server.has_extn("starttls"):
            raise smtplib.SMTPException(
                "O servidor não oferece STARTTLS. Tente porta 465 (SSL) ou desative STARTTLS."
            )
        server.starttls()
        server.ehlo()

    return server


def autenticar_smtp_se_necessario(
    server: smtplib.SMTP,
    usuario: Optional[str],
    senha: Optional[str],
) -> tuple[bool, Optional[str]]:
    """
    Autentica apenas se o servidor anunciar AUTH.
    Retorna (autenticou, motivo_ignorado).
    """
    usuario_limpo = (usuario or "").strip() or None
    senha_limpa = senha or None

    if not usuario_limpo and not senha_limpa:
        return False, None

    if usuario_limpo and not senha_limpa:
        raise ValueError("Senha SMTP não configurada.")

    if not senha_limpa and not usuario_limpo:
        return False, None

    if not server.has_extn("auth"):
        return False, "servidor_sem_auth"

    server.login(usuario_limpo, senha_limpa)
    return True, None


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
    html: Optional[str] = None,
    *,
    corpo_texto: Optional[str] = None,
    anexo_pdf: Optional[tuple[str, bytes]] = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto

    if corpo_texto:
        msg.set_content(corpo_texto)
    else:
        msg.set_content("Seu cliente de e-mail não suporta HTML.")

    if html:
        msg.add_alternative(html, subtype="html")

    if anexo_pdf:
        nome_arquivo, conteudo = anexo_pdf
        msg.add_attachment(
            conteudo,
            maintype="application",
            subtype="pdf",
            filename=nome_arquivo,
        )

    server = abrir_conexao_smtp(host, porta, usar_starttls, timeout=25)
    try:
        autenticar_smtp_se_necessario(server, usuario, senha)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass


def _log_ctx_campos(log_ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "operador": log_ctx.get("operador", "sistema"),
        "tipo": log_ctx.get("tipo", "GERAL"),
        "destinatario": log_ctx.get("destinatario", ""),
        "remetente": log_ctx.get("remetente", ""),
        "assunto": log_ctx.get("assunto", ""),
        "recibo_id": log_ctx.get("recibo_id"),
        "recibo_numero": log_ctx.get("recibo_numero", ""),
        "contribuinte_id": log_ctx.get("contribuinte_id"),
        "contribuinte_nome": log_ctx.get("contribuinte_nome", ""),
        "smtp_host": log_ctx.get("smtp_host", ""),
    }


def _executar_envio_email_com_log(
    log_ctx: dict[str, Any],
    *,
    host: str,
    porta: int,
    usuario: Optional[str],
    senha: Optional[str],
    usar_starttls: bool,
    remetente: str,
    destinatario: str,
    assunto: str,
    html: Optional[str] = None,
    corpo_texto: Optional[str] = None,
    anexo_pdf: Optional[tuple[str, bytes]] = None,
) -> None:
    campos = _log_ctx_campos(log_ctx)
    try:
        enviar_email_smtp(
            host,
            porta,
            usuario,
            senha,
            usar_starttls,
            remetente,
            destinatario,
            assunto,
            html,
            corpo_texto=corpo_texto,
            anexo_pdf=anexo_pdf,
        )
        log_email_aceito_smtp(**campos)
    except Exception as exc:
        log_email_falha(**campos, erro=str(exc))


def disparar_email_background(
    bg: BackgroundTasks,
    *,
    log_ctx: dict[str, Any],
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
        _executar_envio_email_com_log,
        log_ctx,
        host=host,
        porta=porta,
        usuario=usuario,
        senha=senha,
        usar_starttls=usar_starttls,
        remetente=remetente,
        destinatario=destinatario,
        assunto=assunto,
        html=html,
    )


def disparar_email_com_anexo_background(
    bg: BackgroundTasks,
    *,
    log_ctx: dict[str, Any],
    host: str,
    porta: int,
    usuario: Optional[str],
    senha: Optional[str],
    usar_starttls: bool,
    remetente: str,
    destinatario: str,
    assunto: str,
    corpo_texto: str,
    anexo_nome: str,
    anexo_bytes: bytes,
) -> None:
    bg.add_task(
        _executar_envio_email_com_log,
        log_ctx,
        host=host,
        porta=porta,
        usuario=usuario,
        senha=senha,
        usar_starttls=usar_starttls,
        remetente=remetente,
        destinatario=destinatario,
        assunto=assunto,
        corpo_texto=corpo_texto,
        anexo_pdf=(anexo_nome, anexo_bytes),
    )