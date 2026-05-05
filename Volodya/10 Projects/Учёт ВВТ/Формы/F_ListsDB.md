---
type: form
status: in-progress
done_date:
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - form
  - skill/vba
reward_xp: 50
---
# Форма
![[F_ListsDB-1777997740460.webp|1046x594]]
## Назначение формы
- Кратко: для чего форма нужна, кто её пользователь (роль).
## Элементы интерфейса

| Форма | Тип элемента | Имя элемента | Caption / Text |
| --- | --- | --- | --- |
| F_ListsDB | CommandButton | Btn_Add | Добавить запись |
| F_ListsDB | CommandButton | Btn_Change | Изменить запись |
| F_ListsDB | CommandButton | Btn_Delete | Удалить запись |
| F_ListsDB | Frame | Frame0 |  |
| F_ListsDB | Frame | Frame1 |  |
| F_ListsDB | Frame | Frame2 |  |
| F_ListsDB | Frame | Frame3 |  |
| F_ListsDB | Frame | Frame4 |  |
| F_ListsDB | ListBox | LB_Nom |  |
| F_ListsDB | ListBox | LB_NomTypes |  |
| F_ListsDB | ListBox | LB_Roles |  |
| F_ListsDB | ListBox | LB_Services |  |
| F_ListsDB | ListBox | LB_Users |  |
| F_ListsDB | MultiPage | MP_Change |  |

## Поведение

- Что происходит при открытии формы.
- Что происходит при нажатии основных кнопок.
- Валидация данных, сообщения об ошибках.
## Состояния и сценарии
- Состояние “новая запись”.
- Состояние “редактирование”.
- Состояние “просмотр”.
## Связанные задачи
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
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**

Option Explicit

Private Sub LB_Nom_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
' @desc: При двойном клике по списку номенклатур открывает форму редактирования выбранной записи.
' @role: UI
' @todo: Убедиться, что ListIndex проверяется в Btn_Change_Click, чтобы избежать выхода за границы.
    Call Btn_Change_Click
End Sub

Private Sub LB_NomTypes_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
' @desc: При двойном клике по списку типов номенклатур открывает форму редактирования выбранного типа.
' @role: UI
' @todo: Логику всегда централизовать в Btn_Change_Click, как сейчас.
    Call Btn_Change_Click
End Sub

Private Sub LB_Roles_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
' @desc: При двойном клике по списку ролей открывает форму редактирования выбранной роли.
' @role: UI
' @todo: При большом количестве ролей можно добавить отдельную кнопку “Изменить”.
    Call Btn_Change_Click
End Sub

Private Sub LB_Services_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
' @desc: При двойном клике по списку служб открывает форму редактирования выбранной службы.
' @role: UI
' @todo: Следить за согласованностью индексов столбцов с источником данных.
    Call Btn_Change_Click
End Sub

Private Sub LB_Users_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
' @desc: При двойном клике по списку пользователей открывает форму редактирования выбранного пользователя.
' @role: UI
' @todo: При включённом поиске/фильтре убедиться, что данные в LB и в F_Change совпадают.
    Call Btn_Change_Click
End Sub

Private Sub Btn_Add_Click()
' @desc: В зависимости от выбранного раздела (ID_table_lists) открывает форму F_Change в режиме добавления нужной сущности.
' @role: UI
' @todo: Повторяющуюся логику загрузки справочников (ролей, типов НМ) вынести в отдельные helper-процедуры.
    On Error GoTo EH
    Dim rs As DAO.Recordset
    Dim rowCount As Long
    Select Case ID_table_lists
        Case 0:
            ActionBut = "Add"
            ID_table_change = 0
            Load F_Change
            F_Change.PrepareFormForAdd
            F_Change.Show vbModal
            UserForm_Initialize
        Case 1:
            ActionBut = "Add"
            ID_table_change = 1
            Load F_Change
            F_Change.PrepareFormForAdd
            Set rs = GetAllRoles()
            If rs.EOF Then
                Set rs = Nothing
                F_Change.ComB_UserRole.AddItem "Роли не найдены."
            Else
                rs.MoveLast
                rowCount = rs.RecordCount
                rs.MoveFirst
                F_Change.ComB_UserRole.ColumnCount = 8
                F_Change.ComB_UserRole.ColumnWidths = "0 pt;" & F_Change.ComB_UserRole.Width - 2 & " pt;0 pt;0 pt;0 pt;0 pt;0 pt;0 pt"
                F_Change.ComB_UserRole.List = Transpose2D(rs.GetRows(rowCount))
            End If
            F_Change.Show vbModal
            UserForm_Initialize
        Case 2:
            ActionBut = "Add"
            ID_table_change = 2
            Load F_Change
            F_Change.PrepareFormForAdd
            F_Change.Show vbModal
            UserForm_Initialize
        Case 3:
            ActionBut = "Add"
            ID_table_change = 3
            Load F_Change
            F_Change.PrepareFormForAdd
            Set rs = GetAllNomenclatureTypes()
            If rs.EOF Then
                Set rs = Nothing
                F_Change.ComB_NomType.Value = "Типы не найдены."
            Else
                rs.MoveLast
                rowCount = rs.RecordCount
                rs.MoveFirst
                F_Change.ComB_NomType.ColumnCount = 5
                F_Change.ComB_NomType.ColumnWidths = "0 pt;" & F_Change.ComB_NomType.Width - 2 & " pt;0 pt;0 pt;0 pt"
                F_Change.ComB_NomType.List = Transpose2D(rs.GetRows(rowCount))
            End If
            F_Change.Show vbModal
            UserForm_Initialize
        Case 4:
            ActionBut = "Add"
            ID_table_change = 4
            Load F_Change
            F_Change.TB_ServicesName.Tag = 0
            F_Change.PrepareFormForAdd
            F_Change.Show vbModal
            UserForm_Initialize
    End Select
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Exit Sub
EH:
    ShowError "F_ListDB.Btn_Add_Click", Err.Number, Err.description
    Resume CleanExit
