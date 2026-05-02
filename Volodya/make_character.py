import os

md = open("01 Dashboard/Персонаж.md", "w", encoding="utf-8")

md.write("""---
type: character
name: Имя
class: Архитектор-разработчик
xp_total: 0
level: 1
---

# Персонаж

""")

md.write("```dataviewjs\n")
md.write("""const p = dv.current();
const xp = p.xp_total || 0;
const lvls =;[6][7]
let lv = 1;
for (let i = 0; i < lvls.length - 1; i++) { if (xp >= lvls[i]) lv = i + 1; }
const xpA = lvls[lv-1] || 0;
const xpB = lvls[lv] || 9999;
const pct = Math.round(((xp - xpA) / (xpB - xpA)) * 100);
const ranks = ["","Новичок","Ученик","Специалист","Эксперт","Мастер","Архимаг"];
const rank = ranks[Math.min(lv, ranks.length-1)];
const wrap = dv.el("div","",{});
wrap.style.cssText = "padding:12px;background:var(--background-secondary);border-radius:8px;border:1px solid var(--background-modifier-border)";
const ttl = dv.el("div","⚔️ "+(p.name||"Персонаж"),{container:wrap});
ttl.style.cssText = "font-size:1.4em;font-weight:bold;margin-bottom:4px";
const sub = dv.el("div",(p.class||"")+" · "+rank,{container:wrap});
sub.style.cssText = "color:var(--text-muted);margin-bottom:12px";
dv.el("div","🏆 Уровень "+lv+" · "+xp+" XP",{container:wrap});
const bw = dv.el("div","",{container:wrap});
bw.style.cssText = "background:var(--background-modifier-border);border-radius:4px;height:12px;margin:6px 0";
const bf = dv.el("div","",{container:bw});
bf.style.cssText = "background:#7c6bea;width:"+pct+"%;height:12px;border-radius:4px";
const inf = dv.el("div",(xp-xpA)+" / "+(xpB-xpA)+" XP до уровня "+(lv+1),{container:wrap});
inf.style.cssText = "color:var(--text-muted);font-size:0.85em";
""")
md.write("```\n\n")

md.write("## Навыки\n\n")
md.write("```dataviewjs\n")
md.write("""const skills = dv.pages('"02 Profile/Skills"').where(p => p.type === "skill");
const wrap2 = dv.el("div","",{});
wrap2.style.cssText = "padding:12px;background:var(--background-secondary);border-radius:8px;border:1px solid var(--background-modifier-border)";
const clrs = {1:"#888888",2:"#4caf50",3:"#2196f3",4:"#9c27b0",5:"#ff9800"};
for (const s of skills) {
    const xp2 = s.xp || 0;
    const lv2 = s.level || 1;
    const pct2 = Math.min(Math.round((xp2/1000)*100),100);
    const color = clrs[Math.min(lv2,5)];
    const row = dv.el("div","",{container:wrap2});
    row.style.cssText = "margin-bottom:10px";
    const lbl = dv.el("div","",{container:row});
    lbl.style.cssText = "display:flex;justify-content:space-between;margin-bottom:2px";
    dv.el("span","<b>"+(s.name||s.file.name)+"</b> · Ур."+lv2,{container:lbl});
    const xpLbl = dv.el("span",xp2+" XP",{container:lbl});
    xpLbl.style.color = "var(--text-muted)";
    const bw2 = dv.el("div","",{container:row});
    bw2.style.cssText = "background:var(--background-modifier-border);border-radius:4px;height:8px";
    const bf2 = dv.el("div","",{container:bw2});
    bf2.style.cssText = "background:"+color+";width:"+pct2+"%;height:8px;border-radius:4px";
}
""")
md.write("```\n\n")

md.write("## Активные квесты\n\n")
md.write("```dataview\n")
md.write('TABLE deadline as "Срок", reward_xp as "Награда XP"\n')
md.write('FROM "10 Projects"\n')
md.write('WHERE type = "project" AND status = "active"\n')
md.write("SORT deadline ASC\n")
md.write("```\n\n")

md.write("## Последние достижения\n\n")
md.write("```dataview\n")
md.write('TABLE date as "Дата", reward as "Награда"\n')
md.write('FROM "02 Profile/Achievements"\n')
md.write('WHERE type = "achievement"\n')
md.write("SORT date DESC\nLIMIT 5\n")
md.write("```\n")

md.close()
print("Файл создан успешно")