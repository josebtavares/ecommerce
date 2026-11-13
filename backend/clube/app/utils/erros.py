"""Erros que o código apanha para não parar (ex.: um ciclo do worker) mas que alguém tem de ver: vão para o Sentry.
Sem SENTRY_DSN o capture_exception não faz nada."""


def reportar(erro=None):
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(erro)
    except Exception:       # o Sentry nunca pode partir quem o chama
        pass
