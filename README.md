# Carteira de Rendimento

Aplicativo desktop para gestão e acompanhamento de aplicações de renda fixa indexadas ao CDI, SELIC ou taxa prefixada.

## Funcionalidades

- Cadastro de aplicações com produto, número de controle, nota, valor, datas, indexador e tipo
- Suporte a CDB e Operações Compromissadas
- Indexadores: CDI, SELIC e Prefixado (% a.a.)
- Atualização automática das taxas CDI/SELIC via API do Banco Central (SGS)
- Cálculo diário de rendimento bruto com projeção para datas futuras usando a última taxa conhecida
- Apuração de IOF (tabela regressiva 30 dias) e IR (tabela regressiva por prazo)
- Geração de PDF individual por aplicação ou da carteira completa

## Impostos aplicados

| Imposto | Regra |
|---|---|
| IOF | Tabela regressiva de 96% (dia 1) a 0% (dia 30+) |
| IR | 22,5% até 180 dias / 20% até 360 / 17,5% até 720 / 15% acima de 720 |

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
mkvirtualenv carteira-de-rendimento
workon carteira-de-rendimento
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Gerar executável

```bash
workon carteira-de-rendimento
python -m PyInstaller --onefile --windowed --name "Carteira de Rendimento" main.py
```

O `.exe` gerado fica em `dist/`. Execute-o a partir de uma pasta dedicada — as pastas `data/`, `data/pdfs/` e `logs/` são criadas automaticamente ao lado do executável na primeira execução.

## Estrutura

```
app/
  models/         # entidades de domínio (Aplicacao, PosicaoDiaria, etc.)
  controllers/    # CarteiraController — orquestra a lógica de negócio
  services/       # cálculo, demonstrativo, taxas, PDF
  repositories/   # persistência em JSON
  utils/          # formatadores, conversores, calendário, impostos
  views/          # interface gráfica (tkinter)
data/
  aplicacoes.json # aplicações cadastradas
  taxas/          # histórico CDI e SELIC em JSON
  pdfs/           # relatórios gerados
logs/             # arquivos de log
```

