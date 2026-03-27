import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace variables and style block
new_style = """<style>
:root{
  --bg-app: #0B0F19;
  --bg-sidebar: #101623;
  --bg-card: #151C2C;
  --bg-element: #1B2438;
  --bg-hover: #212D42;
  --border: #2A364F;
  --border-light: #354460;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --accent: #3B82F6;
  --accent-glow: rgba(59,130,246,0.3);
  --accent-gradient: linear-gradient(135deg, #3B82F6, #2563EB);
  --danger: #EF4444; --warning: #F59E0B; --success: #10B981; --info: #0EA5E9;
  --danger-bg: rgba(239,68,68,0.15); --warning-bg: rgba(245,158,11,0.15);
  --success-bg: rgba(16,185,129,0.15); --info-bg: rgba(14,165,233,0.15);
  --radius: 12px; --radius-sm: 8px;
  --shadow: 0 4px 20px rgba(0,0,0,0.3);
  --glow: 0 0 15px var(--accent-glow);
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg-app);color:var(--text-primary);display:flex;height:100vh;overflow:hidden;font-size:14px;line-height:1.5}

/* Sidebar */
.sidebar{width:260px;background:var(--bg-sidebar);border-right:1px solid var(--border);display:flex;flex-direction:column;transition:transform 0.3s ease;z-index:999;}
.sidebar-brand{padding:24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;}
.brand-logo{display:flex;align-items:center;gap:12px;text-decoration:none}
.brand-icon{width:40px;height:40px;background:var(--accent-gradient);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:var(--glow)}
.brand-name{font-family:'Fraunces',serif;font-size:18px;font-weight:700;color:var(--text-primary);line-height:1.2}
.brand-tagline{font-size:10px;color:var(--text-secondary);letter-spacing:1.5px;text-transform:uppercase;font-weight:600}
.close-sidebar-btn{display:none;font-size:20px;background:none;border:none;color:var(--text-muted);cursor:pointer;}

.sidebar-scroll{flex:1;overflow-y:auto;padding-bottom:24px;}
.sidebar-scroll::-webkit-scrollbar{width:4px;}
.sidebar-scroll::-webkit-scrollbar-thumb{background:var(--border-light);border-radius:2px;}

.sidebar-section{padding:0 12px;margin-top:12px}
.sidebar-section-label{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text-muted);padding:16px 16px 8px}
.nav-item{display:flex;align-items:center;gap:12px;padding:10px 16px;border-radius:8px;color:var(--text-secondary);cursor:pointer;transition:all .2s;font-size:14px;font-weight:500;margin-bottom:4px;text-decoration:none}
.nav-item:hover{background:var(--bg-hover);color:var(--text-primary)}
.nav-item.active{background:var(--accent-gradient);color:#fff;box-shadow:var(--glow);border:none;}
.nav-icon{font-size:18px;width:20px;text-align:center;}
.nav-badge{margin-left:auto;background:var(--danger);color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;}
.nav-badge.green{background:var(--success)} .nav-badge.amber{background:var(--warning)}

.sidebar-footer{padding:16px;border-top:1px solid var(--border);margin-top:auto;}
.user-card{display:flex;align-items:center;gap:12px;padding:12px;border-radius:10px;background:var(--bg-element);cursor:pointer;border:1px solid var(--border);transition:border-color .2s}
.user-card:hover{border-color:var(--border-light)}
.user-avatar{width:36px;height:36px;background:var(--accent-gradient);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;}
.user-name{font-size:13px;font-weight:600;color:var(--text-primary)}
.user-role{font-size:11px;color:var(--text-muted)}

/* Main View */
.main{flex:1;display:flex;flex-direction:column;position:relative;overflow:hidden;}
.topbar{background:var(--bg-card);border-bottom:1px solid var(--border);padding:0 24px;height:70px;display:flex;align-items:center;gap:16px;z-index:90;}
.hamburger{display:none;background:none;border:none;color:var(--text-primary);font-size:24px;cursor:pointer;}
.topbar-title{font-family:'Fraunces',serif;font-size:20px;font-weight:600;color:var(--text-primary);flex:1;}
.search-bar{display:flex;align-items:center;gap:10px;background:var(--bg-app);border:1px solid var(--border);border-radius:8px;padding:8px 16px;width:300px;transition:all .2s;color:var(--text-primary);}
.search-bar:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow);}
.search-bar input{border:none;background:transparent;font-size:13px;color:var(--text-primary);width:100%;outline:none;}
.search-bar input::placeholder{color:var(--text-muted)}
.topbar-actions{display:flex;align-items:center;gap:12px}
.icon-btn{width:36px;height:36px;border-radius:8px;border:1px solid var(--border);background:var(--bg-element);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;transition:all .2s;position:relative;color:var(--text-secondary)}
.icon-btn:hover{background:var(--bg-hover);color:var(--text-primary);border-color:var(--border-light)}
.notif-dot{position:absolute;top:6px;right:6px;width:8px;height:8px;background:var(--danger);border-radius:50%;border:2px solid var(--bg-element)}

/* Content & Scrolls */
.content{flex:1;padding:24px;overflow-y:auto;scroll-behavior:smooth;}
.content::-webkit-scrollbar{width:8px;}
.content::-webkit-scrollbar-track{background:transparent;}
.content::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}
.content::-webkit-scrollbar-thumb:hover{background:var(--border-light);}

/* Alerts */
.alert-banner{display:flex;align-items:flex-start;gap:16px;background:var(--danger-bg);border:1px solid rgba(239,68,68,0.3);border-left:4px solid var(--danger);border-radius:var(--radius);padding:16px 20px;margin-bottom:24px;animation:slideDown 0.4s ease;}
@keyframes slideDown{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}
.alert-icon{font-size:24px;}
.alert-title{font-weight:700;font-size:15px;color:var(--danger);margin-bottom:4px}
.alert-text{font-size:13px;color:var(--text-primary);line-height:1.5;font-weight:400;}
.alert-text strong{color:#f87171;}
.alert-close{background:rgba(239,68,68,0.1);border:none;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;color:var(--danger);cursor:pointer;transition:background .2s;flex-shrink:0;}
.alert-close:hover{background:rgba(239,68,68,0.2)}

/* Typography */
.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.section-title{font-family:'Fraunces',serif;font-size:20px;font-weight:700;color:var(--text-primary)}
.section-sub{font-size:13px;color:var(--text-muted);margin-top:4px}

/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 20px;border-radius:8px;font-family:inherit;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .2s;text-decoration:none;white-space:nowrap;}
.btn-primary{background:var(--accent-gradient);color:#fff;box-shadow:var(--glow)}
.btn-primary:hover{opacity:0.9;transform:translateY(-1px);}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.btn-secondary{background:var(--bg-element);color:var(--text-primary);border:1px solid var(--border)}
.btn-secondary:hover{background:var(--bg-hover);border-color:var(--border-light)}
.btn-sm{padding:6px 14px;font-size:12px}

/* KPIs Grid */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:20px;margin-bottom:28px;}
.kpi-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;position:relative;overflow:hidden;transition:all .3s;box-shadow:var(--shadow);}
.kpi-card:hover{transform:translateY(-3px);border-color:var(--border-light);box-shadow:0 8px 25px rgba(0,0,0,0.4);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.kpi-card.danger::before{background:var(--danger)} .kpi-card.warning::before{background:var(--warning)}
.kpi-card.success::before{background:var(--success)} .kpi-card.info::before{background:var(--accent)}
.kpi-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px}
.kpi-icon{width:46px;height:46px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px}
.kpi-icon.danger{background:var(--danger-bg);color:var(--danger)}
.kpi-icon.warning{background:var(--warning-bg);color:var(--warning)}
.kpi-icon.success{background:var(--success-bg);color:var(--success)}
.kpi-icon.info{background:var(--info-bg);color:var(--info)}
.kpi-trend{display:flex;align-items:center;gap:4px;font-size:12px;font-weight:700;padding:4px 10px;border-radius:20px}
.kpi-trend.up{background:var(--danger-bg);color:var(--danger)}
.kpi-trend.down{background:var(--success-bg);color:var(--success)}
.kpi-trend.neutral{background:var(--bg-element);color:var(--text-secondary)}
.kpi-value{font-family:'Fraunces',serif;font-size:36px;font-weight:700;color:var(--text-primary);line-height:1;margin-bottom:8px}
.kpi-label{font-size:14px;color:var(--text-secondary);font-weight:600}
.kpi-sub{font-size:12px;color:var(--text-muted);margin-top:6px}

/* Layouts */
.two-col{display:grid;grid-template-columns:1fr;gap:24px;margin-bottom:28px;}
@media(min-width: 1024px) { .two-col{grid-template-columns:2fr 1fr;} }

/* Card System */
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);display:flex;flex-direction:column;}
.card-header{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;}
.card-title{font-family:'Fraunces',serif;font-size:16px;font-weight:700;color:var(--text-primary)}
.card-sub{font-size:12px;color:var(--text-muted);margin-top:4px}
.card-body{padding:24px;flex:1;}

/* Chart overrides */
.bar-chart{display:flex;align-items:flex-end;gap:10px;height:140px;width:100%;}
.bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:8px;height:100%}
.bar-col{flex:1;display:flex;flex-direction:column;justify-content:flex-end;width:100%;background:var(--bg-element);border-radius:6px;overflow:hidden;}
.bar{width:100%;border-radius:6px 6px 0 0;min-height:4px;transition:opacity .2s}
.bar:hover{opacity:0.8;cursor:pointer;}
.bar-label{font-size:11px;color:var(--text-muted);text-align:center;font-family:'JetBrains Mono',monospace;}

/* Threat Feed */
.threat-item{display:flex;align-items:flex-start;gap:16px;padding:16px;border-bottom:1px solid var(--border);transition:all .2s;}
.threat-item:last-child{border-bottom:none;}
.threat-item:hover{background:var(--bg-hover);}
.threat-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-top:6px;box-shadow:0 0 10px currentColor;}
.threat-dot.critical{background:var(--danger);color:var(--danger)}
.threat-dot.high{background:#F97316;color:#F97316}
.threat-dot.medium{background:var(--warning);color:var(--warning)}
.threat-dot.low{background:var(--success);color:var(--success)}
.threat-main{flex:1;min-width:0}
.threat-title{font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:6px;line-height:1.4}
.threat-meta{font-size:12px;color:var(--text-muted)}
.threat-badge{font-size:10px;font-weight:800;padding:4px 10px;border-radius:6px;text-transform:uppercase;letter-spacing:0.5px;}

/* Badges */
.badge-critical{background:var(--danger-bg);color:var(--danger);border:1px solid rgba(239,68,68,0.2)}
.badge-high{background:rgba(249,115,22,0.15);color:#F97316;border:1px solid rgba(249,115,22,0.2)}
.badge-medium{background:var(--warning-bg);color:var(--warning);border:1px solid rgba(245,158,11,0.2)}
.badge-low{background:var(--success-bg);color:var(--success);border:1px solid rgba(16,185,129,0.2)}
.badge-open{background:var(--warning-bg);color:var(--warning);border:1px solid rgba(245,158,11,0.2)}
.badge-resolved{background:var(--success-bg);color:var(--success);border:1px solid rgba(16,185,129,0.2)}

/* Risk Gauge */
.risk-gauge{display:flex;flex-direction:column;align-items:center;padding:10px 0}
.gauge-circle{width:140px;height:140px;border-radius:50%;background:conic-gradient(var(--danger) 0deg, var(--warning) 120deg, var(--success) 200deg, var(--border) 200deg);display:flex;align-items:center;justify-content:center;margin-bottom:16px;box-shadow:0 0 30px rgba(239,68,68,0.15)}
.gauge-inner{width:110px;height:110px;background:var(--bg-card);border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center}
.gauge-val{font-family:'Fraunces',serif;font-size:32px;font-weight:700;color:var(--text-primary);line-height:1}
.gauge-unit{font-size:12px;color:var(--text-muted)}
.gauge-label{font-size:14px;font-weight:700;color:var(--danger);margin-bottom:8px;letter-spacing:0.5px}
.gauge-desc{font-size:12px;color:var(--text-muted);text-align:center;max-width:80%}

.risk-breakdown{width:100%;margin-top:20px;display:flex;flex-direction:column;gap:16px}
.risk-row{display:flex;align-items:center;gap:12px}
.risk-row-label{font-size:13px;color:var(--text-secondary);font-weight:600;width:95px;flex-shrink:0}
.risk-bar-track{flex:1;height:8px;background:var(--bg-element);border-radius:4px;overflow:hidden}
.risk-bar-fill{height:100%;border-radius:4px}
.risk-row-pct{font-size:12px;font-weight:700;color:var(--text-primary);width:36px;text-align:right;font-family:'JetBrains Mono',monospace}

/* Forms */
.portal-form{display:flex;flex-direction:column;gap:20px}
.form-group{display:flex;flex-direction:column;gap:8px}
.form-label{font-size:13px;font-weight:600;color:var(--text-secondary);}
.form-input,.form-select,.form-textarea{font-family:inherit;font-size:14px;color:var(--text-primary);background:var(--bg-app);border:1px solid var(--border);border-radius:8px;padding:12px 16px;outline:none;transition:all .2s;width:100%}
.form-input:focus,.form-select:focus,.form-textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow);background:var(--bg-element);}
.form-textarea{resize:vertical;min-height:100px}
.ai-chip{display:inline-flex;align-items:center;gap:6px;background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);color:#A78BFA;font-size:12px;font-weight:700;padding:6px 12px;border-radius:20px;}

/* Tables */
.table-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
thead tr{border-bottom:2px solid var(--border);background:var(--bg-element);}
th{text-align:left;font-size:12px;font-weight:700;color:var(--text-secondary);letter-spacing:1px;text-transform:uppercase;padding:16px;}
tbody tr{border-bottom:1px solid var(--border);transition:background .2s;cursor:pointer;}
tbody tr:hover{background:var(--bg-hover);}
td{padding:16px;font-size:14px;color:var(--text-primary);vertical-align:middle;}
td.mono{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-secondary);}

/* Modules Grid */
.module-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:20px;margin-bottom:32px;}
.module-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;cursor:pointer;transition:all .3s;box-shadow:var(--shadow);}
.module-card:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:var(--glow);}
.module-icon{font-size:32px;margin-bottom:16px;display:inline-block;padding:12px;background:var(--bg-element);border-radius:12px;border:1px solid var(--border-light);}
.module-title{font-family:'Fraunces',serif;font-size:16px;font-weight:700;color:var(--text-primary);margin-bottom:8px}
.module-desc{font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:16px;}
.module-stat{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-secondary);display:flex;align-items:center;gap:8px;padding-top:16px;border-top:1px solid var(--border);}
.module-stat span{color:var(--accent);font-weight:700}

/* Pills & Badges */
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;padding:6px 12px;border-radius:20px}
.pill::before{content:'●';font-size:10px}
.pill-live{background:var(--success-bg);color:var(--success);border:1px solid rgba(16,185,129,0.2)}
.pill-live::before{animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.pill-idle{background:var(--bg-element);color:var(--text-muted);}
.pill-warn{background:var(--warning-bg);color:var(--warning);border:1px solid rgba(245,158,11,0.2)}

/* Progress tracks */
.progress-track{height:8px;background:var(--bg-app);border-radius:4px;overflow:hidden;border:1px solid var(--border)}
.progress-fill{height:100%;border-radius:4px;box-shadow:var(--glow)}

/* Activity Feed */
.activity-item{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid var(--border);}
.activity-item:last-child{border-bottom:none;}
.activity-avatar{width:36px;height:36px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;}
.act-a1{background:var(--accent-gradient)} .act-a2{background:linear-gradient(135deg,#10B981,#059669)} .act-a3{background:linear-gradient(135deg,#F59E0B,#D97706)} .act-a4{background:linear-gradient(135deg,#8B5CF6,#6D28D9)} .act-a5{background:linear-gradient(135deg,#EF4444,#DC2626)}
.activity-text{font-size:14px;color:var(--text-secondary);line-height:1.5}
.activity-text strong{color:var(--text-primary);font-weight:600}
.activity-time{font-size:12px;color:var(--text-muted);margin-top:6px;font-family:'JetBrains Mono',monospace}

/* Modals */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:all .3s;}
.modal-overlay.open{opacity:1;pointer-events:all}
.modal{background:var(--bg-card);border:1px solid var(--border-light);border-radius:var(--radius);box-shadow:0 24px 50px rgba(0,0,0,0.5);width:600px;max-width:95vw;max-height:90vh;overflow-y:auto;transform:translateY(30px) scale(0.95);transition:all .3s;}
.modal-overlay.open .modal{transform:translateY(0) scale(1)}
.modal-header{padding:24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.modal-title{font-family:'Fraunces',serif;font-size:20px;font-weight:700;color:var(--text-primary)}
.modal-close{width:36px;height:36px;border-radius:8px;background:var(--bg-element);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--text-secondary);transition:all .2s}
.modal-close:hover{background:var(--danger-bg);color:var(--danger);border-color:var(--danger)}
.modal-body{padding:24px;display:flex;flex-direction:column;gap:20px}

/* Toasts */
.toast-container{position:fixed;bottom:24px;right:24px;display:flex;flex-direction:column;gap:12px;z-index:10000}
.toast{display:flex;align-items:flex-start;gap:16px;background:var(--bg-card);border:1px solid var(--border-light);border-radius:12px;padding:16px;box-shadow:var(--shadow);min-width:320px;max-width:400px;animation:toastIn .3s cubic-bezier(0.175, 0.885, 0.32, 1.275) both}
@keyframes toastIn{from{opacity:0;transform:translateX(50px) scale(0.9)}to{opacity:1;transform:translateX(0) scale(1)}}
@keyframes toastOut{to{opacity:0;transform:translateX(50px) scale(0.9)}}
.toast.hide{animation:toastOut .3s ease forwards}
.toast-icon{font-size:24px;margin-top:2px}
.toast-title{font-size:14px;font-weight:700;color:var(--text-primary);margin-bottom:4px}
.toast-msg{font-size:13px;color:var(--text-secondary);line-height:1.5}
.toast-ref{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--accent);font-weight:700;margin-top:8px}
.toast.success{border-left:4px solid var(--success)} .toast.error{border-left:4px solid var(--danger)} .toast.info{border-left:4px solid var(--info)}

/* Mobile Overlay */
.sidebar-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(2px);z-index:998;opacity:0;pointer-events:none;transition:opacity 0.3s;}
.sidebar-overlay.active{opacity:1;pointer-events:all;}

/* RESPONSIVE DESIGN */
@media(max-width:1200px){
  .kpi-grid{grid-template-columns:repeat(2, 1fr);}
  .module-grid{grid-template-columns:repeat(2, 1fr);}
}
@media(max-width:900px){
  .sidebar{position:fixed;top:0;left:0;height:100vh;transform:translateX(-100%);box-shadow:var(--shadow);}
  .sidebar.open{transform:translateX(0);}
  .close-sidebar-btn{display:block;}
  .hamburger{display:block;}
  .topbar-title{font-size:16px;}
  .search-bar{display:none;}
  .two-col, .kpi-grid, .module-grid{grid-template-columns:1fr;}
}
@media(max-width:600px){
  .card-header{flex-direction:column;align-items:flex-start;gap:12px;}
  .content{padding:16px;}
  .alert-banner{flex-direction:column;}
  .btn{width:100%;}
}
</style>"""

