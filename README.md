# Aplicacao de rendimento CDI/Selic

Projeto para calcular aplicacoes pos-fixadas, consultar taxas historicas do Banco Central, salvar cache local em JSON e gerar demonstrativo consolidado da carteira.

## Ideia principal

A aplicacao nao guarda mais varias mudancas de Selic/CDI dentro dela.

Agora a aplicacao guarda apenas a regra contratada:

- produto
- valor aplicado
- data de emissao
- data de vencimento
- indexador: CDI, SELIC ou PREFIXADO
- percentual do indexador, por exemplo 115% CDI

As taxas historicas ficam em arquivos JSON em `data/taxas/` e podem ser atualizadas pela API SGS/BCData do Banco Central.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

## Como testar

```bash
pytest
```

## Series usadas do Banco Central

- CDI diario: serie SGS 12
- Selic diaria: serie SGS 11

As series sao retornadas em percentual ao dia. Por isso, no calculo, o valor recebido e dividido por 100.

## Observacao importante sobre futuro

Para datas futuras, o Banco Central ainda nao possui taxas diarias publicadas. O sistema permite projetar usando a ultima taxa conhecida quando `projetar_com_ultima_taxa=True`.

Isso e uma projecao, nao um valor oficial definitivo.
