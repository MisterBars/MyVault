---
type: project
status: active
deadline: 2027-09-01
reward_xp: 100
project_kind: learning
area:
  - web3
  - blockchain
target_role:
  - web3-backend
  - smart-contract-developer
main_stack:
  - typescript
  - solidity
  - react
  - wagmi
  - hardhat
  - ethers
  - ipfs
tags:
  - project
  - learning
  - web3
---

# ⚔️ web3

## О проекте
- **Тип проекта:** учебный RPG-проект по входу в Web3 / Blockchain Backend.  
- **Главная цель:** последовательно пройти путь от нулевой базы в blockchain до практических pet-проектов и готовности к junior/middle-позициям по web3-направлению.
- **Формат обучения:** через задачи, практику, мини-проекты, GitHub-репозитории и фиксируемый прогресс.
- **Результат на выходе:** набор освоенных модулей, 2–4 подтверждающих pet-проекта, оформленный GitHub-профиль и база заметок, из которой видно реальный прогресс.

## Принципы проекта
- Учёба идёт через **практику**, а не через абстрактное чтение.
- Каждый модуль должен завершаться либо задачей, либо артефактом, либо mini-project.
- Каждая значимая практика должна давать `reward_xp`.
- Любой крупный навык должен быть подтверждён репозиторием, заметкой, демо или разбором.
- Если тема изучена, но не применена руками — модуль не считается полностью закрытым.

## Цель
- Освоить Web3-стек для дальнейшей работы в направлениях Web3 / Blockchain Backend / On-chain analytics / DeFi tooling.

## Критерии завершения проекта
- Закрыты ключевые модули по TypeScript, Solidity, Hardhat/Foundry, ethers.js, React/Wagmi, The Graph, IPFS.
- Есть минимум 2 законченных pet-проекта.
- Есть минимум 1 проект по on-chain аналитике.
- Есть оформленные README и заметки по итогам практики.
- Есть системный прогресс по фазам и накопленный XP.

## Сводка проекта
```dataviewjs
const project = dv.current();

const items = dv.pages()
  .where(p => p.project && p.project.path === project.file.path)
  .where(p => ["module","skill","task","artifact","checkpoint","study-session"].includes(p.type))
  .array();

const modules = items.filter(p => p.type === "module");
const tasks = items.filter(p => p.type === "task");
const artifacts = items.filter(p => p.type === "artifact");
const sessions = items.filter(p => p.type === "study-session");

const doneModules = modules.filter(p => p.status === "done").length;
const doneTasks = tasks.filter(p => p.status === "done").length;
const doneArtifacts = artifacts.filter(p => p.status === "done").length;

const totalXp = items.reduce((sum, p) => sum + (Number(p.reward_xp) || 0), 0);
const earnedXp = items
  .filter(p => p.status === "done")
  .reduce((sum, p) => sum + (Number(p.reward_xp) || 0), 0);

const pctModules = modules.length === 0 ? 0 : Math.round((doneModules / modules.length) * 100);

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

const header = dv.el("div", "Сводка по проекту", { container: wrap });
header.style.cssText = "font-size:0.95em;font-weight:600;color:var(--text-normal);";

const label = dv.el("div", `Модули: ${doneModules} / ${modules.length} (${pctModules}%)`, { container: wrap });
label.style.cssText = "font-size:0.85em;color:var(--text-muted);margin-top:2px;";

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
  width: ${pctModules}%;
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #81c784);
  border-radius: 99px;
  transition: width 0.4s ease;
`;

const row = dv.el("div", "", { container: wrap });
row.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;";

function statCard(title, value) {
  const card = dv.el("div", "", { container: row });
  card.style.cssText = `
    flex: 1;
    min-width: 120px;
    padding: 8px;
    background: var(--background-primary);
    border-radius: 8px;
    border: 1px solid var(--background-modifier-border);
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:4px;
  `;
  dv.el("div", title, { container: card }).style.cssText = "font-size:0.75em;color:var(--text-muted);text-align:center;";
  dv.el("div", String(value), { container: card }).style.cssText = "font-size:1.2em;font-weight:600;color:var(--text-normal);text-align:center;";
}

statCard("Модулей", modules.length);
statCard("Задач", tasks.length);
statCard("Артефактов", artifacts.length);
statCard("Сессий", sessions.length);
statCard("XP earned", `${earnedXp} / ${totalXp}`);
```

## Текущий фокус
- Текущая фаза:
- Текущий модуль:
- Ближайший артефакт:
- Главный блокер:

## Связанные документы
- [[Промт к ИИ]]
- [[Прогресс обучения]]
- [[Схема проекта web3]]

## Активные модули
```dataview
TABLE status as "Статус", phase as "Фаза", reward_xp as "XP"
FROM ""
WHERE type = "module" AND project = this.file.link AND status != "done"
SORT phase ASC, file.name ASC
```

## Связанные задачи
```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок", reward_xp as "XP"
FROM ""
WHERE type = "task" AND project = this.file.link
SORT deadline ASC
```

## Артефакты
```dataview
TABLE status as "Статус", artifact_type as "Тип", repo_url as "Repo", reward_xp as "XP"
FROM ""
WHERE type = "artifact" AND project = this.file.link
SORT status ASC, file.name ASC
```

## Последние учебные сессии
```dataview
TABLE date as "Дата", topic as "Тема", duration as "Длительность", xp_earned as "XP"
FROM ""
WHERE type = "study-session" AND project = this.file.link
SORT date DESC
LIMIT 10
```

## Итог