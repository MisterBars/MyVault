---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: Nomenclatures
table_order: 8
domain: reference
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - reference
  - nomenclature
---

# Таблица `Nomenclatures`

## Назначение
Справочник номенклатурных позиций (конкретных наименований изделий).
Каждая запись — один тип изделия с кодом и наименованием.
Привязывается к `Products.NomenclatureID`.

## Бизнес-смысл
Одна запись = одна номенклатурная единица (например: «Р-168-5УН», «Р-187»).
Позволяет унифицировать наименования изделий вместо свободного ввода.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NomenclatureID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор позиции |
| NomenclatureTypeID | Long | Да | Нет | Да → NomenclatureTypes | — | Yes | Тип номенклатуры |
| NomenclatureCode | Text(50) | Да | Нет | Нет | — | No | Код номенклатуры |
| NomenclatureName | Text(255) | Нет | Нет | Нет | NULL | No | Наименование |
| Description | Memo | Нет | Нет | Нет | NULL | No | Описание |

## Первичный ключ
- `NomenclatureID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| NomenclatureTypeID | `NomenclatureTypes.NomenclatureTypeID` | Да |

## Уникальные ограничения
Нет (NomenclatureCode не уникален принудительно — разные типы могут иметь одинаковый код).

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXNomTypeID | NomenclatureTypeID | Нет |

## Правила заполнения
- `NomenclatureCode` — обязателен.
- `NomenclatureTypeID` — обязателен, выбирается из `NomenclatureTypes`.
- `Products.ExtNomCode` хранит внешний код привязки — соответствует `NomenclatureCode`.

## Правила изменения
- Управляется через `ModNomenclatures`.
- Удаление безопасно только если нет привязанных записей в `Products`.
- Все изменения логируются в `AuditLog`.

## Использование в коде
### Формы
- [[F_ListsDB]] (вкладка 3)
- [[F_Change]] (вкладка 3)

### Модули
- [[ModNomenclatures]]
- [[ModFillsLB]] (FillNomListBox)

### Связанные таблицы
- [[T_NomenclatureTypes]]
- [[T_Products]] (Products.NomenclatureID → Nomenclatures.NomenclatureID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModNomenclatures]] | in-progress |
| Read | [[ModNomenclatures]] GetAllNomenclatures | in-progress |
| Update | [[ModNomenclatures]] | in-progress |
| Delete | [[ModNomenclatures]] (safe) | in-progress |

## Типовые запросы
```sql
SELECT N.NomenclatureCode, N.NomenclatureName, T.TypeName
FROM Nomenclatures AS N
INNER JOIN NomenclatureTypes AS T ON N.NomenclatureTypeID = T.NomenclatureTypeID
ORDER BY T.TypeName, N.NomenclatureCode;
```

## Открытые вопросы
- Нужна ли уникальность пары `(NomenclatureTypeID, NomenclatureCode)`?
- Нужен ли флаг `IsActive`?