# Pipeline de dados de um distribuidor de estética profissional

Pipeline de dados de ponta a ponta para um distribuidor brasileiro de produtos para estética profissional (empresa fictícia). Ele busca os dados de vendas, clientes e produtos nos sistemas da empresa, organiza tudo em camadas e entrega as informações prontas para análise num dashboard.

Este é um projeto de portfólio e de aprendizado em engenharia de dados.

## As fontes

Os dados vêm de dois sistemas de origem, mantidos em outros repositórios. O pipeline só lê dessas fontes, nunca escreve nelas.

| Sistema | O que tem | Como o pipeline acessa |
|---|---|---|
| CRM | clientes, representantes de vendas e campanhas | pela API do CRM, com chave de acesso e paginação |
| ERP | produtos, vendas e itens de venda | direto no banco PostgreSQL do Supabase, com um usuário só de leitura |

A base cobre todo o ano de 2025.

## O fluxo

```
Supabase (Postgres)
 ├─ crm_api ──► API do CRM (outro repositório) ──┐
 └─ erp_postgresql ──────────────────────────────┤  extração (Projeto 1)
                                                 ▼
                 DuckDB: bronze → prata → ouro (dbt, Projeto 2)
                                                 ▼
                                 Dashboard (Streamlit, Projeto 4)
 Orquestração: Airflow + Docker encadeando tudo (Projeto 3)
```

- **Bronze:** cópia fiel dos dados de origem, sem nenhuma limpeza.
- **Prata:** dados limpos e padronizados.
- **Ouro:** modelo dimensional, pronto para análise.

## Os projetos

O pipeline é construído em quatro projetos, um depois do outro.

| Projeto | Pasta | Assunto | Situação |
|---|---|---|---|
| 1 | `extracao/` | Extração das fontes para a camada bronze no DuckDB | em andamento |
| 2 | `transformacao/` | dbt: camadas prata e ouro e testes de dados | a fazer |
| 3 | `orquestracao/` | Docker e Airflow encadeando o pipeline | a fazer |
| 4 | `dashboard/` | Dashboard em Streamlit lendo a camada ouro | a fazer |
