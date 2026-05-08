---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: DocumentTypes
table_order: 9
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - documents
---

# Таблица `DocumentTypes`

## Назначение
Справочник типов приёмосдаточных документов изделия.
Используется в `Products.DocumentTypeID` для указания основания постановки на учёт.

## Бизнес-смысл
Одна запись = один тип документа (накладная, акт приёма, приказ и т.д.).

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DocumentTypeID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор типа |
| TypeName | Text(100) | Да | Нет | Нет | — | No | Наименование типа |

## Первичный ключ
- `DocumentTypeID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет.

## Правила заполнения
- `TypeName` — обязателен.

## Правила изменения
- Управляется через `ModDictionaries`.
- Удаление безопасно только если нет привязанных записей в `Products`.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_Products]] (Products.DocumentTypeID → DocumentTypes.DocumentTypeID)
- [[T_ProductDocTypes]] (отдельный справочник — не путать!)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] | planned |
| Read | [[ModDictionaries]] | planned |
| Update | [[ModDictionaries]] | planned |
| Delete | [[ModDictionaries]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM DocumentTypes ORDER BY TypeName;
```

## Открытые вопросы
- Не путать с `ProductDocTypes` — это разные таблицы с похожим назначением.
  `DocumentTypes` — тип документа-основания для изделия.
  `ProductDocTypes` — тип документа в архиве изделия.
- Нужен ли `IsActive`?