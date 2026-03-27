#!/usr/bin/env python3
"""
CyberSentinel — Flask + SQLite3 Backend Server
Receives all frontend form inputs and stores them in cybersentinel.db
Run: python3 server.py
"""

import sqlite3, json, os, re, secrets
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cybersentinel.db")
AUTH_TTL_HOURS = 24

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,OPTIONS"
    return r

@app.route("/api/<path:p>", methods=["OPTIONS"])
def opt(p): return "", 204

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

def qry(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    rv  = cur.fetchone() if one else cur.fetchall()
    return (dict(rv) if rv else None) if one else [dict(r) for r in rv]

def run(sql, params=()):
    db = get_db(); cur = db.execute(sql, params); db.commit(); return cur.lastrowid

def ok(data=None, msg="ok", code=200):
    return jsonify({"success": True,  "message": msg,  "data": data}), code

def err(msg, code=400):
    return jsonify({"success": False, "message": msg, "data": None}), code

def log(label, action, etype=None, eid=None, detail=None):
    run("INSERT INTO activity_log (actor_type,actor_label,action,entity_type,entity_id,detail) VALUES ('system',?,?,?,?,?)",
        (label, action, etype, eid, detail))

def next_ref(table, col, prefix, yr=False):
    row = qry(f"SELECT {col} FROM {table} ORDER BY id DESC LIMIT 1", one=True)
    num = (int(row[col].split("-")[-1]) + 1) if row else 1000
    return f"{prefix}-{datetime.utcnow().year}-{num}" if yr else f"{prefix}-{num}"

def ensure_runtime_schema():
    if not os.path.exists(DB_PATH):
        return

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")

    cols_users = {r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    if "password_hash" not in cols_users:
        con.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

    cols_complaints = {r[1] for r in con.execute("PRAGMA table_info(complaints)").fetchall()}
    if "submitted_by_user" not in cols_complaints:
        con.execute("ALTER TABLE complaints ADD COLUMN submitted_by_user INTEGER")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(token)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id)")
    con.commit()
    con.close()

def get_token_from_request():
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.headers.get("X-Auth-Token", "").strip()

def get_authenticated_user():
    token = get_token_from_request()
    if not token:
        return None
    return qry(
        """
        SELECT s.id AS session_id, s.user_id, u.full_name, u.initials, u.email, u.role, u.department
        FROM auth_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
        """,
        (token,),
        one=True,
    )

def new_session(user_id):
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=AUTH_TTL_HOURS)).isoformat(timespec="seconds")
    run("INSERT INTO auth_sessions (user_id, token, expires_at) VALUES (?,?,?)", (user_id, token, expires_at))
    return token, expires_at

def initials_for(full_name):
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "US"
    if len(parts) == 1:
        return (parts[0][0:2]).upper()
    return (parts[0][0] + parts[-1][0]).upper()

SEVERITY_ORDER = {
    "info": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}

def severity_value(level):
    return SEVERITY_ORDER.get((level or "").lower(), 0)

def severity_at_least(level, minimum):
    return severity_value(level) >= severity_value(minimum)

# ── frontend ────────────────────────────────────────────────────
@app.route("/")
def frontend():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/login")
def login_frontend():
    return send_from_directory(BASE_DIR, "LOGIN.html")

@app.route("/db-records")
def db_records_frontend():
    return send_from_directory(BASE_DIR, "db_records.html")

