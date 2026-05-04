---
type: author
country:
born:
died:
genres: []
tags:
  - author
aliases: []
---

# {{title}}

## Кратко
Кто это и почему вам интересен.

## Сводка по автору

```dataviewjs
const a = dv.current();
const books = dv.pages('"Volodya/20 Area/Reading/Books"')
  .where(b => b.type === "book" && b.author && String(b.author.path || b.author) === a.file.path)
  .array();

function fmt(v, empty = "—") {
  if (v == null || v === "") return empty;
  if (Array.isArray(v)) return v.length ? v.join(", ") : empty;
  return String(v);
}

function num(v, def = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
}

function calcBookXP(book) {
  const pages = num(book.pages);
  if (pages <= 0) return 0;

  const current = Math.min(num(book.current_page), pages);
  const progress = current / pages;
  const baseXP = 100;
  const sizeCoef = num(book.size_coef, 1);
  const difficultyCoef = num(book.difficulty_coef, 1);
  const finishBonus = String(book.status || "") === "done" ? num(book.finish_bonus, 0) : 0;

  return Math.round(progress * baseXP * sizeCoef * difficultyCoef + finishBonus);
}

const doneBooks = books.filter(b => String(b.status || "") === "done");
const ratedBooks = books.filter(b => num(b.rating) > 0);
const avgRating = ratedBooks.length
  ? (ratedBooks.reduce((s, b) => s + num(b.rating), 0) / ratedBooks.length).toFixed(2)
  : "—";
const totalXP = doneBooks.reduce((s, b) => s + calcBookXP(b), 0);

dv.table(
  ["Параметр", "Значение"],
  [
    ["Страна", fmt(a.country)],
    ["Дата рождения", fmt(a.born)],
    ["Дата смерти", fmt(a.died)],
    ["Жанры", fmt(a.genres)],
    ["Книг в vault", books.length],
    ["Прочитано", doneBooks.length],
    ["Средний рейтинг", avgRating],
    ["Суммарный XP", totalXP]
  ]
);
```

## Что у меня прочитано
```dataview
TABLE status AS "Статус", rating AS "Рейтинг", done_date AS "Дата", pages AS "Стр."
WHERE type = "book"
AND contains(author, this.file.link)
AND !contains(file.path, "90 Templates")
AND !contains(file.path, "40 Archives")
SORT done_date DESC
```

## Заметки
- 

## Похожие авторы
- 
## Связь
- Навык: [[Reading]]