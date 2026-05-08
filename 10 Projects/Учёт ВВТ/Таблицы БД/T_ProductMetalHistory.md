---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductMetalHistory
table_order: 23
domain: metals
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - metals
  - history
---

# Таблица `ProductMetalHistory`

## Назначение
Хранит историю изменений содержания драгметаллов по изделию.
Используется для фиксации корректировок, переоценок, уточнений и изменений, прошедших через workflow.

## Бизнес-смысл
Одна запись = одно событие изменения драгметаллов по одному изделию.
В записи хранится старое и новое значение по каждому металлу, основание изменения, кто изменил и кто утвердил.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MetalHistoryID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор записи истории |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| ChangeDate | DateTime | Да | Нет | Нет | — | Yes | Дата изменения |
| ChangeType | Text(30) | Да | Нет | Нет | — | No | Тип изменения |
| Reason | Text(255) | Нет | Нет | Нет | NULL | No | Причина |
| DocumentNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер документа |
| DocumentDate | DateTime | Нет | Нет | Нет | NULL | No | Дата документа |
| DocumentPath | Memo | Нет | Нет | Нет | NULL | No | Путь к документу |
| GoldOld | Double | Нет | Нет | Нет | NULL | No | Было золота, г |
| GoldNew | Double | Нет | Нет | Нет | NULL | No | Стало золота, г |
| SilverOld | Double | Нет | Нет | Нет | NULL | No | Было серебра, г |
| SilverNew | Double | Нет | Нет | Нет | NULL | No | Стало серебра, г |
| PlatinumOld | Double | Нет | Нет | Нет | NULL | No | Было платины, г |
| PlatinumNew | Double | Нет | Нет | Нет | NULL | No | Стало платины, г |
| MPGOld | Double | Нет | Нет | Нет | NULL | No | Было МПГ, г |
| MPGNew | Double | Нет | Нет | Нет | NULL | No | Стало МПГ, г |
| ChangedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто внёс изменение |
| ApprovedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто утвердил |
| ChangeRequestID | Long | Нет | Нет | Да → ChangeRequests.ChangeRequestID | NULL | No | Связь с заявкой |
| Comment | Memo | Нет | Нет | Нет | NULL | No | Комментарий |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания записи |

## Первичный ключ
- `MetalHistoryID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| ChangedByUserID | `Users.UserID` | Нет |
| ApprovedByUserID | `Users.UserID` | Нет |
| ChangeRequestID | `ChangeRequests.ChangeRequestID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXMHProdID | ProductID | Нет |
| IDXMHDate | ChangeDate | Нет |

## Правила заполнения
- `ProductID`, `ChangeDate`, `ChangeType` обязательны.
- Если изменение проходит через workflow, должен заполняться `ChangeRequestID`.
- Для корректного аудита желательно хранить и старые, и новые значения даже если меняется только один металл.

## Правила изменения
- Управляется через `ModMetals`.
- Должна создаваться одновременно с изменением значений металлов в `Products`.
- После проведения запись истории не должна редактироваться вручную.
- Дополнительно логируется через `AuditLog`.

## Использование в коде
### Модули
- [[ModMetals]]
- [[ModChangeRequests]]

### Связанные таблицы
- [[T_Products]]
- [[T_Users]]
- [[T_ChangeRequests]]
- [[T_MetalOperations]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModMetals]] | planned |
| Read | [[ModMetals]] | planned |
| Update | Обычно не предполагается | — |
| Delete | Обычно не предполагается | — |

## Типовые запросы
```sql
SELECT ChangeDate, ChangeType, GoldOld, GoldNew, SilverOld, SilverNew
FROM ProductMetalHistory
WHERE ProductID = 1
ORDER BY ChangeDate DESC;
```

## Открытые вопросы
- Нужен ли отдельный справочник `ChangeType`?
- Нужно ли хранить итоговую сумму металлов после операции отдельным полем?