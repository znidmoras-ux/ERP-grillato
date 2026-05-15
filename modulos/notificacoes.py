"""
Grillato System - Alarme de Auditoria Diária
==============================================
Módulo 3: Notificações Windows para lembrete de auditoria.

Métodos de notificação (em ordem de prioridade):
1. win10toast / win10toast-click (Windows 10/11 Toast)
2. plyer (cross-platform fallback)
3. ctypes MessageBox (fallback nativo Windows)

Uso com Agendador de Tarefas do Windows:
    Veja instruções no final deste ficheiro.
"""

import sys
import os
from datetime import datetime


def notificar_auditoria(mensagem: str = None, titulo: str = None):
    """
    Dispara notificação de auditoria diária no Windows.

    Args:
        mensagem: Texto personalizado (opcional)
        titulo: Título da notificação (opcional)
    """
    if titulo is None:
        titulo = "Grillato System"

    if mensagem is None:
        mensagem = (
            "Auditoria Diaria Obrigatoria.\n"
            "Lance as notas e valide o estoque."
        )

    # Tenta win10toast primeiro
    if _notificar_win10toast(titulo, mensagem):
        return True

    # Tenta plyer como fallback
    if _notificar_plyer(titulo, mensagem):
        return True

    # Último recurso: MessageBox do Windows
    if _notificar_messagebox(titulo, mensagem):
        return True

    # Se nada funcionar, imprime no terminal
    print(f"\n{'='*50}")
    print(f"  {titulo}")
    print(f"  {mensagem}")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*50}\n")
    return False


def _notificar_win10toast(titulo: str, mensagem: str) -> bool:
    """Notificação via win10toast."""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            titulo,
            mensagem,
            duration=10,
            threaded=True,
        )
        return True
    except ImportError:
        return False
    except Exception:
        return False


def _notificar_plyer(titulo: str, mensagem: str) -> bool:
    """Notificação via plyer (cross-platform)."""
    try:
        from plyer import notification
        notification.notify(
            title=titulo,
            message=mensagem,
            app_name="Grillato System",
            timeout=10,
        )
        return True
    except ImportError:
        return False
    except Exception:
        return False


def _notificar_messagebox(titulo: str, mensagem: str) -> bool:
    """MessageBox nativo do Windows como fallback."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, mensagem, titulo, 0x40  # MB_ICONINFORMATION
        )
        return True
    except Exception:
        return False


def notificar_alerta_runway(dias_restantes: int, caixa: float):
    """Notificação específica de alerta de runway."""
    if dias_restantes <= 7:
        nivel = "CRITICO"
    elif dias_restantes <= 15:
        nivel = "ALERTA"
    else:
        nivel = "INFO"

    mensagem = (
        f"[{nivel}] Runway: {dias_restantes} dias\n"
        f"Caixa: R$ {caixa:,.2f}\n"
        f"Acao imediata necessaria!" if dias_restantes <= 7
        else f"[{nivel}] Runway: {dias_restantes} dias | Caixa: R$ {caixa:,.2f}"
    )
    notificar_auditoria(mensagem=mensagem, titulo="Grillato - Alerta de Caixa")


def notificar_estoque_critico(alertas: list):
    """Notificação de estoque abaixo do nível de segurança."""
    if not alertas:
        return
    msgs = [a["msg"] for a in alertas]
    mensagem = "RISCO DE RUTURA:\n" + "\n".join(msgs)
    notificar_auditoria(mensagem=mensagem, titulo="Grillato - Estoque Critico")


# ======================================================================
# Script standalone para o Agendador de Tarefas do Windows
# ======================================================================
if __name__ == "__main__":
    """
    Execute este ficheiro diretamente para disparar a notificação.

    Para agendar no Windows Task Scheduler:

    1. Abra o Agendador de Tarefas (taskschd.msc)
    2. Clique em "Criar Tarefa Basica..."
    3. Nome: "Grillato - Auditoria Diaria"
    4. Gatilho: Diariamente, às 08:00 (ou horário desejado)
    5. Ação: Iniciar um programa
       - Programa: caminho do python.exe (ex: C:\\Python311\\python.exe)
       - Argumentos: caminho deste ficheiro
         Ex: "C:\\System Grillato\\Grillato System\\modulos\\notificacoes.py"
       - Iniciar em: "C:\\System Grillato\\Grillato System"
    6. Marque "Abrir diálogo de propriedades ao concluir"
    7. Na aba Condições, desmarque "Iniciar somente se AC"
    8. Na aba Configurações, marque "Executar tarefa o mais rápido possível
       após um gatilho agendado ser perdido"

    Alternativa via linha de comando (CMD como Administrador):
    -------------------------------------------------------
    schtasks /create /tn "Grillato_Auditoria" /tr "python C:\\System Grillato\\Grillato System\\modulos\\notificacoes.py" /sc daily /st 08:00 /f

    Para testar manualmente:
    ------------------------
    python notificacoes.py
    """
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Disparando auditoria...")
    notificar_auditoria()
    print("Notificacao enviada.")
