# Carteira de Rendimento

Aplicativo desktop desenvolvido para gestão e acompanhamento de aplicações de renda fixa de uma empresa. O sistema permite cadastrar aplicações, calcular o rendimento dia a dia com base nas taxas históricas do Banco Central e exportar relatórios em PDF e Excel.

> Projeto desenvolvido para uso interno da empresa, substituindo o controle manual em planilhas.

---

## Funcionalidades

### Cadastro de aplicações
Cada aplicação registra:
- Nome do produto, tipo, banco emissor e empresa vinculada
- Valor aplicado, datas de emissão e vencimento
- Indexador e sua configuração (percentual, taxa ou spread)

**Tipos de produto suportados:** CDB · Compromissada · LC · Mútuo

**Indexadores disponíveis:**

| Indexador | Configuração |
|---|---|
| CDI | % do CDI (ex: 110% do CDI) |
| SELIC | % da SELIC (ex: 100% da SELIC) |
| SELIC+ | Spread fixo somado à SELIC diária (ex: SELIC + 0,10% a.a.) |
| Prefixado | Taxa anual fixa (ex: 12,50% a.a.) |

### Cálculo de rendimento
- Cálculo diário acumulado com base nas taxas históricas do Banco Central (API SGS)
- Para datas futuras, projeta usando a última taxa disponível
- Apuração automática de **IOF** e **IR** conforme tabelas regressivas
- Operações Compromissadas são isentas de IOF

#### Tabela de IR

| Prazo | Alíquota |
|---|---|
| Até 180 dias | 22,5% |
| 181 a 360 dias | 20,0% |
| 361 a 720 dias | 17,5% |
| Acima de 720 dias | 15,0% |

#### IOF
Tabela regressiva de 96% (dia 1) a 0% a partir do dia 30.

### Relatórios
- **PDF** — demonstrativo completo da carteira com totais consolidados por empresa
- **Excel** — planilha com todas as colunas: produto, tipo, banco, datas, taxa, rendimento bruto (% e R$), valor atualizado, IR, IOF e resgate líquido

Selecione as aplicações na lista antes de gerar. Os filtros de banco e empresa se aplicam à lista e ao relatório.

### Gestão de resgates
- Marque uma aplicação como resgatada informando a data do resgate
- Aplicações resgatadas aparecem em cinza na lista para histórico
- Relatórios para datas anteriores ao resgate incluem a aplicação normalmente
- O resgate pode ser desfeito a qualquer momento

### Cadastros auxiliares
A tela de **Cadastros** (botão na barra de ações) permite gerenciar:
- **Empresas** — nome e CNPJ; vinculadas a cada aplicação para filtro e relatório
- **Bancos** — banco emissor das aplicações; utilizado também como filtro na lista

---

## Stack

| Camada | Tecnologia |
|---|---|
| Interface | Python · Tkinter · [sv-ttk](https://github.com/rdbende/Sun-Valley-ttk-theme) |
| Banco de dados | PostgreSQL (hospedado no [Neon](https://neon.tech)) |
| ORM / acesso | SQLAlchemy + psycopg2 |
| Taxas externas | API pública do Banco Central (SGS) |
| Relatórios | ReportLab (PDF) · openpyxl (Excel) |

---

## Arquitetura

O projeto segue o padrão **MVC** com **Injeção de Dependências**. O `main.py` é a raiz de composição: cria a conexão com o banco, instancia os repositórios, serviços e controller, e os injeta na view.

```
main.py  →  CarteiraController  →  Repositórios  →  PostgreSQL
                    ↓
             Serviços (cálculo, taxas, PDF, Excel)
                    ↓
         AplicativoCarteira (Tkinter)
```

```
app/
  models/         # entidades de domínio (Aplicacao, Empresa)
  controllers/    # CarteiraController — orquestra a lógica de negócio
  repositories/   # acesso ao banco (aplicações, empresas, bancos, taxas)
  services/       # calculadora, demonstrativo, taxas BCB, PDF, Excel
  utils/          # formatadores, conversores, máscaras de input, impostos
  views/          # interface gráfica (tela principal e cadastros)
  manager.py      # gerenciamento da conexão SQLAlchemy
  logger.py       # configuração de logs
config.py         # leitura de variáveis de ambiente
main.py           # ponto de entrada e composição
```

### Tabelas do banco de dados

```sql
d_empresa    -- empresas cadastradas
d_banco      -- bancos cadastrados
f_aplicacao  -- aplicações de renda fixa (FK para empresa e banco)
f_taxa       -- histórico de taxas CDI e SELIC por data
```

---

## Configuração

### Pré-requisitos
- Python 3.10+
- Instância PostgreSQL acessível (local ou remoto)

### Arquivo de configuração
Copie o exemplo e preencha com os dados do seu banco:
```bash
cp config.example.toml config.toml
```

```toml
[conexoes]
servidor = "seu-servidor.neon.tech"
banco = "nome_do_banco"
```

### Variável de ambiente
Crie o arquivo `.env` na raiz do projeto:
```
CARTEIRA_AUTH=<usuario:senha em base64>
```

A credencial é a string `usuario:senha` codificada em Base64.

### Criar as tabelas
Execute o script `schema.sql` no seu banco PostgreSQL:
```bash
psql -h <servidor> -U <usuario> -d <banco> -f schema.sql
```
Ou cole o conteúdo do arquivo diretamente no cliente de sua preferência (DBeaver, psql, etc.).

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
```bash
python main.py
```

---

## Gerar executável (.exe)

```bash
python -m PyInstaller --onefile --windowed --name "Carteira de Rendimento" main.py
```

O executável gerado fica em `dist/`. Execute-o a partir de uma pasta dedicada — as pastas `data/pdf/`, `data/excel/` e `logs/` são criadas automaticamente ao lado do executável na primeira execução.

---

## Séries do Banco Central utilizadas

| Indexador | Série SGS |
|---|---|
| CDI diário | 12 |
| SELIC diária | 11 |
