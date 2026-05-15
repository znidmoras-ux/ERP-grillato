"""
Grillato System - Radar de Inflacao de Insumos
Modulo 2: Monitorizacao de precos dos insumos da Curva A.
"""

import json
import os
from datetime import datetime
from typing import Optional

TOLERANCIA_PCT = 0.02

ITENS_CURVA_A = {
    "carne_kg":         {"nome": "Carne (Blend)",  "unidade": "R$/kg",   "chave_config": "carne_kg"},
    "cheddar_kg":       {"nome": "Cheddar",        "unidade": "R$/kg",   "chave_config": "cheddar_kg"},
    "bacon_kg":         {"nome": "Bacon",           "unidade": "R$/kg",   "chave_config": "bacon_kg"},
    "batata_kg":        {"nome": "Batata",          "unidade": "R$/kg",   "chave_config": "batata_kg"},
    "pao_brioche_unid": {"nome": "Pao Brioche",    "unidade": "R$/unid", "chave_config": "pao_brioche_unid"},
}

CONSUMO_POR_LANCHE = {
    "carne_kg": 0.070,
    "cheddar_kg": 0.030,
    "bacon_kg": 0.025,
    "batata_kg": 0.100,
    "pao_brioche_unid": 1.0,
}


class RadarInflacao:
    """Gerencia o historico de precos e calculo de variacoes."""

    def __init__(self, config: dict):
        self.config = config
        self.historico_path = config["caminhos"]["historico_precos"]
        self.precos_base = config["insumos_base"]
        self.historico = self._carregar_historico()

    def _carregar_historico(self) -> list:
        if os.path.exists(self.historico_path):
            try:
                with open(self.historico_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, KeyError):
                pass
        return []

    def _salvar_historico(self):
        os.makedirs(os.path.dirname(self.historico_path) or ".", exist_ok=True)
        with open(self.historico_path, "w", encoding="utf-8") as f:
            json.dump(self.historico, f, indent=2, ensure_ascii=False)

    def get_ultimo_registro(self) -> Optional[dict]:
        if self.historico:
            return self.historico[-1]
        return None

    def get_preco_referencia(self, item_key: str) -> float:
        ultimo = self.get_ultimo_registro()
        if ultimo and item_key in ultimo.get("precos", {}):
            return ultimo["precos"][item_key]
        return self.precos_base.get(item_key, 0.0)

    def registrar_precos(self, precos_novos: dict) -> dict:
        resultado = {"data": datetime.now().strftime("%Y-%m-%d %H:%M"), "itens": {}}
        cmv_anterior = 0.0
        cmv_novo = 0.0

        for key, info in ITENS_CURVA_A.items():
            preco_novo = precos_novos.get(key, 0.0)
            preco_ref = self.get_preco_referencia(key)
            consumo = CONSUMO_POR_LANCHE.get(key, 0)

            if preco_ref > 0:
                variacao_pct = (preco_novo - preco_ref) / preco_ref
            else:
                variacao_pct = 0.0

            if variacao_pct > TOLERANCIA_PCT:
                status, cor = "subiu", "vermelho"
            elif variacao_pct < -TOLERANCIA_PCT:
                status, cor = "desceu", "verde"
            else:
                status, cor = "estavel", "amarelo"

            custo_lanche_ref = preco_ref * consumo
            custo_lanche_novo = preco_novo * consumo

            resultado["itens"][key] = {
                "nome": info["nome"],
                "preco_anterior": round(preco_ref, 2),
                "preco_novo": round(preco_novo, 2),
                "variacao_pct": round(variacao_pct * 100, 1),
                "status": status,
                "cor": cor,
                "impacto_lanche": round(custo_lanche_novo - custo_lanche_ref, 2),
            }

            cmv_anterior += custo_lanche_ref
            cmv_novo += custo_lanche_novo

        resultado["cmv_lanche_anterior"] = round(cmv_anterior, 2)
        resultado["cmv_lanche_novo"] = round(cmv_novo, 2)
        resultado["variacao_cmv"] = round(cmv_novo - cmv_anterior, 2)

        entrada = {
            "data": resultado["data"],
            "precos": precos_novos,
            "cmv_lanche": round(cmv_novo, 2),
        }
        self.historico.append(entrada)
        self._salvar_historico()

        return resultado


