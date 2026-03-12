extends Node

# For developers to set from the outside, for example:
#   Online.nakama_host = 'nakama.example.com'
#   Online.nakama_scheme = 'https'
var nakama_server_key: String = 'defaultkey'
var nakama_host: String = '8.229.245.89'
var nakama_port: int = 7350
var nakama_scheme: String = 'http'
var write_logs_to_file := true

const LOG_FILE_PATH := "user://cmpt756_latency_log.txt"
const NAKAMA_HOST_FILE := "user://nakama_host.txt"

# For other scripts to access:
var nakama_client: NakamaClient setget _set_readonly_variable, get_nakama_client
var nakama_session: NakamaSession setget set_nakama_session
var nakama_socket: NakamaSocket setget _set_readonly_variable

# Internal variable for initializing the socket.
var _nakama_socket_connecting := false
var _t0 := {}

signal session_changed (nakama_session)
signal session_connected (nakama_session)
signal socket_connected (nakama_socket)

func _set_readonly_variable(_value) -> void:
	pass

func _ready() -> void:
	# Don't stop processing messages from Nakama when the game is paused.
	Nakama.pause_mode = Node.PAUSE_MODE_PROCESS
	_load_nakama_host_override()
	log_event("nakama_host=" + nakama_host)

func get_nakama_client() -> NakamaClient:
	if nakama_client == null:
		nakama_client = Nakama.create_client(
			nakama_server_key,
			nakama_host,
			nakama_port,
			nakama_scheme,
			Nakama.DEFAULT_TIMEOUT,
			NakamaLogger.LOG_LEVEL.ERROR)

	return nakama_client

func set_nakama_session(_nakama_session: NakamaSession) -> void:
	nakama_session = _nakama_session

	emit_signal("session_changed", nakama_session)

	if nakama_session and not nakama_session.is_exception() and not nakama_session.is_expired():
		emit_signal("session_connected", nakama_session)

func connect_nakama_socket() -> void:
	if nakama_socket != null:
		return
	if _nakama_socket_connecting:
		return
	_nakama_socket_connecting = true

	var new_socket = Nakama.create_socket_from(nakama_client)
	yield(new_socket.connect_async(nakama_session), "completed")
	nakama_socket = new_socket
	_nakama_socket_connecting = false

	emit_signal("socket_connected", nakama_socket)

func is_nakama_socket_connected() -> bool:
	return nakama_socket != null && nakama_socket.is_connected_to_host()

func logout() -> void:
	log_event("logout")

	# Leave/cancel any in-progress online match or matchmaking state.
	var leave_state = OnlineMatch.leave(true)
	if leave_state is GDScriptFunctionState:
		yield(leave_state, "completed")

	# Ensure socket is closed and cleared.
	if nakama_socket:
		if nakama_socket.is_connected_to_host():
			nakama_socket.close()
		nakama_socket = null

	# Clear session/client state so next run starts cleanly.
	nakama_session = null
	nakama_client = null
	_nakama_socket_connecting = false
	_t0.clear()

func mark_start(tag: String) -> void:
	_t0[tag] = OS.get_ticks_msec()
	log_event(tag + "_start")

func mark_end(tag: String) -> int:
	if not _t0.has(tag):
		return -1
	var dt := OS.get_ticks_msec() - int(_t0[tag])
	_t0.erase(tag)
	log_latency(tag, dt)
	return dt

func log_event(msg: String) -> void:
	var timestamp = OS.get_ticks_msec()
	var line = "[EVENT] %s %s" % [str(timestamp), msg]
	print(line)
	_append_log_line(line)

func log_latency(tag: String, ms: int) -> void:
	var timestamp = OS.get_ticks_msec()
	var line = "[LATENCY] %s %s_ms=%s" % [str(timestamp), tag, str(ms)]
	print(line)
	_append_log_line(line)

func open_log_path() -> void:
	var path = ProjectSettings.globalize_path(LOG_FILE_PATH)
	log_event("log_path=" + path)

func _append_log_line(line: String) -> void:
	if not write_logs_to_file:
		return

	var file = File.new()
	var err = file.open(LOG_FILE_PATH, File.READ_WRITE)
	if err != OK:
		err = file.open(LOG_FILE_PATH, File.WRITE)
	if err != OK:
		print("[EVENT] ", OS.get_ticks_msec(), " log_write_failed=", err)
		return

	file.seek_end()
	file.store_line(line)
	file.close()

func _load_nakama_host_override() -> void:
	if OS.has_environment("NAKAMA_HOST"):
		var env_host = OS.get_environment("NAKAMA_HOST").strip_edges()
		if env_host != "":
			nakama_host = env_host
			return

	var file = File.new()
	if not file.file_exists(NAKAMA_HOST_FILE):
		return
	if file.open(NAKAMA_HOST_FILE, File.READ) != OK:
		return

	var file_host = file.get_line().strip_edges()
	file.close()
	if file_host != "":
		nakama_host = file_host
