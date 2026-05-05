---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductDocTypes
table_order: 13
domain: documents
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - documents
---

# Таблица `ProductDocTypes`

## Назначение
Справочник типов документов в архиве изделия (паспорт, формуляр, инструкция,
акт проверки и т.д.).
Используется в `ProductDocuments.DocumentTypeID`.

## Бизнес-смысл
Одна запись = один тип архивного документа изделия.
Не путать с `DocumentTypes` — тот справочник для типа документа-основания
при постановке изделия на учёт.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DocumentTypeID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор типа |
| TypeName | Text(100) | Да | Нет | Нет | — | No | Наименование типа |
| Description | Text(255) | Нет | Нет | Нет | NULL | No | Описание |
| IsActive | YesNo | Да | Нет | Нет | True | No | Признак активности |

## Первичный ключ
- `DocumentTypeID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет.

## Правила заполнения
- `TypeName` — обязателен.
- `IsActive = False` отключает тип без удаления.

## Правила изменения
- Управляется через `ModDocuments`.
- Удаление безопасно только если нет записей в `ProductDocuments` с этим типом.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDocuments]]

### Связанные таблицы
- [[T_ProductDocuments]] (ProductDocuments.DocumentTypeID → ProductDocTypes.DocumentTypeID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDocuments]] | planned |
| Read | [[ModDocuments]] | planned |
| Update | [[ModDocuments]] | planned |
| Delete | [[ModDocuments]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM ProductDocTypes WHERE IsActive = True ORDER BY TypeName;
```

## Открытые вопросы
- Не путать с `DocumentTypes` в UI и коде — рассмотреть переименование одной из таблиц
  для устранения путаницы (например: `AcceptanceDocTypes` vs `ProductDocTypes`).