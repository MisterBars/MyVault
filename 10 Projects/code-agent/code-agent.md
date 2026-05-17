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
  - rag
  - web
skill:
  - python
  - ai
---

# ⚔️ Code Agent

## О проекте

Локальный AI-ассистент на Python с многоагентной архитектурой.

Текущая цель проекта — построить умного помощника для инженерной и проектной работы:
- planner получает задачу пользователя и разбивает её на подзадачи
- worker выполняет подзадачи
- если подзадача слишком сложная, worker может вернуть её planner'у на дополнительную декомпозицию
- результат собирается в единый ответ или цепочку действий

Проект развивается поэтапно:
1. Сначала — текстовые ответы и логика planner/worker
2. Затем — собственный веб-интерфейс и хранение бесед
3. Потом — загрузка файлов в RAG и работа с памятью
4. Далее — инструменты для файлов, git-репозиториев и веб-страниц
5. В перспективе — разделение общей памяти и проектной памяти

## Технологии

- **Язык:** Python 3.12
- **LLM:** Ollama (локально)
- **Основные модели:** `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `qwen3-coder:30b`, `deepseek-coder-v2:16b`, `my-gpu-coder:latest`
- **Embeddings / RAG:** `nomic-embed-text-v2-moe:latest`, `sleechengn/nomic-embed-text:latest`
- **Оркестрация:** сначала прямые HTTP-запросы к Ollama, позже возможен переход на более высокий orchestration layer
- **Интерфейс:** планируется собственный web UI
- **Хранение бесед:** планируется отдельный слой conversation storage
- **Инструменты:** файлы, git, web, retrieval

## Целевая архитектура

```text
User
  ↓
Web UI / CLI
  ↓
Orchestrator
  ↓
PlannerAgent
  ↓
WorkerAgent
  ↓
Tools / RAG / Memory

Если WorkerAgent понимает, что подзадача слишком сложная:
WorkerAgent → обратно в PlannerAgent → новая декомпозиция → продолжение выполнения
```

## Текущая реализация

Сейчас в проекте уже есть раннее ядро, которое полезно как foundation:
- `OllamaClient` — работа с локальным Ollama API
- `Logger` — логирование
- `CodeRunner` — безопасный запуск кода
- `FixLoop` — цикл исправления ошибок
- `CodeAgent` — ранний фасад первой версии проекта

Это не финальная архитектура, а стартовый фундамент для worker-ветки и будущих инструментов исполнения.

## Слои системы

### 1. Core
Базовая инфраструктура проекта:
- конфиг
- логирование
- клиент к LLM
- общие типы данных
- оркестратор

### 2. Agents
Основные агентные роли:
- `PlannerAgent`
- `WorkerAgent`
- позже, при необходимости: специализированные worker-подроли

### 3. Memory / RAG
Память и retrieval:
- общая база знаний
- проектная база знаний
- история бесед
- загруженные пользователем файлы
- позже — извлечённые данные из web-страниц

### 4. Tools
Инструменты, которыми пользуется worker:
- запуск Python-кода
- работа с файлами
- работа с git-репозиториями
- просмотр и анализ веб-страниц
- retrieval из RAG

### 5. Interface
Пользовательские интерфейсы:
- сначала CLI / REPL
- затем собственный веб-интерфейс
- позже возможны дополнительные интерфейсы

## Принципы

- Planner отвечает за декомпозицию, а не за выполнение действий
- Worker отвечает за выполнение подзадач, а не за глобальное планирование
- Если worker не справляется с подзадачей, он возвращает её planner'у на перепланирование
- Все обращения к LLM проходят через единый клиент
- Все внешние действия должны быть оформлены как tools / adapters
- Retrieval и память беседы — разные сущности
- Общие знания и знания по проектам должны храниться раздельно
- Веб-интерфейс развивается параллельно с backend-архитектурой
- Архитектура должна расти поэтапно, без преждевременного усложнения

## Этапы разработки

### Phase 1 — Базовая multi-agent логика
- planner принимает задачу
- worker отвечает на подзадачи
- поддержка возврата задачи на перепланирование
- пока без сложных tool-вызовов

### Phase 2 — Web UI
- чат-интерфейс
- отображение беседы
- хранение всех бесед
- разбиение по проектам / сессиям

### Phase 3 — RAG
- ручная загрузка файлов через web
- индексация документов
- retrieval для planner и worker
- разделение общей и проектной базы знаний

### Phase 4 — Tools: files + git
- чтение файлов
- простые операции с файлами
- работа с git-репозиториями
- анализ структуры проекта

### Phase 5 — Web tools
- просмотр веб-страниц
- извлечение полезной информации
- сохранение нужного контекста в RAG

### Phase 6 — Project memory
- отдельные проектные беседы
- общая память
- проектная память
- переиспользование контекста между сессиями

## Сводка проекта

```dataviewjs
const project = dv.current();
const modules = dv.pages()
  .where(x => (x.type === "module" || x.type === "class") && x.project && x.project.path === project.file.path)
  .array();

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
      const block = match;
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
  .where(p =>
    (p.type === "module" || p.type === "class") &&
    p.project &&
    p.project.path === currentPath &&
    !p.file.path.includes("90 Templates") &&
    !p.file.path.includes("40 Archives")
  )
  .array()
  .sort((a,b) => {
    const ord = {active:0, paused:1, planned:2, backlog:3, done:4};
    const as = ord[a.status] ?? 99, bs = ord[b.status] ?? 99;
    if (as !== bs) return as - bs;
    return String(a.file.name).localeCompare(String(b.file.name), "ru");
  });

