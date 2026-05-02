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

const re = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(re);
    if (!m) continue;

    const scopeRaw = m[1];               // Public / Private / undefined
    const kindRaw = m[2];                // Sub / Function
    const name = m[3];

    const kind = kindRaw.toLowerCase() === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw
      ? scopeRaw                       // "Public" или "Private"
      : "По умолчанию (Public)";       // ничего не указано → Public[web:369][web:375]

    let desc = "";
    if (i + 1 < lines.length) {
      const next = lines[i + 1].trim();
      const mDesc = next.match(/^'\s*@desc:\s*(.+)$/i);
      if (mDesc) desc = mDesc[1];
    }

    rows.push([name, kind, scope, desc]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(["Имя", "Тип", "Область", "Описание"], rows);
}
```
# Код
```vba
Option Explicit

Public Type RoleInfo
    roleID          As Long
    RoleName        As String
    description     As String
    CanManageUsers  As Boolean
    CanManageAdmin  As Boolean
    CanEditAny      As Boolean
    CanApproveAny   As Boolean
    CanChangeOwnPwd As Boolean
End Type

Public Const ROLE_CAN_MANAGE_USERS_FIELD As String = "CanManageUsers"
Public Const ROLE_CAN_MANAGE_ADMIN_FIELD As String = "CanManageAdmin"
Public Const ROLE_CAN_EDIT_ANY_FIELD As String = "CanEditAny"
Public Const ROLE_CAN_APPROVE_ANY_FIELD As String = "CanApproveAny"
Public Const ROLE_CAN_CHANGE_OWN_PWD As String = "CanChangeOwnPwd"

' ================================================================
' Чтение роли по ID
' ================================================================
Public Function GetRoleById(ByVal roleID As Long) As RoleInfo
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim r As RoleInfo
    
    If roleID <= 0 Then Exit Function
        
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset("SELECT * FROM Roles WHERE RoleID=" & roleID, dbOpenSnapshot)
    If Not rs.EOF Then
        r.roleID = NzLng(rs.Fields("RoleID").Value)
        r.RoleName = NzStr(rs.Fields("RoleName").Value)
        r.description = NzStr(rs.Fields("Description").Value)
        r.CanManageUsers = NzBool(rs.Fields("CanManageUsers").Value)
        r.CanManageAdmin = NzBool(rs.Fields("CanManageAdmin").Value)
        r.CanEditAny = NzBool(rs.Fields("CanEditAny").Value)
        r.CanApproveAny = NzBool(rs.Fields("CanApproveAny").Value)
        r.CanChangeOwnPwd = NzBool(rs.Fields("CanChangeOwnPwd").Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    
    GetRoleById = r
End Function

' ================================================================
' Чтение роли по имени
' ================================================================
Public Function GetRoleByName(ByVal RoleName As String) As RoleInfo
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim r As RoleInfo
    
    RoleName = Trim$(RoleName)
    If Len(RoleName) = 0 Then Exit Function
        
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset("SELECT * FROM Roles WHERE RoleName=" & QuoteSql(RoleName), dbOpenSnapshot)
    If Not rs.EOF Then
        r.roleID = NzLng(rs.Fields("RoleID").Value)
        r.RoleName = NzStr(rs.Fields("RoleName").Value)
        r.description = NzStr(rs.Fields("Description").Value)
        r.CanManageUsers = NzBool(rs.Fields("CanManageUsers").Value)
        r.CanManageAdmin = NzBool(rs.Fields("CanManageAdmin").Value)
        r.CanEditAny = NzBool(rs.Fields("CanEditAny").Value)
        r.CanApproveAny = NzBool(rs.Fields("CanApproveAny").Value)
        r.CanChangeOwnPwd = NzBool(rs.Fields("CanChangeOwnPwd").Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    
    GetRoleByName = r
End Function

' ================================================================
' Проверка прав текущего пользователя на управление пользователями
' ================================================================
Public Function CanUserManageUsers(ByVal actingUserId As Long) As Boolean
    Dim r As RoleInfo
    Dim roleID As Long
    
    roleID = GetUserRoleId(actingUserId)
    If roleID <= 0 Then Exit Function
    
    r = GetRoleById(roleID)
    CanUserManageUsers = (r.CanManageUsers Or r.CanManageAdmin Or r.CanEditAny Or r.CanApproveAny)
End Function

' ================================================================
' Проверка прав текущего пользователя на управление админом
' ================================================================
Public Function CanUserManageAdmins(ByVal actingUserId As Long) As Boolean
    Dim r As RoleInfo
    Dim roleID As Long
    
    roleID = GetUserRoleId(actingUserId)
    If roleID <= 0 Then Exit Function
    
    r = GetRoleById(roleID)
    CanUserManageAdmins = r.CanManageAdmin
End Function

' ================================================================
' Проверка прав текущего пользователя на создание ролей
' ================================================================
Public Function CanUserEditRoles(ByVal actingUserId As Long) As Boolean
    ' Только те кто могут редактировать админов
    CanUserEditRoles = CanUserManageAdmins(actingUserId)
End Function

' ================================================================
' Проверка прав текущего пользователя на присвоение данной роли другим пользователям
' ================================================================
Public Function CanUserAssignRoles(ByVal actingUserId As Long, ByVal targerRoleId As Long) As Boolean
    Dim actingRole As RoleInfo
    Dim targetRole As RoleInfo
    Dim actingRoleId As Long
    
    actingRoleId = GetUserRoleId(actingUserId)
    If actingRoleId <= 0 Then Exit Function
    
    actingRole = GetRoleById(actingRoleId)
    targetRole = GetRoleById(targerRoleId)
    
    If actingRole.roleID <= 0 Or targetRole.roleID <= 0 Then Exit Function
    
    ' Если целевая роль - Admin, её может назначать только тот, у кого CanManageAdmin = True
    If StrComp(targetRole.RoleName, Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "ROLE_ADMIN_NAME"), vbTextCompare) = 0 Then
        CanUserAssignRoles = actingRole.CanManageAdmin
    Else
        CanUserAssignRoles = actingRole.CanManageUsers Or actingRole.CanManageAdmin
    End If
End Function

' ================================================================
' Создание роли
' ================================================================
Public Function CreateRole( _
    ByVal RoleName As String, _
    ByVal description As String, _
    ByVal CanManageUsers As Boolean, _
    ByVal CanManageAdmin As Boolean, _
    ByVal CanEditAny As Boolean, _
    ByVal CanApproveAny As Boolean, _
    ByVal CanChangeOwnPwd As Boolean, _
    ByVal actingUserId As Long) As Long

    
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim newID As Long
    
    RoleName = Trim$(RoleName)
    If Len(RoleName) = 0 Then
        ShowWarning "RoleName не может быть пустым."
        GoTo CleanExit
    End If
    If Not CanUserEditRoles(actingUserId) Then
        ShowWarning "У вас нет прав создавать роли."
        GoTo CleanExit
    End If
    
    If GetRoleIdByName(RoleName) > 0 Then
        ShowWarning "Роль с именем " & RoleName & " уже существует."
        GoTo CleanExit
    End If
       
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    
    On Error GoTo EH
    ws.BeginTrans
    
    Set rs = db.OpenRecordset("Roles", dbOpenDynaset, dbAppendOnly)
    rs.AddNew
    rs.Fields("RoleName").Value = Left$(RoleName, 50)
    rs.Fields("Description").Value = Left$(NzStr(description), 255)
    rs.Fields("CanManageUsers").Value = CanManageUsers
    rs.Fields("CanManageAdmin").Value = CanManageAdmin
    rs.Fields("CanEditAny").Value = CanEditAny
    rs.Fields("CanApproveAny").Value = CanApproveAny
    rs.Fields("CanChangeOwnPwd").Value = CanChangeOwnPwd
    rs.Update
    rs.Bookmark = rs.LastModified
    newID = NzLng(rs.Fields("RoleID").Value)
    rs.Close
    Set rs = Nothing
    
    Call WriteAuditEvent(db, "Roles", newID, "RoleName", "", RoleName, "INSERT", "RoleCreate", actingUserId, Null)
    
    ws.CommitTrans
    CreateRole = newID
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    ws.Rollback
    ShowError "CreateRole", Err.Number, Err.description
    Resume CleanExit
End Function

' ================================================================
' Обновление роли
' ================================================================
Public Sub UpdateRole( _
    ByVal roleID As Long, _
    ByVal newRoleName As String, _
    ByVal newDescription As String, _
    ByVal newCanManageUsers As Boolean, _
    ByVal newCanManageAdmin As Boolean, _
    ByVal newCanEditAny As Boolean, _
    ByVal newCanApproveAny As Boolean, _
    ByVal newCanChangeOwnPwd As Boolean, _
    ByVal actingUserId As Long)

    
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim old As RoleInfo
    Dim newR As RoleInfo
    
    If roleID <= 0 Then
        ShowWarning "Неверный RoleID."
        GoTo CleanExit
    End If
    
    If Not CanUserEditRoles(actingUserId) Then
        ShowWarning "У вас нет прав редактировать роли."
        GoTo CleanExit
    End If
    
    old = GetRoleById(roleID)
    If old.roleID <= 0 Then
        ShowWarning "Роль не найдена."
        GoTo CleanExit
    End If
    
    ' Защитим имя Admin от редактирования
    If StrComp(old.RoleName, Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "ROLE_ADMIN_NAME"), vbTextCompare) = 0 Then
        newRoleName = old.RoleName
    End If
    
    ' Если имя меняется, проверяем уникальность
    newRoleName = Trim$(newRoleName)
    If Len(newRoleName) = 0 Then
        ShowWarning "RoleName не может быть пустым."
        GoTo CleanExit
    End If
    
    If StrComp(newRoleName, old.RoleName, vbTextCompare) <> 0 Then
        If GetRoleIdByName(newRoleName) <> 0 Then
            ShowWarning "Роль с именем " & newRoleName & " уже существует."
            GoTo CleanExit
        End If
    End If
    
    newR.roleID = roleID
    newR.RoleName = newRoleName
    newR.description = newDescription
    newR.CanManageUsers = newCanManageUsers
    newR.CanManageAdmin = newCanManageAdmin
    newR.CanEditAny = newCanEditAny
    newR.CanApproveAny = newCanApproveAny
    newR.CanChangeOwnPwd = newCanChangeOwnPwd
        
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    
    On Error GoTo EH
    ws.BeginTrans
    
    Set rs = db.OpenRecordset("SELECT * FROM Roles WHERE RoleID=" & roleID, dbOpenDynaset, dbSeeChanges)
    If rs.EOF Then
        ShowWarning "Роль не найдена при обновлении."
        GoTo CleanExit
    End If
    
    rs.Edit
    rs.Fields("RoleName").Value = Left$(newR.RoleName, 50)
    rs.Fields("Description").Value = Left$(NzStr(newR.description), 255)
    rs.Fields("CanManageUsers").Value = newR.CanManageUsers
    rs.Fields("CanManageAdmin").Value = newR.CanManageAdmin
    rs.Fields("CanEditAny").Value = newR.CanEditAny
    rs.Fields("CanApproveAny").Value = newR.CanApproveAny
    rs.Fields("CanChangeOwnPwd").Value = newR.CanChangeOwnPwd
    rs.Update
    rs.Close
    Set rs = Nothing
    
    If StrComp(old.RoleName, newR.RoleName, vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, "Roles", roleID, "RoleName", old.RoleName, newR.RoleName, "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If NzStr(old.description) <> NzStr(newR.description) Then
        WriteAuditEvent db, "Roles", roleID, "Description", old.description, newR.description, "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If old.CanManageUsers <> newR.CanManageUsers Then
        WriteAuditEvent db, "Roles", roleID, ROLE_CAN_MANAGE_USERS_FIELD, CStr(old.CanManageUsers), CStr(newR.CanManageUsers), "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If old.CanManageAdmin <> newR.CanManageAdmin Then
        WriteAuditEvent db, "Roles", roleID, ROLE_CAN_MANAGE_ADMIN_FIELD, CStr(old.CanManageAdmin), CStr(newR.CanManageAdmin), "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If old.CanEditAny <> newR.CanEditAny Then
        WriteAuditEvent db, "Roles", roleID, ROLE_CAN_EDIT_ANY_FIELD, CStr(old.CanEditAny), CStr(newR.CanEditAny), "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If old.CanApproveAny <> newR.CanApproveAny Then
        WriteAuditEvent db, "Roles", roleID, ROLE_CAN_APPROVE_ANY_FIELD, CStr(old.CanApproveAny), CStr(newR.CanApproveAny), "UPDATE", "RoleUpdate", actingUserId, Null
    End If
    If old.CanChangeOwnPwd <> newR.CanChangeOwnPwd Then
        WriteAuditEvent db, "Roles", roleID, ROLE_CAN_CHANGE_OWN_PWD, CStr(old.CanChangeOwnPwd), CStr(newR.CanChangeOwnPwd), "UPDATE", "RoleUpdate", actingUserId, Null
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
    ws.Rollback
    ShowError "UpdateRole", Err.Number, Err.description
    Resume CleanExit
End Sub

' ================================================================
' Безопасное удаление роли
' ================================================================
Public Sub DeleteRoleSafe(ByVal roleID As Long, ByVal actingUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim r As RoleInfo
    Dim cnt As Long
    
    If roleID <= 0 Then
        ShowWarning "Неверный RoleID."
        GoTo CleanExit
    End If
    
    If Not CanUserEditRoles(actingUserId) Then
        ShowWarning "У вас нет прав редактировать роли."
        GoTo CleanExit
    End If
    
    r = GetRoleById(roleID)
    If r.roleID <= 0 Then
        ShowWarning "Роль не найдена."
        GoTo CleanExit
    End If
    
    ' Защитим Admin от удаления
    If StrComp(r.RoleName, Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "ROLE_ADMIN_NAME"), vbTextCompare) = 0 Then
        ShowWarning "Роль администратора удалять нельзя."
        GoTo CleanExit
    End If
    
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    
    ' Проверим есть ли пользователи с этой ролью
    Set rs = db.OpenRecordset("SELECT COUNT(*) as Cnt FROM Users WHERE RoleID=" & roleID, dbOpenSnapshot)
    If Not rs.EOF Then cnt = NzLng(rs.Fields(0).Value)
    rs.Close
    Set rs = Nothing
    
    If cnt > 0 Then
        ShowWarning "Невозможно удалить роль: к ней привязаны пользователи (" & cnt & ")."
        GoTo CleanExit
    End If
    
    On Error GoTo EH
    ws.BeginTrans
    
    db.Execute "DELETE FROM Roles WHERE RoleID=" & roleID, dbFailOnError
    
    WriteAuditEvent db, "Roles", roleID, "RoleName", r.RoleName, "[DELETED]", "DELETE", "RoleDelete", actingUserId, Null
    
    ws.CommitTrans
        
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    ws.Rollback
    ShowError "DeleteRoleSafe", Err.Number, Err.description
    Resume CleanExit
End Sub

' ================================================================
' Получение роли по имени запросом
' ================================================================
Public Function GetRoleIdByName(ByVal RoleName As String) As Long
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset("SELECT RoleID FROM Roles WHERE RoleName=" & Q(RoleName), dbOpenSnapshot)

    If Not rs.EOF Then GetRoleIdByName = NzLng(rs.Fields("RoleID").Value)

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

' ================================================================
' Создание базовых ролей при создании БД
' ================================================================
Public Sub InitDefaultRoles()
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
        
    Set ws = DBEngine.Workspaces(0)
    Set db = ws.OpenDatabase(ThisWorkbook.Path & "\vvt_db.accdb")
    
    On Error GoTo EH
    ws.BeginTrans
    
    ' Проверяю нет ли уже записей в Roles
    sql = "SELECT COUNT(*) AS Cnt FROM Roles"
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    If Not rs.EOF Then
        If NzLng(rs.Fields(0).Value) > 0 Then
            ' Роли уже есть
            rs.Close
            GoTo CommitAndExit
        End If
    End If
    rs.Close
    Set rs = Nothing
    
    ' Открываю Roles для добвления
    Set rs = db.OpenRecordset("Roles", dbOpenDynaset, dbAppendOnly)
    
    ' Admin
    rs.AddNew
    rs.Fields("RoleName").Value = "Admin"
    rs.Fields("Description").Value = "Полный доступ, управление пользователями и админами"
    rs.Fields("CanManageUsers").Value = True
    rs.Fields("CanManageAdmin").Value = True
    rs.Fields("CanEditAny").Value = True
    rs.Fields("CanApproveAny").Value = True
    rs.Fields("CanChangeOwnPwd").Value = True
    rs.Update
    ' ChiefUser
    rs.AddNew
    rs.Fields("RoleName").Value = "ChiefUser"
    rs.Fields("Description").Value = "Ответственный за учёт, без управления админами"
    rs.Fields("CanManageUsers").Value = True
    rs.Fields("CanManageAdmin").Value = False
    rs.Fields("CanEditAny").Value = True
    rs.Fields("CanApproveAny").Value = True
    rs.Fields("CanChangeOwnPwd").Value = True
    rs.Update
    ' ServiceEditor
    rs.AddNew
    rs.Fields("RoleName").Value = "ServiceEditor"
    rs.Fields("Description").Value = "Редактор по службам, без глобальных прав"
    rs.Fields("CanManageUsers").Value = False
    rs.Fields("CanManageAdmin").Value = False
    rs.Fields("CanEditAny").Value = False
    rs.Fields("CanApproveAny").Value = False
    rs.Fields("CanChangeOwnPwd").Value = True
    rs.Update
    ' User
    rs.AddNew
    rs.Fields("RoleName").Value = "User"
    rs.Fields("Description").Value = "Обычный пользователь: просмотр и заявки на изменения"
    rs.Fields("CanManageUsers").Value = False
    rs.Fields("CanManageAdmin").Value = False
    rs.Fields("CanEditAny").Value = False
    rs.Fields("CanApproveAny").Value = False
    rs.Fields("CanChangeOwnPwd").Value = True
    rs.Update
    
CommitAndExit:
    ws.CommitTrans
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub
EH:
    ws.Rollback
    ShowError "InitDefaultRoles", Err.Number, Err.description
    Resume CleanExit
End Sub

' ================================================================
' Получение данных о всех ролях
' ================================================================
Public Function GetAllRoles() As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String
    
    Set db = OpenCurrentDb
    sql = "SELECT RoleID, RoleName, Description, " & _
          "CanManageUsers, CanManageAdmin, CanEditAny, CanApproveAny, CanChangeOwnPwd " & _
          "FROM Roles " & _
          "ORDER BY RoleName"
    Set GetAllRoles = db.OpenRecordset(sql, dbOpenSnapshot)
End Function
```

## Черновые заметки

