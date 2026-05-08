# Home

# [[Памятка|Памятка по созданию записок]]

## Активные проекты

```dataview
TABLE file.folder as "Папка", deadline as "Срок", reward_xp as "Награда XP"
FROM ""
WHERE type = "project" AND status = "active" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Активные задачи

```dataview
TABLE file.folder as "Папка", skill as "Навык", task_type as "Тип", deadline as "Срок", project as "Проект"
FROM ""
WHERE type = "task" AND status = "active" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Завершённые недавно

```dataview
TABLE file.folder as "Папка", skill as "Навык", task_type as "Тип", file.mtime as "Обновлено"
FROM ""
WHERE type = "task" AND status = "done" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT file.mtime DESC
LIMIT 10
```