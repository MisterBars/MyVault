---
type: project
status: active
deadline: 2026-07-01
reward_xp: 500
tags:
  - project
  - python
  - ai
  - automation
skill:
  - python
  - ai
---
# ⚔️ Code Agent

## О проекте
- **Язык:** Python 3.11+
- **LLM:** Ollama (локально) — модель `qwen2.5-coder:7b` или `deepseek-coder:6.7b`
- **Оркестрация:** LangChain (ChatOllama) или прямые HTTP-запросы к `localhost:11434`
- **Запуск кода:** `subprocess.run` с таймаутом 10с — изолированный sandbox
- **Петля исправления:** агент получает stderr и пересматривает код, до 3 попыток

## Архитектура
```
User Input (строка с задачей)
       ↓
   CodeAgent.solve(task)
       ↓
   OllamaClient.ask(prompt)  →  LLM генерирует Python-код
       ↓
   CodeRunner.run(code)      →  subprocess, timeout=10s
       ↓ (stderr?)
   FixLoop (макс 3 попытки)  →  отправляем ошибку обратно в LLM
       ↓
   Возвращаем результат (stdout или финальную ошибку)
```

## Принципы
- Все взаимодействия с LLM — через `OllamaClient`, не напрямую из агента
- Единый паттерн ошибок: `try/except` + логирование в `Logger`
- `CodeRunner` не знает ничего про LLM — только принимает строку кода и возвращает `(stdout, stderr)`
- `FixLoop` — отдельный класс, не внутри агента

## Сводка проекта

```dataviewjs
const project = dv.current();
const modules = dv.pages()
  .where(x => (x.type === "module" || x.type === "class")
    && x.project && x.project.path === project.file.path
  ).array();

const totalModules = modules.length;
const doneModules = modules.filter(m => m.status === "done").length;
const pctModules = totalModules === 0 ? 0 : Math.round((doneModules / totalModules) * 100);

async function analyzeModule(page) {
  const res = { codeLines: 0, procCount: 0 };
  try {
    const text = await dv.io.load(page.file.path);
    if (!text) return res;
    const reBlock = /```python([\s\S]*?)```/g;
    let match;
    while ((match = reBlock.exec(text)) !== null) {
      const block = match[1];
      const lines = block.split("\n").filter(l => {
        const t = l.trim();
        return t.length > 0 && !t.startsWith("#");
      });
      res.codeLines += lines.length;
      const defs = block.match(/^\s*(?:async\s+)?def\s+\w+/gm) || [];
      res.procCount += defs.length;
    }
  } catch(e) {}
  return res;
}

let totalCodeLines = 0;
let totalProcs = 0;
for (const m of modules) {
  const info = await analyzeModule(m);
  totalCodeLines += info.codeLines;
  totalProcs += info.procCount;
}

const wrap = dv.el("div", "");
wrap.style.cssText = `padding:14px 18px;background:var(--background-secondary);border-radius:12px;border:1px solid var(--background-modifier-border);display:flex;flex-direction:column;gap:10px;`;
const hdr = dv.el("div", "Сводка по проекту", {container: wrap});
hdr.style.cssText = "font-size:0.95em;font-weight:600;color:var(--text-normal);";
const lbl = dv.el("div", `Модули/классы: ${doneModules} / ${totalModules} (${pctModules}%)`, {container: wrap});
lbl.style.cssText = "font-size:0.85em;color:var(--text-muted);margin-top:2px;";
const track = dv.el("div", "", {container: wrap});
track.style.cssText = "width:100%;height:10px;background:var(--background-modifier-border);border-radius:99px;overflow:hidden;";
const fill = dv.el("div", "", {container: track});
fill.style.cssText = `width:${pctModules}%;height:100%;background:linear-gradient(90deg,#4caf50,#81c784);border-radius:99px;transition:width 0.4s ease;`;
const statsRow = dv.el("div", "", {container: wrap});
statsRow.style.cssText = "display:flex;flex-direction:row;gap:8px;margin-top:8px;";
function statCard(title, value) {
  const card = dv.el("div", "", {container: statsRow});
  card.style.cssText = "flex:1;padding:8px;background:var(--background-primary);border-radius:8px;border:1px solid var(--background-modifier-border);display:flex;flex-direction:column;align-items:center;gap:4px;";
  dv.el("div", title, {container: card}).style.cssText = "font-size:0.75em;color:var(--text-muted);text-align:center;";
  dv.el("div", String(value), {container: card}).style.cssText = "font-size:1.2em;font-weight:600;color:var(--text-normal);";
}
statCard("Модулей/классов", totalModules);
statCard("Функций/методов", totalProcs);
statCard("Строк кода", totalCodeLines);
```

## Связанные модули

```dataviewjs
const current = dv.current();
const currentPath = current.file.path;
const modules = dv.pages()
  .where(p => (p.type === "module" || p.type === "class")
    && p.project && p.project.path === currentPath
    && !p.file.path.includes("90 Templates")
    && !p.file.path.includes("40 Archives")
  ).array()
  .sort((a,b) => {
    const ord = {active:0,paused:1,planned:2,done:3};
    const as = ord[a.status]??99, bs = ord[b.status]??99;
    if (as !== bs) return as-bs;
    return String(a.file.name).localeCompare(String(b.file.name),"ru");
  });
const typeLabel = t => t==="module"?"Модуль":t==="class"?"Класс":t||"—";
if (modules.length === 0) {
  dv.paragraph("Связанных модулей пока нет.");
} else {
  dv.table(["Модуль","Тип","Статус","Выполнено"],
    modules.map(m => [
      m.file.link, typeLabel(m.type), m.status||"—",
      m.done_date ? dv.date(m.done_date).toFormat("yyyy-MM-dd") : "—"
    ])
  );
}
```

## Связанные задачи

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task"
  AND project = this.file.link
  AND !contains(file.path, "90 Templates")
  AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Важные файлы
- [[10 Projects/code-agent/Модули/OllamaClient|OllamaClient — HTTP-клиент к Ollama]]
- [[10 Projects/code-agent/Классы/CodeAgent|CodeAgent — основной агент]]
- [[10 Projects/code-agent/Классы/CodeRunner|CodeRunner — запуск кода]]
- [[10 Projects/code-agent/Классы/FixLoop|FixLoop — петля исправления]]
- [[10 Projects/code-agent/Модули/Logger|Logger — логирование]]

## Заметки

## Итог
