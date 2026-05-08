---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: UserServices
table_order: 4
domain: users-and-rights
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - many-to-many
---

# Таблица `UserServices`

## Назначение
Связующая таблица M:N между пользователями и службами.
Определяет, к каким службам у пользователя есть доступ и какие права (редактирование,
согласование) он имеет в каждой из них.

## Бизнес-смысл
Один пользователь может быть привязан к нескольким службам с разными правами.
Одна запись = одна связка «пользователь + служба + права».

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UserServiceID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор связки |
| UserID | Long | Да | Нет | Да → Users.UserID | — | Yes | Пользователь |
| ServiceID | Long | Да | Нет | Да → Services.ServiceID | — | Yes | Служба |
| CanEdit | YesNo | Да | Нет | Нет | False | No | Право редактирования |
| CanApprove | YesNo | Да | Нет | Нет | False | No | Право согласования |

## Первичный ключ
- `UserServiceID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| UserID | `Users.UserID` | Да |
| ServiceID | `Services.ServiceID` | Да |

## Уникальные ограничения
- `(UserID, ServiceID)` — пара уникальна.

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXUSUserID | UserID | Нет |
| IDXUSSvcID | ServiceID | Нет |

## Правила заполнения
- Пара `(UserID, ServiceID)` не может дублироваться.
- По умолчанию оба флага прав `False`.

## Правила изменения
- Управление правами пользователя по службам — через `SaveServiceUsersLinks` и `UpdateUserServiceRights`.
- Промежуточное состояние буферизуется в `ModServiceUsersBuffer` до сохранения.
- Отзыв доступа — `RevokeUserService`.
- Логируется в `AuditLog`.

## Использование в коде
### Формы
- [[F_Change]] (вкладки 4 и 5, блок прав по службам)

### Модули
- [[ModServices]] (SaveServiceUsersLinks, UpdateUserServiceRights, RevokeUserService)
- [[ModServiceUsersBuffer]] (буфер изменений до сохранения)

### Связанные таблицы
- [[T_Users]]
- [[T_Services]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModServices]] SaveServiceUsersLinks | in-progress |
| Read | [[ModServices]] GetServiceUsers | in-progress |
| Update | [[ModServices]] UpdateUserServiceRights | in-progress |
| Delete | [[ModServices]] RevokeUserService | in-progress |

## Типовые запросы
```sql
-- Все службы пользователя с правами
SELECT S.ServiceName, US.CanEdit, US.CanApprove
FROM UserServices AS US
INNER JOIN Services AS S ON US.ServiceID = S.ServiceID
WHERE US.UserID = 1;
```