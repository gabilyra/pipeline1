-- Cria o usuário erp_reader, que o pipeline usa para ler o ERP.
-- Ele só consegue consultar (SELECT) as tabelas do schema erp_postgresql:
-- não escreve em nada e não enxerga o crm_api nem outros schemas.
--
-- Quem executa: a Gabi, no editor SQL do Supabase. O pipeline nunca roda este script.
-- A senha NÃO fica aqui. Ela é definida à parte e guardada só no .env.
--
-- Pode rodar várias vezes sem erro. Rode de novo sempre que a base for recarregada:
-- o gerador apaga e recria o schema erp_postgresql, e as permissões somem junto.
-- O usuário em si continua existindo (com a mesma senha), porque ele não pertence ao schema.

-- 1. Cria o usuário, só se ele ainda não existir.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'erp_reader') THEN
        CREATE ROLE erp_reader LOGIN;
    END IF;
END
$$;

-- 2. Deixa o usuário "entrar" no schema do ERP (sem isso, ele não enxerga as tabelas).
GRANT USAGE ON SCHEMA erp_postgresql TO erp_reader;

-- 3. Deixa o usuário consultar todas as tabelas do schema. Só consultar.
GRANT SELECT ON ALL TABLES IN SCHEMA erp_postgresql TO erp_reader;
