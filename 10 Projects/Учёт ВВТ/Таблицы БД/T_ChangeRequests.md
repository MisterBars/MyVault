---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ChangeRequests
table_order: 21
domain: workflow
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - workflow
---

# Таблица `ChangeRequests`

## Назначение
Хранит заявки на изменение данных изделия.
Используется для workflow: инициирование, блокировка, согласование, применение изменений.

## Бизнес-смысл
Одна запись = одна заявка на изменение по одному изделию.
Заявка содержит общий статус, комментарии, сведения о блокировке, согласовании и применении.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ChangeRequestID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор заявки |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| RequestedByUserID | Long | Да | Нет | Да → Users.UserID | — | No | Кто запросил |
| RequestedAt | DateTime | Да | Нет | Нет | Now | No | Когда запросил |
| RequestType | Text(30) | Да | Нет | Нет | — | No | Тип запроса |
| Status | Text(20) | Да | Нет | Нет | — | Yes | Статус заявки |
| Comment | Memo | Нет | Нет | Нет | NULL | No | Комментарий инициатора |
| ReviewComment | Memo | Нет | Нет | Нет | NULL | No | Комментарий проверяющего |
| ReviewedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто проверил |
| ReviewedAt | DateTime | Нет | Нет | Нет | NULL | No | Когда проверил |
| ApprovalDecision | Text(20) | Нет | Нет | Нет | NULL | No | Решение по заявке |
| AppliedAt | DateTime | Нет | Нет | Нет | NULL | No | Когда изменения применены |
| AppliedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто применил |
| LockedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто удерживает блокировку |
| LockedAt | DateTime | Нет | Нет | Нет | NULL | No | Когда поставлена блокировка |
| LockToken | Text(100) | Нет | Нет | Нет | NULL | Yes | Токен блокировки, связанный с сессией |

## Первичный ключ
- `ChangeRequestID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| RequestedByUserID | `Users.UserID` | Да |
| ReviewedByUserID | `Users.UserID` | Нет |
| AppliedByUserID | `Users.UserID` | Нет |
| LockedByUserID | `Users.UserID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXCRProdID | ProductID | Нет |
| IDXCRStatus | Status | Нет |
| IDXCRLocked | LockedByUserID | Нет |

## Правила заполнения
- `ProductID`, `RequestedByUserID`, `RequestedAt`, `RequestType`, `Status` — обязательны.
- `LockToken` связан с `UserSessions.SessionToken`.
- Статусы могут быть, например: `Draft`, `Pending`, `Approved`, `Rejected`, `Applied`, `Cancelled`.

## Правила изменения
- Управляется через `ModChangeRequests`.
- Пока заявка заблокирована, редактировать её должен только владелец блокировки.
- При завершении сессии пользователя незакрытые блокировки должны сниматься.
- Применение заявки должно обновлять целевую запись в `Products` и журналироваться.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModChangeRequests]]
- [[ModSession]] (cleanup блокировок)

### Связанные таблицы
- [[T_Products]]
- [[T_Users]]
- [[T_ChangeRequestItems]]
- [[T_UserSessions]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModChangeRequests]] | planned |
| Read | [[ModChangeRequests]] | planned |
| Update | [[ModChangeRequests]] | planned |
| Delete | Обычно не удаляется | — |

## Типовые запросы
```sql
SELECT CR.ChangeRequestID, CR.Status, CR.RequestType, U.Login, CR.RequestedAt
FROM ChangeRequests AS CR
INNER JOIN Users AS U ON CR.RequestedByUserID = U.UserID
WHERE CR.ProductID = 1
ORDER BY CR.RequestedAt DESC;
```

## Открытые вопросы
- Нужен ли отдельный справочник статусов и типов заявок вместо `Text`?
- Можно ли иметь несколько активных заявок на одно изделие одновременно?