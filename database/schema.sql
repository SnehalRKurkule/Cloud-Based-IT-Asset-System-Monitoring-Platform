CREATE DATABASE IF NOT EXISTS it_monitoring;
USE it_monitoring;

CREATE TABLE IF NOT EXISTS assets (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    os VARCHAR(100),
    asset_type VARCHAR(50) DEFAULT 'Linux Server',
    location VARCHAR(100) DEFAULT 'Local',
    status ENUM('HEALTHY','WARNING','CRITICAL','OFFLINE') DEFAULT 'HEALTHY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    cpu_usage DECIMAL(5,2) NOT NULL,
    memory_usage DECIMAL(5,2) NOT NULL,
    disk_usage DECIMAL(5,2) NOT NULL,
    uptime_seconds BIGINT DEFAULT 0,
    overall_status ENUM('HEALTHY','WARNING','CRITICAL') NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_metrics_asset FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
    INDEX idx_metrics_asset_time (asset_id, recorded_at)
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    metric_type VARCHAR(30) NOT NULL,
    metric_value DECIMAL(7,2) NOT NULL,
    threshold DECIMAL(7,2) NOT NULL,
    severity ENUM('WARNING','CRITICAL') NOT NULL,
    status ENUM('OPEN','RESOLVED') DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    CONSTRAINT fk_alerts_asset FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
    INDEX idx_alerts_asset_status (asset_id, metric_type, status)
);
