# 🖥️ LAN Manager & Helpdesk Pro

> **Sistema Completo de Monitorização de Rede, Inventário de Ativos de TI e Painel Estratégico de BI** para ambientes corporativos e redes locais.

O **LAN Manager & Helpdesk** é uma aplicação desktop nativa (construída sobre FastAPI e PyWebView) que executa varreduras automáticas via Nmap, mapeia dispositivos ativos em tempo real, regista alterações de IP por endereço MAC e disponibiliza um dashboard dinâmico para cruzamento analítico de hardware e setores.

---

## 🚀 Funcionalidades Principais

* 🔍 **Scanner de Rede Automático (Nmap):** Mapeamento em segundo plano sem travar a interface, descobrindo IP, MAC Address, Hostname e Fabricante (Vendor).
* 🏷️ **Gestão Estruturada de Inventário:** Organização de ativos por **Área (Setor)**, **Time (Equipa)** e **Tipo (Hardware)**.
* 📝 **Registo Dinâmico de Tags (Select2):** Novas áreas ou tipos de equipamento introduzidos manualmente são guardados automaticamente no banco de dados e disponibilizados para os restantes ativos.
* 🕒 **Histórico de IP por MAC (DHCP Tracker):** Linha do tempo visual que regista alterações de endereços IP atribuídos a uma mesma placa de rede.
* 📊 **Painel Estratégico de BI (Chart.js):**
  * Gráficos dinâmicos e empilhados (Barras, Donut, Pizza).
  * Cruzamento analítico flexível (ex: *Área vs Tipo*, *Equipa vs Tipo*).
  * Filtros avançados com suporte a *Blacklist* (Modo Inverso).
  * Persistência de preferências de gráficos no navegador.
* 📥 **Backup e Restauro (CSV):** Exportação e importação rápida de inventários completos.
* 🌓 **Suporte a Tema Escuro/Claro (Dark/Light Mode):** Interface adaptativa com Bootstrap 5 e componentes Select2/DataTables personalizados.
* 💻 **Aplicação Desktop Nativa Windows:** Janela dedicada powered por `PyWebView`, sem necessidade de abrir navegadores manualmente.

---

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python 3.12+, FastAPI, SQLAlchemy, Uvicorn, Python-Nmap, Pandas.
* **Front-end:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Select2 (Bootstrap 5 Theme), DataTables, Chart.js.
* **Database:** SQLite.
* **Desktop Wrapper:** PyWebView & Pythonnet.
* **Automação Windows:** Batch Scripts (`.bat`), PowerShell & Winget.

---

## 📂 Estrutura do Projeto

```
LAN_MANAGER_HELPDESK/
├── app/
│   ├── templates/
│   │   ├── dashboard.html      # Interface do Painel de BI
│   │   └── index.html          # Tabela Principal de Inventário e Modal
│   ├── __init__.py
│   ├── database.py             # Configuração da Sessão SQLite
│   ├── main.py                 # Roteamento FastAPI e Inicialização Desktop (PyWebView)
│   ├── models.py               # Modelos SQLAlchemy (Dispositivo e HistoricoIP)
│   └── scanner.py              # Motor do Nmap e Lógica de Mudança de IP
├── .env                        # Variáveis de Ambiente (Faixas de Rede)
├── .gitignore                  # Ficheiros ignorados pelo Git
├── database.db                 # Banco de Dados SQLite (Gerado automaticamente)
├── INSTALAR_DEPENDENCIAS.bat   # Script Automático de Instalação do Python e Nmap
├── requirements.txt            # Módulos Python do Projeto
└── START.bat                   # Boot do App, Auto-Detecção de IP e Atalho de Inicialização
```

##⚡ Instalação e Execução
1️⃣ Em um Computador Novo (Setup do Zero)
Se estiver a mover a pasta do projeto para uma máquina limpa sem dependências instaladas:

Clique com o botão direito em INSTALAR_DEPENDENCIAS.bat e selecione "Executar como Administrador".

O script irá descarregar e instalar automaticamente o Python 3.12 e o Nmap (com driver Npcap).

Se a janela do Nmap abrir de forma interativa, avance com a instalação padrão certificando-se de manter o Npcap selecionado.

2️⃣ Inicialização do Aplicativo
Para iniciar o sistema (ou após concluir o setup inicial):

Dê dois cliques no ficheiro START.bat.

O script irá:

Instalar/validar os módulos Python do requirements.txt silenciosamente.

Identificar a sub-rede ativa da máquina local (ex: 192.168.85.0/24).

Criar um atalho na pasta de Inicialização do Windows (Startup) para rodar com o sistema.

Abrir a aplicação nativa em uma janela dedicada de 1280x800.

⚙️ Configurações Adicionais (.env)
Para fixar faixas de IP específicas a serem varridas pelo Nmap (ou múltiplas redes simultâneas), pode editar o ficheiro .env na raiz do projeto:

```
# Configuração de Redes (Separe por espaços para múltiplas sub-redes)
NETWORK_RANGES="192.168.85.0/24 192.168.200.0/24"

# Segurança
SECRET_KEY="sua-chave-secreta-aqui"
```

📜 Licença e Suporte
Projeto desenvolvido para fins de Inventário de TI e Suporte de Helpdesk. Sinta-se à vontade para contribuir, abrir Issues ou personalizar de acordo com a infraestrutura da sua rede!
