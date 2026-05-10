---
type: project
status: active
deadline: 2027-03-01
reward_xp: 500
tags:
  - project
skill:
  - typescript
  - solidity
  - web3
  - react
area:
---
# 🔗 web3

## О проекте

Обучающий квест — освоить полный Web3-стек для выхода на рынок удалённой работы (Web3 / Blockchain Backend, DeFi, on-chain аналитика).

Стек включает:
- **TypeScript** — основной язык фазы
- **Solidity** — смарт-контракты на EVM
- **React + Wagmi + WalletConnect** — DApp-фронтенд
- **ethers.js / web3.py** — взаимодействие с сетью
- **Hardhat** — компиляция, тесты, деплой
- **The Graph** — индексация on-chain событий
- **IPFS / Arweave / Ceramic / OrbitDB** — децентрализованные хранилища
- **Node.js + Fastify** — бэкенд-API на TypeScript
- **PostgreSQL + Redis** — классические слои хранения

> ⚡ Фаза 3 стартует после завершения Фаз 0–2. Расчётный старт: ~через 14 мес. от начала обучения.
> Срок фазы: ~4 месяца при 10–15 ч/неделю.

## Цель

Получить навыки для вакансий **Web3 / Blockchain Backend** (TypeScript + Solidity + React + децентрализованные БД) и **DeFi/on-chain аналитики**. Собрать два полноценных пет-проекта в портфолио на GitHub.

## Пет-проекты фазы

| # | Проект | Стек | Статус |
|---|--------|------|--------|
| 🎯 1 | On-chain аналитика: пайплайн + REST API + дашборд | ethers.js, PostgreSQL, FastAPI/Fastify, React | 🔲 |
| 🎯 2 | Web3 DApp — ERC-721 смарт-контракт + React + IPFS | Solidity, Hardhat, React, Wagmi, IPFS/Pinata | 🔲 |

## Пререквизиты

Перед стартом Фазы 3 должны быть завершены:
- ✅ Фаза 0 — Git & GitHub
- ✅ Фаза 1-A — Python
- ✅ Фаза 1-B — SQL / PostgreSQL
- ✅ Фаза 1-C — FastAPI + REST
- ✅ Фаза 1-D — Docker → K8s → Helm
- ✅ Фаза 1-E — Data Engineering
- ✅ Фаза 2 — MLOps

## Сводка прогресса

```dataviewjs
const project = dv.current();

const lessons = dv.pages()
  .where(x =>
    x.type === "lesson" &&
    x.project &&
    x.project.path === project.file.path
  )
  .array();

const total = lessons.length;
const done = lessons.filter(m => m.status === "done").length;
const pct = total === 0 ? 0 : Math.round((done / total) * 100);

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

const header = dv.el("div", "Прогресс обучения", { container: wrap });
header.style.cssText = `font-size: 0.95em; font-weight: 600; color: var(--text-normal);`;

const label = dv.el("div", `Уроков пройдено: ${done} / ${total} (${pct}%)`, { container: wrap });
label.style.cssText = `font-size: 0.85em; color: var(--text-muted); margin-top: 2px;`;

const track = dv.el("div", "", { container: wrap });
track.style.cssText = `width: 100%; height: 10px; background: var(--background-modifier-border); border-radius: 99px; overflow: hidden;`;

const fill = dv.el("div", "", { container: track });
fill.style.cssText = `
  width: ${pct}%;
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #81c784);
  border-radius: 99px;
  transition: width 0.4s ease;
`;

const statsRow = dv.el("div", "", { container: wrap });
statsRow.style.cssText = `display: flex; flex-direction: row; gap: 8px; margin-top: 8px;`;

function statCard(title, value) {
  const card = dv.el("div", "", { container: statsRow });
  card.style.cssText = `
    flex: 1; min-width: 0; padding: 8px;
    background: var(--background-primary);
    border-radius: 8px;
    border: 1px solid var(--background-modifier-border);
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
  `;
  const t = dv.el("div", title, { container: card });
  t.style.cssText = `font-size: 0.75em; color: var(--text-muted); text-align: center;`;
  const v = dv.el("div", String(value), { container: card });
  v.style.cssText = `font-size: 1.2em; font-weight: 600; color: var(--text-normal); text-align: center;`;
}

const totalXP = lessons.filter(m => m.status === "done").reduce((sum, m) => sum + (m.reward_xp || 0), 0);
const phases = [...new Set(lessons.map(m => m.phase).filter(Boolean))];

statCard("Уроков всего", total);
statCard("Пройдено", done);
statCard("XP заработано", totalXP);
```

## Связанные уроки

```dataviewjs
const project = dv.current();

const lessons = dv.pages()
  .where(x =>
    x.type === "lesson" &&
    x.project &&
    x.project.path === project.file.path &&
    !x.file.path.includes("90 Templates") &&
    !x.file.path.includes("40 Archives")
  )
  .array()
  .sort((a, b) => {
    const phaseA = String(a.phase || "");
    const phaseB = String(b.phase || "");
    if (phaseA !== phaseB) return phaseA.localeCompare(phaseB);
    return (a.module_num || 0) - (b.module_num || 0);
  });

if (lessons.length === 0) {
  dv.paragraph("Уроки ещё не созданы.");
} else {
  dv.table(
    ["Урок", "Фаза", "Статус", "XP", "Дата"],
    lessons.map(m => [
      m.file.link,
      m.phase || "—",
      m.status || "—",
      m.reward_xp || "—",
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
1. [[10 Projects/web3/Схема проекта|🗺️ Схема проекта]]
2. [[10 Projects/web3/Прогресс проекта|📊 Прогресс обучения]]

## Заметки

## Итог
