```dataviewjs
const BOOK_PATH = "Volodya/20 Areas/Reading/Books";

function safeNum(v, def = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
}

function calcProgress(b) {
  const pages = safeNum(b.pages);
  const current = Math.min(safeNum(b.current_page), pages);
  if (pages <= 0) return 0;
  return Math.max(0, Math.min(100, Math.round((current / pages) * 100)));
}

function calcXP(b) {
  const pages = safeNum(b.pages);
  const current = Math.min(safeNum(b.current_page), pages);
  const sizeCoef = safeNum(b.size_coef, 1);
  const difficultyCoef = safeNum(b.difficulty_coef, 1);
  const finishBonus = String(b.status || "") === "done" ? safeNum(b.finish_bonus, 0) : 0;
  if (pages <= 0) return 0;
  const progressPart = (current / pages) * 100 * sizeCoef * difficultyCoef;
  return Math.round(progressPart + finishBonus);
}

function stars(r) {
  const n = safeNum(r);
  return n > 0 ? "★".repeat(Math.max(0, Math.min(5, n))) : "";
}

const books = dv.pages(`"${BOOK_PATH}"`)
  .where(b => b.type === "book")
  .map(b => ({
    file: b.file,
    title: b.file.name,
    author: b.author ?? "",
    status: String(b.status || "planned"),
    genres: Array.isArray(b.genres) ? b.genres : (b.genres ? [b.genres] : []),
    pages: safeNum(b.pages),
    current_page: safeNum(b.current_page),
    progress: calcProgress(b),
    xp: calcXP(b),
    rating: safeNum(b.rating),
    favorite: !!b.favorite,
    start_date: b.start_date,
    done_date: b.done_date
  }))
  .array();

dv.header(2, "Сводка");

const totalBooks = books.length;
const doneBooks = books.filter(b => b.status === "done").length;
const readingBooks = books.filter(b => b.status === "reading").length;
const plannedBooks = books.filter(b => b.status === "planned").length;
const totalXP = books.reduce((s, b) => s + (b.status === "done" ? b.xp : 0), 0);

dv.table(
  ["Показатель", "Значение"],
  [
    ["Всего книг", totalBooks],
    ["Прочитано", doneBooks],
    ["Читаю сейчас", readingBooks],
    ["Запланировано", plannedBooks],
    ["XP за завершённые книги", totalXP]
  ]
);

dv.header(2, "Все книги");

dv.table(
  ["Книга", "Автор", "Статус", "Жанры", "Прогресс", "XP", "Рейтинг", "★"],
  books
    .sort((a, b) => {
      if (b.favorite !== a.favorite) return Number(b.favorite) - Number(a.favorite);
      if (b.rating !== a.rating) return b.rating - a.rating;
      return a.title.localeCompare(b.title, "ru");
    })
    .map(b => [
      b.file.link,
      b.author,
      b.status,
      b.genres.join(", "),
      b.progress + "%",
      b.xp,
      b.rating || "",
      b.favorite ? "★" : ""
    ])
);

dv.header(2, "По авторам");

const byAuthor = {};
for (const b of books) {
  const key = b.author?.path || String(b.author || "Без автора");
  if (!byAuthor[key]) {
    byAuthor[key] = {
      author: b.author || "Без автора",
      count: 0,
      done: 0,
      avgRating: 0,
      sumRating: 0,
      totalXP: 0
    };
  }
  byAuthor[key].count += 1;
  if (b.status === "done") byAuthor[key].done += 1;
  if (b.rating > 0) byAuthor[key].sumRating += b.rating;
  if (b.status === "done") byAuthor[key].totalXP += b.xp;
}

const authorRows = Object.values(byAuthor).map(a => {
  const ratedBooks = books.filter(b => (b.author?.path || String(b.author || "Без автора")) === (a.author?.path || String(a.author))).filter(b => b.rating > 0).length;
  return [
    a.author,
    a.count,
    a.done,
    ratedBooks > 0 ? (a.sumRating / ratedBooks).toFixed(2) : "",
    a.totalXP
  ];
}).sort((a, b) => b - a);[4]

dv.table(
  ["Автор", "Книг", "Прочитано", "Средний рейтинг", "XP"],
  authorRows
);

dv.header(2, "По жанрам");

const byGenre = {};
for (const b of books) {
  for (const g of b.genres) {
    if (!byGenre[g]) byGenre[g] = { genre: g, count: 0, done: 0, xp: 0 };
    byGenre[g].count += 1;
    if (b.status === "done") byGenre[g].done += 1;
    if (b.status === "done") byGenre[g].xp += b.xp;
  }
}

dv.table(
  ["Жанр", "Книг", "Прочитано", "XP"],
  Object.values(byGenre)
    .sort((a, b) => b.count - a.count)
    .map(g => [g.genre, g.count, g.done, g.xp])
);

dv.header(2, "Читаю сейчас");

dv.table(
  ["Книга", "Автор", "Страниц", "Текущая", "Прогресс", "XP сейчас"],
  books
    .filter(b => b.status === "reading")
    .sort((a, b) => b.progress - a.progress)
    .map(b => [
      b.file.link,
      b.author,
      b.pages,
      b.current_page,
      b.progress + "%",
      b.xp
    ])
);
```

