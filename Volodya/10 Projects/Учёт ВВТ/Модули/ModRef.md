---
type: module
status: done
done_date: 2026-05-03
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль

## Назначение

Кратко, за что отвечает модуль, какие задачи решает.

## Важные решения

- Почему выбрана такая архитектура.
- Комментарии по производительности/ограничениям.

## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
// Какие типы считаем VBA-кодом
const TYPES = ['module', 'form', 'class'];

// Проект текущего модуля (ссылка)
const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

// Фильтруем только те страницы, у которых такой же project
// p.project может быть ссылкой или массивом ссылок, поэтому используем dv.func.contains
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject));

// === Функция: вытащить все VBA-блоки ```vba из файла ===
async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!inBlock && trimmed.startsWith('```vba')) {
      inBlock = true;
      currentBlock = [];
      continue;
    }
    if (inBlock && trimmed.startsWith('```')) {
      inBlock = false;
      blocks.push(currentBlock.join('\n'));
      currentBlock = [];
      continue;
    }
    if (inBlock) currentBlock.push(line);
  }
  return blocks;
}

// Регэксп объявления процедур / функций (как в твоём шаблоне)
const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

// Индекс: имя процедуры → список мест, где она объявлена
const procIndex = {};

for (const page of allPages) {
  const vbaBlocks = await getVbaBlocks(page.file.path);

  for (const block of vbaBlocks) {
    const lines = block.split('\n');
    for (const line of lines) {
      const m = line.match(reProcDecl);
      if (!m) continue;

      const name = m[3];

      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({
        modulePath: page.file.path,
        moduleLink: page.file.link,
        moduleType: page.type
      });
    }
  }
}

// === Анализируем текущий модуль: кто кого вызывает ===

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const rows = [];

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // пропускаем комментарии
    if (trimmed.startsWith("'")) continue;

    // новая процедура / функция
    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    // ищем вызовы
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // если не хочешь самовызовы — можно фильтрануть
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        rows.push([
          current.file.link,   // Откуда (модуль)
          currentProc,         // Какая процедура
          t.moduleLink,        // Куда (модуль)
          calledName           // Что вызывает
        ]);
      }
    }
  }
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Откуда (модуль)', 'Процедура', 'Куда (модуль)', 'Что вызывает'],
    rows
  );
}
```
# Функции и процедуры
```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);

const vbaBlocks = [];
let inBlock = false;
let current = [];

for (const line of text.split("\n")) {
  if (line.trim().startsWith("```vba")) {
    inBlock = true;
    current = [];
    continue;
  }

  if (inBlock && line.trim().startsWith("```")) {
    inBlock = false;
    vbaBlocks.push(current.join("\n"));
    current = [];
    continue;
  }

  if (inBlock) current.push(line);
}

const reDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;
const reReturnType = /\)\s*As\s+([A-Za-z0-9_\.]+)/i;
const reTag = /^'\s*@([a-zA-Z0-9_]+):\s*(.+)$/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(reDecl);
    if (!m) continue;

    const scopeRaw = m[1];
    const kindRaw = m[2];
    const name = m[3];

    const kindLower = String(kindRaw ?? "").toLowerCase();
    const kind = kindLower === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw ? String(scopeRaw) : "По умолчанию (Public)";

    let j = i;
    while (j < lines.length - 1 && lines[j].trim().endsWith("_")) {
      j++;
    }

    const signatureLines = lines.slice(i, j + 1);
    const signatureText = signatureLines.join(" ");
    const mReturn = signatureText.match(reReturnType);
    const returnType = kind === "Функция" && mReturn ? String(mReturn[1]) : "";

    const tags = {
      desc: "",
      role: "",
      todo: ""
    };

    let k = j + 1;

    while (k < lines.length) {
      const cur = lines[k].trim();

      if (cur === "") {
        k++;
        continue;
      }

      const tagMatch = cur.match(reTag);
      if (!tagMatch) break;

      const tagName = String(tagMatch[1] ?? "").toLowerCase();
      const tagValue = String(tagMatch[2] ?? "").trim();

      if (Object.prototype.hasOwnProperty.call(tags, tagName)) {
        tags[tagName] = tagValue;
      }

      k++;
    }

    rows.push([
      name,
      kind,
      scope,
      returnType,
      tags.desc,
      tags.role,
      tags.todo
    ]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(
    ["Имя", "Тип", "Область", "Возврат", "Описание", "Роль", "TODO"],
    rows
  );
}
```

# Код
```vba
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе**
' @todo: **заметка по процедуре/функции**


' === МОДУЛЬ ПОДКЛЮЧЕНИЯ БИБЛИОТЕК МОЖНО ВЫЗЫВАТЬ ИЗ ДРУГИХ НАДСТРОЕК ===
Option Explicit

Public Sub ConfigureReferencesForAddIn(targetProject As Object, Optional version As Integer)
    On Error Resume Next
    Application.EnableEvents = False
    
    ' Удаляем недействительные зависимости
    RemoveBrokenReferences targetProject
    
    ' Добавляем необходимые зависимости
    AddRequiredReferences targetProject, version
    
    Application.EnableEvents = True
    On Error GoTo 0
