# Carteira de Rendimento

Aplicativo desktop para gestão e acompanhamento de aplicações de renda fixa indexadas ao CDI, SELIC, SELIC+ ou taxa prefixada.

## O que faz

Permite cadastrar aplicações de renda fixa e acompanhar o rendimento dia a dia, com cálculo automático de impostos, projeção de saldo futuro e exportação de relatórios em PDF e Excel.

## Funcionalidades

### Cadastro de aplicações
- Produto, valor aplicado, datas de emissão e vencimento
- Tipos suportados: **CDB** e **Operação Compromissada** (isenta de IOF)
- Indexadores: **CDI**, **SELIC**, **SELIC+** e **Prefixado** (% a.a.)
  - CDI e SELIC: percentual do indexador configurável (ex: 110% do CDI)
  - SELIC+: spread fixo anual somado à SELIC diária (ex: SELIC + 0,10% a.a.)
  - Prefixado: taxa anual fixa
- Banco emissor selecionável (cadastrado previamente na aba Bancos)

### Cálculo de rendimento
- Cálculo diário com base nas taxas históricas do Banco Central (SGS)
- Projeção automática para datas futuras usando a última taxa conhecida
- Apuração de **IOF** (tabela regressiva de 30 dias) e **IR** (tabela regressiva por prazo)
- Operações Compromissadas não sofrem IOF

#### Fórmula SELIC+
O spread é acumulado diariamente de forma composta e somado à taxa SELIC do dia:

```
taxa_dia = selic_dia + (1 + spread_anual / 100) ^ (1 / 252) - 1
rendimento_dia = saldo × taxa_dia
```

### Taxas CDI/SELIC
- Busca automática via API do Banco Central na primeira vez que uma data é calculada
- Taxas armazenadas localmente em JSON

### Relatórios
- **PDF** da carteira completa com totais consolidados
- **Excel** com todas as colunas (produto, tipo, datas, taxa, rendimento bruto em % e R$, valor atualizado, IR, IOF, resgate líquido)
- Filtro por banco: selecione um banco na barra de ações para gerar relatórios apenas das aplicações filtradas

### Gestão de resgates
- Marque uma aplicação como resgatada informando a data do resgate
- Aplicações resgatadas aparecem em cinza na lista mas **não somem** — ficam visíveis para histórico
- Relatórios gerados para datas **anteriores** ao resgate ainda incluem a aplicação normalmente
- Resgate pode ser desfeito a qualquer momento

### Gestão de bancos
- Aba **Bancos** para cadastrar e remover bancos emissores
- Lista de bancos disponível como campo no formulário de nova aplicação
- Filtro por banco na tela principal: filtra a tabela e os relatórios gerados

## Impostos aplicados

| Imposto | Regra |
|---|---|
| IOF | Tabela regressiva de 96% (dia 1) a 0% (dia 30+). Isento para Compromissadas. |
| IR | 22,5% até 180 dias / 20% até 360 dias / 17,5% até 720 dias / 15% acima de 720 dias |

## Séries do Banco Central utilizadas

| Indexador | Série SGS |
|---|---|
| CDI diário | 12 |
| SELIC diária | 11 |

## Requisitos

- Python 3.10+
- Dependências listadas em `requirements.txt`

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Gerar executável

```bash
python -m PyInstaller --onefile --windowed --name "Carteira de Rendimento" main.py
```

O `.exe` gerado fica em `dist/`. Execute-o a partir de uma pasta dedicada — as pastas `data/`, `data/pdf/`, `data/excel/` e `logs/` são criadas automaticamente ao lado do executável na primeira execução.

## Estrutura

```
app/
  models/         # entidades de domínio (Aplicacao, PosicaoDiaria, LinhaCarteira, etc.)
  controllers/    # CarteiraController — orquestra a lógica de negócio
  services/       # cálculo, demonstrativo, taxas, PDF, Excel
  repositories/   # persistência em JSON (aplicações, bancos e taxas)
  utils/          # formatadores, conversores, calendário, impostos
  views/          # interface gráfica (tkinter + sv-ttk)
data/
  aplicacoes.json # aplicações cadastradas
  bancos.json     # bancos cadastrados
  taxas/          # histórico CDI e SELIC em JSON
  pdf/            # relatórios PDF gerados
  excel/          # planilhas Excel geradas
logs/             # arquivos de log (removidos automaticamente após 7 dias)
```
