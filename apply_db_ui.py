import re

with open('db_records.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_style = """<style>
:root{
  --bg-app: #0B0F19;
  --bg-card: #151C2C;
  --bg-element: #1B2438;
  --bg-hover: #212D42;
  --border: #2A364F;
  --border-light: #354460;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --accent: #3B82F6;
  --accent-glow: rgba(59,130,246,0.25);
  --accent-gradient: linear-gradient(135deg, #3B82F6, #2563EB);
  --danger: #EF4444; --warning: #F59E0B; --success: #10B981; --info: #0EA5E9;
  --danger-bg: rgba(239,68,68,0.15); --success-bg: rgba(16,185,129,0.15);
  --radius: 12px;
  --shadow: 0 4px 20px rgba(0,0,0,0.3);
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg-app);color:var(--text-primary);min-height:100vh}
.page{max-width:1200px;margin:0 auto;padding:24px;display:flex;flex-direction:column;gap:24px;}
.topbar{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;display:flex;align-items:center;justify-content:space-between;gap:16px;box-shadow:var(--shadow);flex-wrap:wrap;}
.title{font-family:'Fraunces',serif;font-size:24px;font-weight:700;color:var(--text-primary)}
.subtitle{font-size:13px;color:var(--text-muted);margin-top:4px}
.actions{display:flex;gap:12px;flex-wrap:wrap}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 20px;border-radius:8px;font-family:inherit;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .2s;text-decoration:none;white-space:nowrap;}
.btn-primary{background:var(--accent-gradient);color:#fff;box-shadow:0 0 15px var(--accent-glow)}
.btn-primary:hover{opacity:0.9;transform:translateY(-1px);}
.btn-secondary{background:var(--bg-element);color:var(--text-primary);border:1px solid var(--border)}
.btn-secondary:hover{background:var(--bg-hover);border-color:var(--border-light)}

.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);display:flex;flex-direction:column;overflow:hidden;}
.card-header{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;}
.card-title{font-family:'Fraunces',serif;font-size:18px;font-weight:700;color:var(--text-primary)}
.card-sub{font-size:13px;color:var(--text-muted);margin-top:4px;}
.card-body{padding:24px;overflow-x:auto;}

.pill{display:inline-flex;align-items:center;gap:6px;background:var(--success-bg);border:1px solid rgba(16,185,129,0.2);color:var(--success);font-size:11px;font-weight:700;padding:6px 12px;border-radius:20px}
.pill::before{content:'●';font-size:10px;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

.tabs{display:flex;gap:4px;background:var(--bg-app);padding:4px;border-radius:10px;border:1px solid var(--border);overflow-x:auto;}
.tab{padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;color:var(--text-secondary);cursor:pointer;transition:all .2s;white-space:nowrap;}
.tab:hover{color:var(--text-primary);background:var(--bg-element)}
.tab.active{background:var(--bg-card);color:var(--accent);box-shadow:0 2px 8px rgba(0,0,0,0.2);border:1px solid var(--border)}

.tab-pane{display:none;animation:fadeIn .3s ease;}
.tab-pane.active{display:block;}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}

table{width:100%;border-collapse:collapse;font-size:13px;}
th{background:var(--bg-element);padding:14px;text-align:left;font-size:11px;font-weight:700;color:var(--text-secondary);letter-spacing:1px;text-transform:uppercase;border-bottom:2px solid var(--border);white-space:nowrap;}
td{padding:14px;border-bottom:1px solid var(--border);color:var(--text-primary);vertical-align:middle;}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--bg-hover)}
td.mono{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-muted)}

.empty-state{text-align:center;padding:40px;color:var(--text-muted);font-style:italic;}

::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:var(--border-light)}

@media(max-width:768px){
  .topbar{flex-direction:column;align-items:flex-start;}
  .actions{width:100%;}
  .btn{flex:1;}
  .card-header{flex-direction:column;align-items:flex-start;}
  .tabs{width:100%;}
}
</style>"""

html = re.sub(r'<style>.*?</style>', new_style, html, flags=re.DOTALL)
with open('db_records.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("DB Records UI Successfully Updated!")
