---
type: module
status: done
done_date: 2026-05-02
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

// будем искать вызовы более аккуратно:
// 1) Call Name ...
// 2) Name(...)
// 3) Name <что-то>, но не Name =, не Dim Name, не Set Name =
const reCallPattern = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\b/g;

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

    // Не считать строки, где имя функции слева от "=":
    //   FuncName = ...
    //   Set obj = ...
    //   Dim FuncName As ...
    // Обработаем это внутри цикла по совпадениям.

    let m;
    while ((m = reCallPattern.exec(line)) !== null) {
      const calledName = m[1];

      // Позиция найденного имени в строке
      const idx = m.index;

      // Левая часть строки до имени
      const before = line.slice(0, idx);
      const after = line.slice(idx + calledName.length);

      const beforeTrim = before.trim();
      const afterTrim = after.trimStart();

      // 1) Если это присваивание результата функции: "FuncName = ..."
      //    — имя стоит в начале строки / после пробелов, а сразу после него "="
      const isAssignmentResult =
        beforeTrim === "" && afterTrim.startsWith("=");

      if (isAssignmentResult) {
        // Это возврат из функции, НЕ вызов
        continue;
      }

      // 2) Если это объявление переменной: "Dim FuncName As ..."
      if (/^\s*Dim\s+$/i.test(before) || /^\s*Dim\s+/i.test(beforeTrim)) {
        continue;
      }

      // 3) Если это левая часть Set: "Set obj = ..."
      //    — нас интересуют вызовы, а не имя слева от Set/=
      if (/^\s*Set\s+$/i.test(before) || /^\s*Set\s+/i.test(beforeTrim)) {
        continue;
      }

      // 4) Если после имени нет "(", нет пробела + аргументов, и нет "Call",
      //    можно попасть в кучу ложных срабатываний. Но:
      //    - уже отсекли очевидные присваивания и Dim/Set.
      //    - оставим это как потенциальный вызов (вызов без скобок: Name arg1, arg2).
      //    При желании можно ещё проверить, что после имени не конец строки и не оператор.

      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // не считаем самовызов внутри того же модуля той же процедуры
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

'=========================
'Services + UserServices
'=========================

Public Type ServiceInfo
    serviceID As Long
    serviceName As String
    serviceCode As String
    description As String
    isActive As Boolean
End Type

Public Type UserServiceInfo
    userServiceID As Long
    userID As Long
    serviceID As Long
    canEdit As Boolean
    canApprove As Boolean
End Type

Private Const TBLSERVICES As String = "Services"
Private Const TBLUSERSERVICES As String = "UserService"
Private Const TBLUSERS As String = "Users"
Private Const TBLPRODUCTSERVICES As String = "ProductServices"

Private Const FLDSVCID As String = "ServiceID"
Private Const FLDSVCNAME As String = "ServiceName"
Private Const FLDSVCCODE As String = "ServiceCode"
Private Const FLDSVCDESC As String = "Description"
Private Const FLDSVCACTIVE As String = "IsActive"

Private Const FLDUSID As String = "UserServiceID"
Private Const FLDUSERID As String = "UserID"
Private Const FLDCANEDIT As String = "CanEdit"
Private Const FLDCANAPPROVE As String = "CanApprove"

Private Sub ValidateServiceInput(ByVal serviceName As String, ByVal serviceCode As String)
    serviceName = Trim$(serviceName)
    serviceCode = Trim$(serviceCode)
    
    If LenB(serviceName) = 0 Then
        ShowWarning "Имя сервиса обязательно."
    End If
    
    If Len(serviceName) > 100 Then
        ShowWarning "Имя сервиса должно быть короче 100 символов."
    End If
    
    If Len(serviceCode) > 20 Then
        ShowWarning "Код сервиса должно быть короче 20 символов."
    End If
End Sub

Private Sub ValidateUserServiceInput(ByVal userID As Long, ByVal serviceID As Long)
    If userID <= 0 Then
        ShowWarning "UserID должен быть > 0."
    End If
    If serviceID <= 0 Then
        ShowWarning "serviceID должен быть > 0."
    End If
End Sub

'=========================
'Services
'=========================

Public Function GetServiceById(ByVal serviceID As Long) As ServiceInfo
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As ServiceInfo
    
    If serviceID <= 0 Then Exit Function
    
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset( _
        "SELECT ServiceID, ServiceName, ServiceCode, Description, IsActive " & _
        "FROM Services WHERE ServiceID = " & serviceID, dbOpenSnapshot)
        
    If Not rs.EOF Then
        info.serviceID = NzLng(rs.Fields(FLDSVCID).Value)
        info.serviceName = NzStr(rs.Fields(FLDSVCNAME).Value)
        info.serviceCode = NzStr(rs.Fields(FLDSVCCODE).Value)
        info.description = NzStr(rs.Fields(FLDSVCDESC).Value)
        info.isActive = NzBool(rs.Fields(FLDSVCACTIVE).Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
    
    GetServiceById = info
End Function

Public Function GetServiceIdByName(ByVal serviceName As String) As Long
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    
    serviceName = Trim$(serviceName)
    If LenB(serviceName) = 0 Then Exit Function
    
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset( _
        "SELECT ServiceID FROM Services WHERE ServiceName = " & Q(serviceName), dbOpenSnapshot)
    
    If Not rs.EOF Then
        GetServiceIdByName = NzLng(rs.Fields(0).Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function GetServiceIdByCode(ByVal serviceCode As String) As Long
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    
    serviceCode = Trim$(serviceCode)
    If LenB(serviceCode) = 0 Then Exit Function
    
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset( _
        "SELECT ServiceID FROM Services WHERE ServiceCode = " & Q(serviceCode), dbOpenSnapshot)
    
    If Not rs.EOF Then
        GetServiceIdByCode = NzLng(rs.Fields(0).Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function ServiceNameExists(ByVal serviceName As String, Optional ByVal excludeID As Long = 0, Optional db As DAO.Database = Nothing) As Boolean
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String
    
    serviceName = Trim$(serviceName)
    If LenB(serviceName) = 0 Then Exit Function
    
    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If
    
    sql = "SELECT ServiceID FROM Services WHERE ServiceName = " & Q(serviceName)
    If excludeID > 0 Then
        sql = sql & " AND serviceID <> " & excludeID
    End If
    
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    ServiceNameExists = Not rs.EOF
    
    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function ServiceCodeExists(ByVal serviceCode As String, Optional ByVal excludeID As Long = 0, Optional db As DAO.Database = Nothing) As Boolean
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String
    
    serviceCode = Trim$(serviceCode)
    If LenB(serviceCode) = 0 Then Exit Function
    
    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If
    
    sql = "SELECT ServiceID FROM Services WHERE ServiceCode = " & Q(serviceCode)
    If excludeID > 0 Then
        sql = sql & " AND serviceID <> " & excludeID
    End If
    
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    ServiceCodeExists = Not rs.EOF
    
    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function CreateService( _
    ByVal serviceName As String, _
    ByVal serviceCode As String, _
    ByVal description As String, _
    ByVal isActive As Boolean, _
    ByVal changeByUserId As Long) As Long

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim newID As Long
    
    serviceName = Trim$(serviceName)
    serviceCode = Trim$(serviceCode)
    description = Trim$(description)
    
    ValidateServiceInput serviceName, serviceCode
    
    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans
    
    If ServiceNameExists(serviceName, 0, db) Then
        ShowWarning "Служба с таким именем уже существует."
        GoTo CleanExit
    End If
    
    If LenB(serviceCode) > 0 Then
        If ServiceCodeExists(serviceCode, 0, db) Then
            ShowWarning "Служба с таким кодом уже существует."
            GoTo CleanExit
        End If
    End If
    
    Set rs = db.OpenRecordset(TBLSERVICES, dbOpenDynaset, dbAppendOnly)
    rs.AddNew
    rs.Fields(FLDSVCNAME).Value = serviceName
    If LenB(serviceCode) > 0 Then
        rs.Fields(FLDSVCCODE).Value = serviceCode
    Else
        rs.Fields(FLDSVCCODE).Value = Null
    End If
    If LenB(description) > 0 Then
        rs.Fields(FLDSVCDESC).Value = description
    Else
        rs.Fields(FLDSVCDESC).Value = Null
    End If
    rs.Fields(FLDSVCACTIVE).Value = isActive
    rs.Update
    rs.Bookmark = rs.LastModified
    newID = NzLng(rs.Fields(FLDSVCID).Value)
    rs.Close
    Set rs = Nothing
    
    WriteAuditEvent db, TBLSERVICES, newID, FLDSVCNAME, vbNullString, serviceName, "INSERT", "ServiceCreate", changeByUserId, Null
    WriteAuditEvent db, TBLSERVICES, newID, FLDSVCCODE, vbNullString, serviceCode, "INSERT", "ServiceCreate", changeByUserId, Null
    WriteAuditEvent db, TBLSERVICES, newID, FLDSVCDESC, vbNullString, description, "INSERT", "ServiceCreate", changeByUserId, Null
    WriteAuditEvent db, TBLSERVICES, newID, FLDSVCACTIVE, vbNullString, BoolToText(isActive), "INSERT", "ServiceCreate", changeByUserId, Null
    
    ws.CommitTrans
    CreateService = newID
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "CreateService", Err.Number, Err.description
    Resume CleanExit
End Function

Public Sub UpdateService( _
    ByVal serviceID As Long, _
    ByVal newServiceName As String, _
    ByVal newServiceCode As String, _
    ByVal newDescription As String, _
    ByVal newIsActive As Boolean, _
    ByVal changeByUserId As Long)

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldInfo As ServiceInfo
    
    If serviceID <= 0 Then
        ShowWarning "ServiceID должен быть > 0."
        GoTo CleanExit
    End If
    
    newServiceName = Trim$(newServiceName)
    newServiceCode = Trim$(newServiceCode)
    newDescription = Trim$(newDescription)
    
    ValidateServiceInput newServiceName, newServiceCode
    oldInfo = GetServiceById(serviceID)
    
    If oldInfo.serviceID = 0 Then
        ShowWarning "Служба не найдена."
        GoTo CleanExit
    End If
    
    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans
        
    If StrComp(oldInfo.serviceName, newServiceName, vbTextCompare) <> 0 Then
        If ServiceNameExists(newServiceName, serviceID, db) Then
            ShowWarning "Служба с таким именем уже существует."
            GoTo CleanExit
        End If
    End If
        
    If StrComp(oldInfo.serviceCode, newServiceCode, vbTextCompare) <> 0 Then
        If LenB(newServiceCode) > 0 Then
            If ServiceCodeExists(newServiceCode, serviceID, db) Then
                ShowWarning "Служба с таким кодом уже существует."
                GoTo CleanExit
            End If
        End If
    End If
    
    Set rs = db.OpenRecordset("SELECT * FROM Services WHERE ServiceID = " & serviceID, dbOpenDynaset)
    
    If rs.EOF Then
        ShowWarning "Служба не найдена."
        GoTo CleanExit
    End If
    
    rs.Edit
    rs.Fields(FLDSVCNAME).Value = newServiceName
    If LenB(newServiceCode) > 0 Then
        rs.Fields(FLDSVCCODE).Value = newServiceCode
    Else
        rs.Fields(FLDSVCCODE).Value = Null
    End If
    If LenB(newDescription) > 0 Then
        rs.Fields(FLDSVCDESC).Value = newDescription
    Else
        rs.Fields(FLDSVCDESC).Value = Null
    End If
    rs.Fields(FLDSVCACTIVE).Value = newIsActive
    rs.Update
    rs.Close
    Set rs = Nothing
    
    If StrComp(oldInfo.serviceName, newServiceName, vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, TBLSERVICES, serviceID, FLDSVCNAME, oldInfo.serviceName, newServiceName, "UPDATE", "ServiceUpdate", changeByUserId, Null
    End If
    If NzStr(oldInfo.serviceCode) <> NzStr(newServiceCode) Then
        WriteAuditEvent db, TBLSERVICES, serviceID, FLDSVCCODE, oldInfo.serviceCode, newServiceCode, "UPDATE", "ServiceUpdate", changeByUserId, Null
    End If
    If NzStr(oldInfo.description) <> NzStr(newDescription) Then
        WriteAuditEvent db, TBLSERVICES, serviceID, FLDSVCDESC, oldInfo.description, newDescription, "UPDATE", "ServiceUpdate", changeByUserId, Null
    End If
    If oldInfo.isActive <> newIsActive Then
        WriteAuditEvent db, TBLSERVICES, serviceID, FLDSVCACTIVE, BoolToText(oldInfo.isActive), BoolToText(newIsActive), "UPDATE", "ServiceUpdate", changeByUserId, Null
    End If
    
    ws.CommitTrans
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "UpdateService", Err.Number, Err.description
    Resume CleanExit
End Sub
Public Sub DeleteServiceSafe(ByVal serviceID As Long, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As ServiceInfo
    Dim cnt As Long

    If serviceID <= 0 Then
        ShowWarning "ServiceID должен быть > 0."
        GoTo CleanExit
    End If

    info = GetServiceById(serviceID)
    If info.serviceID = 0 Then
        ShowWarning "Служба не найдена."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb

    Set rs = db.OpenRecordset("SELECT COUNT(*) AS Cnt FROM UserServices WHERE ServiceID = " & serviceID, dbOpenSnapshot)
    If Not rs.EOF Then cnt = NzLng(rs.Fields(0).Value)
    rs.Close
    Set rs = Nothing
    If cnt > 0 Then
        ShowWarning "Служба используется в UserServices. Кол-во связей: " & cnt
        GoTo CleanExit
    End If

    Set rs = db.OpenRecordset("SELECT COUNT(*) AS Cnt FROM ProductServices WHERE ServiceID = " & serviceID, dbOpenSnapshot)
    cnt = 0
    If Not rs.EOF Then cnt = NzLng(rs.Fields(0).Value)
    rs.Close
    Set rs = Nothing
    If cnt > 0 Then
        ShowWarning "Служба используется в ProductServices. Кол-во связей: " & cnt
        GoTo CleanExit
    End If

    On Error GoTo EH
    ws.BeginTrans

    db.Execute "DELETE FROM Services WHERE ServiceID = " & serviceID, dbFailOnError
    WriteAuditEvent db, TBLSERVICES, serviceID, FLDSVCNAME, info.serviceName, "DELETED", "DELETE", "ServiceDelete", changedByUserId, Null

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "DeleteServiceSafe", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Function GetAllServices(Optional ByVal onlyActive As Boolean = False) As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    Set db = OpenCurrentDb

    sql = "SELECT ServiceID, ServiceName, ServiceCode, Description, IsActive FROM Services "
    If onlyActive Then
        sql = sql & "WHERE IsActive = True "
    End If
    sql = sql & "ORDER BY ServiceName"

    Set GetAllServices = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

' =========================
' UserServices
' =========================

Public Function GetUserServiceById(ByVal userServiceID As Long) As UserServiceInfo
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As UserServiceInfo

    If userServiceID <= 0 Then Exit Function

    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset( _
        "SELECT UserServiceID, UserID, ServiceID, CanEdit, CanApprove " & _
        "FROM UserServices WHERE UserServiceID = " & userServiceID, dbOpenSnapshot)

    If Not rs.EOF Then
        info.userServiceID = NzLng(rs.Fields(FLDUSID).Value)
        info.userID = NzLng(rs.Fields(FLDUSERID).Value)
        info.serviceID = NzLng(rs.Fields(FLDSVCID).Value)
        info.canEdit = NzBool(rs.Fields(FLDCANEDIT).Value, False)
        info.canApprove = NzBool(rs.Fields(FLDCANAPPROVE).Value, False)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing

    GetUserServiceById = info
End Function

Public Function UserServiceExists(ByVal userID As Long, ByVal serviceID As Long, Optional ByVal excludeUserServiceID As Long = 0, Optional ByVal db As DAO.Database = Nothing) As Boolean
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String

    ValidateUserServiceInput userID, serviceID

    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If

    sql = "SELECT UserServiceID FROM UserServices WHERE UserID = " & userID & " AND ServiceID = " & serviceID
    If excludeUserServiceID > 0 Then
        sql = sql & " AND UserServiceID <> " & excludeUserServiceID
    End If

    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    UserServiceExists = Not rs.EOF

    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function AssignUserService(ByVal userID As Long, ByVal serviceID As Long, ByVal canEdit As Boolean, ByVal canApprove As Boolean, ByVal changedByUserId As Long) As Long
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim newID As Long

    ValidateUserServiceInput userID, serviceID

    If Not UserExistsById(userID) Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If
    If GetServiceById(serviceID).serviceID = 0 Then
        ShowWarning "Служба не найдена."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans

    If UserServiceExists(userID, serviceID, 0, db) Then
        ShowWarning "Такая связка пользователь-служба уже существует."
        GoTo CleanExit
    End If

    Set rs = db.OpenRecordset(TBLUSERSERVICES, dbOpenDynaset, dbAppendOnly)
    rs.AddNew
    rs.Fields(FLDUSERID).Value = userID
    rs.Fields(FLDSVCID).Value = serviceID
    rs.Fields(FLDCANEDIT).Value = canEdit
    rs.Fields(FLDCANAPPROVE).Value = canApprove
    rs.Update
    rs.Bookmark = rs.LastModified
    newID = NzLng(rs.Fields(FLDUSID).Value)
    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, TBLUSERSERVICES, newID, FLDUSERID, vbNullString, CStr(userID), "INSERT", "UserServiceAssign", changedByUserId, Null
    WriteAuditEvent db, TBLUSERSERVICES, newID, FLDSVCID, vbNullString, CStr(serviceID), "INSERT", "UserServiceAssign", changedByUserId, Null
    WriteAuditEvent db, TBLUSERSERVICES, newID, FLDCANEDIT, vbNullString, BoolToText(canEdit), "INSERT", "UserServiceAssign", changedByUserId, Null
    WriteAuditEvent db, TBLUSERSERVICES, newID, FLDCANAPPROVE, vbNullString, BoolToText(canApprove), "INSERT", "UserServiceAssign", changedByUserId, Null

    ws.CommitTrans
    AssignUserService = newID

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "AssignUserService", Err.Number, Err.description
    Resume CleanExit
End Function

Public Sub UpdateUserService(ByVal userServiceID As Long, ByVal newCanEdit As Boolean, ByVal newCanApprove As Boolean, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldInfo As UserServiceInfo

    If userServiceID <= 0 Then
        ShowWarning "UserServiceID должен быть > 0."
        GoTo CleanExit
    End If

    oldInfo = GetUserServiceById(userServiceID)
    If oldInfo.userServiceID = 0 Then
        ShowWarning "Связь пользователь-служба не найдена."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset("SELECT * FROM UserServices WHERE UserServiceID = " & userServiceID, dbOpenDynaset)
    If rs.EOF Then
        ShowWarning "Связь пользователь-служба не найдена."
        GoTo CleanExit
    End If

    rs.Edit
    rs.Fields(FLDCANEDIT).Value = newCanEdit
    rs.Fields(FLDCANAPPROVE).Value = newCanApprove
    rs.Update
    rs.Close
    Set rs = Nothing

    If oldInfo.canEdit <> newCanEdit Then
        WriteAuditEvent db, TBLUSERSERVICES, userServiceID, FLDCANEDIT, BoolToText(oldInfo.canEdit), BoolToText(newCanEdit), "UPDATE", "UserServiceUpdate", changedByUserId, Null
    End If
    If oldInfo.canApprove <> newCanApprove Then
        WriteAuditEvent db, TBLUSERSERVICES, userServiceID, FLDCANAPPROVE, BoolToText(oldInfo.canApprove), BoolToText(newCanApprove), "UPDATE", "UserServiceUpdate", changedByUserId, Null
    End If

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "UpdateUserService", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Sub RevokeUserService(ByVal userServiceID As Long, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim info As UserServiceInfo

    If userServiceID <= 0 Then
        ShowWarning "UserServiceID должен быть > 0."
        GoTo CleanExit
    End If

    info = GetUserServiceById(userServiceID)
    If info.userServiceID = 0 Then
        ShowWarning "Связь пользователь-служба не найдена."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans

    db.Execute "DELETE FROM UserServices WHERE UserServiceID = " & userServiceID, dbFailOnError

    WriteAuditEvent db, TBLUSERSERVICES, userServiceID, FLDUSERID, CStr(info.userID), "DELETED", "DELETE", "UserServiceDelete", changedByUserId, Null

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    On Error Resume Next
    ws.Rollback
    ShowError "RevokeUserService", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Function GetUserServices(ByVal userID As Long) As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    If userID <= 0 Then Exit Function

    Set db = OpenCurrentDb
    sql = "SELECT US.UserServiceID, US.UserID, US.ServiceID, S.ServiceName, S.ServiceCode, US.CanEdit, US.CanApprove " & _
          "FROM UserServices AS US " & _
          "INNER JOIN Services AS S ON US.ServiceID = S.ServiceID " & _
          "WHERE US.UserID = " & userID & " " & _
          "ORDER BY S.ServiceName"

    Set GetUserServices = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

Public Function GetServiceUsers(ByVal serviceID As Long) As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    If serviceID <= 0 Then Exit Function

    Set db = OpenCurrentDb
    sql = "SELECT US.UserServiceID, US.UserID, U.Login, U.FullName, US.ServiceID, US.CanEdit, US.CanApprove " & _
          "FROM UserServices AS US " & _
          "INNER JOIN Users AS U ON US.UserID = U.UserID " & _
          "WHERE US.ServiceID = " & serviceID & " " & _
          "ORDER BY U.FullName, U.Login"

    Set GetServiceUsers = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

Public Function GetAllUserServices() As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    Set db = OpenCurrentDb
    sql = "SELECT US.UserServiceID, US.UserID, U.Login, U.FullName, " & _
          "US.ServiceID, S.ServiceName, S.ServiceCode, US.CanEdit, US.CanApprove " & _
          "FROM (UserServices AS US " & _
          "INNER JOIN Users AS U ON US.UserID = U.UserID) " & _
          "INNER JOIN Services AS S ON US.ServiceID = S.ServiceID " & _
          "ORDER BY U.FullName, S.ServiceName"

    Set GetAllUserServices = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

Public Function CanUserEditServiceData(ByVal userID As Long, ByVal serviceID As Long) As Boolean
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim roleID As Long
    Dim r As RoleInfo

    If userID <= 0 Or serviceID <= 0 Then Exit Function

    roleID = GetUserRoleId(userID)
    If roleID > 0 Then
        r = GetRoleById(roleID)
        If r.CanEditAny Or r.CanManageAdmin Then
            CanUserEditServiceData = True
            Exit Function
        End If
    End If

    Set db = OpenCurrentDb
    sql = "SELECT TOP 1 UserServiceID FROM UserServices WHERE UserID = " & userID & _
          " AND ServiceID = " & serviceID & " AND CanEdit = True"
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)

    CanUserEditServiceData = Not rs.EOF

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function CanUserApproveServiceData(ByVal userID As Long, ByVal serviceID As Long) As Boolean
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim roleID As Long
    Dim r As RoleInfo

    If userID <= 0 Or serviceID <= 0 Then Exit Function

    roleID = GetUserRoleId(userID)
    If roleID > 0 Then
        r = GetRoleById(roleID)
        If r.CanApproveAny Or r.CanManageAdmin Then
            CanUserApproveServiceData = True
            Exit Function
        End If
    End If

    Set db = OpenCurrentDb
    sql = "SELECT TOP 1 UserServiceID FROM UserServices WHERE UserID = " & userID & _
          " AND ServiceID = " & serviceID & " AND CanApprove = True"
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)

    CanUserApproveServiceData = Not rs.EOF

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Sub UpdateUserServiceRights( _
    ByVal userServiceID As Long, _
    ByVal canEdit As Boolean, _
    ByVal canApprove As Boolean)

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldCanEdit As Boolean
    Dim oldCanApprove As Boolean

    If userServiceID <= 0 Then
        ShowWarning "Не указан UserServiceID."
         GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset( _
        "SELECT UserServiceID, CanEdit, CanApprove FROM UserServices WHERE UserServiceID = " & userServiceID, _
        dbOpenDynaset)

    If rs.EOF Then
        ShowWarning "Связь пользователь-служба не найдена."
         GoTo CleanExit
    End If

    oldCanEdit = NzBool(rs.Fields("CanEdit").Value, False)
    oldCanApprove = NzBool(rs.Fields("CanApprove").Value, False)

    If oldCanEdit <> canEdit Or oldCanApprove <> canApprove Then
        rs.Edit
        rs.Fields("CanEdit").Value = canEdit
        rs.Fields("CanApprove").Value = canApprove
        rs.Update
    End If

    rs.Close
    Set rs = Nothing

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "UpdateUserServiceRights", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Sub SaveServiceUsersLinks(ByVal serviceID As Long, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim items As Collection
    Dim obj As Object
    Dim sql As String

    If serviceID <= 0 Then
        ShowWarning "Не указан ServiceID для сохранения связей."
         GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    On Error GoTo EH
    ws.BeginTrans

    Set items = SvcBuf_Items

    If Not items Is Nothing Then
        For Each obj In items
            If NzBool(obj("RightsByRole"), False) = False Then

                If NzBool(obj("HasDbLink"), False) = True Then
                    If NzBool(obj("PendingDelete"), False) = True Then
                        sql = "DELETE FROM UserServices " & _
                              "WHERE UserID=" & NzLng(obj("UserID")) & _
                              " AND ServiceID=" & serviceID
                        db.Execute sql, dbFailOnError
                    Else
                        sql = "UPDATE UserServices SET " & _
                              "CanEdit=" & BoolToSql(NzBool(obj("CanEdit"), False)) & ", " & _
                              "CanApprove=" & BoolToSql(NzBool(obj("CanApprove"), False)) & " " & _
                              "WHERE UserID=" & NzLng(obj("UserID")) & _
                              " AND ServiceID=" & serviceID
                        db.Execute sql, dbFailOnError
                    End If

                Else
                    If NzBool(obj("PendingDelete"), False) = False Then
                        sql = "INSERT INTO UserServices " & _
                              "(UserID, ServiceID, CanEdit, CanApprove) VALUES (" & _
                              NzLng(obj("UserID")) & ", " & serviceID & ", " & _
                              BoolToSql(NzBool(obj("CanEdit"), False)) & ", " & _
                              BoolToSql(NzBool(obj("CanApprove"), False)) & ")"
                        db.Execute sql, dbFailOnError
                    End If
                End If

            End If
        Next obj
    End If

    ws.CommitTrans
    Call NormalizeServiceUsersBufferAfterSave

CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "SaveServiceUsersLinks", Err.Number, Err.description
    Resume CleanExit
End Sub
```

## Черновые заметки

