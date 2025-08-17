-- Complete Database Schema Export Query
-- Run this in Supabase SQL Editor to get a comprehensive JSON schema document

WITH table_info AS (
  SELECT 
    schemaname,
    tablename,
    tableowner
  FROM pg_tables 
  WHERE schemaname = 'public'
),

column_info AS (
  SELECT 
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.ordinal_position
  FROM information_schema.columns c
  WHERE c.table_schema = 'public'
),

constraint_info AS (
  SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
  FROM information_schema.table_constraints tc
  LEFT JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
  LEFT JOIN information_schema.constraint_column_usage ccu 
    ON tc.constraint_name = ccu.constraint_name
  WHERE tc.table_schema = 'public'
),

index_info AS (
  SELECT 
    t.relname AS table_name,
    i.relname AS index_name,
    ix.indisunique AS is_unique,
    ix.indisprimary AS is_primary,
    array_agg(a.attname ORDER BY c.ordinality) AS columns
  FROM pg_class t
  JOIN pg_index ix ON t.oid = ix.indrelid
  JOIN pg_class i ON i.oid = ix.indexrelid
  JOIN pg_attribute a ON a.attrelid = t.oid
  JOIN unnest(ix.indkey) WITH ORDINALITY c(attnum, ordinality) ON a.attnum = c.attnum
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE n.nspname = 'public'
    AND t.relkind = 'r'
  GROUP BY t.relname, i.relname, ix.indisunique, ix.indisprimary
)

SELECT jsonb_pretty(
  jsonb_build_object(
    'schema_export', jsonb_build_object(
      'exported_at', now(),
      'database_name', current_database(),
      'schema_name', 'public',
      'tables', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'table_name', ti.tablename,
            'table_owner', ti.tableowner,
            'columns', (
              SELECT jsonb_agg(
                jsonb_build_object(
                  'column_name', ci.column_name,
                  'data_type', ci.data_type,
                  'is_nullable', ci.is_nullable,
                  'column_default', ci.column_default,
                  'character_maximum_length', ci.character_maximum_length,
                  'numeric_precision', ci.numeric_precision,
                  'numeric_scale', ci.numeric_scale,
                  'ordinal_position', ci.ordinal_position
                ) ORDER BY ci.ordinal_position
              )
              FROM column_info ci 
              WHERE ci.table_name = ti.tablename
            ),
            'constraints', (
              SELECT jsonb_agg(
                jsonb_build_object(
                  'constraint_name', constr.constraint_name,
                  'constraint_type', constr.constraint_type,
                  'column_name', constr.column_name,
                  'foreign_table_name', constr.foreign_table_name,
                  'foreign_column_name', constr.foreign_column_name
                )
              )
              FROM constraint_info constr 
              WHERE constr.table_name = ti.tablename
            ),
            'indexes', (
              SELECT jsonb_agg(
                jsonb_build_object(
                  'index_name', idx.index_name,
                  'is_unique', idx.is_unique,
                  'is_primary', idx.is_primary,
                  'columns', idx.columns
                )
              )
              FROM index_info idx 
              WHERE idx.table_name = ti.tablename
            )
          ) ORDER BY ti.tablename
        )
        FROM table_info ti
      )
    )
  )
) AS schema_json;