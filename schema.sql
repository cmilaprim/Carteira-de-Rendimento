-- Carteira de Rendimento — schema do banco de dados
-- Execute este script para criar todas as tabelas necessárias.

CREATE TABLE IF NOT EXISTS d_empresa (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL,
    cnpj  TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS d_banco (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS f_aplicacao (
    id                    SERIAL PRIMARY KEY,
    nome_produto          TEXT        NOT NULL,
    valor_aplicado        NUMERIC     NOT NULL,
    data_emissao          DATE        NOT NULL,
    data_vencimento       DATE        NOT NULL,
    indexador             TEXT        NOT NULL,
    percentual_indexador  NUMERIC     NOT NULL DEFAULT 100,
    taxa_prefixada_anual  NUMERIC     NULL,
    spread_anual          NUMERIC     NULL,
    tipo_produto          TEXT        NOT NULL,
    banco_id              INTEGER     NULL REFERENCES d_banco(id),
    data_resgate          DATE        NULL,
    empresa_id            INTEGER     NULL REFERENCES d_empresa(id),
    data_criacao          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS f_taxa (
    indexador  TEXT    NOT NULL,
    data       DATE    NOT NULL,
    valor      NUMERIC NOT NULL,
    PRIMARY KEY (indexador, data)
);