End Sub


Sub RemoveBrokenReferences(targetProject As Object)
    Dim i As Long
    For i = targetProject.References.Count To 1 Step -1
        If targetProject.References(i).IsBroken Then
            targetProject.References.Remove targetProject.References(i)
        End If
    Next i
End Sub

Sub AddRequiredReferences(targetProject As Object, version As Integer)
    Dim excelVersion As Integer
    excelVersion = version 'Val(Application.version)
    
    ' Списки библиотек для разных версий Excel
    Dim libraries2007 As Variant
    Dim libraries2016 As Variant
    
    ' Библиотеки для Excel 2007/2010 (Office 12.0)
    libraries2007 = Array( _
        "Microsoft ActiveX Data Objects 6.0 Library", _
        "Microsoft Office 12.0 Access database engine Object Library", _
        "Microsoft Word 12.0 Object Library", _
        "Microsoft DAO 3.6 Object Library", _
        "Excel", _
        "VBA", _
        "Office", _
        "stdole", _
        "Scripting" _
    )

    ' Библиотеки для Excel 2016 (Office 16.0)
    libraries2016 = Array( _
        "Microsoft ActiveX Data Objects 6.0 Library", _
        "Microsoft Office 16.0 Access database engine Object Library", _
        "Microsoft Word 16.0 Object Library", _
        "Microsoft DAO 3.6 Object Library", _
        "Excel", _
        "VBA", _
        "Office", _
        "stdole", _
        "Scripting" _
    )

    ' Выбираем нужный список библиотек
    Dim libraries As Variant
    If excelVersion <= 14 Then ' Excel 2007/2010
        libraries = libraries2007
    Else ' Excel 2013 и новее
        libraries = libraries2016
    End If
    
    ' Добавляем библиотеки
    Dim libName As Variant
    For Each libName In libraries
        AddReferenceByExactName targetProject, CStr(libName)
    Next libName
End Sub

Sub AddReferenceByExactName(targetProject As Object, refName As String)
    Dim ref As Object
    Dim exists As Boolean
    Dim i As Long
    
    ' Проверяем, есть ли уже такая ссылка
    exists = False
    For i = 1 To targetProject.References.Count
        If targetProject.References(i).name = refName Then
            exists = True
            Exit For
        End If
    Next i
    
    ' Если ссылки нет, пытаемся добавить
    If Not exists Then
        On Error Resume Next
        
        ' Пробуем разные способы добавления для разных типов библиотек
        Select Case refName
            ' Для ADO
            Case "Microsoft ActiveX Data Objects 6.0 Library"
                targetProject.References.AddFromFile "C:\Program Files\Common Files\System\ado\msado15.tlb"
            
            ' Для Access Database Engine
            Case "Microsoft Office 12.0 Access database engine Object Library"
                targetProject.References.AddFromFile "C:\Program Files\Common Files\microsoft shared\OFFICE12\ACEDAO.DLL"
            
            Case "Microsoft Office 16.0 Access database engine Object Library"
                targetProject.References.AddFromFile "C:\Program Files\Common Files\microsoft shared\OFFICE16\ACEDAO.DLL"
                targetProject.References.addfromguid _
                    GUID:="{4AC9E1DA-5BAD-4AC7-86E3-24F4CDCECA28}", _
                    Major:=12, _
                    Minor:=0
            
            ' Для Word
            Case "Microsoft Word 12.0 Object Library"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\Office12\MSWORD.OLB"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\root\Office12\MSWORD.OLB"
            
            Case "Microsoft Word 16.0 Object Library"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\Office16\MSWORD.OLB"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\root\Office16\MSWORD.OLB"
            ' Стандартные библиотеки
            Case "Excel"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\Office12\EXCEL.EXE"
            
            Case "VBA"
                targetProject.References.AddFromFile "C:\Program Files\Common Files\Microsoft Shared\VBA\VBA6\VBE6EXT.OLB"
            
            Case "Office"
                targetProject.References.AddFromFile "C:\Program Files\Microsoft Office\Office12\MSO.DLL"
            
            Case "stdole"
                targetProject.References.AddFromFile "C:\Windows\System32\stdole2.tlb"
            
            Case "Scripting"
                targetProject.References.AddFromFile "C:\Windows\System32\scrrun.dll"
            
'            Case "Microsoft DAO 3.6 Object Library"
'                targetProject.References.AddFromFile "C:\Program Files\Common Files\Microsoft Shared\DAO\dao360.dll"
        End Select
        
        If Err.Number <> 0 Then
            ' Если не удалось добавить по пути, пробуем найти в доступных ссылках
            For Each ref In Application.VBE.ActiveVBProject.References
                If ref.name = refName Then
                    targetProject.References.AddFromFile ref.FullPath
                    Exit For
                End If
            Next ref
        End If
        
        On Error GoTo 0
    End If
End Sub
```

## Черновые заметки

