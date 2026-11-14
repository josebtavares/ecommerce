"""Erros que o código apanha para não parar (ex.: um ciclo do worker) mas que alguém tem de ver: vão para o Sentry.
Sem SENTRY_DSN o capture_exception não faz nada."""


def reportar(erro=None):
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(erro)
    except Exception:       # o Sentry nunca pode partir quem o chama
        pass


# ── Cron Monitors: tarefas agendadas avisam o Sentry quando começam e acabam ──────────────────────────────
# Se o aviso de fim não chegar a tempo (a tarefa não correu ou ficou presa) ou chegar "erro", o Sentry
# manda email. Só na produção: na dev o worker não corre de noite e ia parecer que a tarefa falhou.

def _cron_ligado():
    try:
        from django.conf import settings
        if not getattr(settings, 'SENTRY_LIGADO', False):
            return False
        import sentry_sdk
        return sentry_sdk.get_client().options.get('environment') == 'producao'
    except Exception:
        return False


def cron_inicio(slug, config):
    """Devolve o id do check-in (ou None) para passar ao cron_fim. config: horário, fuso, margem, duração máx."""
    if not _cron_ligado():
        return None
    try:
        from sentry_sdk.crons import capture_checkin
        return capture_checkin(monitor_slug=slug, status='in_progress', monitor_config=config)
    except Exception:
        return None


def cron_fim(slug, check_in_id, ok, duracao=None, config=None):
    if not _cron_ligado():
        return
    try:
        from sentry_sdk.crons import capture_checkin
        capture_checkin(monitor_slug=slug, check_in_id=check_in_id, status='ok' if ok else 'error',
                        duration=duracao, monitor_config=config)
    except Exception:
        pass
