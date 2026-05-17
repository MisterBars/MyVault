---
type: task
task_type: architecture
status: backlog
project: "[[code-agent]]"
deadline: 2026-06-22
reward_xp: 90
phase: architecture
tags:
  - task
  - skill/python
  - skill/ai
---

# Задача: Уточнить Orchestrator

## Что нужно сделать
- [ ] Дополнить [[10 Projects/code-agent/Классы/Orchestrator]]
- [ ] Описать жизненный цикл задачи
- [ ] Описать цикл planner → worker → replan
- [ ] Зафиксировать лимит итераций
- [ ] Зафиксировать условия завершения
- [ ] Описать какие события писать в ConversationStore

## Критерий выполнения
Есть понятный жизненный цикл исполнения задачи в рамках одной беседы.