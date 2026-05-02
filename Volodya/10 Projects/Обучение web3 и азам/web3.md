---
type: project
status: active
deadline: 2027-01-09
reward_xp: 100
tags:
  - project
  - skill/python
---
# ⚔️ web3

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

## Связанные задачи

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.file.link AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Важные файлы
[[Промт к ИИ]]
[[Прогресс обучения]]
## Заметки

## Итог
