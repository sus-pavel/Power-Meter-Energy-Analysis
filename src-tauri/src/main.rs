use serde::Serialize;
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};
use tauri::{AppHandle, Manager, State};

const BACKEND_PORT: u16 = 8765;

#[derive(Clone, Debug, Serialize)]
struct BackendState {
    phase: String,
    message: String,
    app_data_dir: Option<String>,
    db_path: Option<String>,
    log_dir: Option<String>,
    port: u16,
}

impl BackendState {
    fn starting(app_paths: &AppPaths) -> Self {
        Self {
            phase: "starting".into(),
            message: "Starting backend...".into(),
            app_data_dir: Some(app_paths.app_data_dir.to_string_lossy().into_owned()),
            db_path: Some(app_paths.db_path.to_string_lossy().into_owned()),
            log_dir: Some(app_paths.log_dir.to_string_lossy().into_owned()),
            port: BACKEND_PORT,
        }
    }

    fn ready(app_paths: &AppPaths, message: impl Into<String>) -> Self {
        Self {
            phase: "ready".into(),
            message: message.into(),
            app_data_dir: Some(app_paths.app_data_dir.to_string_lossy().into_owned()),
            db_path: Some(app_paths.db_path.to_string_lossy().into_owned()),
            log_dir: Some(app_paths.log_dir.to_string_lossy().into_owned()),
            port: BACKEND_PORT,
        }
    }

    fn error(app_paths: &AppPaths, message: impl Into<String>) -> Self {
        Self {
            phase: "error".into(),
            message: message.into(),
            app_data_dir: Some(app_paths.app_data_dir.to_string_lossy().into_owned()),
            db_path: Some(app_paths.db_path.to_string_lossy().into_owned()),
            log_dir: Some(app_paths.log_dir.to_string_lossy().into_owned()),
            port: BACKEND_PORT,
        }
    }

    fn port_in_use(app_paths: &AppPaths) -> Self {
        Self {
            phase: "port_in_use".into(),
            message: "Port 8765 is already occupied. PowerMeter did not start a backend and will not terminate the existing process.".into(),
            app_data_dir: Some(app_paths.app_data_dir.to_string_lossy().into_owned()),
            db_path: Some(app_paths.db_path.to_string_lossy().into_owned()),
            log_dir: Some(app_paths.log_dir.to_string_lossy().into_owned()),
            port: BACKEND_PORT,
        }
    }
}

#[derive(Clone, Debug)]
struct AppPaths {
    app_data_dir: PathBuf,
    db_path: PathBuf,
    log_dir: PathBuf,
    desktop_log_path: PathBuf,
}

struct BackendSupervisor {
    child: Mutex<Option<Child>>,
    state: Mutex<BackendState>,
    paths: AppPaths,
}

#[tauri::command]
fn backend_state(supervisor: State<'_, BackendSupervisor>) -> BackendState {
    supervisor.state.lock().expect("backend state lock").clone()
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![backend_state])
        .setup(|app| {
            let paths = app_paths()?;
            ensure_app_dirs(&paths)?;
            log_line(&paths, "PowerMeter desktop shell starting");

            let supervisor = BackendSupervisor {
                child: Mutex::new(None),
                state: Mutex::new(BackendState::starting(&paths)),
                paths: paths.clone(),
            };
            app.manage(supervisor);

            let handle = app.handle().clone();
            if let Err(err) = start_backend(&handle, &paths) {
                let message = format!("Backend startup failed: {err}");
                set_state(&handle, BackendState::error(&paths, &message));
                log_line(&paths, &message);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
                let handle = window.app_handle().clone();
                stop_backend(&handle);
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|handle, event| {
            if matches!(event, tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit) {
                stop_backend(handle);
            }
        });
}

fn app_paths() -> tauri::Result<AppPaths> {
    let app_data_dir = dirs::data_dir()
        .unwrap_or_else(|| dirs::home_dir().unwrap_or_else(|| PathBuf::from(".")))
        .join("PowerMeter");
    let log_dir = app_data_dir.join("logs");
    Ok(AppPaths {
        db_path: app_data_dir.join("app.sqlite"),
        desktop_log_path: log_dir.join("desktop.log"),
        app_data_dir,
        log_dir,
    })
}

fn ensure_app_dirs(paths: &AppPaths) -> tauri::Result<()> {
    for dir in [
        &paths.app_data_dir,
        &paths.log_dir,
        &paths.app_data_dir.join("config"),
        &paths.app_data_dir.join("exports"),
        &paths.app_data_dir.join("reports"),
        &paths.app_data_dir.join("cache"),
        &paths.app_data_dir.join("tmp"),
    ] {
        fs::create_dir_all(dir)?;
    }
    Ok(())
}

fn start_backend(app: &AppHandle, paths: &AppPaths) -> tauri::Result<()> {
    if port_accepts_connections(BACKEND_PORT) {
        let message = "Port 8765 is already occupied before launch; backend not started.";
        set_state(app, BackendState::port_in_use(paths));
        log_line(paths, message);
        return Ok(());
    }

    let backend_bin = resolve_backend_binary(app)?;
    let backend_log = paths.log_dir.join("backend.log");
    let backend_stderr_log = paths.log_dir.join("backend.stderr.log");
    let stdout = OpenOptions::new().create(true).append(true).open(&backend_log)?;
    let stderr = OpenOptions::new().create(true).append(true).open(&backend_stderr_log)?;
    let mut command = Command::new(&backend_bin);
    command
        .env("POWERMETER_DESKTOP", "1")
        .env("POWERMETER_DESKTOP_MODE", "1")
        .env("POWERMETER_HOST", "127.0.0.1")
        .env("POWERMETER_APP_DATA_DIR", &paths.app_data_dir)
        .env("POWERMETER_DB_PATH", &paths.db_path)
        .env("POWERMETER_PORT", BACKEND_PORT.to_string())
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr));
    if let Some(backend_dir) = backend_bin.parent() {
        command.current_dir(backend_dir);
    }

    let child = command.spawn()?;
    let child_pid = child.id();
    log_line(paths, &format!("Resolved backend executable: {}", backend_bin.display()));
    log_line(paths, &format!("App data directory: {}", paths.app_data_dir.display()));
    log_line(paths, &format!("Database path: {}", paths.db_path.display()));
    log_line(paths, &format!("Backend stdout log: {}", backend_log.display()));
    log_line(paths, &format!("Backend stderr log: {}", backend_stderr_log.display()));
    log_line(paths, &format!("Started backend child PID: {child_pid}"));
    app.state::<BackendSupervisor>()
        .child
        .lock()
        .expect("backend child lock")
        .replace(child);

    set_state(app, BackendState {
        phase: "checking".into(),
        message: "Checking backend health...".into(),
        app_data_dir: Some(paths.app_data_dir.to_string_lossy().into_owned()),
        db_path: Some(paths.db_path.to_string_lossy().into_owned()),
        log_dir: Some(paths.log_dir.to_string_lossy().into_owned()),
        port: BACKEND_PORT,
    });

    let deadline = Instant::now() + Duration::from_secs(45);
    while Instant::now() < deadline {
        if backend_health_is_powermeter() {
            set_state(app, BackendState::ready(paths, "Backend ready."));
            log_line(paths, "Backend health check passed");
            return Ok(());
        }
        thread::sleep(Duration::from_millis(500));
    }

    let message = "Backend did not become healthy within 45 seconds.";
    set_state(app, BackendState::error(paths, message));
    log_line(paths, message);
    Err(tauri::Error::Anyhow(anyhow::anyhow!(message)))
}

