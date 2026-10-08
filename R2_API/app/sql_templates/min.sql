SELECT ROW_NUMBER() OVER () AS id,
       COUNT(*) OVER() AS total_count,
{selected_columns}
FROM {table_name}
WHERE {stat_column} IS NOT NULL
{where_clause}
ORDER BY {final_sort_by} {final_sort_order}, id ASC
LIMIT {limit} OFFSET {offset};
