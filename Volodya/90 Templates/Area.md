---
type: area
status: active
---
# <% tp.file.title %>

## Что входит в эту сферу

## Постоянные обязанности

## Регулярные задачи
- [ ] Задача 1 #skill/ 🔁 every week
- [ ] Задача 2 #skill/ 🔁 every week

## Активные проекты

```dataview
TABLE status as "Статус", deadline as "Срок"
FROM ""
WHERE type = "project" AND status = "active" AND contains(file.outlinks, this.file.link) AND !contains(file.path, "90 Templates")
SORT deadline ASC
```

## Связанные ресурсы

```dataview
LIST
FROM "30 Resources"
WHERE contains(file.outlinks, this.file.link)
```

## Заметки