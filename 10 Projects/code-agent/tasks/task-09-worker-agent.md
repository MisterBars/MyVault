---
type: task
task_type: architecture
status: backlog
project: "[[code-agent]]"
deadline: 2026-06-20
reward_xp: 80
phase: architecture
tags:
  - task
  - skill/python
  - skill/ai
---

# Задача: Уточнить WorkerAgent

## Что нужно сделать
- [ ] Дополнить [[10 Projects/code-agent/Классы/WorkerAgent]]
- [ ] Описать `done / failed / needs_replan`
- [ ] Описать какие tools worker может использовать в Phase 1
- [ ] Зафиксировать правила возврата ошибки
- [ ] Зафиксировать правила возврата задачи на перепланирование

## Критерий выполнения
Понятно, как worker сообщает результат, ошибку и необходимость перепланирования.