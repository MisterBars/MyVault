---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: Products
table_order: 17
domain: core
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - core
  - products
---

# Таблица `Products`

## Назначение
Центральная таблица системы. Хранит карточку каждого изделия ВВТ:
идентификацию, классификацию, местонахождение, документы-основания,
технические характеристики, данные по драгметаллам, статус и историю списания.

## Бизнес-смысл
Одна запись = одно изделие (единица ВВТ).
Поддерживает иерархию через `ParentProductID` (составная часть → основное изделие).
Soft-delete через `IsDeleted = True`.

---

## Поля — Идентификация

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ProductID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор изделия |
| ParentProductID | Long | Нет | Нет | Да → Products.ProductID | NULL | No | Родительское изделие (self-FK) |
| SerialNumber | Text(100) | Нет | Нет | Нет | NULL | Yes | Серийный номер |
| DecimalNumber | Text(100) | Нет | Нет | Нет | NULL | Yes | Децимальный номер |
| KVTCode | Text(50) | Нет | Нет | Нет | NULL | No | Код КВТ |
| Quantity | Double | Да | Нет | Нет | 1 | No | Количество |
| ExtNomCode | Text(100) | Нет | Нет | Нет | NULL | Yes | Внешний код номенклатуры |

## Поля — Классификация

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NomenclatureID | Long | Нет | Нет | Да → Nomenclatures | NULL | Yes | Номенклатура |
| CategoryID | Long | Нет | Нет | Да → Categories | NULL | No | Категория (I–V) |
| ExploitationTypeID | Long | Нет | Нет | Да → ExploitationTypes | NULL | No | Тип эксплуатации |
| IsOnSchedule | YesNo | Нет | Нет | Нет | NULL | No | Состоит в графике |

## Поля — Местонахождение

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LocationID | Long | Нет | Нет | Да → Locations | NULL | No | Место хранения |
| RespPersonID | Long | Нет | Нет | Да → ResponsiblePersons | NULL | Yes | МОЛ |

## Поля — Производитель и даты

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ManufacturerID | Long | Нет | Нет | Да → Manufacturers | NULL | No | Производитель |
| ManufactureYear | Integer | Нет | Нет | Нет | NULL | No | Год изготовления |
| ManufactureMonth | Integer | Нет | Нет | Нет | NULL | No | Месяц (1–12) |
| ManufactureDay | Integer | Нет | Нет | Нет | NULL | No | День (1–31) |
| ManufactureDatePrecision | Text(10) | Нет | Нет | Нет | NULL | No | Точность даты: year/month/day |
| WarrantyPeriod | Integer | Нет | Нет | Нет | NULL | No | Гарантийный срок |
| WarrantyPeriodUnit | Text(10) | Нет | Нет | Нет | NULL | No | Единица: years/months |
| WarrantyEndDate | DateTime | Нет | Нет | Нет | NULL | No | Дата окончания гарантии |
| OperationLifeYears | Integer | Нет | Нет | Нет | NULL | No | Ресурс (лет) |
| WorkHoursAsOf | DateTime | Нет | Нет | Нет | NULL | No | Дата учёта наработки |
| WorkHoursValue | Double | Нет | Нет | Нет | NULL | No | Наработка (часы) |

## Поля — Документ-основание

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DocumentTypeID | Long | Нет | Нет | Да → DocumentTypes | NULL | No | Тип документа-основания |
| AcceptanceDocNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер документа |
| AcceptanceDate | DateTime | Нет | Нет | Нет | NULL | No | Дата документа |
| InvNumberOS6 | Text(100) | Нет | Нет | Нет | NULL | Yes | Инв. номер ОС-6 |
| OS6Date | DateTime | Нет | Нет | Нет | NULL | No | Дата ОС-6 |
| CommOrderNumber | Text(50) | Нет | Нет | Нет | NULL | No | Номер приказа о вводе |
| CommissionDate | DateTime | Нет | Нет | Нет | NULL | No | Дата ввода в эксплуатацию |
| InitialCost | Currency | Нет | Нет | Нет | NULL | No | Первоначальная стоимость |

## Поля — Драгметаллы

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GoldGrams | Double | Нет | Нет | Нет | NULL | No | Золото (г) |
| SilverGrams | Double | Нет | Нет | Нет | NULL | No | Серебро (г) |
| PlatinumGrams | Double | Нет | Нет | Нет | NULL | No | Платина (г) |
| MPGGrams | Double | Нет | Нет | Нет | NULL | No | МПГ (г) |
| ZipPercent | Integer | Нет | Нет | Нет | NULL | No | ЗИП (%) |
| ZipComposition | Memo | Нет | Нет | Нет | NULL | No | Состав ЗИП |

