from __future__ import annotations

import smtplib
from typing import Literal, Optional

from app.models.sys_models import ConfigAPPF
from app.runtime_paths import resolver_arquivo_assinatura
from app.services.email_service import abrir_conexao_smtp, autenticar_smtp_se_necessario
from app.services.smtp_config_service import SmtpSettings, obter_smtp_da_config

EscopoValidacao = Literal["appf", "email", "tudo"]


def _arquivo_assinatura_existe(caminho: Optional[str]) -> bool:
    return resolver_arquivo_assinatura(caminho) is not None


def testar_conexao_smtp(smtp: SmtpSettings) -> tuple[bool, str]:
    if not (smtp.host or "").strip():
        return False, "Informe o host do servidor SMTP."
    if not (smtp.remetente or "").strip():
        return False, "Informe o e-mail remetente."

    server = None
    try:
        server = abrir_conexao_smtp(smtp.host, int(smtp.porta), smtp.usar_starttls, timeout=20)

        if smtp.usuario and not smtp.senha:
            return (
                False,
                "Usuário SMTP informado, mas não há senha salva. "
                "Informe a senha e salve novamente para testar a autenticação.",
            )
        if smtp.senha and not smtp.usuario:
            return False, "Há senha configurada, mas o usuário SMTP está vazio."

        autenticou, ignorado = autenticar_smtp_se_necessario(server, smtp.usuario, smtp.senha)

        if ignorado == "servidor_sem_auth" and smtp.usuario:
            return (
                True,
                f"Conexão com {smtp.host}:{smtp.porta} OK. "
                "Este servidor não usa autenticação SMTP (usuário/senha serão ignorados no envio).",
            )
        if autenticou:
            return (
                True,
                f"Conexão e autenticação com {smtp.host}:{smtp.porta} verificadas com sucesso.",
            )
        return True, f"Conexão com {smtp.host}:{smtp.porta} estabelecida com sucesso (sem autenticação)."
    except smtplib.SMTPAuthenticationError:
        return False, "Autenticação recusada: verifique usuário e senha SMTP."
    except smtplib.SMTPConnectError:
        return False, f"Não foi possível conectar em {smtp.host}:{smtp.porta}."
    except smtplib.SMTPException as exc:
        return False, f"Erro SMTP: {exc}"
    except TimeoutError:
        return False, "Tempo esgotado ao conectar ao servidor SMTP."
    except OSError as exc:
        return False, f"Erro de rede ao conectar ao SMTP: {exc}"
    except ValueError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Falha ao testar SMTP: {exc}"
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass


def validar_config_appf(cfg: ConfigAPPF) -> list[dict]:
    itens: list[dict] = []

    def add(campo: str, ok: bool, mensagem: str) -> None:
        itens.append({"campo": campo, "ok": ok, "mensagem": mensagem})

    if not (cfg.razao_social or "").strip():
        add("razao_social", False, "Razão social não informada.")
    else:
        add("razao_social", True, "Razão social configurada.")

    if not (cfg.cnpj or "").strip():
        add("cnpj", False, "CNPJ não informado.")
    else:
        add("cnpj", True, "CNPJ configurado.")

    if not (cfg.endereco or "").strip():
        add("endereco", False, "Endereço não informado.")
    else:
        add("endereco", True, "Endereço configurado.")

    if not (cfg.nome_presidente or "").strip():
        add("nome_presidente", False, "Nome do presidente não informado.")
    else:
        add("nome_presidente", True, "Nome do presidente configurado.")

    if not (cfg.nome_tesoureiro or "").strip():
        add("nome_tesoureiro", False, "Nome do tesoureiro não informado.")
    else:
        add("nome_tesoureiro", True, "Nome do tesoureiro configurado.")

    if _arquivo_assinatura_existe(cfg.caminho_assinatura_presidente):
        add("assinatura_presidente", True, "Arquivo de assinatura do presidente encontrado.")
    else:
        add(
            "assinatura_presidente",
            False,
            "Assinatura do presidente não cadastrada ou arquivo ausente no servidor.",
        )

    if _arquivo_assinatura_existe(cfg.caminho_assinatura_tesoureiro):
        add("assinatura_tesoureiro", True, "Arquivo de assinatura do tesoureiro encontrado.")
    else:
        add(
            "assinatura_tesoureiro",
            False,
            "Assinatura do tesoureiro não cadastrada ou arquivo ausente no servidor.",
        )

    return itens


def validar_config_email(cfg: ConfigAPPF) -> list[dict]:
    smtp = obter_smtp_da_config(cfg)
    itens: list[dict] = []

    if not (smtp.host or "").strip():
        itens.append({"campo": "smtp_host", "ok": False, "mensagem": "Host SMTP não informado."})
    else:
        itens.append({"campo": "smtp_host", "ok": True, "mensagem": f"Host SMTP: {smtp.host}."})

    if not (smtp.remetente or "").strip():
        itens.append({"campo": "smtp_remetente", "ok": False, "mensagem": "E-mail remetente não informado."})
    else:
        itens.append({"campo": "smtp_remetente", "ok": True, "mensagem": f"Remetente: {smtp.remetente}."})

    if smtp.usuario and not smtp.senha:
        itens.append(
            {
                "campo": "smtp_senha",
                "ok": False,
                "mensagem": "Usuário SMTP definido, mas a senha ainda não foi configurada.",
            }
        )

    ok_conn, msg_conn = testar_conexao_smtp(smtp)
    itens.append({"campo": "smtp_conexao", "ok": ok_conn, "mensagem": msg_conn})

    return itens


def validar_configuracao(cfg: ConfigAPPF, escopo: EscopoValidacao = "tudo") -> dict:
    itens: list[dict] = []
    if escopo in ("appf", "tudo"):
        itens.extend(validar_config_appf(cfg))
    if escopo in ("email", "tudo"):
        itens.extend(validar_config_email(cfg))

    ok = all(i["ok"] for i in itens)
    return {"ok": ok, "escopo": escopo, "itens": itens}
