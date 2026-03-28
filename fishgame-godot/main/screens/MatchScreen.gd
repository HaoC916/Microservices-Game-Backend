extends "res://main/Screen.gd"

onready var matchmaker_player_count_control := $PanelContainer/VBoxContainer/MatchPanel/SpinBox
onready var join_match_id_control := $PanelContainer/VBoxContainer/JoinPanel/LineEdit

const AUTOTEST_REPEAT_COUNT := 20
const AUTOTEST_COOLDOWN_SEC := 2.0
const AUTOTEST_MATCH_TIMEOUT_SEC := 12.0
const HOTKEY_HELP_TEXT := "Hotkeys\nF8: Print log file path\nF9: Toggle AutoTest matchmaking (20x, 2s cooldown)\nF10: Toggle this help"

var _autotest_running := false
var _autotest_stop_requested := false
var _autotest_match_found := false
var _help_overlay: Label = null
var _help_overlay_visible := false

func _ready() -> void:
	$PanelContainer/VBoxContainer/MatchPanel/MatchButton.connect("pressed", self, "_on_match_button_pressed", [OnlineMatch.MatchMode.MATCHMAKER])
	$PanelContainer/VBoxContainer/CreatePanel/CreateButton.connect("pressed", self, "_on_match_button_pressed", [OnlineMatch.MatchMode.CREATE])
	$PanelContainer/VBoxContainer/JoinPanel/JoinButton.connect("pressed", self, "_on_match_button_pressed", [OnlineMatch.MatchMode.JOIN])
	$LogoutButton.connect("pressed", self, "_on_LogoutButton_pressed")

	OnlineMatch.connect("match_joined", self, "_on_OnlineMatch_joined")
	set_process_unhandled_input(true)
	_setup_hotkey_help_overlay()

func _show_screen(_info: Dictionary = {}) -> void:
	matchmaker_player_count_control.value = 2
	join_match_id_control.text = ''
	_autotest_match_found = false
	if _help_overlay:
		_help_overlay.visible = _help_overlay_visible

func _on_match_button_pressed(mode) -> void:
	var ready_state = _ensure_online_ready("MatchScreen")
	if ready_state is GDScriptFunctionState:
		ready_state = yield(ready_state, "completed")
	if not ready_state:
		return

	ui_layer.hide_message()

	# Call internal method to do actual work.
	match mode:
		OnlineMatch.MatchMode.MATCHMAKER:
			_start_matchmaking()
		OnlineMatch.MatchMode.CREATE:
			_create_match()
		OnlineMatch.MatchMode.JOIN:
			_join_match()

func _ensure_online_ready(next_screen_after_login = null):
	# If our session has expired, show the ConnectionScreen again.
	if Online.nakama_session == null or Online.nakama_session.is_expired():
		ui_layer.show_screen("ConnectionScreen", { reconnect = true, next_screen = next_screen_after_login })

		# Wait to see if we get a new valid session.
		yield(Online, "session_changed")
		if Online.nakama_session == null or Online.nakama_session.is_expired():
			return false

	# Connect socket to realtime Nakama API if not connected.
	if not Online.is_nakama_socket_connected():
		Online.connect_nakama_socket()
		yield(Online, "socket_connected")

	return true

func _start_matchmaking() -> void:
	var min_players = matchmaker_player_count_control.value

	ui_layer.hide_screen()
	ui_layer.show_message("Looking for match...")

	var data = {
		min_count = min_players,
		string_properties = {
			game = "fish_game",
			engine = "godot",
		},
		query = "+properties.game:fish_game +properties.engine:godot",
	}

	OnlineMatch.start_matchmaking(Online.nakama_socket, data)

func _leave_online_state():
	var leave_state = OnlineMatch.leave()
	if leave_state is GDScriptFunctionState:
		yield(leave_state, "completed")

func _wait_for_match_or_timeout(timeout_sec: float):
	var start_msec := OS.get_ticks_msec()
	while not _autotest_stop_requested and not _autotest_match_found:
		var elapsed_sec = float(OS.get_ticks_msec() - start_msec) / 1000.0
		if elapsed_sec >= timeout_sec:
			return false
		yield(get_tree().create_timer(0.2), "timeout")

	return _autotest_match_found

