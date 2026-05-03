---
project:
type: db-table
table: Products
version:
source:
---

# Products

Назначение: … (1–2 предложения)

## Метаданные

- Физическое имя: `_`
- Название по-русски: "Изделия"
- Схема: (если нужна)
- Основной ключ: `_` (AUTOINCREMENT)
- Soft delete: `IsDeleted` (Yes/No, Default False)
- Audit: `AuditLog` по TableName = `_`

## Поля

| Поле | Тип | Ограничения | Описание |
| ---- | --- | ----------- | -------- |

## Индексы

| Имя индекса | Поля | Назначение |
| ----------- | ---- | ---------- |

## Связи

Пример
- FK → `Users(UserID)` по полям: `CreatedByUserID`, `UpdatedByUserID`.
- FK → `Nomenclatures(NomenclatureID)` по `NomenclatureID`.
- FK → `ProductStatuses(StatusID)` по `StatusID`.
- FK ← используется в:
  - `ProductServices(ProductID)`
  - `InventoryItems(ProductID)`
  - `ProductTransfers(ProductID)`
  - `ProductMetalHistory(ProductID)`
  - `MetalOperations(ProductID)`
  - `ProductDocuments(ProductID)`
  - `ChangeRequests(ProductID)`

## Примечания по бизнес-логике

Пример
- `IsDeleted = True` — запись не показывается в основной отчётности, но остаётся для истории и связей.
- При изменениях металлов обязательно создавать запись в `ProductMetalHistory` и `MetalOperations`.
- Для всех операций, меняющих `Products`, логируется запись в `AuditLog` с `TableName = "Products"`.

---

## Как использовать шаблон

1. **Один файл на таблицу**:  
   `db_tables/01_Roles.md`, `db_tables/02_Services.md`, … `db_tables/27_ProductDocuments.md`.

2. В каждом:
   - фронтматтер: `table`, `project`, `version`, `source`;
   - блоки: `Назначение`, `Метаданные`, `Поля` (таблица), `Индексы`, `Связи`, `Примечания`.

3. Твой общий документ `db_schema_vvt_v7_tables.md` можно либо:
   - оставить как “обзор” и линковать оттуда на отдельные файлы таблиц;
   - либо собирать его в Obsidian через Dataview/templater из отдельных таблиц.

Так ты получаешь:

- строгий формат (легко машинно читать/парсить);
- возможность запускать DataviewJS‑чекеры:
  - “есть ли у каждой таблицы PK/CreatedAt/IsDeleted, где это нужно”;
  - “все FK, которые упомянуты в ModCreateDB, присутствуют в описании”;
- удобство чтения: любой модуль/форма может линкануться на конкретную таблицу, а не листать полотнище. [web:443][web:494]

Если хочешь, могу следующим сообщением набросать конкретный Templater‑шаблон, который по имени таблицы и списку полей (в YAML/JSON) сам развернёт такую карточку.