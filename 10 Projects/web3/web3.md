---
type: project
status: active
deadline: 2028-01-01
reward_xp: 1000
tags:
  - project
  - skill/git
  - skill/python
  - skill/sql
  - skill/docker
  - skill/kubernetes
  - skill/web3
skill:
  - git
  - python
  - sql
  - docker
  - kubernetes
  - web3
area:
---
# ⚔️ web3

> Квест: освоить полный стек разработчика (Git → Python → SQL → FastAPI → K8s → Data Eng → MLOps → Web3/Blockchain) для выхода на рынок удалённой работы: Web3, iGaming, DeFi, on-chain аналитика, финтех.

## О проекте

- **Тип:** Обучение / карьерный трек
- **Горизонт:** ~19–20 месяцев при 10–15 часах/неделю
- **Первая реальная работа:** после Фаз 0–1-D (~8–9 месяцев)
- **Целевые роли:** Data Engineer (260k–500k₽), MLOps (до 550k₽), Web3 Backend, Python Backend iGaming ($5000+/мес)
- **GitHub:** https://github.com/MisterBars

## Фазы квеста

| Фаза | Название | Срок | Статус |
|------|----------|------|--------|
| **Фаза 0** | Git & GitHub | ~4 нед. | 🔲 |
| **Фаза 1-A** | Python с нуля до уверенного | ~3 мес. | 🔲 |
| **Фаза 1-B** | SQL + PostgreSQL | ~2 мес. | 🔲 |
| **Фаза 1-C** | FastAPI + REST Backend | ~1.5 мес. | 🔲 |
| **Фаза 1-D** | Docker → Kubernetes → Helm | ~1.5 мес. | 🔲 |
| **Фаза 1-E** | Data Engineering | ~2.5 мес. | 🔲 |
| **Фаза 2** | MLOps | ~5 мес. | 🔲 |
| **Фаза 3** | Web3 + TypeScript + Solidity | ~4 мес. | 🔲 |

## Сводка прогресса

```dataviewjs
const project = dv.current();

const tasks = dv.pages()
  .where(x =>
    x.type === "task" &&
    x.project &&
    x.project.path === project.file.path
  )
  .array();

const totalTasks = tasks.length;
const doneTasks = tasks.filter(t => t.status === "done").length;
const pct = totalTasks === 0 ? 0 : Math.round((doneTasks / totalTasks) * 100);

const totalXP = tasks
  .filter(t => t.status === "done")
  .reduce((sum, t) => {
    if (t.xp) return sum + Number(t.xp);
    const xpMap = { simple: 10, normal: 20, major: 40, boss: 100 };
    return sum + (xpMap[t.task_type] || 20);
  }, 0);

const wrap = dv.el("div", "", {});
wrap.style.cssText = `
  padding: 14px 18px;
  background: var(--background-secondary);
  border-radius: 12px;
  border: 1px solid var(--background-modifier-border);
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const header = dv.el("div", "Сводка по квесту", { container: wrap });
header.style.cssText = "font-size: 0.95em; font-weight: 600; color: var(--text-normal);";

const label = dv.el("div", `Задач выполнено: ${doneTasks} / ${totalTasks} (${pct}%)`, { container: wrap });
label.style.cssText = "font-size: 0.85em; color: var(--text-muted); margin-top: 2px;";

const track = dv.el("div", "", { container: wrap });
track.style.cssText = `
  width: 100%;
  height: 10px;
  background: var(--background-modifier-border);
  border-radius: 99px;
  overflow: hidden;
`;

const fill = dv.el("div", "", { container: track });
fill.style.cssText = `
  width: ${pct}%;
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #81c784);
  border-radius: 99px;
  transition: width 0.4s ease;
`;

const statsRow = dv.el("div", "", { container: wrap });
statsRow.style.cssText = "display: flex; flex-direction: row; gap: 8px; margin-top: 8px;";

function statCard(title, value) {
  const card = dv.el("div", "", { container: statsRow });
  card.style.cssText = `
    flex: 1; min-width: 0; padding: 8px;
    background: var(--background-primary);
    border-radius: 8px;
    border: 1px solid var(--background-modifier-border);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 4px;
  `;
  const t = dv.el("div", title, { container: card });
  t.style.cssText = "font-size: 0.75em; color: var(--text-muted); text-align: center;";
  const v = dv.el("div", String(value), { container: card });
  v.style.cssText = "font-size: 1.2em; font-weight: 600; color: var(--text-normal); text-align: center;";
}

statCard("Задач всего", totalTasks);
statCard("Выполнено", doneTasks);
statCard("Заработано XP", totalXP);
```

## Связанные задачи

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок", skill as "Навык"
FROM ""
WHERE type = "task" AND project = this.file.link AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Стратегия

- **Принцип:** учиться через задачи — ставишь реальную задачу → решаешь → изучаешь по ходу
- **Git с первого дня:** каждая практическая задача = коммит
- **GitHub:** равномерный contribution graph, 3–5 коммитов в неделю

## Важные файлы

1. [[10 Projects/web3/Схема проекта|Схема квеста]]
2. [[10 Projects/web3/Прогресс проекта|Трекер прогресса]]

## Заметки

## Итог