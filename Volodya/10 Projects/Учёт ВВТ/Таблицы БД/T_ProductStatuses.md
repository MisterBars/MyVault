---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductStatuses
table_order: 12
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - products
---

# Таблица `ProductStatuses`

## Назначение
Справочник статусов состояния изделий (в эксплуатации, на ремонте, на хранении,
списано и т.д.).
Используется в карточке изделия как `Products.StatusID`.

## Бизнес-смысл
Одна запись = один статус изделия.
Не путать с `Products.OwnershipStatus` — это другой признак (принадлежность),
а не техническое состояние.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| StatusID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор статуса |
| StatusName | Text(100) | Да | Нет | Нет | — | No | Наименование статуса |

## Первичный ключ
- `StatusID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет.

## Правила заполнения
- `StatusName` — обязателен.
- Таблица заполняется при инициализации.

## Правила изменения
- Управляется через `ModDictionaries`.
- Удаление безопасно только если нет привязанных изделий (`Products.StatusID`).
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_Products]] (Products.StatusID → ProductStatuses.StatusID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] | planned |
| Read | [[ModDictionaries]] | planned |
| Update | [[ModDictionaries]] | planned |
| Delete | [[ModDictionaries]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM ProductStatuses ORDER BY StatusName;
```

## Открытые вопросы
- Чётко разграничить `StatusID` (техническое состояние) и `OwnershipStatus` (принадлежность)
  в UI чтобы пользователь не путался.