# ── auth ────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json(silent=True) or {}
    full_name = str(d.get("full_name", "")).strip()
    email = str(d.get("email", "")).strip().lower()
    password = str(d.get("password", ""))

    if not full_name or not email or not password:
        return err("full_name, email and password are required")
    if len(password) < 8:
        return err("Password must be at least 8 characters")

    existing = qry("SELECT id FROM users WHERE lower(email)=lower(?)", (email,), one=True)
    if existing:
        return err("Email already registered", 409)

    uid = run(
        """
        INSERT INTO users (full_name, initials, email, password_hash, role, department, is_active)
        VALUES (?,?,?,?,?,?,1)
        """,
        (full_name, initials_for(full_name), email, generate_password_hash(password), "viewer", "Citizen Portal"),
    )
    token, expires_at = new_session(uid)
    user = qry("SELECT id, full_name, initials, email, role, department FROM users WHERE id=?", (uid,), one=True)
    return ok({"token": token, "expires_at": expires_at, "user": user}, "Registered", 201)

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    email = str(d.get("email", "")).strip().lower()
    password = str(d.get("password", ""))
    if not email or not password:
        return err("email and password are required")

    user = qry(
        "SELECT id, full_name, initials, email, role, department, password_hash, is_active FROM users WHERE lower(email)=lower(?)",
        (email,),
        one=True,
    )
    if not user or not user.get("password_hash"):
        return err("Invalid credentials", 401)
    if not user.get("is_active"):
        return err("User disabled", 403)
    if not check_password_hash(user["password_hash"], password):
        return err("Invalid credentials", 401)

    run("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user["id"],))
    token, expires_at = new_session(user["id"])
    safe_user = {k: user[k] for k in ("id", "full_name", "initials", "email", "role", "department")}
    return ok({"token": token, "expires_at": expires_at, "user": safe_user}, "Logged in")

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    user = get_authenticated_user()
    if not user:
        return err("Unauthorized", 401)
    return ok({"id": user["user_id"], "full_name": user["full_name"], "initials": user["initials"], "email": user["email"], "role": user["role"], "department": user["department"]})

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    token = get_token_from_request()
    if not token:
        return err("Unauthorized", 401)
    run("UPDATE auth_sessions SET is_active=0 WHERE token=?", (token,))
    return ok(None, "Logged out")

# ── health ──────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return ok({"status":"online","db":DB_PATH,"ts":datetime.utcnow().isoformat()+"Z"})

# ── dashboard ───────────────────────────────────────────────────
@app.route("/api/dashboard/kpis")
def kpis():
    s = qry("SELECT * FROM kpi_snapshots ORDER BY snapped_at DESC LIMIT 1", one=True) or {}
    s["active_threats"]  = qry("SELECT COUNT(*) c FROM incidents WHERE status NOT IN ('resolved','closed')", one=True)["c"]
    s["open_incidents"]  = s["active_threats"]
    s["events_analysed"] = qry("SELECT COUNT(*) c FROM threat_events", one=True)["c"]
    return ok(s)

@app.route("/api/dashboard/threat-volume")
def tvol():
    return ok(qry("SELECT * FROM threat_volume_hourly ORDER BY hour_value"))

@app.route("/api/dashboard/risk-score")
def rscore():
    return ok(qry("SELECT risk_score,phishing_risk,malware_risk,insider_risk,ransomware_risk FROM kpi_snapshots ORDER BY snapped_at DESC LIMIT 1", one=True))

# ── incidents ───────────────────────────────────────────────────
@app.route("/api/incidents", methods=["GET"])
def list_inc():
    sev=request.args.get("severity"); st=request.args.get("status")
    pg=max(1,int(request.args.get("page",1))); pp=min(100,int(request.args.get("per_page",20)))
    sql,p="SELECT i.*,u.full_name assigned_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id WHERE 1=1",[]
    if sev: sql+=" AND i.severity=?"; p.append(sev)
    if st:  sql+=" AND i.status=?";   p.append(st)
    rows=qry(sql+" ORDER BY i.created_at DESC",p); total=len(rows)
    return ok({"items":rows[(pg-1)*pp:pg*pp],"total":total,"page":pg,"per_page":pp,"pages":max(1,(total+pp-1)//pp)})

@app.route("/api/incidents/<int:iid>", methods=["GET"])
def get_inc(iid):
    row=qry("SELECT i.*,u.full_name assigned_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id WHERE i.id=?", (iid,), one=True)
    if not row: return err("Not found",404)
    row["iocs"]=qry("SELECT * FROM iocs WHERE incident_id=?",(iid,))
    row["events"]=qry("SELECT * FROM threat_events WHERE incident_id=? ORDER BY created_at DESC",(iid,))
    return ok(row)

@app.route("/api/incidents", methods=["POST"])
def create_inc():
    d=request.get_json(silent=True) or {}
    miss=[f for f in ("title","type","severity") if not d.get(f)]
    if miss: return err(f"Missing: {', '.join(miss)}")
    if d["severity"] not in {"critical","high","medium","low","info"}: return err("Invalid severity")
    if d["type"] not in {"apt","phishing","malware","insider","ransomware","data_exfil","credential_leak","other"}: return err("Invalid type")
    ref=next_ref("incidents","incident_ref","INC")
    iid=run("INSERT INTO incidents (incident_ref,title,type,severity,status,source,assigned_to,description,ai_confidence,source_ip,dest_ip,affected_host,tags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref,d["title"].strip(),d["type"],d["severity"],d.get("status","open"),d.get("source",""),d.get("assigned_to"),d.get("description","").strip(),d.get("ai_confidence"),d.get("source_ip") or None,d.get("dest_ip") or None,d.get("affected_host") or None,json.dumps(d.get("tags",[]))))
    log("System","create_incident","incident",iid,f"{ref} created — {d['severity']} {d['type']}")
    return ok({"id":iid,"incident_ref":ref},"Incident created",201)

@app.route("/api/incidents/<int:iid>", methods=["PATCH"])
def upd_inc(iid):
    d=request.get_json(silent=True) or {}
    u={k:v for k,v in d.items() if k in {"title","type","severity","status","source","assigned_to","description","ai_confidence","source_ip","dest_ip","affected_host","tags"}}
    if not u: return err("No valid fields")
    run(f"UPDATE incidents SET {','.join(f'{k}=?' for k in u)} WHERE id=?", list(u.values())+[iid])
    return ok({"id":iid},"Incident updated")

# ── threat events ───────────────────────────────────────────────
@app.route("/api/threat-events", methods=["GET"])
def list_ev():
    sev=request.args.get("severity"); pg=max(1,int(request.args.get("page",1))); pp=min(100,int(request.args.get("per_page",20)))
    sql,p="SELECT * FROM threat_events WHERE 1=1",[]
    if sev: sql+=" AND severity=?"; p.append(sev)
    rows=qry(sql+" ORDER BY created_at DESC",p); total=len(rows)
    return ok({"items":rows[(pg-1)*pp:pg*pp],"total":total,"page":pg,"per_page":pp,"pages":max(1,(total+pp-1)//pp)})

@app.route("/api/threat-events", methods=["POST"])
def create_ev():
    d=request.get_json(silent=True) or {}
    miss=[f for f in ("event_type","severity","description") if not d.get(f)]
    if miss: return err(f"Missing: {', '.join(miss)}")
    eid=run("INSERT INTO threat_events (incident_id,event_type,severity,description,source_layer,source_ip,dest_ip,affected_entity,raw_payload) VALUES (?,?,?,?,?,?,?,?,?)",
            (d.get("incident_id"),d["event_type"],d["severity"],d["description"],d.get("source_layer"),d.get("source_ip"),d.get("dest_ip"),d.get("affected_entity"),json.dumps(d.get("raw_payload")) if d.get("raw_payload") else None))
    return ok({"id":eid},"Event stored",201)

@app.route("/api/threat-events/<int:eid>/acknowledge", methods=["POST"])
def ack_ev(eid):
    run("UPDATE threat_events SET is_acknowledged=1 WHERE id=?",(eid,)); return ok({"id":eid},"Acknowledged")

# ── iocs ────────────────────────────────────────────────────────
@app.route("/api/iocs", methods=["GET"])
def list_iocs():
    t=request.args.get("type"); sql,p="SELECT * FROM iocs WHERE is_active=1",[]
    if t: sql+=" AND ioc_type=?"; p.append(t)
    return ok(qry(sql+" ORDER BY last_seen DESC",p))

@app.route("/api/iocs", methods=["POST"])
def create_ioc():
    d=request.get_json(silent=True) or {}
    if not d.get("ioc_type") or not d.get("value"): return err("ioc_type and value required")
    if d["ioc_type"] not in {"ip","domain","hash","email","url","cve"}: return err("Invalid ioc_type")
    iid=run("INSERT INTO iocs (incident_id,ioc_type,value,confidence,threat_actor,notes) VALUES (?,?,?,?,?,?)",
            (d.get("incident_id"),d["ioc_type"],d["value"].strip(),d.get("confidence",1.0),d.get("threat_actor"),d.get("notes","")))
    return ok({"id":iid},"IOC stored",201)

# ── dark web leaks ──────────────────────────────────────────────
@app.route("/api/dark-web-leaks", methods=["GET"])
def list_leaks(): return ok(qry("SELECT * FROM dark_web_leaks ORDER BY detected_at DESC"))

@app.route("/api/dark-web-leaks", methods=["POST"])
def create_leak():
    d=request.get_json(silent=True) or {}
    if not d.get("source_site") or not d.get("leak_type"): return err("source_site and leak_type required")
    lid=run("INSERT INTO dark_web_leaks (incident_id,source_site,leak_type,records_count,severity,summary,tor_url,is_verified) VALUES (?,?,?,?,?,?,?,?)",
            (d.get("incident_id"),d["source_site"],d["leak_type"],d.get("records_count",0),d.get("severity","high"),d.get("summary",""),d.get("tor_url"),int(d.get("is_verified",False))))
    return ok({"id":lid},"Leak recorded",201)

# ── complaints ──────────────────────────────────────────────────
@app.route("/api/complaints", methods=["GET"])
def list_comp():
    st=request.args.get("status"); cat=request.args.get("category")
    mine = request.args.get("mine") == "1"
    pg=max(1,int(request.args.get("page",1))); pp=min(100,int(request.args.get("per_page",20)))
    sql,p="SELECT * FROM complaints WHERE 1=1",[]
    if mine:
        user = get_authenticated_user()
        if not user:
            return err("Unauthorized", 401)
        sql += " AND submitted_by_user=?"
        p.append(user["user_id"])
    if st:  sql+=" AND status=?";      p.append(st)
    if cat: sql+=" AND ai_category=?"; p.append(cat)
    rows=qry(sql+" ORDER BY created_at DESC",p); total=len(rows)
    return ok({"items":rows[(pg-1)*pp:pg*pp],"total":total,"page":pg,"per_page":pp,"pages":max(1,(total+pp-1)//pp)})

@app.route("/api/complaints/<int:cid>", methods=["GET"])
def get_comp(cid):
    row=qry("SELECT * FROM complaints WHERE id=?",(cid,),one=True)
    if not row: return err("Not found",404)
    return ok(row)

@app.route("/api/complaints", methods=["POST"])
def create_comp():
    """Main endpoint — receives Citizen Complaint Portal form data → SQLite."""
    d=request.get_json(silent=True) or {}
    miss=[f for f in ("complainant_name","description") if not str(d.get(f,"")).strip()]
    if miss: return err(f"Missing: {', '.join(miss)}")
    if len(d["description"].strip())<10: return err("Description too short")
    user = get_authenticated_user()
    submitted_by = user["user_id"] if user else None
    ref=next_ref("complaints","complaint_ref","CNF",yr=True)
    cid=run("INSERT INTO complaints (complaint_ref,complainant_name,complainant_phone,complainant_email,description,incident_date,ai_category,ai_severity,ai_confidence,submitted_by_user,status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (ref,d["complainant_name"].strip(),d.get("complainant_phone","").strip() or None,d.get("complainant_email","").strip() or None,d["description"].strip(),d.get("incident_date") or None,d.get("ai_category") or None,d.get("ai_severity") or None,d.get("ai_confidence") or None,submitted_by,"received"))
    log(d["complainant_name"].strip(),"submit_complaint","complaint",cid,f"{ref} — {d.get('ai_category','unclassified')}")
    return ok({"id":cid,"complaint_ref":ref,"status":"received","message":f"Registered as {ref}. We will contact you shortly."},"Complaint submitted",201)

@app.route("/api/complaints/<int:cid>", methods=["PATCH"])
def upd_comp(cid):
    d=request.get_json(silent=True) or {}
    u={k:v for k,v in d.items() if k in {"status","ai_category","ai_severity","ai_confidence","assigned_to","linked_incident","resolution_notes"}}
    if not u: return err("No valid fields")
    run(f"UPDATE complaints SET {','.join(f'{k}=?' for k in u)} WHERE id=?",list(u.values())+[cid])
    return ok({"id":cid},"Complaint updated")

# ── playbooks ───────────────────────────────────────────────────
@app.route("/api/playbooks", methods=["GET"])
def list_pb(): return ok(qry("SELECT id,name,description,trigger_type,threat_type,severity_min,is_active FROM playbooks"))

@app.route("/api/playbooks/<int:pid>/execute", methods=["POST"])
def exec_pb(pid):
    d=request.get_json(silent=True) or {}
    pb=qry("SELECT * FROM playbooks WHERE id=?",(pid,),one=True)
    if not pb: return err("Not found",404)
    if not pb["is_active"]: return err("Playbook disabled")
    steps=json.loads(pb["steps"])
    eid=run("INSERT INTO playbook_executions (playbook_id,incident_id,triggered_by,status,steps_completed,steps_total) VALUES (?,?,?,?,?,?)",
            (pid,d.get("incident_id"),d.get("triggered_by","manual"),"running",0,len(steps)))
    return ok({"execution_id":eid,"playbook":pb["name"],"steps":len(steps)},"Playbook started",202)

@app.route("/api/playbook-executions", methods=["GET"])
def list_execs():
    return ok(qry("SELECT pe.*,pb.name playbook_name FROM playbook_executions pe JOIN playbooks pb ON pe.playbook_id=pb.id ORDER BY pe.started_at DESC LIMIT 20"))

# ── activity / health / users / search ──────────────────────────
@app.route("/api/activity")
def activity(): return ok(qry("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",(min(100,int(request.args.get("limit",20))),)))

@app.route("/api/system-health", methods=["GET"])
def sys_health(): return ok(qry("SELECT * FROM system_health sh WHERE recorded_at=(SELECT MAX(recorded_at) FROM system_health s2 WHERE s2.component=sh.component)"))

@app.route("/api/system-health", methods=["POST"])
def push_health():
    d=request.get_json(silent=True) or {}
    if not d.get("component"): return err("component required")
    run("INSERT INTO system_health (component,status,uptime_pct,avg_latency_ms,active_jobs,events_ingested) VALUES (?,?,?,?,?,?)",
        (d["component"],d.get("status","online"),d.get("uptime_pct"),d.get("avg_latency_ms"),d.get("active_jobs",0),d.get("events_ingested",0)))
    return ok(None,"Recorded",201)

@app.route("/api/users")
def list_users(): return ok(qry("SELECT id,full_name,initials,email,role,department,is_active FROM users"))

@app.route("/api/users/<int:uid>")
def get_user(uid):
    row=qry("SELECT id,full_name,initials,email,role,department FROM users WHERE id=?",(uid,),one=True)
    if not row: return err("Not found",404)
    row["recent_incidents"]=qry("SELECT incident_ref,title,severity,status FROM incidents WHERE assigned_to=? ORDER BY created_at DESC LIMIT 5",(uid,))
    return ok(row)

@app.route("/api/search")
def search():
    q=request.args.get("q","").strip()
    if len(q)<2: return err("Min 2 chars")
    like=f"%{q}%"
    return ok({"incidents":qry("SELECT incident_ref,title,severity,status FROM incidents WHERE title LIKE ? OR incident_ref LIKE ? LIMIT 5",(like,like)),"complaints":qry("SELECT complaint_ref,complainant_name,ai_category,status FROM complaints WHERE complainant_name LIKE ? OR description LIKE ? OR complaint_ref LIKE ? LIMIT 5",(like,like,like)),"iocs":qry("SELECT ioc_type,value,confidence FROM iocs WHERE value LIKE ? LIMIT 5",(like,))})

@app.route("/api/stats/incidents")
def inc_stats(): return ok({"by_severity":qry("SELECT severity,COUNT(*) count FROM incidents GROUP BY severity"),"by_status":qry("SELECT status,COUNT(*) count FROM incidents GROUP BY status"),"by_type":qry("SELECT type,COUNT(*) count FROM incidents GROUP BY type ORDER BY count DESC")})

@app.route("/api/stats/complaints")
def comp_stats(): return ok({"by_category":qry("SELECT ai_category,COUNT(*) count FROM complaints GROUP BY ai_category"),"by_status":qry("SELECT status,COUNT(*) count FROM complaints GROUP BY status"),"total":qry("SELECT COUNT(*) count FROM complaints",one=True)["count"]})

@app.route("/api/intelligence/classify-text", methods=["POST"])
def classify_text():
    d = request.get_json(silent=True) or {}
    text = str(d.get("text", "")).strip().lower()
    if len(text) < 8:
        return err("text must be at least 8 characters")

    model = {
        "ransomware": {
            "severity": "critical",
            "signals": {"ransom": 3, "decrypt": 2, "encrypted": 3, "bitcoin": 2, "extortion": 3, "locked": 2},
        },
        "phishing": {
            "severity": "high",
            "signals": {"otp": 3, "verify": 2, "suspended": 2, "click": 1, "credential": 2, "password": 2, "bank": 2},
        },
        "malware": {
            "severity": "high",
            "signals": {"trojan": 3, "malware": 3, "payload": 2, "keylogger": 3, "virus": 2, "exe": 1},
        },
        "financial_fraud": {
            "severity": "high",
            "signals": {"upi": 3, "debit": 2, "credit card": 2, "wallet": 2, "refund scam": 3, "transaction": 2},
        },
        "data_exfiltration": {
            "severity": "critical",
            "signals": {"data leak": 3, "exfil": 3, "dump": 2, "records exposed": 3, "unauthorized download": 2},
        },
        "account_takeover": {
            "severity": "medium",
            "signals": {"unknown login": 3, "2fa": 2, "account hacked": 3, "session hijack": 3, "reset link": 2},
        },
    }

    ip_hits = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    domain_hits = re.findall(r"\b[a-z0-9.-]+\.(?:com|net|org|io|co|in|ru|cn|biz|xyz)\b", text)
    url_hits = re.findall(r"https?://[^\s]+", text)
    email_hits = re.findall(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", text)
    cve_hits = re.findall(r"cve-\d{4}-\d{4,7}", text)
    sha_hits = re.findall(r"\b[a-f0-9]{32,64}\b", text)

    extracted_iocs = []
    extracted_iocs.extend({"type": "ip", "value": v} for v in ip_hits[:5])
    extracted_iocs.extend({"type": "domain", "value": v} for v in domain_hits[:5])
    extracted_iocs.extend({"type": "url", "value": v} for v in url_hits[:5])
    extracted_iocs.extend({"type": "email", "value": v} for v in email_hits[:5])
    extracted_iocs.extend({"type": "cve", "value": v.upper()} for v in cve_hits[:5])
    extracted_iocs.extend({"type": "hash", "value": v} for v in sha_hits[:5])

    scored = []
    for category, cfg in model.items():
        score = 0
        matched_signals = []
        for signal, weight in cfg["signals"].items():
            if signal in text:
                score += weight
                matched_signals.append(signal)
        if score > 0:
            scored.append({
                "category": category,
                "severity": cfg["severity"],
                "score": score,
                "matched_signals": matched_signals,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    if scored:
        best = scored[0]
        category = best["category"]
        severity = best["severity"]
        raw_conf = 0.45 + (best["score"] * 0.06) + (min(len(extracted_iocs), 4) * 0.03)
        confidence = min(0.99, raw_conf)
    else:
        category = "suspicious_activity"
        severity = "medium"
        confidence = 0.52 if extracted_iocs else 0.45

    matched = [
        {
            "category": s["category"],
            "severity": s["severity"],
            "score": s["score"],
            "matched_signals": s["matched_signals"],
            "confidence": round(min(0.98, 0.42 + s["score"] * 0.06), 2),
        }
        for s in scored[:4]
    ]

    recommendations = {
        "critical": ["Isolate affected endpoint", "Escalate to incident commander", "Preserve forensic artifacts"],
        "high": ["Block suspicious IOC", "Reset impacted credentials", "Collect relevant logs"],
        "medium": ["Monitor for repeat activity", "Notify user and helpdesk", "Add case to analyst queue"],
        "low": ["Track and observe", "Add to baseline monitoring"],
    }

    return ok({
        "category": category,
        "severity": severity,
        "confidence": round(confidence, 2),
        "matches": matched,
        "extracted_iocs": extracted_iocs[:12],
        "recommendations": recommendations.get(severity, recommendations["low"]),
    })

@app.route("/api/intelligence/dark-web-monitor", methods=["GET"])
def intel_dark_web_monitor():
    summary = {
        "total_leaks": qry("SELECT COUNT(*) c FROM dark_web_leaks", one=True)["c"],
        "verified_leaks": qry("SELECT COUNT(*) c FROM dark_web_leaks WHERE is_verified=1", one=True)["c"],
        "total_records": qry("SELECT COALESCE(SUM(records_count),0) c FROM dark_web_leaks", one=True)["c"],
        "critical_or_high": qry("SELECT COUNT(*) c FROM dark_web_leaks WHERE severity IN ('critical','high')", one=True)["c"],
    }
    by_type = qry("SELECT leak_type, COUNT(*) count FROM dark_web_leaks GROUP BY leak_type ORDER BY count DESC")
    by_severity = qry("SELECT severity, COUNT(*) count FROM dark_web_leaks GROUP BY severity")
    recent = qry("SELECT * FROM dark_web_leaks ORDER BY detected_at DESC LIMIT 25")
    return ok({"summary": summary, "by_type": by_type, "by_severity": by_severity, "recent": recent})

@app.route("/api/intelligence/threat-feed", methods=["GET"])
def intel_threat_feed():
    limit = min(50, max(5, int(request.args.get("limit", 12))))
    events = qry(
        """
        SELECT te.*, i.incident_ref, i.type incident_type
        FROM threat_events te
        LEFT JOIN incidents i ON i.id = te.incident_id
        ORDER BY te.created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    unacked = qry("SELECT COUNT(*) c FROM threat_events WHERE is_acknowledged=0", one=True)["c"]
    top_sources = qry(
        """
        SELECT COALESCE(source_layer,'unknown') source_layer, COUNT(*) count
        FROM threat_events
        GROUP BY COALESCE(source_layer,'unknown')
        ORDER BY count DESC
        LIMIT 8
        """
    )
    ioc_snapshot = qry(
        "SELECT ioc_type, COUNT(*) count FROM iocs WHERE is_active=1 GROUP BY ioc_type ORDER BY count DESC"
    )
    return ok({
        "events": events,
        "unacknowledged_count": unacked,
        "top_sources": top_sources,
        "ioc_snapshot": ioc_snapshot,
    })

@app.route("/api/intelligence/forecast", methods=["GET"])
def intel_forecast():
    rows = qry(
        """
        SELECT hour_label, hour_value, critical_high, medium, low, recorded_date
        FROM threat_volume_hourly
        ORDER BY recorded_date DESC, hour_value DESC
        LIMIT 24
        """
    )
    if not rows:
        return ok({"history": [], "projection": [], "trend": "stable", "avg_load": 0})

    rows = list(reversed(rows))
    history = []
    for r in rows:
        total = (r.get("critical_high") or 0) + (r.get("medium") or 0) + (r.get("low") or 0)
        history.append({
            "hour_label": r.get("hour_label"),
            "hour_value": r.get("hour_value"),
            "total": total,
            "critical_high": r.get("critical_high") or 0,
            "medium": r.get("medium") or 0,
            "low": r.get("low") or 0,
        })

    n = len(history)
    first = history[0]["total"]
    last = history[-1]["total"]
    slope = (last - first) / max(1, n - 1)
    avg_load = round(sum(h["total"] for h in history) / max(1, n), 2)

    projection = []
    base = last
    for i in range(1, 4):
        pred = max(0, round(base + slope * i))
        projection.append({"step": i, "predicted_total": pred})

    if slope > 2:
        trend = "rising"
    elif slope < -2:
        trend = "falling"
    else:
        trend = "stable"

    return ok({
        "history": history[-12:],
        "projection": projection,
        "trend": trend,
        "avg_load": avg_load,
        "slope": round(slope, 2),
    })

@app.route("/api/intelligence/forensics", methods=["GET"])
def intel_forensics():
    focus_incidents = qry(
        """
        SELECT id, incident_ref, title, type, severity, status, source_ip, dest_ip, affected_host, created_at
        FROM incidents
        WHERE status NOT IN ('resolved','closed')
        ORDER BY CASE severity
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
            ELSE 5 END,
            created_at DESC
        LIMIT 10
        """
    )

    hot_iocs = qry(
        """
        SELECT i.*, inc.incident_ref, inc.severity incident_severity
        FROM iocs i
        LEFT JOIN incidents inc ON inc.id = i.incident_id
        WHERE i.is_active=1
        ORDER BY i.confidence DESC, i.last_seen DESC
        LIMIT 20
        """
    )

    for ioc in hot_iocs:
        recency_bonus = 10 if (ioc.get("last_seen") or "")[:10] == datetime.utcnow().date().isoformat() else 0
        confidence_score = int((ioc.get("confidence") or 0) * 100)
        sev_bonus = 8 if severity_at_least(ioc.get("incident_severity"), "high") else 0
        ioc["risk_score"] = min(100, confidence_score + recency_bonus + sev_bonus)

    return ok({
        "focus_incidents": focus_incidents,
        "hot_iocs": hot_iocs,
        "active_ioc_count": qry("SELECT COUNT(*) c FROM iocs WHERE is_active=1", one=True)["c"],
    })

@app.route("/api/intelligence/playbooks/recommend", methods=["GET"])
def intel_playbook_recommend():
    incident_id = request.args.get("incident_id")
    incident_type = request.args.get("incident_type")
    incident_severity = request.args.get("incident_severity")

    if incident_id:
        inc = qry("SELECT type, severity FROM incidents WHERE id=?", (incident_id,), one=True)
        if not inc:
            return err("Incident not found", 404)
        incident_type = incident_type or inc.get("type")
        incident_severity = incident_severity or inc.get("severity")

    rows = qry("SELECT id, name, description, threat_type, severity_min, trigger_type FROM playbooks WHERE is_active=1")
    scored = []
    for pb in rows:
        score = 0
        if incident_type and pb.get("threat_type") and pb["threat_type"] == incident_type:
            score += 50
        if incident_type and not pb.get("threat_type"):
            score += 20
        if incident_severity and severity_at_least(incident_severity, pb.get("severity_min") or "medium"):
            score += 30
        if pb.get("trigger_type") == "auto":
            score += 5
        if score > 0 or (not incident_type and not incident_severity):
            pb["relevance_score"] = score
            scored.append(pb)

    scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return ok({
        "incident_type": incident_type,
        "incident_severity": incident_severity,
        "recommended": scored[:10],
    })

if __name__ == "__main__":
    ensure_runtime_schema()
    if not os.path.exists(DB_PATH):
        print(f"⚠  DB not found. Run: python3 init_db.py")
    else:
        print(f"✓  DB: {DB_PATH}")
        print(f"✓  API: http://localhost:5050")
    app.run(debug=True, port=5050)
