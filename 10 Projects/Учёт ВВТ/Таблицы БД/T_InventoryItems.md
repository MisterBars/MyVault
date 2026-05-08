---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: InventoryItems
table_order: 26
domain: inventory
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - inventory
  - snapshot
---

# Таблица `InventoryItems`

## Назначение
Хранит строки инвентаризации по изделиям.
Содержит снимок данных изделия на момент инвентаризации и фактические значения по драгметаллам для сверки. [file:24][file:19]

## Бизнес-смысл
Одна запись = одна строка инвентаризации по одному изделию в рамках одного приказа.
Это snapshot-таблица: часть полей копируется из карточки изделия на момент проведения инвентаризации, чтобы потом можно было сравнить план и факт. [file:24][file:1]

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| InventoryItemID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор строки |
| InventoryOrderID | Long | Да | Нет | Да → InventoryOrders.InventoryOrderID | — | No | Приказ инвентаризации |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | No | Изделие |
| SeqNumber | Integer | Да | Нет | Нет | — | Unique within order | Порядковый номер строки |
| SnapName | Text(255) | Нет | Нет | Нет | NULL | No | Снимок наименования |
| SnapSerialNum | Text(100) | Нет | Нет | Нет | NULL | No | Снимок серийного номера |
| SnapInventNum | Text(100) | Нет | Нет | Нет | NULL | No | Снимок инвентарного номера |
| SnapMfgYear | Text(10) | Нет | Нет | Нет | NULL | No | Снимок года изготовления |
| SnapGoldGrams | Double | Нет | Нет | Нет | NULL | No | Снимок золота |
| SnapSilverGrams | Double | Нет | Нет | Нет | NULL | No | Снимок серебра |
| SnapPlatinumGrams | Double | Нет | Нет | Нет | NULL | No | Снимок платины |
| SnapMPGGrams | Double | Нет | Нет | Нет | NULL | No | Снимок МПГ |
| ActualGoldGrams | Double | Нет | Нет | Нет | NULL | No | Фактическое золото |
| ActualSilverGrams | Double | Нет | Нет | Нет | NULL | No | Фактическое серебро |
| ActualPlatinumGrams | Double | Нет | Нет | Нет | NULL | No | Фактическая платина |
| ActualMPGGrams | Double | Нет | Нет | Нет | NULL | No | Фактический МПГ |
| ItemNote | Memo | Нет | Нет | Нет | NULL | No | Примечание по строке |

## Первичный ключ
- `InventoryItemID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| InventoryOrderID | `InventoryOrders.InventoryOrderID` | Да |
| ProductID | `Products.ProductID` | Да |

## Уникальные ограничения
- `(InventoryOrderID, SeqNumber)` — номер строки уникален в пределах одного приказа. [file:24][file:19]

## Правила заполнения
- `InventoryOrderID`, `ProductID`, `SeqNumber` обязательны. [file:24][file:19]
- Snapshot-поля должны заполняться при создании строки, а не вычисляться на лету. [file:24][file:1]
- Фактические значения могут отличаться от snapshot и используются для выявления расхождений. [file:24]

## Правила изменения
- Управляется через `ModInventory`, который в прогрессе уже указан как модуль для `InventoryOrders` и `InventoryItems`. [file:1]
- После завершения инвентаризации snapshot-поля не должны пересчитываться. [file:24][file:1]
- Изменения строк должны логироваться в `AuditLog`, особенно по фактическим значениям и примечаниям. [file:1][file:24]

## Использование в коде
### Модули
- [[ModInventory]]

### Связанные таблицы
- [[T_InventoryOrders]]
- [[T_Products]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModInventory]] | planned |
| Read | [[ModInventory]] | planned |
| Update | [[ModInventory]] | planned |
| Delete | [[ModInventory]] | planned |

## Типовые запросы
```sql
SELECT SeqNumber, SnapName, SnapSerialNum, SnapGoldGrams, ActualGoldGrams, ItemNote
FROM InventoryItems
WHERE InventoryOrderID = 1
ORDER BY SeqNumber;
```

## Открытые вопросы
- Нужны ли отдельные поля для отклонения `DiffGold`, `DiffSilver` и т.д. или они считаются запросом?
- Нужен ли уникальный индекс также на `(InventoryOrderID, ProductID)` чтобы одно изделие не попало дважды?