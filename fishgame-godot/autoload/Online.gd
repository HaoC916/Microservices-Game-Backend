extends Node

# For developers to set from the outside, for example:
#   Online.nakama_host = 'nakama.example.com'
#   Online.nakama_scheme = 'https'
var nakama_server_key: String = 'defaultkey'
var nakama_host: String = '8.229.101.251'
var nakama_port: int = 7350
var nakama_scheme: String = 'http'
var admin_api_host: String = nakama_host
var admin_api_port: int = 8000
var telemetry_mode: String = "async" # allowed: off|async|sync
var write_logs_to_file := true

const LOG_FILE_PATH := "user://cmpt756_latency_log.txt"
const NAKAMA_HOST_FILE := "user://nakama_host.txt"
const ADMIN_API_HOST_FILE := "user://admin_api_host.txt"
const TELEMETRY_MODE_FILE := "user://telemetry_mode.txt"
const TELEMETRY_TIMEOUT_SECONDS := 2.0

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
	admin_api_host = nakama_host
	_load_admin_api_host_override()
	_load_telemetry_mode_override()
	log_event("nakama_host=" + nakama_host)
	log_event("telemetry_mode=%s admin_api=%s:%s" % [telemetry_mode, admin_api_host, str(admin_api_port)])

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

func send_telemetry_event_sync(event_name: String, payload: Dictionary = {}):
	var event_payload = {
		event = event_name,
		ts_ms = OS.get_ticks_msec(),
		client_mode = telemetry_mode,
		client_tag = "fishgame",
	}
	for key in payload:
		event_payload[key] = payload[key]

	var request = HTTPRequest.new()
	request.timeout = TELEMETRY_TIMEOUT_SECONDS
	add_child(request)

	var err = request.request(
		_get_telemetry_url(),
		["Content-Type: application/json"],
		true,
		HTTPClient.METHOD_POST,
		JSON.print(event_payload)
	)
	if err != OK:
		request.queue_free()
		return {
			ok = false,
			error = "request_start_failed:%s" % str(err),
		}

	var result = yield(request, "request_completed")
	request.queue_free()

	var request_result = result[0]
	var response_code = result[1]
	if request_result != HTTPRequest.RESULT_SUCCESS:
		return {
			ok = false,
			error = "request_failed:%s" % str(request_result),
			status_code = response_code,
		}

	return {
		ok = true,
		status_code = response_code,
	}

func send_telemetry_event_async(event_name: String, payload: Dictionary = {}) -> void:
	var event_payload = {
		event = event_name,
		ts_ms = OS.get_ticks_msec(),
		client_mode = telemetry_mode,
		client_tag = "fishgame",
	}
	for key in payload:
		event_payload[key] = payload[key]

	var request = HTTPRequest.new()
	request.timeout = TELEMETRY_TIMEOUT_SECONDS
	add_child(request)
	request.connect("request_completed", self, "_on_async_telemetry_request_completed", [request], CONNECT_ONESHOT)

	var err = request.request(
		_get_telemetry_url(),
		["Content-Type: application/json"],
		true,
		HTTPClient.METHOD_POST,
		JSON.print(event_payload)
	)
	if err != OK:
		request.queue_free()
		log_event("telemetry_async_fail:request_start_failed:%s" % str(err))

func _on_async_telemetry_request_completed(_result: int, _response_code: int, _headers: PoolStringArray, _body: PoolByteArray, request: HTTPRequest) -> void:
	if is_instance_valid(request):
		request.queue_free()

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

func _load_admin_api_host_override() -> void:
	var file = File.new()
	if not file.file_exists(ADMIN_API_HOST_FILE):
		return
	if file.open(ADMIN_API_HOST_FILE, File.READ) != OK:
		return

	var file_host = file.get_line().strip_edges()
	file.close()
	if file_host != "":
		admin_api_host = file_host

func _load_telemetry_mode_override() -> void:
	var file = File.new()
	if not file.file_exists(TELEMETRY_MODE_FILE):
		telemetry_mode = _normalize_telemetry_mode(telemetry_mode)
		return
	if file.open(TELEMETRY_MODE_FILE, File.READ) != OK:
		telemetry_mode = _normalize_telemetry_mode(telemetry_mode)
		return

	var file_mode = file.get_line().strip_edges()
	file.close()
	if file_mode != "":
		telemetry_mode = _normalize_telemetry_mode(file_mode)
	else:
		telemetry_mode = _normalize_telemetry_mode(telemetry_mode)

func _normalize_telemetry_mode(value: String) -> String:
	var mode = value.to_lower().strip_edges()
	if mode != "off" and mode != "async" and mode != "sync":
		return "async"
	return mode

func _get_telemetry_url() -> String:
	return "http://%s:%s/telemetry/event" % [admin_api_host, str(admin_api_port)]
