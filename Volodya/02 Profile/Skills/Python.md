---
type: skill
skill_id: python
title: Python
tags:
  - skill/python
---
# Python

```dataviewjs
const p = dv.current();
const xp = p.xp || 0;
const maxXp = 1000;
const pct = Math.min(Math.round((xp / maxXp) * 100), 100);
dv.paragraph(`
<div style="padding:10px; background:var(--background-secondary); border-radius:8px;">
  <b>Уровень ${p.level || 1}</b> · ${xp} XP
  <div style="background:var(--background-modifier-border); border-radius:4px; height:10px; margin-top:6px;">
    <div style="background:#4caf50; width:${pct}%; height:10px; border-radius:4px;"></div>
  </div>
  <div style="color:var(--text-muted); font-size:0.85em; margin-top:4px;">${xp} / ${maxXp} XP</div>
</div>
`);
```

## Описание

## Как качается навык
- Задачи с тегом `#skill/python`
- Сниппеты и решения задач
- Завершённые Python-проекты

## Связанные проекты

```dataview
LIST
FROM "10 Projects"
WHERE contains(file.outlinks, this.file.link)
```