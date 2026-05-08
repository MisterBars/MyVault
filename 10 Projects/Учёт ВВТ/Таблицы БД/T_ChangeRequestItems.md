---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ChangeRequestItems
table_order: 22
domain: workflow
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - workflow
---

# Таблица `ChangeRequestItems`

## Назначение
Хранит состав изменений внутри заявки `ChangeRequests`.
Каждая запись описывает изменение одного поля: старое значение, новое значение и тип данных.

## Бизнес-смысл
Одна запись = одно изменение одного поля в рамках одной заявки.
Вместе строки формируют diff между текущим состоянием изделия и предлагаемыми изменениями.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ChangeItemID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор строки изменения |
| ChangeRequestID | Long | Да | Нет | Да → ChangeRequests.ChangeRequestID | — | Yes | Родительская заявка |
| FieldName | Text(100) | Да | Нет | Нет | — | No | Имя поля таблицы `Products` |
| FieldDataType | Text(20) | Нет | Нет | Нет | NULL | No | Тип данных поля |
| OldValue | Memo | Нет | Нет | Нет | NULL | No | Старое значение |
| NewValue | Memo | Нет | Нет | Нет | NULL | No | Новое значение |

## Первичный ключ
- `ChangeItemID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ChangeRequestID | `ChangeRequests.ChangeRequestID` | Да |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXCRICRID | ChangeRequestID | Нет |

## Правила заполнения
- `ChangeRequestID` и `FieldName` обязательны.
- `FieldName` должен соответствовать реальному полю таблицы `Products`.
- `FieldDataType` может принимать значения `Text`, `Number`, `Date`, `Boolean` и т.д.
- `OldValue` и `NewValue` хранятся текстом для универсальности.

## Правила изменения
- Управляется через `ModChangeRequests`.
- Строки заявки обычно формируются автоматически при сравнении исходных и новых значений.
- После согласования и применения изменения не должны редактироваться вручную.
- Логируется в `AuditLog`.

## Использование в коде
### Модули
- [[ModChangeRequests]]

### Связанные таблицы
- [[T_ChangeRequests]]
- [[T_Products]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModChangeRequests]] | planned |
| Read | [[ModChangeRequests]] | planned |
| Update | [[ModChangeRequests]] | planned |
| Delete | Обычно не удаляется отдельно | — |

## Типовые запросы
```sql
SELECT FieldName, FieldDataType, OldValue, NewValue
FROM ChangeRequestItems
WHERE ChangeRequestID = 1
ORDER BY ChangeItemID;
```

## Открытые вопросы
- Нужна ли защита от дублирования `FieldName` в пределах одной заявки?
- Нужно ли хранить человекочитаемый caption поля отдельно от `FieldName`?