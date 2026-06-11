#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--hidden"]),
        ))
        .setup(|_app| {
            tracing_subscriber::fmt()
                .with_env_filter(
                    tracing_subscriber::EnvFilter::try_from_default_env()
                        .unwrap_or_else(|_| "info".into()),
                )
                .init();
            tracing::info!("starlight-voice tauri shell starting");
            match sidecar::health_json() {
                Ok(health) => tracing::info!(sidecar.health = %health, "sidecar health check passed"),
                Err(err) => tracing::warn!(sidecar.error = %err, "sidecar health check unavailable"),
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
