"""Temporizador independente da interface e do controle virtual."""

import math
import random
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    minimum: float = 3.0
    maximum: float = 10.0
    simulate: bool = False

    def __post_init__(self):
        if not (math.isfinite(self.minimum) and math.isfinite(self.maximum)):
            raise ValueError("Informe intervalos numéricos finitos.")
        if not 0.5 <= self.minimum <= self.maximum <= 3600:
            raise ValueError("Use 0,5 a 3600 segundos, com mínimo ≤ máximo.")


def run(settings, stop, is_focused, pad_factory, emit,
        clock=time.monotonic, choose_delay=random.uniform):
    """Executa até stop; todas as esperas podem ser interrompidas."""
    pad = None
    count = 0
    due = None
    last_status = None
    try:
        if not settings.simulate:
            pad = pad_factory()
        while not stop.is_set():
            focused = settings.simulate or is_focused()
            if not focused:
                due = None  # Ao voltar ao jogo, aguarda um intervalo completo.
                status = "Pausado · coloque o Fortnite em primeiro plano"
            else:
                if due is None:
                    due = clock() + choose_delay(settings.minimum, settings.maximum)
                remaining = due - clock()
                if remaining <= 0:
                    # Revalida o foco imediatamente antes de enviar o botão.
                    if not stop.is_set() and (settings.simulate or is_focused()):
                        sent = settings.simulate or pad.tap_y(stop)
                        if sent:
                            count += 1
                            emit("count", count)
                    due = None
                    continue
                prefix = "Simulação" if settings.simulate else "Ligado"
                status = f"{prefix} · próximo Y em {remaining:.1f} s"
            if status != last_status:
                emit("status", status)
                last_status = status
            stop.wait(0.1)
    except Exception as exc:
        emit("error", str(exc))
    finally:
        try:
            if pad is not None:
                pad.close()
        except Exception as exc:
            emit("error", f"Falha ao liberar o controle: {exc}")
        emit("done", None)
