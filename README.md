# Carteira de Rendimento

Sistema para calcular, gerenciar e acompanhar aplicações financeiras pós-fixadas indexadas a CDI ou SELIC.

## Funcionalidades

- **Cálculo de rendimento** para aplicações indexadas a CDI, SELIC ou com taxa prefixada
- **Atualização automática de taxas** do Banco Central (via API SGS/BCData)
- **Cache local** de taxas históricas em JSON para consultas offline
- **Interface gráfica** para facilitar o cadastro e gestão das aplicações
- **Geração de demonstrativo** consolidado em PDF
- **Projeção de rendimento** para datas futuras

## Características

A aplicação armazena apenas os dados contratuais das aplicações:
- Produto e valor aplicado
- Datas de emissão e vencimento
- Indexador (CDI, SELIC ou PREFIXADO)
- Percentual do indexador (ex: 115% CDI)

As taxas históricas são mantidas em `data/taxas/` e podem ser atualizadas pela API do Banco Central.

## Quick Start

### Instalação

```bash
pip install -r requirements.txt
```

### Executar a aplicação

```bash
python main.py
```

### Rodar testes

```bash
pytest
```

## Dados do Banco Central

As séries de taxas utilizadas:
- **CDI diário**: Série SGS 12
- **SELIC diária**: Série SGS 11

> Nota: As séries são retornadas em percentual ao dia e são convertidas para cálculos no sistema.

## Importante

Para datas futuras onde o Banco Central ainda não publicou as taxas diárias, o sistema permite projetar usando a última taxa conhecida (`projetar_com_ultima_taxa=True`). Esta é uma projeção, não um valor oficial.

## Estrutura do Projeto

```
app/
  ├── core/          # Cálculos e lógica principal
  ├── taxas/         # Integração com Banco Central
  ├── armazenamento/ # Persistência de dados
  ├── relatorios/    # Geração de PDFs
  └── ui/            # Interface gráfica
data/
  ├── aplicacoes.json # Dados das aplicações
  └── taxas/          # Cache de taxas do BCB
tests/               # Testes unitários
```
