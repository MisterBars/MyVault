---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ArchiveCases
table_order: 16
domain: documents
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - documents
  - archive
---

# Таблица `ArchiveCases`

## Назначение
Справочник архивных дел (томов, папок).
Используется для привязки документов изделий к физическому архивному делу.

## Бизнес-смысл
Одна запись = одно архивное дело (папка / том).
Документы изделий (`ProductDocuments`) могут ссылаться на архивное дело и страницу.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CaseID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор дела |
| CaseNumber | Text(100) | Да | Нет | Нет | — | Yes | Номер дела |
| CaseTitle | Text(255) | Да | Нет | Нет | — | No | Заголовок дела |
| PeriodFrom | DateTime | Нет | Нет | Нет | NULL | Yes | Начало периода |
| PeriodTo | DateTime | Нет | Нет | Нет | NULL | Yes | Конец периода |
| Description | Memo | Нет | Нет | Нет | NULL | No | Описание |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания записи |
| IsActive | YesNo | Да | Нет | Нет | True | No | Признак активности |

## Первичный ключ
- `CaseID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| CreatedByUserID | `Users.UserID` | Нет |

## Уникальные ограничения
Нет (CaseNumber не ограничен принудительно).

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXACNum | CaseNumber | Нет |
| IDXACFrom | PeriodFrom | Нет |
| IDXACTo | PeriodTo | Нет |

## Правила заполнения
- `CaseNumber` и `CaseTitle` — обязательны.
- `PeriodTo = NULL` — дело ещё открыто.
- `IsActive = False` — дело закрыто / передано.

## Правила изменения
- Управляется через `ModDocuments`.
- Удаление безопасно только если нет привязанных документов в `ProductDocuments`.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModDocuments]]

### Связанные таблицы
- [[T_ProductDocuments]] (ProductDocuments.ArchiveCaseID → ArchiveCases.CaseID)
- [[T_Users]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDocuments]] | planned |
| Read | [[ModDocuments]] | planned |
| Update | [[ModDocuments]] | planned |
| Delete | [[ModDocuments]] (safe) | planned |

## Типовые запросы
```sql
SELECT * FROM ArchiveCases WHERE IsActive = True ORDER BY CaseNumber;
```