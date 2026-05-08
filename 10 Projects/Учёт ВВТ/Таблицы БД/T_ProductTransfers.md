---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductTransfers
table_order: 20
domain: transfers
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - transfers
---

# Таблица `ProductTransfers`

## Назначение
Хранит историю перемещений и передачи изделий.
Используется для фиксации внутренних и внешних перемещений, а также как источник актуального статуса принадлежности.

## Бизнес-смысл
Одна запись = одно событие перемещения изделия.
По этим записям можно восстановить историю: куда, когда, по какому документу и на каком основании изделие было передано.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TransferID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор перемещения |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| TransferType | Text(30) | Да | Нет | Нет | — | No | Тип перемещения |
| OrderNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер приказа |
| OrderDate | DateTime | Нет | Нет | Нет | NULL | No | Дата приказа |
| TransferDate | DateTime | Да | Нет | Нет | — | Yes | Дата перемещения |
| DestinationOrgName | Text(255) | Нет | Нет | Нет | NULL | No | Организация назначения |
| DestinationAddress | Memo | Нет | Нет | Нет | NULL | No | Адрес назначения |
| DestinationContact | Text(255) | Нет | Нет | Нет | NULL | No | Контактное лицо |
| BasisDocumentType | Text(100) | Нет | Нет | Нет | NULL | No | Тип документа-основания |
| BasisDocumentPath | Memo | Нет | Нет | Нет | NULL | No | Путь к файлу основания |
| InventoryOrderID | Long | Нет | Нет | Да → InventoryOrders.InventoryOrderID | NULL | No | Связь с инвентаризацией |
| Comment | Memo | Нет | Нет | Нет | NULL | No | Примечание |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания записи |

## Первичный ключ
- `TransferID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| InventoryOrderID | `InventoryOrders.InventoryOrderID` | Нет |
| CreatedByUserID | `Users.UserID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXPTProdID | ProductID | Нет |
| IDXPTDate | TransferDate | Нет |

## Правила заполнения
- `TransferType` и `TransferDate` обязательны.
- `Destination*` поля заполняются при внешней передаче.
- `InventoryOrderID` используется, если передача зафиксирована в рамках инвентаризации.

## Правила изменения
- Управляется через `ModTransfers`.
- Последняя по дате запись может использоваться для расчёта текущего `OwnershipStatus` изделия.
- Изменение уже проведённого перемещения должно быть ограничено и логироваться.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModTransfers]]

### Связанные таблицы
- [[T_Products]]
- [[T_InventoryOrders]]
- [[T_Users]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModTransfers]] | planned |
| Read | [[ModTransfers]] | planned |
| Update | [[ModTransfers]] | planned |
| Delete | [[ModTransfers]] | planned |

## Типовые запросы
```sql
SELECT PT.TransferDate, PT.TransferType, PT.OrderNumber, PT.DestinationOrgName
FROM ProductTransfers AS PT
WHERE PT.ProductID = 1
ORDER BY PT.TransferDate DESC;
```

## Открытые вопросы
- Нужно ли нормализовать `TransferType` в отдельный справочник?
- Обновляется ли `Products.OwnershipStatus` автоматически по последнему перемещению?