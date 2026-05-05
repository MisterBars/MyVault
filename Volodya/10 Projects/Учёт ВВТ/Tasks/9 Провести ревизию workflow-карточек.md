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
# Провести ревизию workflow-карточек

## Что нужно сделать
- [ ] Проверить и заполнить:
    - [ ] `T_ChangeRequests.md
    - [ ] `T_ChangeRequestItems.md`
- [ ] В `ChangeRequests` описать статусы заявки, блокировки, согласование и применение.
- [ ] В `ChangeRequests` явно зафиксировать связь `LockToken <-> UserSessions.SessionToken`.
- [ ] В `ChangeRequestItems` описать diff-модель: `FieldName`, `FieldDataType`, `OldValue`, `NewValue`.
- [ ] Указать реальный модуль `ModChangeRequests`.
## Критерии готовности
- Обе карточки совпадают со структурой v7.
- В `T_ChangeRequests.md` отражены поля блокировок: `LockedByUserID`, `LockedAt`, `LockToken`.
- В карточках зафиксирована принадлежность к workflow и модулю `ModChangeRequests`.
- В `T_ChangeRequestItems.md` явно описано, что строки представляют изменения полей изделия.
## Заметки по ходу

## Итог