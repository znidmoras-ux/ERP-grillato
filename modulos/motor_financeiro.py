"""
Grillato System - Motor Financeiro
===================================
Modulo 1: Runway Tracker & Processamento de CSV de Vendas
"""

import csv
import json
import os
from datetime import datetime, timedelta
from collections import deque
from typing import Optional


class MotorFinanceiro:
    """Motor de Queima de Caixa (Runway Tracker)."""

    def __init__(self, config: dict):
        self.config = config
        fin = config["financeiro"]
        self.meta_diaria = fin["meta_breakeven_diaria"]
        self.caixa_inicial = fin["caixa_sobrevivencia"]
        self.custo_fixo_mensal = fin["custo_fixo_mensal"]
        self.dias_operacao = fin["dias_operacao_mes"]
        self.log_path = config["caminhos"]["log_runway"]
        self.estado = self._carregar_estado()

    def _carregar_estado(self) -> dict:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "caixa_atual" in data:
                    return data
            except (json.JSONDecodeError, KeyError):
                pass
        return {
            "caixa_atual": self.caixa_inicial,
            "historico_diario": [],
            "media_movel_3d": 0.0,
            "runway_dias": 0,
            "ultima_atualizacao": None,
        }

    def _salvar_estado(self):
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)

    def processar_csv_vendas(self, caminho_csv: str) -> dict:
        if not os.path.exists(caminho_csv):
            raise FileNotFoundError(f"CSV nao encontrado: {caminho_csv}")
        registros = []
        with open(caminho_csv, "r", encoding="utf-8-sig") as f:
            amostra = f.read(2048)
            f.seek(0)
            delimitador = ";" if amostra.count(";") > amostra.count(",") else ","
            leitor = csv.DictReader(f, delimiter=delimitador)
            campos = [c.strip().lower() for c in (leitor.fieldnames or [])]
            for linha in leitor:
                linha_norm = {k.strip().lower(): v.strip() for k, v in linha.items()}
                registros.append(linha_norm)
        return self._extrair_metricas(registros, campos)

    def _extrair_metricas(self, registros: list, campos: list) -> dict:
        faturamento_total = 0.0
        faturamento_direto = 0.0
        faturamento_ifood = 0.0
        total_pedidos = 0
        for reg in registros:
            valor = self._extrair_valor(reg)
            if valor <= 0:
                continue
            total_pedidos += 1
            faturamento_total += valor
            canal = self._detectar_canal(reg)
            if canal == "direto":
                faturamento_direto += valor
            else:
                faturamento_ifood += valor
        ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0.0
        return {
            "data_processamento": datetime.now().strftime("%Y-%m-%d"),
            "faturamento_bruto": round(faturamento_total, 2),
            "faturamento_direto": round(faturamento_direto, 2),
            "faturamento_ifood": round(faturamento_ifood, 2),
            "total_pedidos": total_pedidos,
            "ticket_medio": round(ticket_medio, 2),
        }

    def _extrair_valor(self, reg: dict) -> float:
        chaves = [
            "valor total", "valor_total", "total", "valor",
            "receita", "revenue", "amount", "subtotal",
            "valor do pedido", "valor_pedido",
        ]
        for chave in chaves:
            if chave in reg:
                return self._parse_moeda(reg[chave])
        return 0.0

    def _detectar_canal(self, reg: dict) -> str:
        chaves = ["canal", "origem", "source", "channel", "tipo"]
        for chave in chaves:
            if chave in reg:
                val = reg[chave].lower()
                if any(t in val for t in ["ifood", "marketplace", "plataforma"]):
                    return "ifood"
                if any(t in val for t in ["direto", "menu", "share", "whatsapp", "loja"]):
                    return "direto"
        return "ifood"

    @staticmethod
    def _parse_moeda(texto: str) -> float:
        if not texto:
            return 0.0
        limpo = texto.replace("R$", "").replace(" ", "").strip()
        if "," in limpo and "." in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        elif "," in limpo:
            limpo = limpo.replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return 0.0

    def atualizar_runway(self, metricas_dia: dict) -> dict:
        fat_bruto = metricas_dia["faturamento_bruto"]
        deficit = 0.0
        if fat_bruto < self.meta_diaria:
            deficit = self.meta_diaria - fat_bruto
            self.estado["caixa_atual"] = round(self.estado["caixa_atual"] - deficit, 2)
        superavit = max(0, fat_bruto - self.meta_diaria)
        entrada = {
            "data": metricas_dia["data_processamento"],
            "faturamento": fat_bruto,
            "deficit": round(deficit, 2),
            "superavit": round(superavit, 2),
            "caixa_pos": self.estado["caixa_atual"],
            "pedidos": metricas_dia["total_pedidos"],
            "ticket_medio": metricas_dia["ticket_medio"],
        }
        self.estado["historico_diario"].append(entrada)
        ultimos_3 = self.estado["historico_diario"][-3:]
        media_fat_3d = sum(d["faturamento"] for d in ultimos_3) / len(ultimos_3)
        deficit_medio_3d = max(0, self.meta_diaria - media_fat_3d)
        self.estado["media_movel_3d"] = round(media_fat_3d, 2)
        if deficit_medio_3d > 0:
            self.estado["runway_dias"] = int(self.estado["caixa_atual"] / deficit_medio_3d)
        else:
            self.estado["runway_dias"] = -1
        self.estado["ultima_atualizacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._salvar_estado()
        return self._gerar_relatorio(metricas_dia, deficit, deficit_medio_3d)

    def _gerar_relatorio(self, metricas: dict, deficit_hoje: float, deficit_medio_3d: float) -> dict:
        caixa = self.estado["caixa_atual"]
        runway = self.estado["runway_dias"]
        if runway == -1:
            risco, cor = "SUSTENTAVEL", "verde"
        elif runway <= 7:
            risco, cor = "CRITICO", "vermelho"
        elif runway <= 15:
            risco, cor = "ALERTA", "amarelo"
        else:
            risco, cor = "MONITORAR", "amarelo"
        return {
            "data": metricas["data_processamento"],
            "faturamento_bruto": metricas["faturamento_bruto"],
            "faturamento_direto": metricas.get("faturamento_direto", 0),
            "faturamento_ifood": metricas.get("faturamento_ifood", 0),
            "total_pedidos": metricas["total_pedidos"],
            "ticket_medio": metricas["ticket_medio"],
            "meta_diaria": self.meta_diaria,
            "deficit_hoje": round(deficit_hoje, 2),
            "deficit_medio_3d": round(deficit_medio_3d, 2),
            "caixa_restante": caixa,
            "runway_dias": runway,
            "nivel_risco": risco,
            "cor_risco": cor,
            "media_movel_3d": self.estado["media_movel_3d"],
            "pct_meta": round((metricas["faturamento_bruto"] / self.meta_diaria) * 100, 1),
        }

    def registrar_dia_manual(self, faturamento: float, pedidos: int, pct_direto: float = 0.3) -> dict:
        metricas = {
            "data_processamento": datetime.now().strftime("%Y-%m-%d"),
            "faturamento_bruto": round(faturamento, 2),
            "faturamento_direto": round(faturamento * pct_direto, 2),
            "faturamento_ifood": round(faturamento * (1 - pct_direto), 2),
            "total_pedidos": pedidos,
            "ticket_medio": round(faturamento / max(pedidos, 1), 2),
        }
        return self.atualizar_runway(metricas)

    def get_status_caixa(self) -> dict:
        return {
            "caixa_atual": self.estado["caixa_atual"],
            "caixa_inicial": self.caixa_inicial,
            "pct_consumido": round(
                (1 - self.estado["caixa_atual"] / self.caixa_inicial) * 100, 1
            ) if self.caixa_inicial > 0 else 0.0,
            "runway_dias": self.estado["runway_dias"],
            "media_movel_3d": self.estado["media_movel_3d"],
            "dias_registrados": len(self.estado["historico_diario"]),
            "ultima_atualizacao": self.estado["ultima_atualizacao"],
        }

    def remover_ultimo_dia(self) -> bool:
        historico = self.estado["historico_diario"]
        if not historico:
            return False
        removido = historico.pop()
        self.estado["caixa_atual"] = round(
            self.estado["caixa_atual"] + removido.get("deficit", 0), 2
        )
        if historico:
            ultimos_3 = historico[-3:]
            media = sum(d["faturamento"] for d in ultimos_3) / len(ultimos_3)
            self.estado["media_movel_3d"] = round(media, 2)
            deficit_medio = max(0, self.meta_diaria - media)
            if deficit_medio > 0:
                self.estado["runway_dias"] = int(self.estado["caixa_atual"] / deficit_medio)
            else:
                self.estado["runway_dias"] = -1
        else:
            self.estado["media_movel_3d"] = 0.0
            self.estado["runway_dias"] = 0
        self.estado["ultima_atualizacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._salvar_estado()
        return True

    def atualizar_caixa_manual(self, novo_saldo: float):
        self.estado["caixa_atual"] = round(novo_saldo, 2)
        self.estado["ultima_atualizacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._salvar_estado()

    def limpar_historico(self):
        self.estado = {
            "caixa_atual": self.caixa_inicial,
            "historico_diario": [],
            "media_movel_3d": 0.0,
            "runway_dias": 0,
            "ultima_atualizacao": None,
        }
        self._salvar_estado()
