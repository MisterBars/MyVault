---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: UserSessions
table_order: 5
domain: users-and-rights
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - session
---

# Таблица `UserSessions`

## Назначение
Хранит активные и завершённые сессии пользователей.
Используется для контроля одновременных входов, heartbeat-мониторинга активности
и корректного завершения работы при сбоях.

## Бизнес-смысл
Одна запись = один сеанс работы пользователя в Excel-надстройке.
Сессия открывается при входе в `FAuth`, закрывается при выходе или по таймауту.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SessionID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор сессии |
| UserID | Long | Да | Нет | Да → Users.UserID | — | Yes | Пользователь |
| SessionToken | Text(100) | Да | Нет | Нет | — | Unique | GUID-токен сессии |
| LoginTime | DateTime | Да | Нет | Нет | Now | Yes | Время входа |
| LastPing | DateTime | Нет | Нет | Нет | NULL | Yes | Последний heartbeat |
| LogoutTime | DateTime | Нет | Нет | Нет | NULL | No | Время выхода |
| SessionStatus | Text(20) | Да | Нет | Нет | Active | Yes | Статус сессии |
| WorkbookHost | Text(100) | Нет | Нет | Нет | NULL | No | Имя компьютера (COMPUTERNAME) |

## Первичный ключ
- `SessionID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| UserID | `Users.UserID` | Да |

## Уникальные ограничения
- `SessionToken`

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXSessUserID | UserID | Нет |
| IDXSessLogin | LoginTime | Нет |
| IDXSessPing | LastPing | Нет |
| IDXSessStatus | SessionStatus | Нет |

## Допустимые значения SessionStatus
| Значение | Смысл |
| --- | --- |
| `Active` | Пользователь работает |
| `Closed` | Корректный выход |
| `Expired` | Сессия истекла по таймауту |
| `Crashed` | Приложение завершилось аварийно |

## Правила заполнения
- `SessionToken` генерируется как GUID при старте сессии.
- `WorkbookHost` = `Environ("COMPUTERNAME")`.
- `LastPing` обновляется периодически через heartbeat-таймер.

## Правила изменения
- Создаётся только в `SessionStartup`.
- `SessionStatus` меняется только через `SessionShutdown` или cleanup-процедуру.
- `LockToken` в `ChangeRequests` связан с `SessionToken` — при закрытии сессии блокировки снимаются.
- Логируется в `AuditLog`.

## Использование в коде
### Формы
- [[F_Auth]] (создаёт сессию при входе)

### Модули
- [[ModSession]] (SessionStartup, SessionShutdown, heartbeat, cleanup, timeout)

### Связанные таблицы
- [[T_Users]]
- [[T_ChangeRequests]] (LockToken связан с SessionToken)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModSession]] SessionStartup | in-progress |
| Read | [[ModSession]] | in-progress |
| Update | [[ModSession]] heartbeat, cleanup | in-progress |
| Delete | Не используется (soft через SessionStatus) | — |

## Типовые запросы
```sql
-- Все активные сессии
SELECT U.Login, S.LoginTime, S.LastPing, S.WorkbookHost
FROM UserSessions AS S
INNER JOIN Users AS U ON S.UserID = U.UserID
WHERE S.SessionStatus = 'Active';
```