## Прочитанные книги
```dataview
TABLE author AS "Автор", genres AS "Жанры", rating AS "Рейтинг", done_date AS "Прочитано"
FROM "Volodya/20 Area/Reading/Books"
WHERE type = "book" AND status = "done"
SORT done_date DESC
```
# Инструкция по заполнению карточек книг и авторов

Ниже описано, какие поля заполнять в карточках `book` и `author`, какие из них обязательные, а какие дополнительные.

---

## Карточка книги

### Базовый шаблон

```yaml
***
type: book
status: planned
author: "[[Имя Автора]]"
title_original:
series:
year:
language: ru
format: ebook
genres: []
tags: [book]
skill: reading

pages: 0
current_page: 0
size_coef: 1.0
difficulty_coef: 1.0
finish_bonus: 30

start_date:
done_date:
rating:
favorite: false
source:
cover:
aliases: []
***
```

### Что означает каждое поле

- `type` — тип заметки. Для книги всегда `book`.
- `status` — текущий статус книги:
  - `planned` — запланирована;
  - `reading` — читается сейчас;
  - `done` — дочитана;
  - `dropped` — брошена.
- `author` — ссылка на карточку автора. Писать лучше в виде `[[Имя Автора]]`.
- `title_original` — оригинальное название книги, если нужно.
- `series` — серия или цикл, если книга входит в серию.
- `year` — год издания книги.
- `language` — язык книги, например `ru`, `en`.
- `format` — формат чтения, например:
  - `ebook`
  - `paper`
  - `audio`
- `genres` — список жанров. Заполняется списком.
- `tags` — обычные теги заметки. Для книги минимум можно держать `book`.
- `skill` — навык, в вашей системе для книг это обычно `reading`.

### Поля для расчёта прогресса и XP

- `pages` — общее количество страниц.
- `current_page` — текущая страница.
- `size_coef` — коэффициент размера книги.
- `difficulty_coef` — коэффициент сложности.
- `finish_bonus` — бонус XP за полное завершение книги.

### Поля активности

- `start_date` — дата начала чтения.
- `done_date` — дата завершения чтения.
- `rating` — личная оценка книги, например от 1 до 5.
- `favorite` — любимая книга или нет: `true` / `false`.
- `source` — откуда книга взята.
- `cover` — ссылка на обложку, если используете.
- `aliases` — альтернативные названия.

---

## Как заполнять книгу по статусам

### 1. Книга в планах

