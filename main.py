"""
╔══════════════════════════════════════════════════════════════╗
║              GRILLATO SYSTEM - CFO VIRTUAL                   ║
║         Motor Financeiro & Controle Operacional              ║
║                   Arapongas - PR                             ║
╚══════════════════════════════════════════════════════════════╝

Sistema local de monitorização de fluxo de caixa, CMV e estoque
para a Grillato Hamburgueria.

Uso:
    python main.py                  → Menu interativo principal
    python main.py --csv vendas.csv → Processa CSV de vendas
    python main.py --radar          → Abre Radar de Inflação
    python main.py --notificar      → Dispara notificação de auditoria
    python main.py --status         → Status rápido do caixa
"""

import json
import os
import sys
import argparse
from datetime import datetime

# Garante que o diretório raiz está no path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from modulos.motor_financeiro import MotorFinanceiro
from modulos.gestao_estoque import GestaoEstoque
from modulos.notificacoes import (
    notificar_auditoria,
    notificar_alerta_runway,
    notificar_estoque_critico,
)


# ======================================================================
# Configuração
# ======================================================================
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def carregar_config() -> dict:
    """Carrega e resolve paths relativos do config.json."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Resolve caminhos relativos para absolutos
    for chave, caminho in config["caminhos"].items():
        if not os.path.isabs(caminho):
            config["caminhos"][chave] = os.path.join(ROOT_DIR, caminho)

    return config


# ======================================================================
# Formatação de Terminal
# ======================================================================
class Cores:
    """Códigos ANSI para cores no terminal Windows (cmd/PowerShell)."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    DIM = "\033[2m"

    @staticmethod
    def ativar_ansi_windows():
        """Ativa suporte a ANSI no terminal Windows."""
        if sys.platform == "win32":
            os.system("")  # Truque para ativar VT100 no cmd


def banner():
    Cores.ativar_ansi_windows()
    print(f"""
{Cores.RED}{'='*60}
  ╔═╗╦═╗╦╦  ╦  ╔═╗╔╦╗╔═╗  ╔═╗╦ ╦╔═╗╔╦╗╔═╗╔╦╗
  ║ ╦╠╦╝║║  ║  ╠═╣ ║ ║ ║  ╚═╗╚╦╝╚═╗ ║ ║╣ ║║║
  ╚═╝╩╚═╩╩═╝╩═╝╩ ╩ ╩ ╚═╝  ╚═╝ ╩ ╚═╝ ╩ ╚═╝╩ ╩
{'='*60}{Cores.RESET}
  {Cores.DIM}CFO Virtual | Arapongas - PR | {datetime.now().strftime('%d/%m/%Y %H:%M')}{Cores.RESET}
""")


def separador(titulo: str = ""):
    if titulo:
        print(f"\n{Cores.CYAN}--- {titulo} {'─' * (50 - len(titulo))}{Cores.RESET}")
    else:
        print(f"{Cores.DIM}{'─' * 60}{Cores.RESET}")


def exibir_relatorio_runway(relatorio: dict):
    """Exibe relatório de runway formatado no terminal."""
    separador("RELATORIO DE RUNWAY")

    # Risco
    cor_risco = {
        "vermelho": Cores.RED,
        "amarelo": Cores.YELLOW,
        "verde": Cores.GREEN,
    }.get(relatorio["cor_risco"], Cores.YELLOW)

    print(f"""
  {Cores.BOLD}Data:{Cores.RESET} {relatorio['data']}
  {Cores.BOLD}Faturamento:{Cores.RESET} R$ {relatorio['faturamento_bruto']:,.2f}  ({relatorio['pct_meta']:.0f}% da meta)
    Direto:  R$ {relatorio.get('faturamento_direto', 0):,.2f}
    iFood:   R$ {relatorio.get('faturamento_ifood', 0):,.2f}
  {Cores.BOLD}Pedidos:{Cores.RESET} {relatorio['total_pedidos']}  |  Ticket Medio: R$ {relatorio['ticket_medio']:,.2f}

  {Cores.BOLD}Meta Diaria:{Cores.RESET}      R$ {relatorio['meta_diaria']:,.2f}
  {Cores.BOLD}Deficit Hoje:{Cores.RESET}     {Cores.RED}R$ {relatorio['deficit_hoje']:,.2f}{Cores.RESET}
  {Cores.BOLD}Media Movel 3d:{Cores.RESET}   R$ {relatorio['media_movel_3d']:,.2f}

  {cor_risco}{Cores.BOLD}╔══════════════════════════════════════════╗
  ║  CAIXA RESTANTE:  R$ {relatorio['caixa_restante']:>10,.2f}          ║
  ║  RUNWAY:          {relatorio['runway_dias'] if relatorio['runway_dias'] >= 0 else 'SUSTENTAVEL':>10} dias          ║
  ║  NIVEL DE RISCO:  {relatorio['nivel_risco']:>10}               ║
  ╚══════════════════════════════════════════╝{Cores.RESET}
""")


def exibir_status_estoque(resultado: dict):
    """Exibe resultado do processamento de estoque."""
    separador("ESTOQUE - BAIXA DO DIA")

    vendas = resultado["vendas"]
    print(f"  Vendas: {vendas['smash']} smashs + {vendas['alto']} altos = {vendas['total']} lanches")
    print(f"\n  {'Insumo':<20} {'Consumo':>10} {'Saldo':>10}")
    print(f"  {'─'*42}")

    for insumo, qtd in resultado["consumo"].items():
        saldo = resultado["saldo_atual"].get(insumo, 0)
        unidade = "un" if "unid" in insumo else "kg"
        print(f"  {insumo:<20} -{qtd:>8.3f} {saldo:>8.3f} {unidade}")

    if resultado["alertas"]:
        print(f"\n{Cores.RED}{Cores.BOLD}  *** ALERTAS DE RUTURA ***{Cores.RESET}")
        for alerta in resultado["alertas"]:
            print(f"  {Cores.RED}{alerta['msg']}{Cores.RESET}")


# ======================================================================
# Menu Interativo
# ======================================================================
def menu_principal(config: dict):
    """Menu interativo principal do sistema."""
    motor = MotorFinanceiro(config)
    estoque = GestaoEstoque(config)

    while True:
        separador("MENU PRINCIPAL")
        print(f"""
  {Cores.BOLD}1.{Cores.RESET} Registrar vendas do dia (manual)
  {Cores.BOLD}2.{Cores.RESET} Processar CSV de vendas
  {Cores.BOLD}3.{Cores.RESET} Abrir Radar de Inflacao
  {Cores.BOLD}4.{Cores.RESET} Registrar entrada de estoque
  {Cores.BOLD}5.{Cores.RESET} Baixar estoque (vendas do dia)
  {Cores.BOLD}6.{Cores.RESET} Projecao de estoque
  {Cores.BOLD}7.{Cores.RESET} Status do caixa (Runway)
  {Cores.BOLD}8.{Cores.RESET} Disparar notificacao de auditoria
  {Cores.BOLD}0.{Cores.RESET} Sair
""")
        opcao = input(f"  {Cores.CYAN}Opcao > {Cores.RESET}").strip()

        if opcao == "1":
            _registrar_vendas_manual(motor)
        elif opcao == "2":
            _processar_csv(motor)
        elif opcao == "3":
            _abrir_radar(config)
        elif opcao == "4":
            _registrar_entrada_estoque(estoque)
        elif opcao == "5":
            _baixar_estoque_vendas(estoque)
        elif opcao == "6":
            _projecao_estoque(estoque)
        elif opcao == "7":
            _status_caixa(motor)
        elif opcao == "8":
            notificar_auditoria()
            print(f"  {Cores.GREEN}Notificacao disparada.{Cores.RESET}")
        elif opcao == "0":
            print(f"\n  {Cores.DIM}Grillato System encerrado.{Cores.RESET}\n")
            break
        else:
            print(f"  {Cores.YELLOW}Opcao invalida.{Cores.RESET}")


def _registrar_vendas_manual(motor: MotorFinanceiro):
    """Opção 1: Registro manual de vendas."""
    separador("REGISTRO MANUAL DE VENDAS")
    try:
        fat = float(input("  Faturamento bruto do dia (R$): ").replace(",", "."))
        ped = int(input("  Numero de pedidos: "))
        pct = input("  % vendas diretas (0-100, Enter=30): ").strip()
        pct_direto = float(pct.replace(",", ".")) / 100 if pct else 0.3

        relatorio = motor.registrar_dia_manual(fat, ped, pct_direto)
        exibir_relatorio_runway(relatorio)

        # Notifica se runway crítico
        if relatorio["runway_dias"] >= 0 and relatorio["runway_dias"] <= 7:
            notificar_alerta_runway(
                relatorio["runway_dias"], relatorio["caixa_restante"]
            )

    except (ValueError, KeyboardInterrupt):
        print(f"  {Cores.YELLOW}Entrada cancelada ou invalida.{Cores.RESET}")


def _processar_csv(motor: MotorFinanceiro):
    """Opção 2: Processar CSV de vendas."""
    separador("PROCESSAR CSV DE VENDAS")
    caminho = input("  Caminho do CSV: ").strip().strip('"')

    if not caminho:
        # Lista CSVs disponíveis na pasta padrão
        pasta_csv = motor.config["caminhos"]["csv_vendas"]
        if os.path.exists(pasta_csv):
            csvs = [f for f in os.listdir(pasta_csv) if f.endswith(".csv")]
            if csvs:
                print(f"\n  CSVs disponiveis em {pasta_csv}:")
                for i, f in enumerate(csvs, 1):
                    print(f"    {i}. {f}")
                sel = input(f"\n  Selecione (1-{len(csvs)}): ").strip()
                try:
                    caminho = os.path.join(pasta_csv, csvs[int(sel) - 1])
                except (ValueError, IndexError):
                    print(f"  {Cores.YELLOW}Selecao invalida.{Cores.RESET}")
                    return
            else:
                print(f"  {Cores.YELLOW}Nenhum CSV encontrado em {pasta_csv}{Cores.RESET}")
                return
        else:
            print(f"  {Cores.YELLOW}Pasta de CSVs nao encontrada.{Cores.RESET}")
            return

    try:
        metricas = motor.processar_csv_vendas(caminho)
        relatorio = motor.atualizar_runway(metricas)
        exibir_relatorio_runway(relatorio)
    except FileNotFoundError as e:
        print(f"  {Cores.RED}Erro: {e}{Cores.RESET}")
    except Exception as e:
        print(f"  {Cores.RED}Erro ao processar CSV: {e}{Cores.RESET}")


def _abrir_radar(config: dict):
    """Opção 3: Abre o Radar de Inflação."""
    separador("RADAR DE INFLACAO")
    print(f"  {Cores.CYAN}Abrindo interface grafica...{Cores.RESET}")
    try:
        from modulos.radar_inflacao import abrir_radar
        abrir_radar(config)
    except ImportError as e:
        print(f"  {Cores.RED}Erro: tkinter nao disponivel. {e}{Cores.RESET}")
        print(f"  {Cores.YELLOW}Instale com: pip install tk{Cores.RESET}")
    except Exception as e:
        print(f"  {Cores.RED}Erro ao abrir radar: {e}{Cores.RESET}")


def _registrar_entrada_estoque(estoque: GestaoEstoque):
    """Opção 4: Registra entrada de insumo."""
    separador("ENTRADA DE ESTOQUE")
    insumos = ["carne_kg", "bacon_kg", "cheddar_kg", "batata_kg", "pao_brioche_unid"]

    print("  Insumos disponiveis:")
    for i, ins in enumerate(insumos, 1):
        saldo = estoque.inventario.get(ins, 0)
        print(f"    {i}. {ins:<20} (saldo: {saldo:.2f})")

    try:
        sel = int(input("\n  Selecione o insumo (1-5): ")) - 1
        insumo = insumos[sel]
        qtd = float(input(f"  Quantidade ({insumo}): ").replace(",", "."))
        forn = input("  Fornecedor (opcional): ").strip()

        estoque.registrar_entrada(insumo, qtd, forn)
        print(f"\n  {Cores.GREEN}Entrada registrada: +{qtd} {insumo}{Cores.RESET}")
        print(f"  Novo saldo: {estoque.inventario[insumo]:.2f}")
    except (ValueError, IndexError, KeyboardInterrupt):
        print(f"  {Cores.YELLOW}Entrada cancelada ou invalida.{Cores.RESET}")


def _baixar_estoque_vendas(estoque: GestaoEstoque):
    """Opção 5: Deduz estoque pelas vendas do dia."""
    separador("BAIXA DE ESTOQUE (VENDAS DO DIA)")
    try:
        smash = int(input("  Qtd Smashs vendidos (70g): "))
        alto = int(input("  Qtd Altos vendidos (100g): "))

        resultado = estoque.processar_vendas_dia(smash, alto)
        exibir_status_estoque(resultado)

        # Notifica se houver alertas
        if resultado["alertas"]:
            notificar_estoque_critico(resultado["alertas"])

    except (ValueError, KeyboardInterrupt):
        print(f"  {Cores.YELLOW}Entrada cancelada ou invalida.{Cores.RESET}")


def _projecao_estoque(estoque: GestaoEstoque):
    """Opção 6: Projeção de dias de estoque."""
    separador("PROJECAO DE ESTOQUE")
    try:
        ms = input("  Media smashs/dia (Enter=10): ").strip()
        ma = input("  Media altos/dia (Enter=5): ").strip()
        media_s = int(ms) if ms else 10
        media_a = int(ma) if ma else 5

        proj = estoque.projetar_dias_estoque(media_s, media_a)

        print(f"\n  {'Insumo':<20} {'Saldo':>8} {'Consumo/dia':>12} {'Dias':>8}")
        print(f"  {'─'*50}")
        for key, dados in proj.items():
            if key == "gargalo":
                continue
            print(
                f"  {key:<20} {dados['saldo']:>8.2f} "
                f"{dados['consumo_dia']:>12.3f} "
                f"{dados['dias_restantes']:>8.1f}"
            )

        g = proj["gargalo"]
        cor = Cores.RED if g["dias"] < 3 else Cores.YELLOW
        print(f"\n  {cor}Gargalo: {g['insumo']} ({g['dias']:.1f} dias){Cores.RESET}")

    except (ValueError, KeyboardInterrupt):
        print(f"  {Cores.YELLOW}Projecao cancelada.{Cores.RESET}")


def _status_caixa(motor: MotorFinanceiro):
    """Opção 7: Status atual do caixa."""
    separador("STATUS DO CAIXA")
    status = motor.get_status_caixa()

    runway = status["runway_dias"]
    if runway == -1:
        cor = Cores.GREEN
        runway_txt = "SUSTENTAVEL"
    elif runway <= 7:
        cor = Cores.RED
        runway_txt = f"{runway} dias"
    else:
        cor = Cores.YELLOW
        runway_txt = f"{runway} dias"

    print(f"""
  {Cores.BOLD}Caixa Inicial:{Cores.RESET}       R$ {status['caixa_inicial']:>10,.2f}
  {Cores.BOLD}Caixa Atual:{Cores.RESET}         R$ {status['caixa_atual']:>10,.2f}
  {Cores.BOLD}Consumido:{Cores.RESET}            {status['pct_consumido']:.1f}%
  {Cores.BOLD}Runway:{Cores.RESET}               {cor}{runway_txt}{Cores.RESET}
  {Cores.BOLD}Media Movel 3d:{Cores.RESET}      R$ {status['media_movel_3d']:>10,.2f}
  {Cores.BOLD}Dias Registrados:{Cores.RESET}     {status['dias_registrados']}
  {Cores.BOLD}Ultima Atualizacao:{Cores.RESET}  {status['ultima_atualizacao'] or 'Nenhum dado'}
""")


# ======================================================================
# CLI / Entry Point
# ======================================================================
def main():
    """Ponto de entrada principal."""
    banner()
    config = carregar_config()

    parser = argparse.ArgumentParser(description="Grillato System - CFO Virtual")
    parser.add_argument("--csv", help="Caminho do CSV de vendas para processar")
    parser.add_argument("--radar", action="store_true", help="Abrir Radar de Inflacao")
    parser.add_argument("--notificar", action="store_true", help="Disparar notificacao")
    parser.add_argument("--status", action="store_true", help="Status do caixa")

    args = parser.parse_args()

    if args.csv:
        motor = MotorFinanceiro(config)
        metricas = motor.processar_csv_vendas(args.csv)
        relatorio = motor.atualizar_runway(metricas)
        exibir_relatorio_runway(relatorio)

    elif args.radar:
        from modulos.radar_inflacao import abrir_radar
        abrir_radar(config)

    elif args.notificar:
        notificar_auditoria()

    elif args.status:
        motor = MotorFinanceiro(config)
        _status_caixa(motor)

    else:
        # Menu interativo
        menu_principal(config)


if __name__ == "__main__":
    main()
