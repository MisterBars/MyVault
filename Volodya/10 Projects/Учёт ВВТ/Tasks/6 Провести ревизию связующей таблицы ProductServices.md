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
# ## Провести ревизию связующей таблицы `ProductServices`

## Что нужно сделать
- [ ] Проверить карточку `T_ProductServices.md`.
- [ ] Явно зафиксировать M:N между `Products` и `Services`.
- [ ] Описать уникальность пары `(ProductID, ServiceID)`.
- [ ] Описать правило `IsPrimary`.
## Критерии готовности
- Карточка совпадает с v7 по полям и FK.
- В карточке зафиксировано уникальное ограничение `(ProductID, ServiceID)`.
- В карточке описано бизнес-правило основной службы изделия.
## Заметки по ходу

## Итог