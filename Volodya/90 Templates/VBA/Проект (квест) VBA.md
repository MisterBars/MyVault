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
const modules = dv.pages()
  .where(x =>
    (x.type === "module" || x.type === "form" || x.type === "class") &&
    x.project &&
    x.project.path === dv.current().file.path
  );

const totalBlocks = modules.length;
const doneBlocks = modules.where(m => m.status === "done").length;
const pctBlocks = totalBlocks === 0 ? 0 : Math.round((doneBlocks / totalBlocks) * 100);

const wrap = dv.el("div", "", {});
wrap.style.cssText = `
  padding: 10px 14px;
  background: var(--background-secondary);
  border-radius: 8px;
  border: 1px solid var(--background-modifier-border);
`;

// Текст над баром
const label = dv.el("div", `Модули/формы/классы: ${doneBlocks} / ${totalBlocks} (${pctBlocks}%)`, { container: wrap });
label.style.cssText = "margin-bottom: 6px; font-size: 0.9em; color: var(--text-muted);";

// Фон бара (серая подложка)
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
    p.type === "module" &&
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

if (modules.length === 0) {
  dv.paragraph("Связанных модулей пока нет.");
} else {
  dv.table(
    ["Модуль", "Тип модуля", "Статус", "Выполнено"],
    modules.map(m => [
      m.file.link,
      m.module_type || m.skill || "—",
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
- 

## Заметки

## Итог