End Sub

Private Sub Btn_Change_Click()
' @desc: Открывает F_Change в режиме изменения, заполняя её данными выбранной строки (роль, пользователь, тип НМ, НМ, служба).
' @role: UI
' @todo: Код сильно разветвлён; позже можно разбить отдельные кейсы (Roles/Users/NomTypes/Noms/Services) на отдельные процедуры.
    On Error GoTo EH
    Dim rs As DAO.Recordset
    Dim rowCount As Long
    Select Case ID_table_lists
        Case 0:
            If Me.LB_Roles.ListIndex < 1 Then
                ShowWarning "Выберите роль для редактирования.", vbExclamation
                Exit Sub
            Else
                ActionBut = "Change"
                ID_table_change = 0
                Load F_Change
                
                F_Change.PrepareFormForChange
                F_Change.TB_RoleName.Tag = NzLng(LB_Roles.List(LB_Roles.ListIndex, 0))
                F_Change.TB_RoleName.Value = NzStr(LB_Roles.List(LB_Roles.ListIndex, 1))
                F_Change.TB_RoleDescription.Value = NzStr(LB_Roles.List(LB_Roles.ListIndex, 2))
                F_Change.CB_CanManageUsers.Value = IIf(NzStr(LB_Roles.List(LB_Roles.ListIndex, 3)) = "Да", True, False)
                F_Change.CB_CanManageAdmin.Value = IIf(NzStr(LB_Roles.List(LB_Roles.ListIndex, 4)) = "Да", True, False)
                F_Change.CB_CanEditAny.Value = IIf(NzStr(LB_Roles.List(LB_Roles.ListIndex, 5)) = "Да", True, False)
                F_Change.CB_CanApproveAny.Value = IIf(NzStr(LB_Roles.List(LB_Roles.ListIndex, 6)) = "Да", True, False)
                F_Change.CB_CanChangeOwnPWD.Value = IIf(NzStr(LB_Roles.List(LB_Roles.ListIndex, 7)) = "Да", True, False)
                
                F_Change.Show vbModal
                UserForm_Initialize
            End If
        Case 1:
            If Me.LB_Users.ListIndex < 1 Then
                ShowWarning "Выберите пользователя для редактирования.", vbExclamation
                Exit Sub
            Else
                ActionBut = "Change"
                ID_table_change = 1
                Set rs = GetAllRoles()
                Load F_Change
                
                F_Change.PrepareFormForChange
                F_Change.TB_UserLogin.Tag = NzLng(LB_Users.List(LB_Users.ListIndex, 0))
                F_Change.TB_UserLogin.Value = NzStr(LB_Users.List(LB_Users.ListIndex, 1))
                F_Change.TB_UserFullName.Value = NzStr(LB_Users.List(LB_Users.ListIndex, 2))
                If rs.EOF Then
                    Set rs = Nothing
                    F_Change.ComB_UserRole.AddItem "Роли не найдены."
                Else
                    rs.MoveLast
                    rowCount = rs.RecordCount
                    rs.MoveFirst
                    F_Change.ComB_UserRole.ColumnCount = 8
                    F_Change.ComB_UserRole.ColumnWidths = "0 pt;" & F_Change.ComB_UserRole.Width - 2 & " pt;0 pt;0 pt;0 pt;0 pt;0 pt;0 pt"
                    F_Change.ComB_UserRole.List = Transpose2D(rs.GetRows(rowCount))
                    F_Change.ComB_UserRole.Text = NzStr(LB_Users.List(LB_Users.ListIndex, 3))
                End If
                F_Change.CB_UserIsActive.Value = IIf(NzStr(LB_Users.List(LB_Users.ListIndex, 4)) = "Да", True, False)
                
                F_Change.Show vbModal
                UserForm_Initialize
            End If
        Case 2:
            If Me.LB_NomTypes.ListIndex < 1 Then
                ShowWarning "Выберите тип для редактирования.", vbExclamation
                Exit Sub
            Else
                ActionBut = "Change"
                ID_table_change = 2
                Load F_Change
                
                F_Change.PrepareFormForChange
                F_Change.TB_NomTypesName.Tag = NzLng(LB_NomTypes.List(LB_NomTypes.ListIndex, 0))
                F_Change.TB_NomTypesName.Value = NzStr(LB_NomTypes.List(LB_NomTypes.ListIndex, 1))
                F_Change.TB_NomTypesKod.Value = NzStr(LB_NomTypes.List(LB_NomTypes.ListIndex, 2))
                F_Change.TB_NomTypesDescription.Value = NzStr(LB_NomTypes.List(LB_NomTypes.ListIndex, 3))
                F_Change.CB_NomTypesIsActive.Value = IIf(NzStr(LB_NomTypes.List(LB_NomTypes.ListIndex, 4)) = "Да", True, False)
                
                F_Change.Show vbModal
                UserForm_Initialize
            End If
        Case 3:
            If Me.LB_Nom.ListIndex < 1 Then
                ShowWarning "Выберите номенклатуру для редактирования.", vbExclamation
                Exit Sub
            Else
                ActionBut = "Change"
                ID_table_change = 3
                Set rs = GetAllNomenclatureTypes()
                Load F_Change
                
                F_Change.PrepareFormForChange
                F_Change.ComB_NomType.Tag = NzLng(LB_Nom.List(LB_Nom.ListIndex, 0))
                F_Change.TB_NomKod.Value = NzStr(LB_Nom.List(LB_Nom.ListIndex, 2))
                F_Change.TB_NomName.Value = NzStr(LB_Nom.List(LB_Nom.ListIndex, 3))
                F_Change.TB_NomDescription.Value = NzStr(LB_Nom.List(LB_Nom.ListIndex, 4))
                If rs.EOF Then
                    Set rs = Nothing
                    F_Change.ComB_NomType.Value = "Типы не найдены."
                Else
                    rs.MoveLast
                    rowCount = rs.RecordCount
                    rs.MoveFirst
                    F_Change.ComB_NomType.ColumnCount = 5
                    F_Change.ComB_NomType.ColumnWidths = "0 pt;" & F_Change.ComB_NomType.Width - 2 & " pt;0 pt;0 pt;0 pt"
                    F_Change.ComB_NomType.List = Transpose2D(rs.GetRows(rowCount))
                End If
                F_Change.ComB_NomType.Text = NzStr(LB_Nom.List(LB_Nom.ListIndex, 1))
                
                F_Change.Show vbModal
                UserForm_Initialize
            End If
        Case 4:
            If Me.LB_Services.ListIndex < 1 Then
                ShowWarning "Выберите службу для редактирования.", vbExclamation
                Exit Sub
            Else
                ActionBut = "Change"
                ID_table_change = 4
                Load F_Change
                
                F_Change.TB_ServicesName.Tag = NzLng(LB_Services.List(LB_Services.ListIndex, 0))
                F_Change.PrepareFormForChange
                F_Change.TB_ServicesName.Value = NzStr(LB_Services.List(LB_Services.ListIndex, 1))
                F_Change.TB_ServicesCode.Value = NzStr(LB_Services.List(LB_Services.ListIndex, 2))
                F_Change.TB_ServicesDescription.Value = NzStr(LB_Services.List(LB_Services.ListIndex, 3))
                F_Change.CB_ServicesIsActive.Value = IIf(NzStr(LB_Services.List(LB_Services.ListIndex, 4)) = "Да", True, False)
                
                F_Change.Show vbModal
                UserForm_Initialize
            End If
    End Select
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Exit Sub
EH:
    ShowError "F_ListDB.Btn_Change_Click", Err.Number, Err.description
    Resume CleanExit
