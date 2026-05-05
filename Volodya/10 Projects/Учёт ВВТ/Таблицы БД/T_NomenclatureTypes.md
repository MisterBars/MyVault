---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: NomenclatureTypes
table_order: 7
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

# Таблица `NomenclatureTypes`

## Назначение
Справочник типов номенклатуры (вид техники: связь, метрология, разведка и т.д.).
Является группировкой для таблицы `Nomenclatures`.

## Бизнес-смысл
Одна запись = один вид/тип техники.
Позволяет фильтровать и группировать номенклатуру по классу изделий.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NomenclatureTypeID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор типа |
| TypeName | Text(100) | Да | Нет | Нет | — | Unique | Наименование типа |
| TypeCode | Text(20) | Нет | Нет | Нет | NULL | Unique | Код типа (METR, SVYZ, RAZV…) |
| Description | Text(255) | Нет | Нет | Нет | NULL | No | Описание |
| IsActive | YesNo | Да | Нет | Нет | True | No | Признак активности |

## Первичный ключ
- `NomenclatureTypeID`

## Внешние ключи
Нет.

## Уникальные ограничения
- `TypeName`
- `TypeCode`

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXNomTypeCode | TypeCode | Да |

## Правила заполнения
- `TypeName` — обязателен, уникален.
- `TypeCode` — рекомендуется заполнять, уникален.
- `IsActive = False` отключает тип без удаления.

## Правила изменения
- Управляется через `ModNomenclatureTypes`.
- Удаление безопасно только если нет привязанных записей в `Nomenclatures`.
- Все изменения логируются в `AuditLog`.

## Использование в коде
### Формы
- [[F_ListsDB]] (вкладка 2)
- [[F_Change]] (вкладка 2)

### Модули
- [[ModNomenclatureTypes]]
- [[ModFillsLB]] (FillNomTypesListBox)

### Связанные таблицы
- [[T_Nomenclatures]] (Nomenclatures.NomenclatureTypeID → NomenclatureTypes.NomenclatureTypeID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModNomenclatureTypes]] | in-progress |
| Read | [[ModNomenclatureTypes]] GetAllNomenclatureTypes | in-progress |
| Update | [[ModNomenclatureTypes]] | in-progress |
| Delete | [[ModNomenclatureTypes]] (safe) | in-progress |

## Типовые запросы
```sql
SELECT * FROM NomenclatureTypes WHERE IsActive = True ORDER BY TypeName;
```

## Открытые вопросы
- Нужна ли иерархия типов (ParentTypeID)?