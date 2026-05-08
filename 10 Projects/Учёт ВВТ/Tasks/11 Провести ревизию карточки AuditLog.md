---
type: task
status: active
done_date:
skill:
  - vba
task_type: normal
project: "[[Учёт ВВТ]]"
deadline:
tags:
  - task
---
# Провести ревизию карточки `AuditLog`

## Что нужно сделать
- [ ] Проверить и заполнить `T_AuditLog.md`.
- [ ] Описать аудит CRUD-изменений и бизнес-событий.
- [ ] Зафиксировать поля `TableName`, `RecordID`, `FieldName`, `OldValue`, `NewValue`, `ActionType`, `BusinessEventType`, `ChangedByUserID`, `ChangedAt`, `ChangeRequestID`, `WorkstationName`.
- [ ] Указать `ModAudit` как основной модуль.
- [ ] Добавить правило, какие изменения должны обязательно логироваться.
## Критерии готовности
- Карточка совпадает с v7 по полям и FK.
- В карточке описан смысл `ActionType` и `BusinessEventType`.
- В карточке указано, что `WriteAuditEvent` используется как единая точка записи аудита.
- В карточке отражены индексы `IDXALTable`, `IDXALRecordID`, `IDXALDate`, `IDXALCRID`.
## Заметки по ходу

## Итог