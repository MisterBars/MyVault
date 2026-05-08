---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: Manufacturers
table_order: 6
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - manufacturers
---

# Таблица `Manufacturers`

## Назначение
Справочник производителей техники.
Используется при заполнении карточки изделия (`Products.ManufacturerID`).

## Бизнес-смысл
Одна запись = один производитель.
Хранит краткое и полное наименование, адрес, телефон.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ManufacturerID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор производителя |
| ShortName | Text(100) | Да | Нет | Нет | — | No | Краткое наименование |
| FullName | Text(255) | Нет | Нет | Нет | NULL | No | Полное наименование |
| Address | Text(255) | Нет | Нет | Нет | NULL | No | Адрес |
| Phone | Text(50) | Нет | Нет | Нет | NULL | No | Телефон |

## Первичный ключ
- `ManufacturerID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет (ShortName не ограничен уникальностью).

## Правила заполнения
- `ShortName` — обязателен.
- Остальные поля опциональны.

## Правила изменения
- Управляется через `ModDictionaries`.
- Удаление только если нет привязанных изделий (`Products.ManufacturerID`).
- Логируется в `AuditLog`.

## Использование в коде
### Формы
- Через `FListDB` / `FChangeDB` (справочники)

### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_Products]] (Products.ManufacturerID → Manufacturers.ManufacturerID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] | planned |
| Read | [[ModDictionaries]] | planned |
| Update | [[ModDictionaries]] | planned |
| Delete | [[ModDictionaries]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM Manufacturers ORDER BY ShortName;
```

## Открытые вопросы
- Нужен ли `IsActive` по аналогии с другими справочниками?
- Нужна ли уникальность `ShortName`?