End Sub

Private Sub Btn_Delete_Click()
' @desc: В зависимости от текущего раздела удаляет выбранную запись через соответствующий Safe-метод и обновляет список.
' @role: UI
' @todo: Для единообразия добавить обработчик EH и ShowError, как в Btn_Add/Btn_Change.
    On Error GoTo EH
    Select Case ID_table_lists
        Case 0:
            If Me.LB_Roles.ListIndex < 1 Then
                ShowWarning "Невозможно удалить строку заголовков.", vbExclamation
                Exit Sub
            Else
                Call DeleteRoleSafe(Me.LB_Roles.List(Me.LB_Roles.ListIndex, 0), g_CurrentUserID)
                UserForm_Initialize
            End If
        Case 1:
            If Me.LB_Users.ListIndex < 1 Then
                ShowWarning "Невозможно удалить строку заголовков.", vbExclamation
                Exit Sub
            Else
                Call DeleteUserSmart(Me.LB_Users.List(Me.LB_Users.ListIndex, 0), g_CurrentUserID)
                UserForm_Initialize
            End If
        Case 2:
            If Me.LB_NomTypes.ListIndex < 1 Then
                ShowWarning "Невозможно удалить строку заголовков.", vbExclamation
                Exit Sub
            Else
                Call DeleteNomenclatureTypeSafe(Me.LB_NomTypes.List(Me.LB_NomTypes.ListIndex, 0), g_CurrentUserID)
                UserForm_Initialize
            End If
        Case 3:
            If Me.LB_Nom.ListIndex < 1 Then
                ShowWarning "Невозможно удалить строку заголовков.", vbExclamation
                Exit Sub
            Else
                Call DeleteNomenclatureSafe(Me.LB_Nom.List(Me.LB_Nom.ListIndex, 0), g_CurrentUserID)
                UserForm_Initialize
            End If
        Case 4:
            If Me.LB_Services.ListIndex < 1 Then
                ShowWarning "Невозможно удалить строку заголовков.", vbExclamation
                Exit Sub
            Else
                Call DeleteServiceSafe(Me.LB_Services.List(Me.LB_Services.ListIndex, 0), g_CurrentUserID)
                UserForm_Initialize
            End If
    End Select
