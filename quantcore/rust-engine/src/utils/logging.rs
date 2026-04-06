//! 日志模块

use log::{debug, error, info, warn};

/// 初始化日志
pub fn init_logger() {
    env_logger::init();
}

/// 记录信息
pub fn log_info(message: &str) {
    info!("{}", message);
}

/// 记录警告
pub fn log_warn(message: &str) {
    warn!("{}", message);
}

/// 记录错误
pub fn log_error(message: &str) {
    error!("{}", message);
}

/// 记录调试信息
pub fn log_debug(message: &str) {
    debug!("{}", message);
}
