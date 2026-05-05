---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: InventoryOrders
table_order: 19
domain: inventory
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - inventory
---

# Таблица `InventoryOrders`

## Назначение
Хранит приказы / распоряжения на проведение инвентаризации.
Является шапкой документа для набора строк в `InventoryItems`.

## Бизнес-смысл
Одна запись = одна инвентаризация по службе или группе изделий.
Фиксирует номер, дату приказа, дату фактической инвентаризации, комиссию и статус.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| InventoryOrderID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор инвентаризации |
| OrderNumber | Text(50) | Да | Нет | Нет | — | No | Номер приказа |
| OrderDate | DateTime | Да | Нет | Нет | — | No | Дата приказа |
| InventoryDate | DateTime | Да | Нет | Нет | — | No | Дата инвентаризации |
| ServiceID | Long | Нет | Нет | Да → Services.ServiceID | NULL | No | Служба |
| Status | Text(20) | Нет | Нет | Нет | NULL | No | Статус документа |
| CommissionChairman | Text(200) | Нет | Нет | Нет | NULL | No | Председатель комиссии |
| CommissionMembers | Memo | Нет | Нет | Нет | NULL | No | Состав комиссии |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |

## Первичный ключ
- `InventoryOrderID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ServiceID | `Services.ServiceID` | Нет |
| CreatedByUserID | `Users.UserID` | Нет |

## Уникальные ограничения
Нет.

## Правила заполнения
- `OrderNumber`, `OrderDate`, `InventoryDate` — обязательны.
- `Status` может использовать значения `Draft`, `InProgress`, `Completed`.
- `ServiceID` может быть `NULL`, если приказ охватывает не одну конкретную службу.

## Правила изменения
- Управляется через `ModInventory`.
- После завершения инвентаризации изменение шапки должно быть ограничено.
- Удаление безопасно только если нет строк в `InventoryItems`, либо каскадно по бизнес-правилу.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModInventory]]

### Связанные таблицы
- [[T_InventoryItems]]
- [[T_Services]]
- [[T_Users]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModInventory]] | planned |
| Read | [[ModInventory]] | planned |
| Update | [[ModInventory]] | planned |
| Delete | [[ModInventory]] | planned |

## Типовые запросы
```sql
SELECT IO.OrderNumber, IO.InventoryDate, S.ServiceName, IO.Status
FROM InventoryOrders AS IO
LEFT JOIN Services AS S ON IO.ServiceID = S.ServiceID
ORDER BY IO.InventoryDate DESC;
```

## Открытые вопросы
- Нужен ли отдельный справочник статусов инвентаризации вместо `Text(20)`?