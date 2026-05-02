## Активные проекты
```dataview
TABLE status as "Статус", deadline as "Срок"
FROM ""
WHERE type = "project" AND contains(file.path, "10 Projects") AND status = "active"
SORT deadline ASC
```

# Последние измененные
```dataview
TABLE file.mtime as "Изменено"
WHERE !contains(file.path, "90 Templates")
SORT file.mtime DESC
LIMIT 10
```
