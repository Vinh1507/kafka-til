import json

# JSON từ Debezium (thông báo mà bạn cung cấp)

# Chuyển đổi JSON thành dictionary
def convert_DML(debezium_message):
    message = json.loads(debezium_message)

    # Lấy dữ liệu "before", "after" và thông tin bảng
    before_data = message['payload'].get('before')
    after_data = message['payload'].get('after')
    table = message['payload']['source']['table']
    db = message['payload']['source']['db']
    operation = message['payload']['op']

    # Kiểm tra thao tác và xây dựng câu lệnh SQL tương ứng
    if operation == 'c' and after_data:  # INSERT
        columns = ', '.join(after_data.keys())
        values = ', '.join([str(v) if v is not None else 'NULL' for v in after_data.values()])
        insert_statement = f"INSERT INTO {db}.{table} ({columns}) VALUES ({values});"
        return insert_statement

    elif operation == 'u' and after_data:  # UPDATE
        # Tạo phần SET cho câu lệnh UPDATE
        set_clauses = [f"{k} = {('NULL' if v is None else v)}" for k, v in after_data.items()]
        set_statement = ', '.join(set_clauses)

        # Xác định khóa chính (ở đây giả sử là trường "id")
        primary_key = before_data.get('id') if before_data else None
        if primary_key:
            update_statement = f"UPDATE {db}.{table} SET {set_statement} WHERE id = {primary_key};"
            return update_statement
        else:
            return None  # Không thể tạo câu lệnh UPDATE nếu không có id

    elif operation == 'd' and before_data:  # DELETE
        # Xác định khóa chính (giả sử là trường "id")
        primary_key = before_data.get('id') if before_data else None
        if primary_key:
            delete_statement = f"DELETE FROM {db}.{table} WHERE id = {primary_key};"
            return delete_statement
        else:
            return None  # Không thể tạo câu lệnh DELETE nếu không có id

    return None

def extract_DDL(json_message):
    # Chuyển đổi chuỗi JSON thành dictionary
    message = json.loads(json_message)
    
    # Kiểm tra trường "tableChanges" trước
    table_changes = message.get("tableChanges", [])
    if table_changes:
        for change in table_changes:
            if change.get("type") == "CREATE":
                table_info = change.get("table", {})
                table_name = change.get("id", "").replace("\"", "")
                columns = table_info.get("columns", [])
                
                # Xây dựng danh sách các cột
                column_definitions = []
                for column in columns:
                    col_name = column.get("name")
                    col_type = column.get("typeExpression")
                    optional = "NULL" if column.get("optional", True) else "NOT NULL"
                    auto_increment = " AUTO_INCREMENT" if column.get("autoIncremented", False) else ""
                    column_definitions.append(f"{col_name} {col_type} {optional}{auto_increment}")
                
                # Kết hợp câu lệnh CREATE TABLE
                column_definitions_str = ", ".join(column_definitions)
                create_table_statement = f"CREATE TABLE {table_name} ({column_definitions_str});"
                return create_table_statement

    # Nếu không có "tableChanges", fallback sử dụng "ddl"
    ddl_statement = message.get("ddl", None)
    if ddl_statement:
        return ddl_statement

    # Nếu không tìm thấy DDL hoặc tableChanges, trả về None
    return None



sample_debezium_message = '''
{
  "schema": {
    "type": "struct",
    "fields": [
      {
        "type": "struct",
        "fields": [
          {"type": "int32", "optional": true, "field": "id"}
        ],
        "optional": true,
        "name": "second.test_db.tmp2.Value",
        "field": "before"
      },
      {
        "type": "struct",
        "fields": [
          {"type": "int32", "optional": true, "field": "id"}
        ],
        "optional": true,
        "name": "second.test_db.tmp2.Value",
        "field": "after"
      },
      {
        "type": "struct",
        "fields": [
          {"type": "string", "optional": false, "field": "version"},
          {"type": "string", "optional": false, "field": "connector"},
          {"type": "string", "optional": false, "field": "name"},
          {"type": "int64", "optional": false, "field": "ts_ms"},
          {"type": "string", "optional": true, "name": "io.debezium.data.Enum", "version": 1, "parameters": {"allowed": "true,last,false,incremental"}, "default": "false", "field": "snapshot"},
          {"type": "string", "optional": false, "field": "db"},
          {"type": "string", "optional": true, "field": "sequence"},
          {"type": "string", "optional": true, "field": "table"},
          {"type": "int64", "optional": false, "field": "server_id"},
          {"type": "string", "optional": true, "field": "gtid"},
          {"type": "string", "optional": false, "field": "file"},
          {"type": "int64", "optional": false, "field": "pos"},
          {"type": "int32", "optional": false, "field": "row"},
          {"type": "int64", "optional": true, "field": "thread"},
          {"type": "string", "optional": true, "field": "query"}
        ],
        "optional": false,
        "name": "io.debezium.connector.mysql.Source",
        "field": "source"
      },
      {
        "type": "string",
        "optional": false,
        "field": "op"
      },
      {
        "type": "int64",
        "optional": true,
        "field": "ts_ms"
      },
      {
        "type": "struct",
        "fields": [
          {"type": "string", "optional": false, "field": "id"},
          {"type": "int64", "optional": false, "field": "total_order"},
          {"type": "int64", "optional": false, "field": "data_collection_order"}
        ],
        "optional": true,
        "name": "event.block",
        "version": 1,
        "field": "transaction"
      }
    ],
    "optional": false,
    "name": "second.test_db.tmp2.Envelope",
    "version": 1
  },
  "payload": {
    "before": null,
    "after": {"id": 2},
    "source": {
      "version": "2.4.2.Final",
      "connector": "mysql",
      "name": "second",
      "ts_ms": 1733468083000,
      "snapshot": "false",
      "db": "test_db",
      "sequence": null,
      "table": "tmp2",
      "server_id": 1,
      "gtid": null,
      "file": "binlog.000002",
      "pos": 3112,
      "row": 1,
      "thread": 34,
      "query": null
    },
    "op": "c",
    "ts_ms": 1733468083997,
    "transaction": null
  }
}
'''

sample_debezium_create_table = '''
{
  "source" : {
    "server" : "second"
  },
  "position" : {
    "transaction_id" : null,
    "ts_sec" : 1733471297,
    "file" : "binlog.000002",
    "pos" : 8910,
    "server_id" : 1
  },
  "ts_ms" : 1733471297595,
  "databaseName" : "test_db",
  "ddl" : "create table tmp12 (id int)",
  "tableChanges" : [ {
    "type" : "CREATE",
    "id" : "\\"test_db\\".\\"tmp12\\"",
    "table" : {
      "defaultCharsetName" : "utf8mb4",
      "primaryKeyColumnNames" : [ ],
      "columns" : [ {
        "name" : "id",
        "jdbcType" : 4,
        "typeName" : "INT",
        "typeExpression" : "INT",
        "charsetName" : null,
        "position" : 1,
        "optional" : true,
        "autoIncremented" : false,
        "generated" : false,
        "comment" : null,
        "hasDefaultValue" : true,
        "enumValues" : [ ]
      } ],
      "attributes" : [ ]
    },
    "comment" : null
  } ]
}
'''