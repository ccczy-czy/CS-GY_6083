-- a) Write a query listing all the tables that have at least two outgoing foreign keys referencing distinct tables.

SELECT
    tc.table_name                               AS referencing_table,
    COUNT(DISTINCT ccu.table_name)              AS distinct_referenced_tables
FROM information_schema.table_constraints      AS tc
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
    AND tc.constraint_schema = rc.constraint_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON rc.unique_constraint_name   = ccu.constraint_name
    AND rc.unique_constraint_schema = ccu.constraint_schema
WHERE tc.constraint_type   = 'FOREIGN KEY'
  AND tc.constraint_schema = 'public'
GROUP BY tc.table_name
HAVING COUNT(DISTINCT ccu.table_name) >= 2
ORDER BY tc.table_name;

-- b) Write a query to list all columns in the database that are configured to store timestamp/date type columns.

SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type IN (
      'date',
      'time without time zone',
      'time with time zone',
      'timestamp without time zone',
      'timestamp with time zone',
      'interval'
  )
ORDER BY table_name, column_name;

-- c) For each attribute in the Flight table, output how many distinct values each attribute has in the current database.

SELECT
    'flight_number'  AS attribute,
    COUNT(DISTINCT flight_number)  AS distinct_values
FROM flight

UNION ALL

SELECT
    'departure_date',
    COUNT(DISTINCT departure_date)
FROM flight

UNION ALL

SELECT
    'plane_type',
    COUNT(DISTINCT plane_type)
FROM flight

ORDER BY attribute;

-- d) Find all the tables where the primary key is composite (has more than one attribute).

SELECT
    kcu.table_name,
    COUNT(*) AS pk_column_count
FROM information_schema.key_column_usage     AS kcu
JOIN information_schema.table_constraints    AS tc
    ON  kcu.constraint_name   = tc.constraint_name
    AND kcu.constraint_schema = tc.constraint_schema
    AND kcu.table_name        = tc.table_name
WHERE tc.constraint_type   = 'PRIMARY KEY'
  AND tc.constraint_schema = 'public'
GROUP BY kcu.table_name
HAVING COUNT(*) > 1
ORDER BY kcu.table_name;

-- e) Find all attributes containing the substring "name".

SELECT
    table_name,
    column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name ILIKE '%name%'
ORDER BY table_name, column_name;
