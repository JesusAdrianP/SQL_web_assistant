from db_connection import DBConnection

# Obtener las columnas de las tablas en el esquema 'public'
def get_db_columns_schema():
    db = DBConnection()
    db.generate_db_connection()
    db.execute("""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
    """)
    columnas = db.fetchall()
    db.quit_db_connection()
    return columnas


# Obtener claves primarias
def get_db_pk_schema():
    db = DBConnection()
    db.generate_db_connection()
    db.execute("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
    """)
    pk_info = db.fetchall()
    primary_keys = {table: column for table, column in pk_info}
    db.quit_db_connection()
    return primary_keys

# Obtener claves foráneas
def get_db_fk_schema():
    db = DBConnection()
    db.generate_db_connection()
    db.execute("""
        SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
    """)
    fk_info = cursor.fetchall()
    db.quit_db_connection()
    return fk_info


#Organiza el esquema de la bd en el formato que el modelo puede procesar
def parse_schema():
    foreign_keys = {}
    fk_info = get_db_fk_schema()
    for table, column, foreign_table, foreign_column in fk_info:
        foreign_keys.setdefault(table, []).append(f'foreign_key: "{column}" {foreign_column} from "{foreign_table}" "{foreign_column}"')

    tables = {}
    columnas = get_db_columns_schema()
    for table, column, col_type in columnas:
        tables.setdefault(table, []).append(f'"{column}" {col_type}') 

    schema_parts = []
    primary_keys = get_db_pk_schema()
    for table, columns in tables.items():
        schema_line = f'"{table}" ' + " , ".join(columns)
        if table in primary_keys:
            schema_line += f' , primary key: "{primary_keys[table]}"'
        if table in foreign_keys:
            schema_line += " , " + " , ".join(foreign_keys[table])
        schema_parts.append(schema_line)

    schema = ' [SEP] '.join(schema_parts)

    return schema