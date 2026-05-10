---
type: module
status: planned
done_date:
project: "[[web3]]"
phase: 3
skill:
  - solidity
domain: smart-contracts
difficulty: medium
reward_xp: 50
artifact:
tags:
  - module
  - web3
---

# Модуль: {{title}}

## Назначение
Кратко, чему учит этот модуль и зачем он нужен в проекте.

## Что нужно понять
- [ ] —
- [ ] —
- [ ] —

## Что нужно уметь руками
- [ ] —
- [ ] —
- [ ] —

## Критерий завершения
- Модуль считается закрытым, когда:
  - [ ] теория понята;
  - [ ] выполнена минимум одна практическая задача;
  - [ ] есть заметка / код / мини-артефакт;
  - [ ] могу коротко объяснить тему своими словами.

## Важные решения / заметки
- —
- —
- —

## Связанные задачи
```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок", reward_xp as "XP"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Связанные артефакты
```dataview
TABLE status as "Статус", artifact_type as "Тип", repo_url as "Repo", reward_xp as "XP"
FROM ""
WHERE type = "artifact" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT file.name ASC
```

## Связанные сессии
```dataview
TABLE date as "Дата", duration as "Длительность", xp_earned as "XP"
FROM ""
WHERE type = "study-session" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT date DESC
```

## Подтемы
- [[ ]]

## Черновые заметки