"""
Grillato ERP - Ponto de entrada para Streamlit Cloud
"""
import sys
import os

# Garantir que o diretorio raiz esta no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from erp.app import main

if __name__ == "__main__":
    main()
