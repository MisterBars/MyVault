---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ResponsiblePersons
table_order: 14
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
---

# Таблица `ResponsiblePersons`

## Назначение
Справочник материально-ответственных лиц.
Используется при назначении ответственного за изделие и за место хранения.

## Бизнес-смысл
Одна запись = одно МОЛ (военнослужащий или гражданский сотрудник).
Не связан напрямую с таблицей `Users` — МОЛ может не иметь учётной записи в системе.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PersonID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор МОЛ |
| FullName | Text(200) | Да | Нет | Нет | — | No | ФИО |
| PersonPosition | Text(200) | Нет | Нет | Нет | NULL | No | Должность |
| WorkPhone | Text(50) | Нет | Нет | Нет | NULL | No | Рабочий телефон |
| MobilePhone | Text(50) | Нет | Нет | Нет | NULL | No | Мобильный телефон |
| IsActive | YesNo | Да | Нет | Нет | True | No | Признак активности |

## Первичный ключ
- `PersonID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет.

## Правила заполнения
- `FullName` — обязателен.
- `IsActive = False` — МОЛ убыл / снят с должности, но запись остаётся для истории.

## Правила изменения
- Управляется через `ModDictionaries`.
- Удаление безопасно только если нет привязанных изделий и мест хранения.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDictionaries]]

### Связанные таблицы
- [[T_Products]] (Products.RespPersonID → ResponsiblePersons.PersonID)
- [[T_Locations]] (Locations.RespPersonID → ResponsiblePersons.PersonID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDictionaries]] | planned |
| Read | [[ModDictionaries]] | planned |
| Update | [[ModDictionaries]] | planned |
| Delete | [[ModDictionaries]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM ResponsiblePersons WHERE IsActive = True ORDER BY FullName;
```

## Открытые вопросы
- Нужна ли связь с `Users.UserID` для тех МОЛ, у кого есть учётная запись?
- Нужен ли отдельный тип МОЛ (военный / гражданский)?