## Поля — Статус и списание

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| StatusID | Long | Нет | Нет | Да → ProductStatuses | NULL | Yes | Статус изделия |
| StateDocPath | Memo | Нет | Нет | Нет | NULL | No | Путь к документу о состоянии |
| OwnershipStatus | Text(30) | Нет | Нет | Нет | NULL | No | Статус принадлежности |
| LastServiceDate | DateTime | Нет | Нет | Нет | NULL | No | Дата последнего ТО |
| LastServiceNote | Text(255) | Нет | Нет | Нет | NULL | No | Примечание по ТО |
| WriteOffStatus | Text(30) | Нет | Нет | Нет | NULL | No | Статус списания |
| WriteOffPlanYear | Integer | Нет | Нет | Нет | NULL | No | Плановый год списания |
| WriteOffOrdNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер приказа о списании |
| WriteOffBy | Text(255) | Нет | Нет | Нет | NULL | No | Кем списано |
| WriteOffDocPath | Memo | Нет | Нет | Нет | NULL | No | Путь к приказу о списании |
| WriteOffDate | DateTime | Нет | Нет | Нет | NULL | No | Дата списания |
| UtilizationNote | Memo | Нет | Нет | Нет | NULL | No | Примечание по утилизации |
| GeneralNote | Memo | Нет | Нет | Нет | NULL | No | Общее примечание |

## Поля — Служебные

| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |
| UpdatedAt | DateTime | Нет | Нет | Нет | NULL | No | Дата изменения |
| UpdatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто изменил |
| IsDeleted | YesNo | Да | Нет | Нет | False | Yes | Soft-delete |

---

## Первичный ключ
- `ProductID`

## Внешние ключи
| Поле | Ссылка |
| --- | --- |
| ParentProductID | `Products.ProductID` (self-FK) |
| NomenclatureID | `Nomenclatures.NomenclatureID` |
| CategoryID | `Categories.CategoryID` |
| ExploitationTypeID | `ExploitationTypes.ExploitationTypeID` |
| LocationID | `Locations.LocationID` |
| RespPersonID | `ResponsiblePersons.PersonID` |
| ManufacturerID | `Manufacturers.ManufacturerID` |
| DocumentTypeID | `DocumentTypes.DocumentTypeID` |
| StatusID | `ProductStatuses.StatusID` |
| CreatedByUserID | `Users.UserID` |
| UpdatedByUserID | `Users.UserID` |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXProdSerial | SerialNumber | Нет |
| IDXProdDecimal | DecimalNumber | Нет |
| IDXProdOS6 | InvNumberOS6 | Нет |
| IDXProdExtNom | ExtNomCode | Нет |
| IDXProdPerson | RespPersonID | Нет |
| IDXProdStatus | StatusID | Нет |
| IDXProdDeleted | IsDeleted | Нет |
| IDXProdNom | NomenclatureID | Нет |

## Правила заполнения
- `Quantity = 1` по умолчанию.
- `IsDeleted = False` по умолчанию — физически не удаляется.
- `ManufactureDatePrecision` управляет отображением даты изготовления: `year` / `month` / `day`.
- Поля драгметаллов изменяются только через workflow `ChangeRequests` или `ProductMetalHistory`.
- Поля списания заполняются только при наличии соответствующего документа.

## Правила изменения
- Создание и редактирование — `ModProducts`.
- Поля драгметаллов — только через `ModMetals` с записью в `ProductMetalHistory`.
- Изменения значимых полей — через `ChangeRequests` / `ChangeRequestItems`.
- Soft-delete через `IsDeleted = True`, не `DELETE`.
- Все изменения логируются в `AuditLog`.

## Использование в коде
### Формы
- [[F_Change]] (вкладка изделия)
- [[F_ChangeDB]]
- [[F_ListsDB]]

### Модули
- [[ModProducts]] (основной CRUD)
- [[ModMetals]] (драгметаллы)
- [[ModTransfers]] (перемещения)
- [[ModChangeRequests]] (workflow изменений)
- [[ModInventory]] (инвентаризация)
- [[ModDocuments]] (документы изделия)

### Связанные таблицы
- [[T_ProductServices]]
- [[T_ProductTransfers]]
- [[T_ChangeRequests]]
- [[T_ProductMetalHistory]]
- [[T_MetalOperations]]
- [[T_InventoryItems]]
- [[T_ProductDocuments]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModProducts]] | planned |
| Read | [[ModProducts]] | planned |
| Update | [[ModProducts]] / [[ModMetals]] / [[ModChangeRequests]] | planned |
| Delete | [[ModProducts]] soft-delete IsDeleted | planned |

## Типовые запросы
```sql
-- Активные изделия службы
SELECT P.ProductID, P.SerialNumber, N.NomenclatureName,
       L.LocationName, RP.FullName
FROM Products AS P
LEFT JOIN Nomenclatures AS N ON P.NomenclatureID = N.NomenclatureID
LEFT JOIN Locations AS L ON P.LocationID = L.LocationID
LEFT JOIN ResponsiblePersons AS RP ON P.RespPersonID = RP.PersonID
INNER JOIN ProductServices AS PS ON P.ProductID = PS.ProductID
WHERE P.IsDeleted = False AND PS.ServiceID = 1
ORDER BY N.NomenclatureName, P.SerialNumber;
```

## Открытые вопросы
- Нужен ли `ShortPurpose` (краткое назначение) — был в v6, убрать или оставить?
- Как именно отображать дату изготовлен