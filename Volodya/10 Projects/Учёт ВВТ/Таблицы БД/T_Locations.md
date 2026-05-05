---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: Locations
table_order: 15
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - locations
---

# Таблица `Locations`

## Назначение
Справочник мест хранения / дислокации изделий.
Поддерживает иерархию через self-FK `ParentLocationID` (склад → комната → стеллаж).

## Бизнес-смысл
Одна запись = одно место хранения.
За каждое место может быть назначен ответственный (`RespPersonID`).
Иерархия позволяет строить дерево мест хранения любой глубины.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LocationID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор места |
| LocationName | Text(200) | Да | Нет | Нет | — | No | Наименование |
| LocationCode | Text(20) | Нет | Нет | Нет | NULL | No | Короткий код |
| ParentLocationID | Long | Нет | Нет | Да → Locations.LocationID | NULL | No | Родительское место (self-FK) |
| RespPersonID | Long | Нет | Нет | Да → ResponsiblePersons.PersonID | NULL | No | Ответственное лицо |

## Первичный ключ
- `LocationID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ParentLocationID | `Locations.LocationID` | Нет (NULL = корневой узел) |
| RespPersonID | `ResponsiblePersons.PersonID` | Нет |

## Уникальные ограничения
Нет.

## Правила заполнения
- `LocationName` — обязателен.
- `ParentLocationID = NULL` — место верхнего уровня (объект, склад).
- `RespPersonID` — необязателен, но рекомендуется для корневых узлов.

## Правила изменения
- Управляется через `ModDictionaries`.
- Удаление безопасно только если нет дочерних мест и привязанных изделий.
- При удалении МОЛ нужно проверять `RespPersonID` во всех местах хранения.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_ResponsiblePersons]]
- [[T_Products]] (Products.LocationID → Locations.LocationID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] | planned |
| Read | [[ModDictionaries]] | planned |
| Update | [[ModDictionaries]] | planned |
| Delete | [[ModDictionaries]] (safe) | planned |

## Типовые запросы
```sql
-- Корневые места хранения
SELECT * FROM Locations WHERE ParentLocationID IS NULL ORDER BY LocationName;

-- Дочерние места для конкретного узла
SELECT * FROM Locations WHERE ParentLocationID = 1 ORDER BY LocationName;
```

## Открытые вопросы
- Нужен ли `IsActive` для мест хранения?
- Как обрабатывать перемещение изделий между местами — через `ProductTransfers` или отдельно?