def abrir_radar(config: dict):
    """Abre o Radar de Inflacao via Tkinter (requer tkinter no Windows)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        print("ERRO: tkinter nao disponivel. Use o dashboard Streamlit.")
        return

    radar = RadarInflacao(config)
    COR_FUNDO = "#1a1a2e"
    COR_CARD = "#16213e"
    COR_TEXTO = "#eaeaea"
    COR_TITULO = "#e94560"
    COR_VERDE = "#27ae60"
    COR_AMARELO = "#f39c12"
    COR_VERMELHO = "#e74c3c"
    COR_INPUT_BG = "#0f3460"

    entries = {}
    labels_status = {}

    root = tk.Tk()
    root.title("Grillato - Radar de Inflacao")
    root.configure(bg=COR_FUNDO)
    root.resizable(False, False)
    largura, altura = 520, 580
    x = (root.winfo_screenwidth() // 2) - (largura // 2)
    y = (root.winfo_screenheight() // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")

    fh = tk.Frame(root, bg=COR_FUNDO)
    fh.pack(fill="x", padx=16, pady=(16, 8))
    tk.Label(fh, text="RADAR DE INFLACAO", font=("Segoe UI", 16, "bold"),
             fg=COR_TITULO, bg=COR_FUNDO).pack(anchor="w")
    tk.Label(fh, text="Insira os precos atualizados da nota fiscal",
             font=("Segoe UI", 9), fg="#8a8a9a", bg=COR_FUNDO).pack(anchor="w")

    ft = tk.Frame(root, bg=COR_CARD, relief="flat")
    ft.pack(fill="x", padx=16, pady=8)
    fi = tk.Frame(ft, bg=COR_CARD)
    fi.pack(fill="x", padx=12, pady=8)

    for i, (key, info) in enumerate(ITENS_CURVA_A.items()):
        ref = radar.get_preco_referencia(key)
        tk.Label(fi, text=info["nome"], width=18, anchor="w",
                 font=("Segoe UI", 9), fg=COR_TEXTO, bg=COR_CARD
                 ).grid(row=i, column=0, sticky="w", pady=4)
        tk.Label(fi, text=f"R$ {ref:.2f}", width=10, anchor="e",
                 font=("Segoe UI", 9), fg="#8a8a9a", bg=COR_CARD
                 ).grid(row=i, column=1, pady=4)
        entry = tk.Entry(fi, width=10, justify="center",
                         font=("Segoe UI", 10, "bold"),
                         bg=COR_INPUT_BG, fg="#ffffff",
                         insertbackground="#ffffff",
                         relief="flat", highlightthickness=1,
                         highlightcolor=COR_TITULO)
        entry.insert(0, f"{ref:.2f}")
        entry.grid(row=i, column=2, pady=4, padx=8)
        entries[key] = entry
        lbl = tk.Label(fi, text="  --  ", width=4,
                       font=("Segoe UI", 10, "bold"),
                       bg=COR_CARD, fg="#6a6a7a")
        lbl.grid(row=i, column=3, pady=4)
        labels_status[key] = lbl

    fr = tk.Frame(root, bg=COR_FUNDO)
    fr.pack(fill="both", expand=True, padx=16, pady=(4, 16))
    label_res = tk.Label(fr, text="Insira os precos e clique ANALISAR",
                         font=("Segoe UI", 9), fg="#6a6a7a", bg=COR_FUNDO,
                         wraplength=480, justify="left")
    label_res.pack(anchor="w")

    def analisar():
        precos = {}
        for key, entry in entries.items():
            try:
                t = entry.get().replace(",", ".").replace("R$", "").strip()
                v = float(t)
                if v <= 0:
                    raise ValueError
                precos[key] = v
            except (ValueError, TypeError):
                messagebox.showerror("Erro", f"Valor invalido para {ITENS_CURVA_A[key]['nome']}")
                return
        res = radar.registrar_precos(precos)
        for key, dados in res["itens"].items():
            lbl = labels_status[key]
            if dados["cor"] == "vermelho":
                lbl.config(text=f"+{dados['variacao_pct']:.0f}%", fg=COR_VERMELHO)
            elif dados["cor"] == "verde":
                lbl.config(text=f"{dados['variacao_pct']:.0f}%", fg=COR_VERDE)
            else:
                lbl.config(text="  =  ", fg=COR_AMARELO)
        var = res["variacao_cmv"]
        if var > 0:
            label_res.config(
                text=f"ALERTA: CMV SUBIU R$ {var:.2f}/lanche. +R$ {var*17:.2f}/dia",
                fg=COR_VERMELHO)
        elif var < 0:
            label_res.config(
                text=f"CMV DESCEU R$ {abs(var):.2f}/lanche. Economia R$ {abs(var)*17:.2f}/dia",
                fg=COR_VERDE)
        else:
            label_res.config(text="Precos estaveis.", fg=COR_AMARELO)

    fb = tk.Frame(root, bg=COR_FUNDO)
    fb.pack(fill="x", padx=16, pady=4)
    fb.pack(before=fr)
    tk.Button(fb, text="ANALISAR PRECOS", font=("Segoe UI", 10, "bold"),
              bg=COR_TITULO, fg="white", activebackground="#c0392b",
              relief="flat", padx=16, pady=6, command=analisar
              ).pack(side="left", expand=True, fill="x", padx=(0, 4))
    tk.Button(fb, text="FECHAR", font=("Segoe UI", 10),
              bg="#2a2a4a", fg=COR_TEXTO, relief="flat",
              padx=16, pady=6, command=root.destroy
              ).pack(side="right")

    root.mainloop()
