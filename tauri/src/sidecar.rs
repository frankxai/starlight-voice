use std::path::PathBuf;
use std::process::Command;

pub fn sidecar_src_path() -> Result<PathBuf, String> {
    let cwd = std::env::current_dir().map_err(|err| err.to_string())?;
    Ok(cwd.join("sidecar").join("src"))
}

pub fn health_json() -> Result<String, String> {
    let pythonpath = sidecar_src_path()?;
    let output = Command::new("python")
        .args(["-m", "starlight_voice", "health"])
        .env("PYTHONPATH", pythonpath)
        .output()
        .map_err(|err| format!("failed to start Python sidecar: {err}"))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}
