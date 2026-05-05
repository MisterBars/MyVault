---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductServices
table_order: 18
domain: core
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - core
  - many-to-many
---

# Таблица `ProductServices`

## Назначение
Связующая таблица M:N между изделиями и службами.
Определяет, к каким службам относится изделие, и какая служба является основной.

## Бизнес-смысл
Одна запись = одна связка «изделие + служба».
Одно изделие может быть связано с несколькими службами, но одна из них может быть отмечена как основная через `IsPrimary`.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ProductServiceID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор связки |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| ServiceID | Long | Да | Нет | Да → Services.ServiceID | — | Yes | Служба |
| IsPrimary | YesNo | Да | Нет | Нет | False | No | Основная служба |
| AssignedAt | DateTime | Нет | Нет | Нет | Now | No | Дата назначения |
| AssignedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто назначил |

## Первичный ключ
- `ProductServiceID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| ServiceID | `Services.ServiceID` | Да |
| AssignedByUserID | `Users.UserID` | Нет |

## Уникальные ограничения
- `(ProductID, ServiceID)` — одна и та же связка не должна дублироваться.

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXPSProdID | ProductID | Нет |
| IDXPSSvcID | ServiceID | Нет |

## Правила заполнения
- Пара `(ProductID, ServiceID)` обязательна и уникальна.
- `IsPrimary = True` должен быть максимум у одной службы на одно изделие.
- `AssignedAt` по умолчанию = `Now`.

## Правила изменения
- Управляется через `ModProducts`.
- При смене основной службы нужно сбрасывать `IsPrimary` у остальных связей изделия.
- Удаление связи допустимо только если это не нарушает правила видимости изделия.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModProducts]]

### Связанные таблицы
- [[T_Products]]
- [[T_Services]]
- [[T_Users]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModProducts]] | planned |
| Read | [[ModProducts]] | planned |
| Update | [[ModProducts]] | planned |
| Delete | [[ModProducts]] | planned |

## Типовые запросы
```sql
SELECT P.ProductID, S.ServiceName, PS.IsPrimary
FROM ProductServices AS PS
INNER JOIN Products AS P ON PS.ProductID = P.ProductID
INNER JOIN Services AS S ON PS.ServiceID = S.ServiceID
WHERE P.IsDeleted = False;
```

## Открытые вопросы
- Нужна ли жёсткая проверка, что у изделия всегда ровно одна основная служба?