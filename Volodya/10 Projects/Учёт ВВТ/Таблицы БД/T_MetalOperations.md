---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: MetalOperations
table_order: 24
domain: metals
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - metals
  - operations
---

# Таблица `MetalOperations`

## Назначение
Хранит хозяйственные и учётные операции по драгметаллам.
Используется для регистрации поступления, списания, извлечения, передачи и иных операций, связанных с металлами изделия.

## Бизнес-смысл
Одна запись = одна операция по одному изделию.
В отличие от `ProductMetalHistory`, здесь фиксируется не изменение карточки изделия, а факт операции за определённый учётный период.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MetalOperationID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор операции |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| OperationDate | DateTime | Да | Нет | Нет | — | Yes | Дата операции |
| OperationType | Text(30) | Да | Нет | Нет | — | No | Тип операции |
| AccountingPeriodYear | Integer | Да | Нет | Нет | — | Yes | Учётный год |
| AccountingPeriodHalfYear | Integer | Нет | Нет | Нет | NULL | No | Полугодие |
| GoldAmount | Double | Нет | Нет | Нет | NULL | No | Золото, г |
| SilverAmount | Double | Нет | Нет | Нет | NULL | No | Серебро, г |
| PlatinumAmount | Double | Нет | Нет | Нет | NULL | No | Платина, г |
| MPGAmount | Double | Нет | Нет | Нет | NULL | No | МПГ, г |
| QuantityItems | Double | Нет | Нет | Нет | NULL | No | Количество единиц |
| BasisDocumentNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер документа-основания |
| BasisDocumentDate | DateTime | Нет | Нет | Нет | NULL | No | Дата документа-основания |
| BasisDocumentPath | Memo | Нет | Нет | Нет | NULL | No | Путь к документу |
| Counterparty | Text(255) | Нет | Нет | Нет | NULL | No | Контрагент |
| Comment | Memo | Нет | Нет | Нет | NULL | No | Комментарий |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания записи |

## Первичный ключ
- `MetalOperationID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| CreatedByUserID | `Users.UserID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXMOProdID | ProductID | Нет |
| IDXMODate | OperationDate | Нет |
| IDXMOYear | AccountingPeriodYear | Нет |

## Правила заполнения
- `ProductID`, `OperationDate`, `OperationType`, `AccountingPeriodYear` обязательны.
- `AccountingPeriodHalfYear` обычно принимает 1 или 2.
- Значения металлов могут быть заполнены выборочно, в зависимости от типа операции.

## Правила изменения
- Управляется через `ModMetals`.
- Не должна подменять `ProductMetalHistory` — это отдельный журнал операций.
- Изменения должны сопровождаться записью в `AuditLog`.
- После закрытия отчётного периода редактирование должно быть ограничено.

## Использование в коде
### Модули
- [[ModMetals]]

### Связанные таблицы
- [[T_Products]]
- [[T_Users]]
- [[T_ProductMetalHistory]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModMetals]] | planned |
| Read | [[ModMetals]] | planned |
| Update | [[ModMetals]] | planned |
| Delete | [[ModMetals]] | planned |

## Типовые запросы
```sql
SELECT AccountingPeriodYear, OperationType, GoldAmount, SilverAmount, PlatinumAmount, MPGAmount
FROM MetalOperations
WHERE ProductID = 1
ORDER BY OperationDate DESC;
```

## Открытые вопросы
- Нужен ли отдельный справочник `OperationType`?
- Нужна ли уникальность на уровне документа-основания?