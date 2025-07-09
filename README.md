# 📱 Backup Cartão Pro v6.0

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge\&logo=python)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-lightgrey?style=for-the-badge\&logo=windowsterminal)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Backup inteligente para fotos, vídeos e metadados de câmeras profissionais**

*A maneira mais segura e intuitiva de organizar seus arquivos do cartão SD.*

</div>

---

## 🌟 Visão Geral

O **Backup Cartão Pro v6.0** é uma aplicação com interface moderna voltada para fotógrafos e criadores que desejam fazer backup seguro de fotos, vídeos e metadados (XMP/XML) a partir de cartões SD. Organiza tudo por data, tipo de arquivo e ainda permite renomear os arquivos com prefixos personalizados.

* 🚀 Backup seguro e sem sobrescrever
* 🎨 Interface dark com feedback em tempo real
* 🎥 Suporte a múltiplas marcas e formatos
* 📂 Organização automática por data e categoria

---

## ✨ Funcionalidades

* ✅ Suporte a arquivos de Sony (ARW), Canon (CR2/CR3), Nikon (NEF), Fuji (RAF), Olympus (ORF), DNG, JPEG, MP4, MOV, entre outros
* ✅ Interface com tema escuro, botões estilizados e progressos visuais
* ✅ Análise detalhada por data com previews
* ✅ Renomeação personalizada com prefixo e númeração
* ✅ Log detalhado de operações com erros e sucessos

---

## 📦 Instalação

1. **Clone o repositório**

```bash
git clone https://github.com/seu-usuario/backup-cartao-pro.git
cd backup-cartao-pro
```

2. **Crie o ambiente virtual**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate   # Windows
```

3. **Instale as dependências**

```bash
pip install -r requirements.txt
```

> 📁 *Opcional: para previews de imagem, instale o Pillow:*

```bash
pip install Pillow
```

---

## ⚙️ Configuração

Nenhuma variável sensível é necessária. O sistema já é funcional por padrão.

---

## 🚀 Como Usar

1. Execute o programa:

```bash
python backup_cartao.py
```

2. Siga os passos na interface:

   * Selecione a pasta do cartão SD
   * Escolha onde salvar o backup
   * Analise o cartão
   * Inicie o backup, selecione datas e opções

3. Acompanhe o progresso com logs visuais e resumos.

---

## 🏗️ Arquitetura

```
backup-cartao-pro/
├── backup_cartao.py         # Script principal com interface Tkinter
├── README.md                # Documentação do projeto
├── requirements.txt         # Dependências Python
├── .gitignore               # Padrões ignorados no Git
├── LICENSE                  # Licença MIT
├── CHANGELOG.md             # Histórico de versões
└── setup.sh                 # Script opcional de instalação
```

---

## 📜 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Se desejar sugerir melhorias ou reportar problemas, abra uma Issue ou Pull Request.

---

## 🧠 Créditos

Desenvolvido por **NASCO COMPANY** com foco em segurança, usabilidade e praticidade para o dia a dia de criadores visuais.

> *Versão 6.0 — repaginada com foco total em experiência do usuário final.*
