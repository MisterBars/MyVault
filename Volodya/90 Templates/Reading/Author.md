---
type: author
country:
born:
died:
genres: []
tags: [author]
aliases: []
---

# {{title}}

## Кратко
Кто это и почему вам интересен.

## Основное
- Страна:
- Дата рождения:
- Дата смерти:
- Жанры:

## Что у меня прочитано
```dataview
TABLE status AS "Статус", rating AS "Рейтинг", done_date AS "Дата", pages AS "Стр."
FROM "Volodya/20 Area/Reading/Books"
WHERE author = this.file.link
SORT done_date DESC
```

## Заметки
- 

## Похожие авторы
- 