End Sub

Private Sub Btn_Cansel_Click()
' @desc: Прячет форму списков без изменения данных.
' @role: UI
' @todo: Переименовать в Btn_Cancel_Click для единообразия в проекте.
    Me.Hide
End Sub

Private Sub UserForm_Initialize()
' @desc: При создании формы вызывает PrepareForm для настройки вкладки и заполнения списков по текущему разделу.
' @role: UI
' @todo: Если PrepareForm кидает ошибку, она уже ловится внутри, так что здесь отдельный handler не нужен.
    Call PrepareForm
End Sub

Public Sub PrepareForm()
' @desc: Настраивает внешний вид формы (MultiPage, размеры, заголовок) и заполняет нужный ListBox по ID_table_lists.
' @role: UI
' @todo: Вынести расчёт размеров и позиции кнопок в отдельный helper, чтобы не дублировать в других формах.
    On Error GoTo ErrRS
    MP_Change.Style = fmTabStyleNone
    MP_Change.Value = ID_table_lists
    MP_Change.Height = Me.Controls("Frame" & ID_table_lists).Height
    MP_Change.Width = Frame0.Width
    Me.Height = MP_Change.Top + MP_Change.Height + 29
    Me.Width = MP_Change.Width + 14
    Select Case ID_table_lists
        Case 0:
            Me.Caption = "Редактирование ролей - " & g_CurrentLogin
            FillRolesListBox Me.LB_Roles
        Case 1:
            Me.Caption = "Редактирование пользователей - " & g_CurrentLogin
            FillUsersListBox Me.LB_Users
        Case 2:
            Me.Caption = "Типы номенклатур - " & g_CurrentLogin
            FillNomTypesListBox Me.LB_NomTypes
        Case 3:
            Me.Caption = "Номенклатуры - " & g_CurrentLogin
            FillNomListBox Me.LB_Nom
        Case 4:
            Me.Caption = "Службы - " & g_CurrentLogin
            FillServicesListBox Me.LB_Services
    End Select
    Exit Sub
ErrRS:
    ShowError "F_ListDB.PrepareForm", Err.Number, Err.description
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
' @desc: При закрытии по крестику не выгружает форму, а только скрывает её (Hide), чтобы сохранить состояние.
' @role: UI
' @todo: Если нужно очищать состояние между открытиями, добавить Reset-логику перед Hide.
    If CloseMode = vbFormControlMenu Then
        Cancel = True
        Me.Hide
    End If
End Sub
```

## Черновые заметки