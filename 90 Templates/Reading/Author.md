---
type: author
country:
born:
died:
genres: []
tags:
  - author
cover:
aliases: []
---

# {{title}}

```dataviewjs
const a = dv.current();
const cover = a.cover;

function getCoverSrc(value) {
  if (!value) return null;

  try {
    const t = dv.func.typeof(value);

    if (t === "link" && value.path) {
      const file = app.metadataCache.getFirstLinkPathDest(value.path, "");
      if (!file) return null;
      return app.vault.getResourcePath(file);
    }

    if (t === "string") {
      const s = String(value).trim();
      if (!s) return null;

      if (/^https?:\/\//i.test(s)) {
        return s;
      }

      const file = app.metadataCache.getFirstLinkPathDest(s, "");
      if (file) {
        return app.vault.getResourcePath(file);
      }

      return s;
    }
  } catch (e) {
    return null;
  }

  return null;
}

const src = getCoverSrc(cover);

if (src) {
  const wrap = dv.el("div", "", {});
  wrap.style.cssText = "text-align:center; margin: 0 0 16px 0;";

  const img = document.createElement("img");
  img.src = src;
  img.alt = a.file.name || "Фото автора";
  img.style.cssText = `
    max-width: 220px;
    max-height: 280px;
    width: auto;
    height: auto;
    border-radius: 12px;
    object-fit: cover;
    border: 1px solid var(--background-modifier-border);
    box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    background: var(--background-secondary);
  `;

  img.onerror = () => {
    wrap.style.display = "none";
  };

  wrap.appendChild(img);
}
```
## Кратко
<p align="justify">Кто это и почему вам интересен.</p>

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