fn stop_backend(app: &AppHandle) {
    let supervisor = app.state::<BackendSupervisor>();
    let paths = supervisor.paths.clone();
    let maybe_child = supervisor.child.lock().expect("backend child lock").take();
    if let Some(mut child) = maybe_child {
        log_line(&paths, "Stopping backend sidecar");
        #[cfg(unix)]
        {
            let _ = unsafe { libc::kill(child.id() as i32, libc::SIGTERM) };
        }
        for _ in 0..20 {
            if matches!(child.try_wait(), Ok(Some(_))) {
                log_line(&paths, "Backend sidecar exited cleanly");
                return;
            }
            thread::sleep(Duration::from_millis(100));
        }
        if let Err(err) = child.kill() {
            log_line(&paths, &format!("Backend sidecar kill failed: {err}"));
        } else {
            let _ = child.wait();
            log_line(&paths, "Backend sidecar killed after graceful wait");
        }
    }
}

fn set_state(app: &AppHandle, state: BackendState) {
    if let Some(supervisor) = app.try_state::<BackendSupervisor>() {
        *supervisor.state.lock().expect("backend state lock") = state;
    }
}

fn resolve_backend_binary(app: &AppHandle) -> tauri::Result<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push(resource_dir.join("backend").join("powermeter-backend"));
    }
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            if let Some(contents_dir) = exe_dir.parent() {
                candidates.push(contents_dir.join("Resources").join("backend").join("powermeter-backend"));
            }
        }
    }
    candidates.push(PathBuf::from("../backend/dist/powermeter-backend/powermeter-backend"));
    candidates.push(PathBuf::from("backend/dist/powermeter-backend/powermeter-backend"));
    candidates
        .into_iter()
        .find(|candidate| candidate.exists())
        .ok_or_else(|| tauri::Error::Anyhow(anyhow::anyhow!("Backend sidecar binary was not found in app resources.")))
}

fn port_accepts_connections(port: u16) -> bool {
    let Ok(mut addrs) = ("127.0.0.1", port).to_socket_addrs() else {
        return false;
    };
    let Some(addr) = addrs.next() else {
        return false;
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok()
}

fn backend_health_is_powermeter() -> bool {
    let Ok(mut stream) = TcpStream::connect(("127.0.0.1", BACKEND_PORT)) else {
        return false;
    };
    let request = b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
    if stream.write_all(request).is_err() {
        return false;
    }
    let mut response = String::new();
    if stream.read_to_string(&mut response).is_err() {
        return false;
    }
    response.starts_with("HTTP/1.1 200") && response.contains("\"app\":\"PowerMeter\"") && response.contains("\"status\":\"ok\"")
}

fn log_line(paths: &AppPaths, message: &str) {
    let _ = fs::create_dir_all(&paths.log_dir);
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(&paths.desktop_log_path) {
        let _ = writeln!(file, "{message}");
    }
}