func _run_autotest() -> void:
	Online.log_event("[AUTOTEST] mode=on iterations=%s" % str(AUTOTEST_REPEAT_COUNT))
	for i in range(AUTOTEST_REPEAT_COUNT):
		if _autotest_stop_requested:
			break

		var ready_state = _ensure_online_ready("MatchScreen")
		if ready_state is GDScriptFunctionState:
			ready_state = yield(ready_state, "completed")
		if not ready_state:
			Online.log_event("[AUTOTEST] stopping:no_valid_session")
			break

		_autotest_match_found = false
		Online.log_event("[AUTOTEST] start_matchmaking")
		_start_matchmaking()

		var found = _wait_for_match_or_timeout(AUTOTEST_MATCH_TIMEOUT_SEC)
		if found is GDScriptFunctionState:
			found = yield(found, "completed")

		var leave_state = _leave_online_state()
		if leave_state is GDScriptFunctionState:
			yield(leave_state, "completed")

		ui_layer.hide_message()
		ui_layer.show_screen("MatchScreen")

		if not found:
			Online.log_event("[AUTOTEST] timeout_cancel_matchmaking")

		if _autotest_stop_requested:
			break

		yield(get_tree().create_timer(AUTOTEST_COOLDOWN_SEC), "timeout")

	_autotest_running = false
	_autotest_stop_requested = false
	_autotest_match_found = false
	Online.log_event("[AUTOTEST] mode=off")

func _create_match() -> void:
	OnlineMatch.create_match(Online.nakama_socket)

func _join_match() -> void:
	var match_id = join_match_id_control.text.strip_edges()
	if match_id == '':
		ui_layer.show_message("Need to paste Match ID to join")
		return
	if not match_id.ends_with('.'):
		match_id += '.'

	OnlineMatch.join_match(Online.nakama_socket, match_id)

func _on_OnlineMatch_joined(match_id: String, match_mode: int):
	if _autotest_running and match_mode == OnlineMatch.MatchMode.MATCHMAKER:
		_autotest_match_found = true
		Online.log_event("[AUTOTEST] match_joined")
		return

	var info = {
		players = OnlineMatch.players,
		clear = true,
	}

	if match_mode != OnlineMatch.MatchMode.MATCHMAKER:
		info['match_id'] = match_id

	ui_layer.show_screen("ReadyScreen", info)

func _on_PasteButton_pressed() -> void:
	join_match_id_control.text = OS.clipboard

func _on_LeaderboardButton_pressed() -> void:
	ui_layer.show_screen("LeaderboardScreen")

func _show_connection_screen_after_logout() -> void:
	ui_layer.hide_screen()
	ui_layer.hide_message()
	ui_layer.show_screen("ConnectionScreen", {
		reconnect = false,
		next_screen = "MatchScreen",
		skip_auto_login = true,
	})

func _on_LogoutButton_pressed() -> void:
	_autotest_stop_requested = true
	_autotest_running = false
	ui_layer.show_message("Logging out...")

	var logout_state = Online.logout()
	if logout_state is GDScriptFunctionState:
		yield(logout_state, "completed")

	_show_connection_screen_after_logout()

func _setup_hotkey_help_overlay() -> void:
	_help_overlay = Label.new()
	_help_overlay.name = "HotkeyHelpOverlay"
	_help_overlay.text = HOTKEY_HELP_TEXT
	_help_overlay.rect_position = Vector2(12, 12)
	_help_overlay.rect_min_size = Vector2(560, 80)
	_help_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_help_overlay.modulate = Color(1, 1, 1, 0.85)
	_help_overlay.add_color_override("font_color_shadow", Color(0, 0, 0, 0.9))
	_help_overlay.add_constant_override("shadow_offset_x", 1)
	_help_overlay.add_constant_override("shadow_offset_y", 1)
	add_child(_help_overlay)
	_help_overlay.visible = _help_overlay_visible

func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return

	if event.scancode == KEY_F8:
		# F8 is intentionally non-destructive: print log path only.
		Online.open_log_path()
		get_tree().set_input_as_handled()
		return

	if event.scancode == KEY_F10:
		_help_overlay_visible = not _help_overlay_visible
		if _help_overlay:
			_help_overlay.visible = _help_overlay_visible
		Online.log_event("help_overlay_visible=" + str(_help_overlay_visible))
		get_tree().set_input_as_handled()
		return

	if event.scancode == KEY_F9:
		if _autotest_running:
			_autotest_stop_requested = true
			Online.log_event("[AUTOTEST] stop_requested")
			get_tree().set_input_as_handled()
			return

		_autotest_running = true
		_autotest_stop_requested = false
		_run_autotest()
		get_tree().set_input_as_handled()
