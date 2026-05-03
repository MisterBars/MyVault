---
type: project
status: active
deadline: 
reward_xp: 100
tags:
  - project
---
# ⚔️ <% tp.file.title %>

## Цель

## Результат
```dataviewjs
const project = dv.current();

const modules = dv.pages()
  .where(x =>
    (x.type === "module" || x.type === "form" || x.type === "class") &&
    x.project &&
    x.project.path === project.file.path
  )
  .array();

const totalBlocks = modules.length;
const doneBlocks = modules.filter(m => m.status === "done").length;
const pctBlocks = totalBlocks === 0 ? 0 : Math.round((doneBlocks / totalBlocks) * 100);

// список служебных строк, которые не считаем как "код"
const SERVICE_LINES = [
  /^Option\s+Explicit$/i,
  /^Option\s+Compare\s+Database$/i,
  /^Option\s+Compare\s+Text$/i,
  /^Option\s+Compare\s+Binary$/i,
  /^Attribute\s+VB\_/i
];

function isServiceLine(line) {
  for (const re of SERVICE_LINES) {
    if (re.test(line)) return true;
  }
  return false;
}

async function countCodeLinesForPage(page) {
  try {
    const text = await dv.io.load(page.file.path);
    if (!text) return 0;

    const lines = text.split("\n");

    let count = 0;

    for (const raw of lines) {
      const line = raw.trim();

      // пустые строки
      if (line.length === 0) continue;

      // комментарии: ' ... или Rem ...
      if (line.startsWith("'")) continue;
      if (/^Rem\b/i.test(line)) continue;

      // служебные директивы/атрибуты
      if (isServiceLine(line)) continue;

      count++;
    }

    return count;
  } catch (e) {
    console.error("Ошибка при подсчёте строк кода для", page.file.path, e);
    return 0;
  }
}

let totalCodeLines = 0;

for (const m of modules) {
  totalCodeLines += await countCodeLinesForPage(m);
}

const wrap = dv.el("div", "", {});
wrap.style.cssText = `
  padding: 10px 14px;
  background: var(--background-secondary);
  border-radius: 8px;
  border: 1px solid var(--background-modifier-border);
`;

// Текст над баром
const label = dv.el(
  "div",
  `Модули/формы/классы: ${doneBlocks} / ${totalBlocks} (${pctBlocks}%)`,
  { container: wrap }
);
label.style.cssText = "margin-bottom: 6px; font-size: 0.9em; color: var(--text-muted);";

// Фон бара
const track = dv.el("div", "", { container: wrap });
track.style.cssText = `
  width: 100%;
  height: 10px;
  background: var(--background-modifier-border);
  border-radius: 99px;
  overflow: hidden;
`;

// Заполненная часть
const fill = dv.el("div", "", { container: track });
fill.style.cssText = `
  width: ${pctBlocks}%;
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #81c784);
  border-radius: 99px;
  transition: width 0.4s ease;
`;

// Строки кода
const linesLabel = dv.el(
  "div",
  `Строк кода во всех модулях: ${totalCodeLines}`,
  { container: wrap }
);
linesLabel.style.cssText =
  "margin-top: 8px; font-size: 0.9em; color: var(--text-muted);";
```

## Связанные модули
```dataviewjs
const current = dv.current();
const currentPath = current.file.path;
const currentName = current.file.name;
const currentWiki = `[[${currentName}]]`;

function projectMatches(value) {
  if (!value) return false;

  if (Array.isArray(value)) {
    return value.some(v => projectMatches(v));
  }

  if (typeof value === "string") {
    return value === currentWiki || value === currentName;
  }

  if (value.path) {
    return value.path === currentPath;
  }

  return false;
}

const modules = dv.pages()
  .where(p =>
    (p.type === "module" || p.type === "form" || p.type === "class") &&
    projectMatches(p.project) &&
    !p.file.path.includes("90 Templates") &&
    !p.file.path.includes("40 Archives")
  )
  .array()
  .sort((a, b) => {
    const statusOrder = { active: 0, paused: 1, planned: 2, done: 3 };
    const as = statusOrder[a.status] ?? 99;
    const bs = statusOrder[b.status] ?? 99;
    if (as !== bs) return as - bs;

    const ad = a.done_date ? dv.date(a.done_date).ts : Infinity;
    const bd = b.done_date ? dv.date(b.done_date).ts : Infinity;
    if (ad !== bd) return ad - bd;

    return String(a.file.name).localeCompare(String(b.file.name), "ru");
  });

function prettyModuleType(t) {
  if (!t) return "—";
  const v = String(t).toLowerCase();
  if (v === "module") return "Модуль";
  if (v === "form") return "Форма";
  if (v === "class") return "Класс";
  return t;
}

if (modules.length === 0) {
  dv.paragraph("Связанных модулей пока нет.");
} else {
  dv.table(
    ["Модуль", "Тип модуля", "Статус", "Выполнено"],
    modules.map(m => [
      m.file.link,
      prettyModuleType(m.type),
      m.status || "—",
      m.done_date ? dv.date(m.done_date).toFormat("yyyy-MM-dd") : "—"
    ])
  );
}
```

## Связанные задачи
```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.file.link AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Важные файлы
- 1
- 2
## Заметки

## Итог