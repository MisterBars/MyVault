```dataviewjs
const root = dv.el("div", "", { cls: "reading-dashboard-root" });

function clear(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function safeNum(v, def = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
}

function fmt(v, empty = "—") {
  if (v == null || v === "") return empty;
  if (Array.isArray(v)) return v.length ? v.join(", ") : empty;
  return String(v);
}

function fmtDate(v, empty = "—") {
  if (v == null || v === "") return empty;
  try {
    const d = dv.date(v);
    return d ? d.toFormat("dd.MM.yyyy") : empty;
  } catch (e) {
    return empty;
  }
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

function statusLabel(status) {
  const map = {
    planned: "Запланировано",
    reading: "Читаю",
    done: "Прочитано",
    dropped: "Отложено"
  };
  return map[status] || status || "—";
}

function make(tag, parent, text = "", style = "") {
  const el = document.createElement(tag);
  if (text !== null && text !== undefined && text !== "") el.textContent = text;
  if (style) el.style.cssText = style;
  if (parent) parent.appendChild(el);
  return el;
}

function renderCellContent(td, value) {
  if (value instanceof HTMLElement) {
    td.appendChild(value);
  } else {
    td.textContent = value == null || value === "" ? "—" : String(value);
  }
}

function fileLinkEl(book) {
  const a = document.createElement("a");
  a.textContent = book.title;
  a.href = book.file.path;
  a.className = "internal-link";
  a.dataset.href = book.file.path;
  a.setAttribute("target", "_blank");
  a.setAttribute("rel", "noopener noreferrer");
  return a;
}

function renderHTMLTable(parent, headers, rows) {
  const wrap = make("div", parent, "", `
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--background-modifier-border);
    border-radius: 14px;
    background: var(--background-secondary);
  `);

  const table = make("table", wrap, "", `
    width: 100%;
    border-collapse: collapse;
    min-width: 760px;
  `);

  const thead = make("thead", table);
  const trHead = make("tr", thead);

  headers.forEach(h => {
    const th = make("th", trHead, h, `
      text-align: left;
      padding: 12px 14px;
      font-size: 0.9em;
      color: #82aaff;
      border-bottom: 1px solid var(--background-modifier-border);
      background: color-mix(in srgb, var(--background-secondary) 85%, black 15%);
      white-space: nowrap;
    `);
  });

  const tbody = make("tbody", table);

  if (!rows.length) {
    const tr = make("tr", tbody);
    const td = make("td", tr, "Нет данных", `
      padding: 14px;
      color: var(--text-muted);
    `);
    td.colSpan = headers.length;
    return;
  }

  rows.forEach((row, idx) => {
    const tr = make("tr", tbody, "", `
      border-bottom: ${idx === rows.length - 1 ? "none" : "1px solid var(--background-modifier-border)"};
    `);

    row.forEach(cell => {
      const td = make("td", tr, "", `
        padding: 12px 14px;
        vertical-align: top;
        color: var(--text-normal);
      `);
      renderCellContent(td, cell);
    });
  });
}

const allBooks = dv.pages()
  .where(b =>
    b.type === "book" &&
    !b.file.path.includes("90 Templates") &&
    !b.file.path.includes("40 Archives")
  )
  .map(b => ({
    file: b.file,
    title: b.file.name,
    author: b.author ?? "—",
    authorKey: b.author?.path || String(b.author || "Без автора"),
    status: String(b.status || "planned"),
    genres: Array.isArray(b.genres) ? b.genres.map(x => String(x)) : (b.genres ? [String(b.genres)] : []),
    pages: safeNum(b.pages),
    current_page: safeNum(b.current_page),
    progress: calcProgress(b),
    xp: calcXP(b),
    rating: safeNum(b.rating),
    favorite: !!b.favorite,
    start_date: b.start_date,
    done_date: b.done_date,
    cover: b.cover ? String(b.cover).trim() : ""
  }))
  .array();

const uniqueGenres = [...new Set(allBooks.flatMap(b => b.genres).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ru"));
const uniqueAuthors = [...new Set(allBooks.map(b => b.authorKey))].map(key => {
  const found = allBooks.find(b => b.authorKey === key);
  return { key, label: found?.author || "Без автора" };
}).sort((a, b) => String(a.label).localeCompare(String(b.label), "ru"));

const state = {
  view: "summary",
  status: "all",
  genre: "all",
  author: "all",
  favorite: "all"
};

function getFilteredBooks() {
  return allBooks.filter(b => {
    if (state.status !== "all" && b.status !== state.status) return false;
    if (state.genre !== "all" && !b.genres.includes(state.genre)) return false;
    if (state.author !== "all" && b.authorKey !== state.author) return false;
    if (state.favorite === "only" && !b.favorite) return false;
    return true;
  });
}

function renderStatCard(parent, label, value, color = "#7bd389") {
  const card = make("div", parent, "", `
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 14px;
    padding: 14px;
    min-height: 92px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  `);

  make("div", card, label, `
    color: var(--text-muted);
    font-size: 0.9em;
    margin-bottom: 8px;
  `);

  make("div", card, String(value), `
    font-size: 1.65em;
    font-weight: 700;
    color: ${color};
    line-height: 1.1;
  `);
}

function renderSummary(parent, books) {
  const totalBooks = books.length;
  const doneBooks = books.filter(b => b.status === "done").length;
  const readingBooks = books.filter(b => b.status === "reading").length;
  const plannedBooks = books.filter(b => b.status === "planned").length;
  const droppedBooks = books.filter(b => b.status === "dropped").length;
  const totalXP = books.reduce((s, b) => s + (b.status === "done" ? b.xp : 0), 0);
  const avgRatingBooks = books.filter(b => b.rating > 0);
  const avgRating = avgRatingBooks.length
    ? (avgRatingBooks.reduce((s, b) => s + b.rating, 0) / avgRatingBooks.length).toFixed(2)
    : "—";

  const grid = make("div", parent, "", `
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  `);

  renderStatCard(grid, "Всего книг", totalBooks, "#7bd389");
  renderStatCard(grid, "Прочитано", doneBooks, "#82aaff");
  renderStatCard(grid, "Читаю сейчас", readingBooks, "#f7c46c");
  renderStatCard(grid, "Запланировано", plannedBooks, "#c792ea");
  renderStatCard(grid, "Отложено", droppedBooks, "#ff8b94");
  renderStatCard(grid, "XP", totalXP, "#89ddff");
  renderStatCard(grid, "Средний рейтинг", avgRating, "#ffd166");

  make("div", parent, "Сейчас читаю", `
    font-size: 1.05em;
    font-weight: 700;
    margin: 12px 0;
    color: #82aaff;
  `);

  const current = books.filter(b => b.status === "reading").sort((a, b) => b.progress - a.progress).slice(0, 6);

  if (!current.length) {
    make("div", parent, "Нет книг со статусом reading.", `
      color: var(--text-muted);
      padding: 12px;
      background: var(--background-secondary);
      border: 1px solid var(--background-modifier-border);
      border-radius: 12px;
    `);
    return;
  }

  const cards = make("div", parent, "", `
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px;
  `);

  for (const b of current) {
    const card = make("div", cards, "", `
      background: var(--background-secondary);
      border: 1px solid var(--background-modifier-border);
      border-radius: 14px;
      padding: 14px;
    `);

    const top = make("div", card, "", `
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
    `);

    const left = make("div", top);
    left.appendChild(fileLinkEl(b));
    left.firstChild.style.cssText = "font-weight:700;color:#7bd389;text-decoration:none;";
    make("div", left, fmt(b.author), `font-size: 0.92em; color: var(--text-muted); margin-top: 6px;`);

    make("div", top, b.progress + "%", `
      font-weight: 700;
      color: #f7c46c;
      white-space: nowrap;
    `);

    const bar = make("div", card, "", `
      width: 100%;
      height: 10px;
      border-radius: 999px;
      background: var(--background-primary);
      border: 1px solid var(--background-modifier-border);
      overflow: hidden;
      margin: 10px 0;
    `);

    make("div", bar, "", `
      width: ${b.progress}%;
      height: 100%;
      background: linear-gradient(90deg, #7bd389, #82aaff);
    `);

    const meta = make("div", card, "", `
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 0.9em;
      color: var(--text-muted);
    `);

    make("div", meta, `Страниц: ${b.pages || "—"}`);
    make("div", meta, `Текущая: ${b.current_page || "—"}`);
    make("div", meta, `XP: ${b.xp}`);
    make("div", meta, `Рейтинг: ${b.rating || "—"}`);
  }
}

function renderView(content, books) {
  clear(content);

  if (state.view === "summary") {
    renderSummary(content, books);
    return;
  }

  if (state.view === "all") {
    const rows = books
      .slice()
      .sort((a, b) => {
        if (b.favorite !== a.favorite) return Number(b.favorite) - Number(a.favorite);
        if (b.rating !== a.rating) return b.rating - a.rating;
        return a.title.localeCompare(b.title, "ru");
      })
      .map(b => [
        fileLinkEl(b),
        fmt(b.author),
        statusLabel(b.status),
        b.genres.length ? b.genres.join(", ") : "—",
        b.progress + "%",
        b.status === "done" ? b.xp : "—",
        b.rating || "",
        b.favorite ? "★" : ""
      ]);

    renderHTMLTable(content, ["Книга", "Автор", "Статус", "Жанры", "Прогресс", "XP", "Рейтинг", "★"], rows);
    return;
  }

  if (state.view === "authors") {
    const byAuthor = {};
    for (const b of books) {
      const key = b.authorKey;
      if (!byAuthor[key]) {
        byAuthor[key] = { author: b.author, count: 0, done: 0, sumRating: 0, ratedCount: 0, totalXP: 0 };
      }
      byAuthor[key].count += 1;
      if (b.status === "done") byAuthor[key].done += 1;
      if (b.rating > 0) {
        byAuthor[key].sumRating += b.rating;
        byAuthor[key].ratedCount += 1;
      }
      if (b.status === "done") byAuthor[key].totalXP += b.xp;
    }

    const rows = Object.values(byAuthor)
      .map(a => [
        fmt(a.author),
        a.count,
        a.done,
        a.ratedCount > 0 ? (a.sumRating / a.ratedCount).toFixed(2) : "",
        a.totalXP
      ])
      .sort((a, b) => b[4] - a[4] || b[2] - a[2] || String(a[0]).localeCompare(String(b[0]), "ru"));

    renderHTMLTable(content, ["Автор", "Книг", "Прочитано", "Средний рейтинг", "XP"], rows);
    return;
  }

  if (state.view === "genres") {
    const byGenre = {};
    for (const b of books) {
      for (const g of b.genres) {
        const genre = String(g).trim();
        if (!genre) continue;
        if (!byGenre[genre]) byGenre[genre] = { genre, count: 0, done: 0, xp: 0 };
        byGenre[genre].count += 1;
        if (b.status === "done") byGenre[genre].done += 1;
        if (b.status === "done") byGenre[genre].xp += b.xp;
      }
    }

    const rows = Object.values(byGenre)
      .sort((a, b) => b.count - a.count || b.xp - a.xp)
      .map(g => [g.genre, g.count, g.done, g.xp]);

    renderHTMLTable(content, ["Жанр", "Книг", "Прочитано", "XP"], rows);
    return;
  }

  if (state.view === "reading") {
    const rows = books
      .filter(b => b.status === "reading")
      .sort((a, b) => b.progress - a.progress || a.title.localeCompare(b.title, "ru"))
      .map(b => [
        fileLinkEl(b),
        fmt(b.author),
        b.pages || "—",
        b.current_page || "—",
        b.progress + "%",
        b.xp,
        b.rating || ""
      ]);

    renderHTMLTable(content, ["Книга", "Автор", "Страниц", "Текущая", "Прогресс", "XP сейчас", "Рейтинг"], rows);
    return;
  }

  if (state.view === "done") {
    const rows = books
      .filter(b => b.status === "done")
      .sort((a, b) => {
        const da = a.done_date ? dv.date(a.done_date) : null;
        const db = b.done_date ? dv.date(b.done_date) : null;
        if (da && db) return db.ts - da.ts;
        if (db) return 1;
        if (da) return -1;
        return 0;
      })
      .map(b => [
        fileLinkEl(b),
        fmt(b.author),
        fmtDate(b.done_date),
        b.pages || "—",
        b.xp,
        b.rating || "",
        stars(b.rating),
        b.favorite ? "★" : ""
      ]);

    renderHTMLTable(content, ["Книга", "Автор", "Завершена", "Страниц", "XP", "Рейтинг", "★", "Избранное"], rows);
    return;
  }
}

function renderDashboard() {
  clear(root);

  const shell = make("div", root, "", `
    background: var(--background-primary-alt, var(--background-primary));
    border: 1px solid var(--background-modifier-border);
    border-radius: 18px;
    padding: 16px;
  `);

  make("div", shell, "Reading Dashboard", `
    font-size: 1.3em;
    font-weight: 800;
    color: #7bd389;
    margin-bottom: 14px;
  `);

  const tabBar = make("div", shell, "", `
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 14px;
  `);

  const views = [
    ["summary", "Сводка"],
    ["all", "Все книги"],
    ["authors", "Авторы"],
    ["genres", "Жанры"],
    ["reading", "Читаю сейчас"],
    ["done", "Прочитанные"]
  ];

  for (const [key, label] of views) {
    const btn = make("button", tabBar, label, `
      border: 1px solid var(--background-modifier-border);
      background: ${state.view === key ? "linear-gradient(90deg, #7bd389, #82aaff)" : "var(--background-secondary)"};
      color: ${state.view === key ? "#111" : "var(--text-normal)"};
      border-radius: 10px;
      padding: 8px 12px;
      cursor: pointer;
      font-weight: 600;
    `);

    btn.addEventListener("click", () => {
      state.view = key;
      renderDashboard();
    });
  }

  const filters = make("div", shell, "", `
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
  `);

  function addSelect(labelText, value, options, onChange) {
    const wrap = make("div", filters, "", `
      display: flex;
      flex-direction: column;
      gap: 6px;
    `);

    make("label", wrap, labelText, `
      font-size: 0.9em;
      color: var(--text-muted);
    `);

    const sel = make("select", wrap, "", `
      background: var(--background-secondary);
      color: var(--text-normal);
      border: 1px solid var(--background-modifier-border);
      border-radius: 10px;
      padding: 8px 10px;
    `);

    for (const opt of options) {
      const o = document.createElement("option");
      o.value = opt.value;
      o.textContent = opt.label;
      if (opt.value === value) o.selected = true;
      sel.appendChild(o);
    }

    sel.addEventListener("change", e => {
      onChange(e.target.value);
      renderDashboard();
    });
  }

  addSelect("Статус", state.status, [
    { value: "all", label: "Все" },
    { value: "planned", label: "Запланировано" },
    { value: "reading", label: "Читаю" },
    { value: "done", label: "Прочитано" },
    { value: "dropped", label: "Отложено" }
  ], v => state.status = v);

  addSelect("Жанр", state.genre, [
    { value: "all", label: "Все" },
    ...uniqueGenres.map(g => ({ value: g, label: g }))
  ], v => state.genre = v);

  addSelect("Автор", state.author, [
    { value: "all", label: "Все" },
    ...uniqueAuthors.map(a => ({ value: a.key, label: String(a.label) }))
  ], v => state.author = v);

  addSelect("Избранное", state.favorite, [
    { value: "all", label: "Все" },
    { value: "only", label: "Только избранное" }
  ], v => state.favorite = v);

  const actions = make("div", shell, "", `
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  `);

  const filteredBooks = getFilteredBooks();

  make("div", actions, `Найдено книг: ${filteredBooks.length}`, `
    color: var(--text-muted);
    font-size: 0.92em;
  `);

  const resetBtn = make("button", actions, "Сбросить фильтры", `
    border: 1px solid var(--background-modifier-border);
    background: var(--background-secondary);
    color: var(--text-normal);
    border-radius: 10px;
    padding: 8px 12px;
    cursor: pointer;
    font-weight: 600;
  `);

  resetBtn.addEventListener("click", () => {
    state.status = "all";
    state.genre = "all";
    state.author = "all";
    state.favorite = "all";
    renderDashboard();
  });

  const content = make("div", shell, "", `width: 100%;`);
  renderView(content, filteredBooks);
}

renderDashboard();
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

Также если необходимо указать опыт в других навыках, то указываем из в конце карточки в формате #skill/навык/03 где 03 - 30 % опыта от книги добавить к навыку.
Если нужна связь для глафа, то в блоке связей указываем ссылку на навык.

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