```yaml
***
type: book
status: planned
author: "[[Айзек Азимов]]"
title_original: Foundation
series: Foundation
year: 1951
language: ru
format: ebook
genres: [sci-fi]
tags: [book, sci-fi]
skill: reading

pages: 320
current_page: 0
size_coef: 1.0
difficulty_coef: 1.0
finish_bonus: 30

start_date:
done_date:
rating:
favorite: false
source: Флибуста
cover:
aliases: []
***
```

### 2. Книга читается сейчас

```yaml
***
type: book
status: reading
author: "[[Айзек Азимов]]"
title_original: Foundation
series: Foundation
year: 1951
language: ru
format: ebook
genres: [sci-fi]
tags: [book, sci-fi]
skill: reading

pages: 320
current_page: 128
size_coef: 1.0
difficulty_coef: 1.0
finish_bonus: 30

start_date: 2026-05-01
done_date:
rating:
favorite: false
source: Флибуста
cover:
aliases: []
***
```

### 3. Книга дочитана

```yaml
***
type: book
status: done
author: "[[Айзек Азимов]]"
title_original: Foundation
series: Foundation
year: 1951
language: ru
format: ebook
genres: [sci-fi]
tags: [book, sci-fi, finished]
skill: reading

pages: 320
current_page: 320
size_coef: 1.0
difficulty_coef: 1.0
finish_bonus: 30

start_date: 2026-05-01
done_date: 2026-05-10
rating: 5
favorite: true
source: Флибуста
cover:
aliases: []
***
```

### 4. Книга брошена

```yaml
***
type: book
status: dropped
author: "[[Автор]]"
title_original:
series:
year:
language: ru
format: ebook
genres: [nonfiction]
tags: [book, dropped]
skill: reading

pages: 250
current_page: 47
size_coef: 1.0
difficulty_coef: 1.2
finish_bonus: 30

start_date: 2026-05-02
done_date:
rating: 2
favorite: false
source:
cover:
aliases: []
***
```

---

## Рекомендации по коэффициентам книги

### `size_coef` — размер книги
- До 150 страниц → `0.8`
- 151–300 страниц → `1.0`
- 301–500 страниц → `1.3`
- 501–800 страниц → `1.6`
- 800+ страниц → `2.0`

### `difficulty_coef` — сложность
- Лёгкая / обычная книга → `1.0`
- Более плотная или сложная → `1.2`
- Техническая / философская / тяжёлая → `1.5`

### `finish_bonus`
- Обычно можно держать `30`
- Для очень значимых или сложных книг можно поднять до `50`

---

## Карточка автора

### Базовый шаблон

```yaml
***
type: author
country:
born:
died:
genres: []
tags: [author]
aliases: []
***
```

### Что означает каждое поле

- `type` — тип заметки. Для автора всегда `author`.
- `country` — страна автора.
- `born` — дата рождения.
- `died` — дата смерти, если есть.
- `genres` — основные жанры автора.
- `tags` — теги заметки, обычно `author`.
- `aliases` — альтернативные написания имени.

---

## Пример карточки автора

```yaml
***
type: author
country: СССР / США
born: 1920-01-02
died: 1992-04-06
genres: [sci-fi, nonfiction]
tags: [author, sci-fi]
aliases: [Азимов, Isaac Asimov]
***
```

---

## Важные правила заполнения

- Поле `author` в книге всегда лучше заполнять ссылкой: `[[Имя Автора]]`, так связи на графе и в Dataview будут работать лучше.
- Для ссылок в YAML безопаснее использовать кавычки, например `author: "[[Айзек Азимов]]"` [web:66][web:74].
- Поле `genres` лучше хранить списком, например `genres: [sci-fi, cyberpunk]`, а не одной строкой, потому что так удобнее сортировать и группировать в Dataview [web:69][web:75].
- `pages` и `current_page` должны быть числами.
- Если книга дочитана, желательно ставить:
  - `status: done`
  - `current_page = pages`
  - `done_date` заполнена
- XP вручную в книге не хранится, он 