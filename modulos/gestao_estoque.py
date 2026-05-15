"""
Grillato System - Gestao de Estoque
Modulo 4: Controle de inventario com foco no teto de 17 pedidos/dia.
"""

import json
import os
from datetime import datetime
from typing import Tuple

CONSUMO_SMASH = {
    "carne_kg": 0.070,
    "bacon_kg": 0.025,
    "cheddar_kg": 0.030,
    "pao_brioche_unid": 1,
    "batata_kg": 0.100,
}

CONSUMO_ALTO = {
    "carne_kg": 0.100,
    "bacon_kg": 0.035,
    "cheddar_kg": 0.040,
    "pao_brioche_unid": 1,
    "batata_kg": 0.120,
}


class GestaoEstoque:
    """Controla o inventario de insumos da Grillato."""

    def __init__(self, config: dict):
        self.config = config
        self.log_path = config["caminhos"]["log_estoque"]
        self.estoque_seguranca = config["producao"]["estoque_seguranca"]
        self.inventario = self._carregar_inventario()

    def _carregar_inventario(self) -> dict:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "carne_kg" in data:
                    return data
            except (json.JSONDecodeError, KeyError):
                pass
        return {
            "carne_kg": 0.0,
            "bacon_kg": 0.0,
            "cheddar_kg": 0.0,
            "pao_brioche_unid": 0,
            "batata_kg": 0.0,
            "ultima_atualizacao": None,
            "historico_movimentos": [],
        }

    def _salvar_inventario(self):
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.inventario, f, indent=2, ensure_ascii=False)

    def registrar_entrada(self, insumo: str, quantidade: float, fornecedor: str = ""):
        if insumo not in self.inventario or insumo in ("ultima_atualizacao", "historico_movimentos"):
            raise ValueError(f"Insumo desconhecido: {insumo}")
        self.inventario[insumo] = round(self.inventario[insumo] + quantidade, 3)
        movimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": "entrada",
            "insumo": insumo,
            "quantidade": quantidade,
            "fornecedor": fornecedor,
            "saldo_pos": self.inventario[insumo],
        }
        self.inventario["historico_movimentos"].append(movimento)
        self.inventario["ultima_atualizacao"] = movimento["data"]
        self._salvar_inventario()

    def processar_vendas_dia(self, qtd_smash: int, qtd_alto: int) -> dict:
        consumo_total = {}
        for insumo in ["carne_kg", "bacon_kg", "cheddar_kg", "batata_kg", "pao_brioche_unid"]:
            consumo_smash = CONSUMO_SMASH.get(insumo, 0) * qtd_smash
            consumo_alto = CONSUMO_ALTO.get(insumo, 0) * qtd_alto
            total = round(consumo_smash + consumo_alto, 3)
            consumo_total[insumo] = total
            self.inventario[insumo] = round(max(0, self.inventario[insumo] - total), 3)
        movimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": "saida_vendas",
            "qtd_smash": qtd_smash,
            "qtd_alto": qtd_alto,
            "consumo": consumo_total,
        }
        self.inventario["historico_movimentos"].append(movimento)
        self.inventario["ultima_atualizacao"] = movimento["data"]
        alertas = self._verificar_estoque_seguranca()
        self._salvar_inventario()
        return {
            "data": movimento["data"],
            "vendas": {"smash": qtd_smash, "alto": qtd_alto, "total": qtd_smash + qtd_alto},
            "consumo": consumo_total,
            "saldo_atual": self._get_saldo(),
            "alertas": alertas,
        }

    def _verificar_estoque_seguranca(self) -> list:
        alertas = []
        carne = self.inventario.get("carne_kg", 0)
        bacon = self.inventario.get("bacon_kg", 0)
        lim_carne = self.estoque_seguranca.get("carne_kg", 2.0)
        lim_bacon = self.estoque_seguranca.get("bacon_kg", 1.0)
        if carne < lim_carne:
            lr = int(carne / 0.070)
            alertas.append({
                "tipo": "RISCO_RUTURA", "insumo": "Carne",
                "saldo_kg": carne, "limite_kg": lim_carne, "lanches_restantes": lr,
                "msg": f"CARNE ABAIXO DO LIMITE: {carne:.2f}kg (min: {lim_carne}kg). Restam ~{lr} smashs.",
            })
        if bacon < lim_bacon:
            lr = int(bacon / 0.025)
            alertas.append({
                "tipo": "RISCO_RUTURA", "insumo": "Bacon",
                "saldo_kg": bacon, "limite_kg": lim_bacon, "lanches_restantes": lr,
                "msg": f"BACON ABAIXO DO LIMITE: {bacon:.2f}kg (min: {lim_bacon}kg). Restam ~{lr} lanches com bacon.",
            })
        return alertas

    def _get_saldo(self) -> dict:
        return {k: v for k, v in self.inventario.items() if k not in ("ultima_atualizacao", "historico_movimentos")}

    def projetar_dias_estoque(self, media_smash_dia: int = 10, media_alto_dia: int = 5) -> dict:
        resultado = {}
        for insumo in ["carne_kg", "bacon_kg", "cheddar_kg", "batata_kg", "pao_brioche_unid"]:
            consumo_dia = (
                CONSUMO_SMASH.get(insumo, 0) * media_smash_dia
                + CONSUMO_ALTO.get(insumo, 0) * media_alto_dia
            )
            saldo = self.inventario.get(insumo, 0)
            dias = saldo / consumo_dia if consumo_dia > 0 else float("inf")
            resultado[insumo] = {
                "saldo": saldo,
                "consumo_dia": round(consumo_dia, 3),
                "dias_restantes": round(dias, 1),
            }
        gargalo = min(resultado.items(), key=lambda x: x[1]["dias_restantes"])
        resultado["gargalo"] = {"insumo": gargalo[0], "dias": gargalo[1]["dias_restantes"]}
        return resultado

    def get_status(self) -> dict:
        alertas = self._verificar_estoque_seguranca()
        return {
            "saldo": self._get_saldo(),
            "alertas": alertas,
            "ultima_atualizacao": self.inventario.get("ultima_atualizacao"),
            "total_movimentos": len(self.inventario.get("historico_movimentos", [])),
        }
