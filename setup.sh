#!/bin/bash
echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
echo "Instalando dependências..."
pip install -r requirements.txt
echo "Pronto! Rode com: python backup_cartao.py"
