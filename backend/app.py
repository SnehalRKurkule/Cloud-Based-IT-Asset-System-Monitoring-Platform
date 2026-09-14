from flask import Flask, jsonify, request, render_template
from db import get_db

app = Flask(__name__)

CPU_WARNING, CPU_CRITICAL = 70, 85
MEM_WARNING, MEM_CRITICAL = 80, 90
DISK_WARNING, DISK_CRITICAL = 80, 90


def metric_severity(value, warning, critical):
    if value >= critical:
        return "CRITICAL"
    if value >= warning:
        return "WARNING"
    return "HEALTHY"


def overall_status(cpu, memory, disk):
    levels = [
        metric_severity(cpu, CPU_WARNING, CPU_CRITICAL),
        metric_severity(memory, MEM_WARNING, MEM_CRITICAL),
        metric_severity(disk, DISK_WARNING, DISK_CRITICAL),
    ]
    if "CRITICAL" in levels:
        return "CRITICAL"
    if "WARNING" in levels:
        return "WARNING"
    return "HEALTHY"


def process_alert(cursor, asset_id, metric_type, value, warning, critical):
    severity = metric_severity(value, warning, critical)

    if severity == "HEALTHY":
        cursor.execute(
            """UPDATE alerts
               SET status='RESOLVED', resolved_at=NOW()
               WHERE asset_id=%s AND metric_type=%s AND status='OPEN'""",
            (asset_id, metric_type),
        )
        return

    threshold = critical if severity == "CRITICAL" else warning

    cursor.execute(
        """SELECT alert_id, severity FROM alerts
           WHERE asset_id=%s AND metric_type=%s AND status='OPEN'
           ORDER BY created_at DESC LIMIT 1""",
        (asset_id, metric_type),
    )
    existing = cursor.fetchone()

    if existing:
        if existing["severity"] != severity:
            cursor.execute(
                """UPDATE alerts
                    SET severity=%s, metric_value=%s, threshold=%s
                    WHERE alert_id=%s""",
                    (severity, value, threshold, existing["alert_id"]),
            )
    else:
        cursor.execute(
            """INSERT INTO alerts
               (asset_id, metric_type, metric_value, threshold, severity)
               VALUES (%s,%s,%s,%s,%s)""",
            (asset_id, metric_type, value, threshold, severity),
        )


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/assets", methods=["GET"])
def get_assets():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            a.asset_id,
            a.hostname,
            a.ip_address,
            a.os,
            a.status,
            a.updated_at,

            (
                SELECT m.cpu_usage
                FROM metrics m
                WHERE m.asset_id = a.asset_id
                ORDER BY m.metric_id DESC
                LIMIT 1
            ) AS cpu_usage,

            (
                SELECT m.memory_usage
                FROM metrics m
                WHERE m.asset_id = a.asset_id
                ORDER BY m.metric_id DESC
                LIMIT 1
            ) AS memory_usage,

            (
                SELECT m.disk_usage
                FROM metrics m
                WHERE m.asset_id = a.asset_id
                ORDER BY m.metric_id DESC
                LIMIT 1
            ) AS disk_usage

        FROM assets a
        ORDER BY a.hostname;
    """

    cursor.execute(query)
    assets = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(assets)


@app.route("/api/assets/register", methods=["POST"])
def register_asset():
    data = request.get_json(force=True)

    if not data.get("hostname"):
        return jsonify({"error": "hostname is required"}), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """INSERT INTO assets
           (hostname, ip_address, os, asset_type, location, status)
           VALUES (%s,%s,%s,%s,%s,'HEALTHY')
           ON DUPLICATE KEY UPDATE
             ip_address=VALUES(ip_address),
             os=VALUES(os),
             asset_type=VALUES(asset_type),
             location=VALUES(location)""",
        (
            data["hostname"], data.get("ip_address"), data.get("os"),
            data.get("asset_type", "Linux Server"), data.get("location", "Local")
        ),
    )

    db.commit()
    cursor.close()
    db.close()
    return jsonify({"message": "Asset registered successfully"}), 201


@app.route("/api/metrics", methods=["POST"])
def receive_metrics():
    data = request.get_json(force=True)
    required = ["hostname", "cpu_usage", "memory_usage", "disk_usage", "uptime_seconds"]

    if any(field not in data for field in required):
        return jsonify({"error": "Missing required metric fields"}), 400

    cpu = float(data["cpu_usage"])
    memory = float(data["memory_usage"])
    disk = float(data["disk_usage"])
    uptime = int(data["uptime_seconds"])
    status = overall_status(cpu, memory, disk)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT asset_id FROM assets WHERE hostname=%s", (data["hostname"],))
    asset = cursor.fetchone()

    if not asset:
        cursor.close()
        db.close()
        return jsonify({"error": "Asset not registered"}), 404

    asset_id = asset["asset_id"]

    cursor.execute(
        """INSERT INTO metrics
           (asset_id, cpu_usage, memory_usage, disk_usage, uptime_seconds, overall_status)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (asset_id, cpu, memory, disk, uptime, status),
    )

    process_alert(cursor, asset_id, "CPU", cpu, CPU_WARNING, CPU_CRITICAL)
    process_alert(cursor, asset_id, "MEMORY", memory, MEM_WARNING, MEM_CRITICAL)
    process_alert(cursor, asset_id, "DISK", disk, DISK_WARNING, DISK_CRITICAL)

    cursor.execute("UPDATE assets SET status=%s WHERE asset_id=%s", (status, asset_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": "Metrics received", "asset_id": asset_id, "status": status}), 201


@app.route("/api/dashboard/summary")
def dashboard_summary():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT COUNT(*) AS total_assets,
                  SUM(status='HEALTHY') AS healthy,
                  SUM(status='WARNING') AS warning,
                  SUM(status='CRITICAL') AS critical,
                  SUM(status='OFFLINE') AS offline
           FROM assets"""
    )
    summary = cursor.fetchone()
    cursor.close()
    db.close()

    for key in ["total_assets", "healthy", "warning", "critical", "offline"]:
        summary[key] = int(summary[key] or 0)

    return jsonify(summary)


@app.route("/api/alerts")
def get_alerts():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT a.alert_id, s.hostname, a.metric_type, a.metric_value,
                  a.threshold, a.severity, a.status, a.created_at, a.resolved_at
           FROM alerts a JOIN assets s ON a.asset_id=s.asset_id
           ORDER BY a.created_at DESC LIMIT 20"""
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)


@app.route("/api/assets/<int:asset_id>/metrics")
def asset_metrics(asset_id):
    limit = min(int(request.args.get("limit", 20)), 100)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT cpu_usage, memory_usage, disk_usage,
                  uptime_seconds, overall_status, recorded_at
           FROM metrics WHERE asset_id=%s
           ORDER BY recorded_at DESC LIMIT %s""",
        (asset_id, limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

#------------Route to get Specific Asset Details----------------
@app.route("/assets/<int:asset_id>")
def asset_details(asset_id):

    return render_template(
        "asset_details.html",
        asset_id=asset_id
    )

@app.route("/api/assets/<int:asset_id>", methods=["GET"])
def get_asset_details(asset_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            asset_id,
            hostname,
            ip_address,
            os,
            status,
            updated_at
        FROM assets
        WHERE asset_id = %s
    """

    cursor.execute(query, (asset_id,))

    asset = cursor.fetchone()

    cursor.close()
    db.close()

    if not asset:
        return jsonify({
            "error": "Asset not found"
        }), 404

    return jsonify(asset)

# -----------------------Metrics History Route-----------------------
@app.route("/api/assets/<int:asset_id>/metrics", methods=["GET"])
def get_asset_metrics(asset_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            metric_id,
            cpu_usage,
            memory_usage,
            disk_usage,
            recorded_at
        FROM metrics
        WHERE asset_id = %s
        ORDER BY timestamp ASC
        LIMIT 100
    """

    cursor.execute(query, (asset_id,))

    metrics = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(metrics)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
