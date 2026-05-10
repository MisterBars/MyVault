---
type: phase
status: locked
project: "[[10 Projects/web3/web3]]"
phase_id: phase0
phase_name: Git & GitHub
phase_emoji: ⚙️
duration_weeks: 4
skill:
  - git
tags:
  - web3
  - phase0
started: 2026-05-10
completed:
---
# ⚙️ Фаза 0 — Git & GitHub

> Стартовая фаза всего квеста: научиться уверенно работать с Git и GitHub так, чтобы любое дальнейшее обучение сразу оформлялось в репозитории, коммитах, ветках и понятной истории изменений.

## Зачем нужна эта фаза

- Понять, как хранить и версионировать свои проекты без хаоса.
- Привыкнуть к GitHub как к основной рабочей площадке.
- Построить базу под все следующие фазы: Python, SQL, FastAPI, Kubernetes и Web3.

## Результат фазы

После завершения фазы я умею:

- Создавать и вести локальные Git-репозитории.
- Работать с коммитами, ветками, merge/rebase.
- Понимать и решать merge conflicts.
- Оформлять GitHub-профиль и README репозиториев.
- Работать через Issues, Pull Requests и базовый CI через GitHub Actions.

## Прогресс модулей

```dataview
TABLE status as "Статус", task_type as "Тип", xp as "XP", deadline as "Срок"
FROM "10 Projects/web3/Модули"
WHERE type = "task"
  AND contains(tags, "phase0")
SORT file.name ASC
```

## XP по фазе

```dataviewjs
const tasks = dv.pages('"10 Projects/web3/Модули"')
  .where(x => x.type === "task" && x.tags && x.tags.includes("phase0"))
  .array();

const total = tasks.length;
const done = tasks.filter(t => t.status === "done");
const doneCount = done.length;

const xpMap = { simple: 10, normal: 20, major: 40, boss: 100 };
const earnedXP = done.reduce((sum, t) => sum + (Number(t.xp) || xpMap[t.task_type] || 20), 0);
const pct = total === 0 ? 0 : Math.round((doneCount / total) * 100);

dv.paragraph(`Прогресс: ${doneCount}/${total} (${pct}%)`);
dv.paragraph(`Заработано XP: ${earnedXP}`);
```

## Модули фазы

- [[10 Projects/web3/Модули/0.1 Что такое Git]]
- [[10 Projects/web3/Модули/0.2 Базовые команды Git]]
- [[10 Projects/web3/Модули/0.3 Удалённый репозиторий и GitHub]]
- [[10 Projects/web3/Модули/0.4 Ветки и merge conflicts]]
- [[10 Projects/web3/Модули/0.5 rebase stash cherry-pick]]
- [[10 Projects/web3/Модули/0.6 gitignore и gitattributes]]
- [[10 Projects/web3/Модули/0.7 Conventional Commits]]
- [[10 Projects/web3/Модули/0.8 GitHub профиль и README]]
- [[10 Projects/web3/Модули/0.9 Оформление репозиториев]]
- [[10 Projects/web3/Модули/0.10 Pull Requests Issues Code Review]]
- [[10 Projects/web3/Модули/0.11 GitHub Actions базовый CI-CD]]

## Артефакты фазы

- Минимум 1 учебный репозиторий для практики.
- Оформленный GitHub-профиль.
- Несколько репозиториев с нормальным README.
- Один workflow в GitHub Actions.

## Итог фазы

> Заполняется после завершения: что усвоил, где были сложности, что надо повторить перед переходом в Python.