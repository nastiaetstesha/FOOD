import json
import sqlite3
from pathlib import Path

def import_data():
    db_path = "db.sqlite3"
    json_file = "all_selected_data.json"
    
    if not Path(db_path).exists():
        print("❌ Ошибка: База данных db.sqlite3 не найдена")
        return
    
    if not Path(json_file).exists():
        print("❌ Ошибка: Файл all_selected_data.json не найден")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("📥 Загрузка данных из JSON...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        table_mapping = {
            "food_tags": "foodplan_app_foodtag",
            "ingredients": "foodplan_app_ingredient",
            "menu_types": "foodplan_app_menutype",
            "price_ranges": "foodplan_app_pricerange", 
            "recipes": "foodplan_app_recipe",
            "recipe_ingredients": "foodplan_app_recipeingredient",
            "daily_menus": "foodplan_app_dailymenu",
            "daily_menu_users": "foodplan_app_dailymenu_users"
        }
        
        total_imported = 0
        
        for json_key, table_name in table_mapping.items():
            if json_key in data and data[json_key]:
                records = data[json_key]
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor.fetchone():
                    print(f"⚠️ Таблица {table_name} не существует. Пропускаем.")
                    continue
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"❌ В таблице {table_name} уже есть {count} записей. Импорт отменен.")
                    conn.close()
                    return
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if columns:
                    placeholders = ', '.join(['?' for _ in columns])
                    columns_str = ', '.join(columns)
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    values_list = []
                    for record in records:
                        values = [record.get(col) for col in columns]
                        values_list.append(values)
                    
                    cursor.executemany(sql, values_list)
                    imported_count = len(records)
                    total_imported += imported_count
                    print(f"✅ {table_name}: {imported_count} записей")
                else:
                    print(f"⚠️ {table_name}: не найдены колонки")
            else:
                print(f"⚠️ {table_name}: нет данных в JSON")
        
        conn.commit()
        
        if total_imported > 0:
            print(f"\n🎉 Импорт завершен! Всего импортировано: {total_imported} записей")
        else:
            print(f"\nℹ️ Не было импортировано ни одной записи")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при импорте: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_data()