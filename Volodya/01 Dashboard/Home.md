# Home

## Активные проекты

```dataview
TABLE file.folder as "Папка", deadline as "Срок", reward_xp as "Награда XP"
FROM ""
WHERE type = "project" AND status = "active" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Активные задачи

```dataview
TABLE file.folder as "Папка", skill as "Навык", task_type as "Тип", deadline as "Срок", project as "Проект"
FROM ""
WHERE type = "task" AND status = "active" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Завершённые недавно

```dataview
TABLE file.folder as "Папка", skill as "Навык", task_type as "Тип", file.mtime as "Обновлено"
FROM ""
WHERE type = "task" AND status = "done" AND !contains(file.path, "90 Templates") AND !contains(file.path, "40 Archives")
SORT file.mtime DESC
LIMIT 10
```

## Навыки

```dataviewjs
const rewards = { simple: 10, normal: 20, major: 40, boss: 100 };
const skillNotes = dv.pages().where(x => x.type === "skill" && !x.file.path.includes("90 Templates"));

function levelFromXP(xp) {
  if (xp >= 750) return 5;
  if (xp >= 500) return 4;
  if (xp >= 250) return 3;
  if (xp >= 100) return 2;
  return 1;
}

const rows = [];

for (const s of skillNotes) {
  const id = s.skill_id;
  const tasks = dv.pages()
    .where(x =>
      x.type === "task" &&
      x.status === "done" &&
      x.skill === id &&
      !x.file.path.includes("90 Templates") &&
      !x.file.path.includes("40 Archives")
    );

  const xp = tasks.array().reduce((sum, t) => {
    if (t.xp) return sum + t.xp;
    return sum + (rewards[t.task_type || "simple"] || 10);
  }, 0);

  rows.push([s.file.link, xp, levelFromXP(xp)]);
}

dv.table(["Навык", "XP", "Уровень"], rows);
```
