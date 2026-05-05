---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: AuditLog
table_order: 25
domain: audit
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - audit
---

# Таблица `AuditLog`

## Назначение
Хранит универсальный журнал изменений по системе.
Используется для фиксации вставки, изменения и удаления записей, а также бизнес-событий, связанных с workflow и критичными операциями. [file:24][file:19]

## Бизнес-смысл
Одна запись = одно изменение одного поля или одно бизнес-событие.
Журнал нужен для расследования, контроля действий пользователей и восстановления истории изменений. [file:24][file:1]

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AuditLogID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор записи |
| TableName | Text(100) | Да | Нет | Нет | — | Yes | Имя таблицы |
| RecordID | Long | Да | Нет | Нет | — | Yes | ID изменённой записи |
| FieldName | Text(100) | Нет | Нет | Нет | NULL | No | Имя поля, если логируется конкретное поле |
| OldValue | Memo | Нет | Нет | Нет | NULL | No | Старое значение |
| NewValue | Memo | Нет | Нет | Нет | NULL | No | Новое значение |
| ActionType | Text(10) | Да | Нет | Нет | — | No | Тип действия: INSERT / UPDATE / DELETE |
| BusinessEventType | Text(50) | Нет | Нет | Нет | NULL | No | Бизнес-тип события |
| ChangedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто изменил |
| ChangedAt | DateTime | Да | Нет | Нет | Now | Yes | Дата и время изменения |
| ChangeRequestID | Long | Нет | Нет | Да → ChangeRequests.ChangeRequestID | NULL | Yes | Связь с заявкой |
| WorkstationName | Text(100) | Нет | Нет | Нет | NULL | No | Имя рабочей станции |

## Первичный ключ
- `AuditLogID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ChangedByUserID | `Users.UserID` | Нет |
| ChangeRequestID | `ChangeRequests.ChangeRequestID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXALTable | TableName | Нет |
| IDXALRecordID | RecordID | Нет |
| IDXALDate | ChangedAt | Нет |
| IDXALCRID | ChangeRequestID | Нет |

## Правила заполнения
- `TableName`, `RecordID`, `ActionType`, `ChangedAt` обязательны. [file:24][file:19]
- `FieldName` может быть `NULL`, если логируется не поле, а событие целиком. [file:24]
- `ActionType` должен быть ограничен значениями `INSERT`, `UPDATE`, `DELETE`. [file:24][file:19]
- `BusinessEventType` используется для событий уровня предметной области, например `MetalChange` или `Transfer`. [file:25][file:1]

## Правила изменения
- Пишется через `ModAudit.WriteAuditEvent`, который в прогрессе уже отмечен как используемый в CRUD-операциях. [file:1]
- Записи аудита после создания не должны редактироваться и не должны удаляться из UI. [file:1][file:24]
- Для критичных изменений желательно логировать не только событие, но и значения до/после. [file:24][file:25]

## Использование в коде
### Модули
- [[ModAudit]]
- [[ModUsers]]
- [[ModRoles]]
- [[ModServices]]
- [[ModProducts]]
- [[ModTransfers]]
- [[ModChangeRequests]]
- [[ModMetals]]
- [[ModInventory]]
- [[ModDocuments]]

### Связанные таблицы
- [[T_Users]]
- [[T_ChangeRequests]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModAudit]] WriteAuditEvent | in-progress |
| Read | Отчёты / просмотр журнала | planned |
| Update | Не допускается | — |
| Delete | Не допускается | — |

## Типовые запросы
```sql
SELECT TableName, RecordID, FieldName, OldValue, NewValue, ActionType, ChangedAt
FROM AuditLog
WHERE TableName = 'Products' AND RecordID = 1
ORDER BY ChangedAt DESC;
```

## Открытые вопросы
- Нужен ли отдельный флаг, различающий системный аудит и бизнес-события?
- Нужна ли архивация старых записей аудита при росте объёма?