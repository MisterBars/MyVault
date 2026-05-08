---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: Services
table_order: 2
domain: users-and-rights
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - services
---

# Таблица `Services`

## Назначение
Хранит подразделения / службы организации.
Используется для разграничения доступа к изделиям: пользователь видит только
изделия своей службы.

## Бизнес-смысл
Одна запись = одна служба (воинская часть, подразделение, отдел).
Через `UserServices` пользователь привязывается к одной или нескольким службам.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ServiceID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор службы |
| ServiceName | Text(100) | Да | Нет | Нет | — | No | Полное название службы |
| ServiceCode | Text(20) | Нет | Нет | Нет | NULL | No | Короткий код службы |
| Description | Memo | Нет | Нет | Нет | NULL | No | Описание |
| IsActive | YesNo | Да | Нет | Нет | True | No | Признак активности |

## Первичный ключ
- `ServiceID`

## Внешние ключи
Нет.

## Уникальные ограничения
Нет (ServiceName и ServiceCode не уникальны принудительно).

## Правила заполнения
- `ServiceName` — обязателен.
- `IsActive = False` используется для мягкого отключения службы без удаления.

## Правила изменения
- Создавать и редактировать службы может пользователь с `CanManageAdmin`.
- Удаление через `DeleteServiceSafe` — только если нет привязанных пользователей и изделий.
- Все изменения логируются в `AuditLog`.

## Использование в коде
### Формы
- [[F_ListsDB]] (вкладка 4)
- [[F_Change]] (вкладка 4)

### Модули
- [[ModServices]]
- [[ModFillsLB]] (FillServicesListBox)
- [[ModServiceUsersBuffer]]

### Связанные таблицы
- [[T_UserServices]]
- [[T_ProductServices]]
- [[T_InventoryOrders]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModServices]] CreateService | in-progress |
| Read | [[ModServices]] GetAllServices, GetServiceUsers | in-progress |
| Update | [[ModServices]] UpdateService | in-progress |
| Delete | [[ModServices]] DeleteServiceSafe | in-progress |

## Типовые запросы
```sql
SELECT * FROM Services WHERE IsActive = True ORDER BY ServiceName;
```

## Открытые вопросы
- Нужен ли `ServiceCode` как уникальный?
- Нужна ли иерархия служб (ParentServiceID)?