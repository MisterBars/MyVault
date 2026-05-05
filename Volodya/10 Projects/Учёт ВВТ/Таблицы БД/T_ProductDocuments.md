---
type: db-table
status: planned
project: "[[Учёт ВВТ]]"
table_name: ProductDocuments
table_order: 27
domain: documents
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - documents
  - archive
---

# Таблица `ProductDocuments`

## Назначение
Хранит документы, относящиеся к изделию: паспорт, формуляр, инструкции, акты, удостоверения и прочие архивные вложения.
Связывает изделие, тип документа и при необходимости архивное дело. 

## Бизнес-смысл
Одна запись = один документ, относящийся к одному изделию.
Документ может существовать как файл по пути `FilePath`, а также иметь привязку к физическому архивному делу и странице. 

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DocumentID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор документа |
| ProductID | Long | Да | Нет | Да → Products.ProductID | — | Yes | Изделие |
| DocumentTypeID | Long | Да | Нет | Да → ProductDocTypes.DocumentTypeID | — | Yes | Тип документа |
| DocumentNumber | Text(100) | Нет | Нет | Нет | NULL | No | Номер документа |
| DocumentDate | DateTime | Нет | Нет | Нет | NULL | Yes | Дата документа |
| DocumentTitle | Text(255) | Нет | Нет | Нет | NULL | No | Заголовок |
| IssuedBy | Text(255) | Нет | Нет | Нет | NULL | No | Кем выдан |
| ReceivedDate | DateTime | Нет | Нет | Нет | NULL | No | Когда получен |
| ValidUntil | DateTime | Нет | Нет | Нет | NULL | No | Действителен до |
| FilePath | Memo | Нет | Нет | Нет | NULL | No | Путь к файлу |
| Description | Memo | Нет | Нет | Нет | NULL | No | Описание |
| Comment | Memo | Нет | Нет | Нет | NULL | No | Комментарий |
| ArchiveCaseID | Long | Нет | Нет | Да → ArchiveCases.CaseID | NULL | Yes | Архивное дело |
| ArchivePage | Text(50) | Нет | Нет | Нет | NULL | No | Страница / лист дела |
| CreatedByUserID | Long | Нет | Нет | Да → Users.UserID | NULL | No | Кто создал |
| CreatedAt | DateTime | Да | Нет | Нет | Now | No | Дата создания записи |

## Первичный ключ
- `DocumentID`

## Внешние ключи
| Поле | Ссылка | Обязательность |
| --- | --- | --- |
| ProductID | `Products.ProductID` | Да |
| DocumentTypeID | `ProductDocTypes.DocumentTypeID` | Да |
| ArchiveCaseID | `ArchiveCases.CaseID` | Нет |
| CreatedByUserID | `Users.UserID` | Нет |

## Индексы
| Имя | Поля | Unique |
| --- | --- | --- |
| IDXPDProdID | ProductID | Нет |
| IDXPDDType | DocumentTypeID | Нет |
| IDXPDDate | DocumentDate | Нет |
| IDXPDArchive | ArchiveCaseID | Нет |

## Правила заполнения
- `ProductID` и `DocumentTypeID` обязательны. 
- `FilePath` может быть `NULL`, если документ пока описан только как бумажный архивный экземпляр. 
- `ArchiveCaseID` и `ArchivePage` используются для связи с физическим архивом. 
- Не путать `DocumentTypeID` этой таблицы с `DocumentTypes` из `Products`: здесь ссылка идёт на `ProductDocTypes`. 

## Правила изменения
- Управляется через `ModDocuments`, который по прогрессу отвечает за `ProductDocuments`, `ArchiveCases`, `ProductDocTypes`. 
- При удалении или смене типа документа нужно проверять целостность ссылок на файл и архивное дело. 
- Изменения должны логироваться в `AuditLog`. 

## Использование в коде
### Модули
- [[ModDocuments]]

### Связанные таблицы
- [[T_Products]]
- [[T_ProductDocTypes]]
- [[T_ArchiveCases]]
- [[T_Users]]

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModDocuments]] | planned |
| Read | [[ModDocuments]] | planned |
| Update | [[ModDocuments]] | planned |
| Delete | [[ModDocuments]] | planned |

## Типовые запросы
```sql
SELECT D.DocumentDate, T.TypeName, D.DocumentNumber, D.DocumentTitle, D.FilePath
FROM ProductDocuments AS D
INNER JOIN ProductDocTypes AS T ON D.DocumentTypeID = T.DocumentTypeID
WHERE D.ProductID = 1
ORDER BY D.DocumentDate DESC;
```

## Открытые вопросы
- Нужен ли флаг `IsOriginal / IsCopy`?
- Нужно ли хранить размер файла, расширение и контрольную сумму отдельно от `FilePath`?