html = re.sub(r'<style>.*?</style>', new_style, html, flags=re.DOTALL)

# Add sidebar overlay
if 'sidebarOverlay' not in html:
    html = html.replace('<!-- SIDEBAR -->', '<!-- SIDEBAR -->\n<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>')

# Add topbar hamburger
if "class=\"hamburger\"" not in html:
    html = html.replace('<header class="topbar">', '<header class="topbar">\n    <button class="hamburger" onclick="toggleSidebar()">☰</button>')

# Wrap sidebar section in sidebar-scroll and add close button natively
if 'close-sidebar-btn' not in html:
    old_brand = """  <div class="sidebar-brand">
    <a href="#" class="brand-logo">
      <div class="brand-icon">🛡</div>
      <div>
        <div class="brand-name">CyberSentinel</div>
        <div class="brand-tagline">Neural Defense OS</div>
      </div>
    </a>
  </div>"""
    new_brand = """  <div class="sidebar-brand">
    <a href="#" class="brand-logo">
      <div class="brand-icon">🛡</div>
      <div>
        <div class="brand-name">CyberSentinel</div>
        <div class="brand-tagline">Defense OS</div>
      </div>
    </a>
    <button class="close-sidebar-btn" onclick="toggleSidebar()">✕</button>
  </div>
  <div class="sidebar-scroll">"""
    html = html.replace(old_brand, new_brand)
    
    # Close sidebar-scroll before footer
    html = html.replace('  <div class="sidebar-footer">', '  </div>\n  <div class="sidebar-footer">')

# Modify toggle JS
js_toggle = """
// ─── SIDEBAR TOGGLE ─────────────────────────────────────────────
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').classList.toggle('active');
}
"""
if "toggleSidebar()" not in html:
    html = html.replace('// ─── TOAST ──', js_toggle + '\n// ─── TOAST ──')

# Minor inline style cleanups for form AI Box
html = html.replace('background:linear-gradient(135deg,#FEF8F0,#FEF0E0)', 'background:var(--info-bg)')
html = html.replace('color:var(--rust)', 'color:var(--info)')
html = html.replace('border-left:4px solid var(--terracotta)', '')
html = html.replace('color:var(--mahogany)', 'color:var(--text-primary)')


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("UI Successfully Updated!")
