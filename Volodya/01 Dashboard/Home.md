## Активные проекты
```dataview
TABLE status as "Статус", deadline as "Срок"
FROM "10 Projects"
WHERE status = "active"
SORT deadline ASC
```

# Последние измененные
```dataview
TABLE file.mtime as "Изменено"
WHERE !contains(file.path, "90 Templates")
SORT file.mtime DESC
LIMIT 10
```
