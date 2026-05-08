---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: Categories
table_order: 10
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - categories
---

# Таблица `Categories`

## Назначение
Справочник категорий состояния изделий (I, II, III, IV, V).
Соответствует категорийности техники по нормативным документам.

## Бизнес-смысл
Одна запись = одна категория. Категория отражает техническое состояние изделия:
I — новое, V — списание.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CategoryID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор категории |
| CategoryNum | Integer | Да | Нет | Нет | — | No | Номер категории (1–5) |
| CategoryName | Text(50) | Да | Нет | Нет | — | No | Название (I, II, III, IV, V) |
| Description | Memo | Нет | Нет | Нет | NULL | No | Описание категории |

## Первичный ключ
- `CategoryID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет (CategoryNum не ограничен уникальностью принудительно, но фактически уникален).

## Правила заполнения
- `CategoryNum` — обязателен, значения 1–5.
- `CategoryName` — обязателен, значения I–V.
- Таблица заполняется один раз при инициализации БД.

## Правила изменения
- Управляется через `ModDictionaries`.
- Фактически неизменяемый справочник — только чтение в runtime.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_Products]] (Products.CategoryID → Categories.CategoryID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] / инициализация | planned |
| Read | [[ModDictionaries]] | planned |
| Update | Не предполагается | — |
| Delete | Не предполагается | — |

## Типовые запросы
```sql
SELECT * FROM Categories ORDER BY CategoryNum;
```