const typeLabel = t => t === "module" ? "Модуль" : t === "class" ? "Класс" : t || "—";

if (modules.length === 0) {
  dv.paragraph("Связанных модулей пока нет.");
} else {
  dv.table(
    ["Модуль", "Тип", "Статус", "Выполнено"],
    modules.map(m => [
      m.file.link,
      typeLabel(m.type),
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
WHERE type = "task"
  AND project = this.file.link
  AND !contains(file.path, "90 Templates")
  AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Важные файлы

### Текущее ядро
- [[10 Projects/code-agent/Модули/OllamaClient|OllamaClient — HTTP-клиент к Ollama]]
- [[10 Projects/code-agent/Модули/Logger|Logger — логирование]]
- [[10 Projects/code-agent/Классы/CodeAgent|CodeAgent — ранний фасад первой версии]]
- [[10 Projects/code-agent/Классы/CodeRunner|CodeRunner — запуск кода]]
- [[10 Projects/code-agent/Классы/FixLoop|FixLoop — петля исправления]]

### Карточки новой архитектуры
- [[10 Projects/code-agent/Классы/PlannerAgent|PlannerAgent — декомпозиция задач]]
- [[10 Projects/code-agent/Классы/WorkerAgent|WorkerAgent — выполнение подзадач]]
- [[10 Projects/code-agent/Классы/Orchestrator|Orchestrator — координация planner/worker]]
- [[10 Projects/code-agent/Модули/ConversationStore|ConversationStore — хранение бесед]]
- [[10 Projects/code-agent/Модули/RAGService|RAGService — retrieval и память]]
- [[10 Projects/code-agent/Модули/WebUI|WebUI — пользовательский интерфейс]]

## Статус заметок
Главный файл проекта обновлён под актуальную multi-agent архитектуру.

Карточки базовой новой архитектуры уже созданы:
- PlannerAgent
- WorkerAgent
- Orchestrator
- ConversationStore
- RAGService
- WebUI

Старые заметки v1 сохраняются как foundation для worker/tools слоя.
Следующий этап — выровнять задачи под новую архитектуру и зафиксировать контракты между planner, worker и orchestrator.
## Заметки

### Текущая рабочая гипотеза
Сейчас проект движется к локальному инженерному AI-ассистенту с planner/worker архитектурой, web UI, RAG и project memory.

### Что важно не забыть
- не перегрузить первую версию
- сначала стабилизировать planner/worker ответы
- UI и backend развивать параллельно
- RAG вводить после появления нормальной структуры бесед и проектов

## Итог

Проект больше не воспринимается как просто “генератор Python-кода”.
Цель — собрать локальную платформу умного AI-помощника для работы с проектами, знаниями, файлами, git и веб-контекстом.
