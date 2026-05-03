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
- Для заполнения ListBox'ов в формах

## Важные решения
- Удобно не переполнять код форм

## Задачи по модулю
```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)
```dataviewjs
const TYPES = ['module', 'form', 'class'];

const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject))
  .array();

// Диагностика — сохраняем, но не показываем
const debugModulesCount = allPages.length;

async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();

    if (!inBlock && trimmed.toLowerCase().startsWith('```vba')) {
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

const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

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

// Диагностика — сохраняем, но не показываем
const debugProcNames = Object.keys(procIndex);
const debugProcCount = debugProcNames.length;

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("'")) continue;

    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        const key = `${currentProc}||${t.modulePath}`;
        if (!callMap.has(key)) {
          callMap.set(key, {
            fromProc: currentProc,
            toModuleLink: t.moduleLink,
            calledNames: new Set()
          });
        }

        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];

for (const entry of callMap.values()) {
  const calledList = Array.from(entry.calledNames).sort().join(", ");
  rows.push([
    entry.fromProc,
    entry.toModuleLink,
    calledList
  ]);
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Процедура', 'Куда (модуль)', 'Что вызывает'],
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


Option Explicit

Public Sub FillRolesListBox(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox ролей
' @role: UI
' @todo: --
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    Set rs = GetAllRoles()
    
    lst.Clear
    lst.ColumnCount = 8
    lst.ColumnWidths = "35 pt;90 pt;0 pt;70 pt;70 pt;60 pt;70 pt;70 pt"
    
    If rs Is Nothing Then Exit Sub
    
    If rs.EOF Then
        lst.AddItem "ID"
        lst.List(0, 1) = "Роль"
        lst.List(0, 2) = ""
        lst.List(0, 3) = "Польз."
        lst.List(0, 4) = "Админ"
        lst.List(0, 5) = "Ред."
        lst.List(0, 6) = "Согл."
        lst.List(0, 7) = "Свой пароль"
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim dataArr(0 To rowCount, 0 To 7)
    
    dataArr(0, 0) = "ID"
    dataArr(0, 1) = "Роль"
    dataArr(0, 2) = ""
    dataArr(0, 3) = "Польз."
    dataArr(0, 4) = "Админ"
    dataArr(0, 5) = "Ред."
    dataArr(0, 6) = "Согл."
    dataArr(0, 7) = "Свой пароль"
    
    i = 1
    Do While Not rs.EOF
        dataArr(i, 0) = NzLng(rs.Fields("RoleID").Value)
        dataArr(i, 1) = NzStr(rs.Fields("RoleName").Value)
        dataArr(i, 2) = NzStr(rs.Fields("Description").Value)
        dataArr(i, 3) = IIf(NzBool(rs.Fields("CanManageUsers").Value), "Да", "Нет")
        dataArr(i, 4) = IIf(NzBool(rs.Fields("CanManageAdmin").Value), "Да", "Нет")
        dataArr(i, 5) = IIf(NzBool(rs.Fields("CanEditAny").Value), "Да", "Нет")
        dataArr(i, 6) = IIf(NzBool(rs.Fields("CanApproveAny").Value), "Да", "Нет")
        dataArr(i, 7) = IIf(NzBool(rs.Fields("CanChangeOwnPwd").Value), "Да", "Нет")
        i = i + 1
        rs.MoveNext
    Loop
    
    lst.List = dataArr
    F_ListsDB.LB_Roles.ListIndex = 1
    rs.Close
    Set rs = Nothing
End Sub

Public Sub FillUsersListBox(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox пользователей
' @role: UI
' @todo: --
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    Set rs = GetAllUsers()
    
    lst.Clear
    lst.ColumnCount = 5
    lst.ColumnWidths = "40 pt;90 pt;140 pt;90 pt;55 pt"
    
    If rs Is Nothing Then Exit Sub
    
    If rs.EOF Then
        lst.AddItem "ID"
        lst.List(0, 1) = "Логин"
        lst.List(0, 2) = "Полное имя"
        lst.List(0, 3) = "Роль"
        lst.List(0, 4) = "Активен"
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim dataArr(0 To rowCount, 0 To 4)
    
    dataArr(0, 0) = "ID"
    dataArr(0, 1) = "Логин"
    dataArr(0, 2) = "Полное имя"
    dataArr(0, 3) = "Роль"
    dataArr(0, 4) = "Активен"
    
    i = 1
    Do While Not rs.EOF
        dataArr(i, 0) = NzLng(rs.Fields("UserID").Value)
        dataArr(i, 1) = NzStr(rs.Fields("Login").Value)
        dataArr(i, 2) = NzStr(rs.Fields("FullName").Value)
        dataArr(i, 3) = NzStr(rs.Fields("RoleName").Value)
        dataArr(i, 4) = IIf(NzBool(rs.Fields("IsActive").Value), "Да", "Нет")
        i = i + 1
        rs.MoveNext
    Loop
    
    lst.List = dataArr
    F_ListsDB.LB_Users.ListIndex = 1
    rs.Close
    Set rs = Nothing
End Sub

Public Sub FillNomTypesListBox(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox типов номенклатур
' @role: UI
' @todo: --
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    Set rs = GetAllNomenclatureTypes()
    
    lst.Clear
    lst.ColumnCount = 5
    lst.ColumnWidths = "40 pt;140 pt;90 pt;0 pt;55 pt"
    
    If rs Is Nothing Then Exit Sub
    If rs.EOF Then
        lst.AddItem "ID"
        lst.List(0, 1) = "Номенклатура"
        lst.List(0, 2) = "КОД"
        lst.List(0, 3) = "Описание"
        lst.List(0, 4) = "Активен"
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim dataArr(0 To rowCount, 0 To 4)
    
    dataArr(0, 0) = "ID"
    dataArr(0, 1) = "Номенклатура"
    dataArr(0, 2) = "КОД"
    dataArr(0, 3) = "Описание"
    dataArr(0, 4) = "Активен"
    
    i = 1
    Do While Not rs.EOF
        dataArr(i, 0) = NzLng(rs.Fields("NomenclatureTypeID").Value)
        dataArr(i, 1) = NzStr(rs.Fields("TypeName").Value)
        dataArr(i, 2) = NzStr(rs.Fields("TypeCode").Value)
        dataArr(i, 3) = NzStr(rs.Fields("Description").Value)
        dataArr(i, 4) = IIf(NzBool(rs.Fields("IsActive").Value), "Да", "Нет")
        i = i + 1
        rs.MoveNext
    Loop
    
    lst.List = dataArr
    F_ListsDB.LB_NomTypes.ListIndex = 1
    rs.Close
    Set rs = Nothing
End Sub

Public Sub FillNomListBox(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox номенклатур
' @role: UI
' @todo: --
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    Set rs = GetAllNomenclatures()
    
    lst.Clear
    lst.ColumnCount = 5
    lst.ColumnWidths = "40 pt;120 pt;90 pt;210 pt;0 pt"
    
    If rs Is Nothing Then Exit Sub
    If rs.EOF Then
        lst.AddItem "ID"
        lst.List(0, 1) = "Тип"
        lst.List(0, 2) = "Код"
        lst.List(0, 3) = "Наименование"
        lst.List(0, 4) = "Описание"
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim dataArr(0 To rowCount, 0 To 5)
    
    dataArr(0, 0) = "ID"
    dataArr(0, 1) = "Тип"
    dataArr(0, 2) = "Код"
    dataArr(0, 3) = "Наименование"
    dataArr(0, 4) = "Описание"
    
    i = 1
    Do While Not rs.EOF
        dataArr(i, 0) = NzLng(rs.Fields("NomenclatureID").Value)
        dataArr(i, 1) = NzStr(rs.Fields("TypeName").Value)
        dataArr(i, 2) = NzStr(rs.Fields("NomenclatureCode").Value)
        dataArr(i, 3) = NzStr(rs.Fields("NomenclatureName").Value)
        dataArr(i, 4) = NzStr(rs.Fields("Description").Value)
        i = i + 1
        rs.MoveNext
    Loop
    
    lst.List = dataArr
    F_ListsDB.LB_Nom.ListIndex = 1
    rs.Close
    Set rs = Nothing
End Sub

Public Sub FillServicesListBox(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox служб
' @role: UI
' @todo: --
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    Set rs = GetAllServices()
    
    lst.Clear
    lst.ColumnCount = 5
    lst.ColumnWidths = "40 pt;180 pt;90 pt;0 pt;40 pt"
        
    If rs Is Nothing Then Exit Sub
    If rs.EOF Then
        lst.AddItem "ID"
        lst.List(0, 1) = "Служба"
        lst.List(0, 2) = "Код"
        lst.List(0, 3) = "Описание"
        lst.List(0, 4) = "Активна"
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim dataArr(0 To rowCount, 0 To 5)
    
    dataArr(0, 0) = "ID"
    dataArr(0, 1) = "Служба"
    dataArr(0, 2) = "Код"
    dataArr(0, 3) = "Описание"
    dataArr(0, 4) = "Активна"
    
    i = 1
    Do While Not rs.EOF
        dataArr(i, 0) = NzLng(rs.Fields("ServiceID").Value)
        dataArr(i, 1) = NzStr(rs.Fields("ServiceName").Value)
        dataArr(i, 2) = NzStr(rs.Fields("ServiceCode").Value)
        dataArr(i, 3) = NzStr(rs.Fields("Description").Value)
        dataArr(i, 4) = IIf(NzBool(rs.Fields("IsActive").Value), "Да", "Нет")
        i = i + 1
        rs.MoveNext
    Loop
    
    lst.List = dataArr
    F_ListsDB.LB_Services.ListIndex = 1
    rs.Close
    Set rs = Nothing
End Sub

Public Sub InitServiceFormState(ByVal lst1 As MSForms.ListBox, ByVal lst2 As MSForms.ListBox, ByVal serviceID As Long)
' @desc: инициализация формы служб
' @role: UI
' @todo: --
    On Error GoTo EH
    Dim rs As DAO.Recordset
    
    F_Change.mIsDirty = False

    If ActionBut = "Change" Then
        Set rs = GetUsersByService(serviceID)
        Call SvcBuf_LoadFromServiceRecordset(rs)
        If Not rs Is Nothing Then rs.Close
        Set rs = Nothing
    ElseIf ActionBut = "Add" Then
        Set rs = GetUsersForNewService()
        Call SvcBuf_LoadForNewService(rs)
        If Not rs Is Nothing Then rs.Close
        Set rs = Nothing
    Else
        Call SvcBuf_Init
    End If

    RefreshAllServiceLists lst1, lst2
    Exit Sub
EH:
    ShowError "InitServiceFormState", Err.Number, Err.description
End Sub

Public Sub RefreshUsersByServiceList(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox пользователей с отношением к службе
' @role: UI
' @todo: --
    On Error GoTo EH
    Dim items As Collection
    Dim obj As Object
    Dim dataArr() As Variant
    Dim i As Long
    Dim rowCount As Long
    Dim rightsText As String

    Set items = SvcBuf_Items

    lst.Clear
    lst.ColumnCount = 8
    lst.ColumnWidths = "0 pt;40 pt;80 pt;40 pt;40 pt;30 pt;0 pt;0 pt"
    ' 0 UserID
    ' 1 Login
    ' 2 FullName
    ' 3 CanEdit
    ' 4 CanApprove
    ' 5 SourceText
    ' 6 RightsByRole hidden
    ' 7 PendingDelete hidden

    If items Is Nothing Or items.Count = 0 Then Exit Sub

    rowCount = SvcBuf_CountVisibleAssigned()
    If rowCount = 0 Then Exit Sub

    ReDim dataArr(0 To rowCount, 0 To 7)

    dataArr(0, 0) = ""
    dataArr(0, 1) = "Login"
    dataArr(0, 2) = "ФИО"
    dataArr(0, 3) = "Редакт."
    dataArr(0, 4) = "Соглас."
    dataArr(0, 5) = "Источник"
    dataArr(0, 6) = ""
    dataArr(0, 7) = ""

    i = 1
    For Each obj In items
        If NzBool(obj("PendingDelete"), False) = False Then
            If NzBool(obj("RightsByRole"), False) Then
                rightsText = "Роль"
            Else
                rightsText = "Связь"
            End If

            dataArr(i, 0) = NzLng(obj("UserID"))
            dataArr(i, 1) = NzStr(obj("Login"))
            dataArr(i, 2) = NzStr(obj("FullName"))
            dataArr(i, 3) = IIf(NzBool(obj("CanEdit"), False), "Да", "Нет")
            dataArr(i, 4) = IIf(NzBool(obj("CanApprove"), False), "Да", "Нет")
            dataArr(i, 5) = rightsText
            dataArr(i, 6) = IIf(NzBool(obj("RightsByRole"), False), 1, 0)
            dataArr(i, 7) = IIf(NzBool(obj("PendingDelete"), False), 1, 0)
            i = i + 1
        End If
    Next obj

    lst.List = dataArr
    Exit Sub
EH:
    ShowError "RefreshUsersByServiceList", Err.Number, Err.description
End Sub

Public Sub RefreshUsersWithoutServiceList(ByVal lst As MSForms.ListBox)
' @desc: Заполняет ListBox пользователей без отношения к службе
' @role: UI
' @todo: --
    On Error GoTo EH
    Dim rs As DAO.Recordset
    Dim dataArr() As Variant
    Dim rowCount As Long
    Dim r As Long
    Dim i As Long
    Dim userID As Long

    lst.Clear
    lst.ColumnCount = 3
    lst.ColumnWidths = "0 pt;40 pt;100 pt"

    If ActionBut = "Change" Then
        Set rs = GetUsersForNewService()
    Else
        Set rs = GetUsersForNewService()
    End If

    If rs Is Nothing Then Exit Sub
    If rs.EOF Then
        rs.Close
        Set rs = Nothing
        Exit Sub
    End If

    rs.MoveLast
    rs.MoveFirst

    ReDim dataArr(0 To rs.RecordCount, 0 To 2)

    dataArr(0, 0) = ""
    dataArr(0, 1) = "Login"
    dataArr(0, 2) = "ФИО"

    i = 1
    Do While Not rs.EOF
        userID = NzLng(rs.Fields("UserID").Value)

        If (NzBool(rs.Fields("RoleCanEditAny").Value, False) = False) _
           And (NzBool(rs.Fields("RoleCanApproveAny").Value, False) = False) Then

            If SvcBuf_CanAppearInLeftList(userID) Then
                dataArr(i, 0) = userID
                dataArr(i, 1) = NzStr(rs.Fields("Login").Value)
                dataArr(i, 2) = NzStr(rs.Fields("FullName").Value)
                i = i + 1
            End If
        End If

        rs.MoveNext
    Loop

    If i = 1 Then
        lst.Clear
    Else
        ReDim outArr(0 To i - 1, 0 To 2)

        For r = 0 To i - 1
            outArr(r, 0) = dataArr(r, 0)
            outArr(r, 1) = dataArr(r, 1)
            outArr(r, 2) = dataArr(r, 2)
        Next r

        lst.List = outArr
    End If

    rs.Close
    Set rs = Nothing
    Exit Sub
EH:
    ShowError "RefreshUsersWithoutServiceList", Err.Number, Err.description
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
End Sub

Public Sub RefreshAllServiceLists(ByVal lst1 As MSForms.ListBox, ByVal lst2 As MSForms.ListBox)
' @desc: Обновляет ListBox отношений пользователей к службе
' @role: UI
' @todo: --
    RefreshUsersByServiceList lst1
    RefreshUsersWithoutServiceList lst2
End Sub
```

## Черновые заметки

