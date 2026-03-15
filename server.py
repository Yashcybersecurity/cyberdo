#!/usr/bin/env python3
"""
CyberSentinel — Flask + SQLite3 Backend Server
Receives all frontend form inputs and stores them in cybersentinel.db
Run: python3 server.py
"""

import sqlite3, json, os
from datetime import datetime
from flask import Flask, jsonify, request, g, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cybersentinel.db")

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
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

# ── frontend ────────────────────────────────────────────────────
@app.route("/")
def frontend():
    return send_from_directory(BASE_DIR, "index.html")

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
    pg=max(1,int(request.args.get("page",1))); pp=min(100,int(request.args.get("per_page",20)))
    sql,p="SELECT * FROM complaints WHERE 1=1",[]
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
    ref=next_ref("complaints","complaint_ref","CNF",yr=True)
    cid=run("INSERT INTO complaints (complaint_ref,complainant_name,complainant_phone,complainant_email,description,incident_date,ai_category,ai_severity,ai_confidence,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (ref,d["complainant_name"].strip(),d.get("complainant_phone","").strip() or None,d.get("complainant_email","").strip() or None,d["description"].strip(),d.get("incident_date") or None,d.get("ai_category") or None,d.get("ai_severity") or None,d.get("ai_confidence") or None,"received"))
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

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"⚠  DB not found. Run: python3 init_db.py")
    else:
        print(f"✓  DB: {DB_PATH}")
        print(f"✓  API: http://localhost:5050")
    app.run(debug=True, port=5050)
