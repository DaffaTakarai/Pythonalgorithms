#!/usr/bin/env python3
"""
cyt_gui.py — Cybersentra Helpdesk (Desktop GUI - CustomTkinter)
Features:
 - CustomTkinter modern UI (dark/light)
 - Login (bcrypt + seeded users)
 - Dashboard: cards + interactive charts (matplotlib)
 - Tickets tab: Treeview table, search, filter, create, update, delete
 - Analytics tab: larger charts, click-to-filter interactions
 - Users tab: admin-only user management
 - Export tickets to CSV
 - Notifications (messageboxes)
 - SQLite backend (ticket.db)

Dependencies:
    pip install customtkinter bcrypt matplotlib pillow

Run:
    python cyt_gui.py
"""

import os
import sqlite3
import bcrypt
import csv
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# -----------------------------
# Configuration
# -----------------------------
APP_NAME = "Cybersentra Helpdesk — Desktop Pro"
DB_FILE = "ticket.db"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 720

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# -----------------------------
# Database helpers
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    need_seed = not os.path.exists(DB_FILE)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        division TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Normal',
        status TEXT DEFAULT 'Open',
        division TEXT,
        assigned_to TEXT,
        created_by TEXT,
        created_at TEXT
    )''')
    conn.commit()

    # seed users
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()['c'] == 0:
        seed_users = [
            ("admin","admin","admin","IT Support"),
            ("it_support","12345","user","IT Support"),
            ("security","12345","user","Security"),
            ("finance","12345","user","Finance"),
            ("marketing","12345","user","Marketing"),
            ("hr","12345","user","HR"),
        ]
        for u,p,role,div in seed_users:
            pw = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
            cur.execute("INSERT INTO users (username,password,role,division) VALUES (?,?,?,?)", (u,pw,role,div))
        conn.commit()

    # seed sample tickets
    cur.execute("SELECT COUNT(*) as c FROM tickets")
    if cur.fetchone()['c'] == 0:
        now = datetime.utcnow()
        samples = [
            ("VPN access issue","User can't authenticate to VPN","High","IT Support",None,"it_support",(now - timedelta(days=1)).isoformat()),
            ("Suspicious email reported","Possible phishing", "Normal","Security",None,"security",(now - timedelta(days=3)).isoformat()),
            ("Invoice discrepancy","Invoice #123 total mismatch","Normal","Finance",None,"finance",(now - timedelta(days=2)).isoformat()),
            ("Landing page 500","Marketing site shows 500", "High","Marketing",None,"marketing",(now - timedelta(days=5)).isoformat()),
            ("HR portal bug","Can't submit leave request","Low","HR",None,"hr",(now - timedelta(days=4)).isoformat()),
        ]
        for t in samples:
            cur.execute('INSERT INTO tickets (title,description,priority,division,assigned_to,created_by,created_at) VALUES (?,?,?,?,?,?,?)', t)
        conn.commit()
    conn.close()

# -----------------------------
# Data helpers
# -----------------------------
def fetch_users():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id,username,role,division FROM users ORDER BY username")
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

def fetch_tickets(status=None, division=None, q=None):
    conn = get_conn(); cur = conn.cursor()
    sql = "SELECT * FROM tickets"
    clauses = []; params = []
    if status and status != 'All': clauses.append("status=?"); params.append(status)
    if division and division != 'All': clauses.append("division=?"); params.append(division)
    if q: clauses.append("(title LIKE ? OR description LIKE ?)"); params.extend([f"%{q}%", f"%{q}%"])
    if clauses: sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

def counts_by_status():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) as c FROM tickets GROUP BY status")
    data = {r['status']: r['c'] for r in cur.fetchall()}
    conn.close()
    total = sum(data.values()) if data else 0
    return {
        'Open': data.get('Open', 0),
        'In Progress': data.get('In Progress', 0),
        'Resolved': data.get('Resolved', 0),
        'Total': total
    }

def tickets_per_division():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT division, COUNT(*) as c FROM tickets GROUP BY division")
    rows = cur.fetchall(); conn.close()
    divs = [r['division'] or 'Unknown' for r in rows]
    counts = [r['c'] for r in rows]
    return divs, counts

def tickets_over_time(days=14):
    conn = get_conn(); cur = conn.cursor()
    end = datetime.utcnow().date()
    start = end - timedelta(days=days-1)
    buckets = {}
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        buckets[d] = 0
    cur.execute("SELECT created_at FROM tickets WHERE created_at IS NOT NULL")
    for r in cur.fetchall():
        try:
            dt = datetime.fromisoformat(r['created_at'])
            d = dt.date().isoformat()
            if d in buckets:
                buckets[d] += 1
        except Exception:
            continue
    conn.close()
    dates = list(buckets.keys())
    counts = [buckets[d] for d in dates]
    return dates, counts

# -----------------------------
# App: Main Window
# -----------------------------
class HelpdeskApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # state
        self.current_user = None  # dict row
        self.active_filter_status = 'All'
        self.active_filter_division = 'All'
        self.active_search_q = ''

        # Create frames: splash -> login -> main (we'll show login first)
        self.login_window = LoginFrame(self, on_success=self.on_login_success)
        self.login_window.pack(fill='both', expand=True)

    def on_login_success(self, user_row):
        self.current_user = user_row
        self.login_window.pack_forget()
        # build main UI
        self.main_ui = MainUI(self, user_row)
        self.main_ui.pack(fill='both', expand=True)

    def on_close(self):
        if messagebox.askokcancel("Exit", "Quit application?"):
            self.destroy()

# -----------------------------
# Login Frame
# -----------------------------
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self, corner_radius=8)
        card.grid(row=0, column=0, padx=24, pady=24, sticky='nsew')

        ctk.CTkLabel(card, text=APP_NAME, font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20,8))
        ctk.CTkLabel(card, text="Please login to continue", text_color="#bfcfe6").pack(pady=(0,12))

        frm = ctk.CTkFrame(card)
        frm.pack(padx=16, pady=8, fill='x')

        ctk.CTkLabel(frm, text="Username").pack(anchor='w')
        self.ent_user = ctk.CTkEntry(frm, width=300)
        self.ent_user.pack(pady=(4,8))
        ctk.CTkLabel(frm, text="Password").pack(anchor='w')
        self.ent_pass = ctk.CTkEntry(frm, width=300, show='*')
        self.ent_pass.pack(pady=(4,10))
        self.ent_pass.bind("<Return>", lambda e: self.try_login())

        btn = ctk.CTkButton(frm, text="Login", command=self.try_login)
        btn.pack(pady=(6,16))

        ctk.CTkLabel(card, text="Default: admin/admin  • sample users: it_support,... (pwd 12345)", text_color="#93a6c0").pack(pady=(0,16))

    def try_login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        if not u or not p:
            messagebox.showwarning("Validation", "Please enter username and password")
            return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (u,))
        row = cur.fetchone(); conn.close()
        if not row:
            messagebox.showerror("Login failed", "User not found")
            return
        try:
            ok = bcrypt.checkpw(p.encode(), row['password'].encode())
        except Exception:
            ok = False
        if ok:
            user_row = dict(row)
            self.on_success(user_row)
        else:
            messagebox.showerror("Login failed", "Wrong password")

# -----------------------------
# Main UI (after login)
# -----------------------------
class MainUI(ctk.CTkFrame):
    def __init__(self, parent, user_row):
        super().__init__(parent)
        self.parent = parent
        self.user = user_row
        self.pack_propagate(False)
        self.build_ui()

    def build_ui(self):
        # layout: sidebar | content
        self.grid_columnconfigure(1, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=0, column=0, sticky='nsw', padx=(12,6), pady=12)
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, sticky='nsew', padx=(6,12), pady=12)

        # Sidebar
        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12,8))
        self.btn_overview = ctk.CTkButton(self.sidebar, text="Overview", command=self.show_overview)
        self.btn_tickets = ctk.CTkButton(self.sidebar, text="Tickets", command=self.show_tickets)
        self.btn_analytics = ctk.CTkButton(self.sidebar, text="Analytics", command=self.show_analytics)
        self.btn_users = ctk.CTkButton(self.sidebar, text="Users", command=self.show_users)
        self.btn_export = ctk.CTkButton(self.sidebar, text="Export CSV", command=self.export_csv)
        self.btn_logout = ctk.CTkButton(self.sidebar, text="Logout", fg_color="red", command=self.logout)

        self.btn_overview.pack(fill='x', padx=12, pady=(6,6))
        self.btn_tickets.pack(fill='x', padx=12, pady=(6,6))
        self.btn_analytics.pack(fill='x', padx=12, pady=(6,6))
        if self.user['role'] == 'admin':
            self.btn_users.pack(fill='x', padx=12, pady=(6,6))
        self.btn_export.pack(fill='x', padx=12, pady=(6,6))
        self.btn_logout.pack(side='bottom', pady=12, padx=12)

        # Header: user and theme toggle
        hdr = ctk.CTkFrame(self.content)
        hdr.pack(fill='x', padx=12, pady=(6,8))
        ctk.CTkLabel(hdr, text=f"Hello, {self.user['username']}", text_color="#cfe9ff").pack(side='left')
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        self.theme_toggle = ctk.CTkOptionMenu(hdr, values=["dark","light"], variable=self.theme_var, command=self.change_theme)
        self.theme_toggle.pack(side='right')

        # Content frames (stacked)
        self.frames = {}
        for name in ['overview','tickets','analytics','users']:
            f = ctk.CTkFrame(self.content)
            f.pack(fill='both', expand=True)
            f.place(x=0, y=50, relwidth=1, relheight=1, anchor='nw')
            f.lower()
            self.frames[name] = f

        # Build each frame
        self.build_overview(self.frames['overview'])
        self.build_tickets(self.frames['tickets'])
        self.build_analytics(self.frames['analytics'])
        self.build_users(self.frames['users'])

        # show overview by default
        self.show_overview()

    def change_theme(self, val):
        ctk.set_appearance_mode(val)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure?"):
            self.master.current_user = None
            self.destroy()
            # restart main app by recreating login
            self.master.login_window = LoginFrame(self.master, on_success=self.master.on_login_success)
            self.master.login_window.pack(fill='both', expand=True)

    # -------------------------
    # Overview frame
    # -------------------------
    def build_overview(self, parent):
        self.ov_parent = parent
        parent.grid_columnconfigure(0, weight=1)
        # top cards
        card_row = ctk.CTkFrame(parent)
        card_row.pack(fill='x', padx=12, pady=(12,8))
        self.card_total = self.make_card(card_row, "Total Tickets", "0")
        self.card_open = self.make_card(card_row, "Open", "0")
        self.card_progress = self.make_card(card_row, "In Progress", "0")
        self.card_resolved = self.make_card(card_row, "Resolved", "0")
        self.card_total.pack(side='left', expand=True, padx=6, pady=6)
        self.card_open.pack(side='left', expand=True, padx=6, pady=6)
        self.card_progress.pack(side='left', expand=True, padx=6, pady=6)
        self.card_resolved.pack(side='left', expand=True, padx=6, pady=6)

        # charts area
        charts_frame = ctk.CTkFrame(parent)
        charts_frame.pack(fill='both', expand=True, padx=12, pady=(6,12))

        left = ctk.CTkFrame(charts_frame)
        left.pack(side='left', fill='both', expand=True, padx=(0,6))
        right = ctk.CTkFrame(charts_frame, width=360)
        right.pack(side='left', fill='y', padx=(6,0))

        # Matplotlib figures
        self.fig_status = Figure(figsize=(4,3), dpi=100)
        self.ax_status = self.fig_status.add_subplot(111)
        self.canvas_status = FigureCanvasTkAgg(self.fig_status, master=left)
        self.canvas_status.get_tk_widget().pack(fill='both', expand=False, pady=6)

        self.fig_trend = Figure(figsize=(6,3), dpi=100)
        self.ax_trend = self.fig_trend.add_subplot(111)
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=left)
        self.canvas_trend.get_tk_widget().pack(fill='both', expand=False, pady=6)

        self.fig_div = Figure(figsize=(4,4.5), dpi=100)
        self.ax_div = self.fig_div.add_subplot(111)
        self.canvas_div = FigureCanvasTkAgg(self.fig_div, master=right)
        self.canvas_div.get_tk_widget().pack(fill='both', expand=True, pady=6)

        # recent list
        recent_card = ctk.CTkFrame(parent)
        recent_card.pack(fill='x', padx=12, pady=(6,12))
        ctk.CTkLabel(recent_card, text="Recent Tickets", font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=6, pady=(6,2))
        self.recent_container = ctk.CTkScrollableFrame(recent_card, height=140)
        self.recent_container.pack(fill='x', padx=6, pady=(4,8))

        # bind clicks on division bars to filter tickets
        self.canvas_div.mpl_connect('button_press_event', self.on_div_click)

    def make_card(self, parent, title, value):
        c = ctk.CTkFrame(parent, corner_radius=8)
        c.inner_title = ctk.CTkLabel(c, text=title, text_color="#bcd9ff")
        c.inner_title.pack(anchor='w', padx=12, pady=(8,0))
        c.inner_value = ctk.CTkLabel(c, text=value, font=ctk.CTkFont(size=20, weight="bold"))
        c.inner_value.pack(anchor='w', padx=12, pady=(6,12))
        return c

    def show_overview(self):
        # raise the frame
        self.frames['overview'].lift()
        self.update_overview()

    def update_overview(self):
        counts = counts_by_status()
        self.card_total.inner_value.configure(text=str(counts.get('Total',0)))
        self.card_open.inner_value.configure(text=str(counts.get('Open',0)))
        self.card_progress.inner_value.configure(text=str(counts.get('In Progress',0)))
        self.card_resolved.inner_value.configure(text=str(counts.get('Resolved',0)))

        # status pie
        self.ax_status.clear()
        sc = counts
        labels = ['Open','In Progress','Resolved']
        sizes = [sc.get(k,0) for k in labels]
        if sum(sizes)==0:
            self.ax_status.text(0.5,0.5,"No data",ha='center',va='center')
        else:
            self.ax_status.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=140)
            self.ax_status.set_title("Status Distribution")
        self.canvas_status.draw()

        # trend
        self.ax_trend.clear()
        dates, tcounts = tickets_over_time(days=14)
        self.ax_trend.plot(dates, tcounts, marker='o')
        self.ax_trend.set_title("Tickets - Last 14 Days")
        self.ax_trend.tick_params(axis='x', rotation=45)
        self.canvas_trend.draw()

        # div bar
        self.ax_div.clear()
        divs, div_counts = tickets_per_division()
        if not divs:
            self.ax_div.text(0.5,0.5,"No data",ha='center',va='center')
        else:
            bars = self.ax_div.barh(divs, div_counts, picker=True)
            self.ax_div.set_title("Tickets by Division (click bar to filter)")
            self.ax_div.invert_yaxis()
            # store bars for click handling
            self._div_bars = bars
        self.canvas_div.draw()

        # recent
        for w in self.recent_container.winfo_children():
            w.destroy()
        rows = fetch_tickets()
        for r in rows[:8]:
            rowf = ctk.CTkFrame(self.recent_container, fg_color="#071226")
            rowf.pack(fill='x', pady=4, padx=6)
            lbl = ctk.CTkLabel(rowf, text=f"#{r['id']} {r['title']}", anchor='w')
            lbl.pack(side='left', padx=6)
            btn = ctk.CTkButton(rowf, text="View", width=80, command=lambda tid=r['id']: self.open_ticket_dialog(tid))
            btn.pack(side='right', padx=6)

    def on_div_click(self, event):
        # map click to bar index
        if not hasattr(self, '_div_bars'):
            return
        for idx, bar in enumerate(self._div_bars):
            contains, _ = bar.contains(event)
            if contains:
                division = bar.get_y()  # y position not label; instead derive label via index
                # fetch corresponding label
                labels = [t.get_text() for t in self.ax_div.get_yticklabels()]
                if idx < len(labels):
                    div_label = labels[idx]
                    self.show_tickets()
                    # set filters in tickets tab and refresh
                    self.tickets_status_combo.set("All")
                    self.tickets_division_combo.set(div_label)
                    self.load_tickets()
                break

    # -------------------------
    # Tickets frame
    # -------------------------
    def build_tickets(self, parent):
        self.tickets_parent = parent
        # controls
        ctrl = ctk.CTkFrame(parent)
        ctrl.pack(fill='x', padx=12, pady=(12,6))
        self.tickets_search = ctk.CTkEntry(ctrl, placeholder_text="Search title/description", width=300)
        self.tickets_search.pack(side='left', padx=(6,8))
        self.tickets_search.bind("<Return>", lambda e: self.load_tickets())
        self.tickets_status_combo = ctk.CTkOptionMenu(ctrl, values=["All","Open","In Progress","Resolved"], width=140, command=lambda v: self.load_tickets())
        self.tickets_status_combo.set("All")
        self.tickets_status_combo.pack(side='left', padx=(6,8))
        self.tickets_division_combo = ctk.CTkOptionMenu(ctrl, values=["All","IT Support","Security","Finance","Marketing","HR"], width=160, command=lambda v: self.load_tickets())
        self.tickets_division_combo.set("All")
        self.tickets_division_combo.pack(side='left', padx=(6,8))
        ctk.CTkButton(ctrl, text="Filter", command=self.load_tickets).pack(side='left', padx=6)
        ctk.CTkButton(ctrl, text="New Ticket", fg_color="#0b84ff", command=self.create_ticket_dialog).pack(side='right', padx=6)

        # table
        table_card = ctk.CTkFrame(parent)
        table_card.pack(fill='both', expand=True, padx=12, pady=(6,12))
        cols = ("id","title","division","priority","status","assigned_to","created_at")
        self.tree = ttk.Treeview(table_card, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=120, anchor='w')
        self.tree.pack(fill='both', expand=True, side='left', padx=(6,0), pady=6)
        # scrollbar
        sb = ttk.Scrollbar(table_card, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side='left', fill='y')

        # context buttons
        actions = ctk.CTkFrame(parent)
        actions.pack(fill='x', padx=12, pady=(0,12))
        ctk.CTkButton(actions, text="View", command=self.action_view_ticket).pack(side='left', padx=6)
        ctk.CTkButton(actions, text="Assign", command=self.action_assign_ticket).pack(side='left', padx=6)
        ctk.CTkButton(actions, text="Set In Progress", command=lambda: self.action_update_status("In Progress")).pack(side='left', padx=6)
        ctk.CTkButton(actions, text="Resolve", command=lambda: self.action_update_status("Resolved")).pack(side='left', padx=6)
        ctk.CTkButton(actions, text="Delete", fg_color="red", command=self.action_delete_ticket).pack(side='left', padx=6)

        # load initial
        self.load_tickets()

    def show_tickets(self):
        self.frames['tickets'].lift()
        self.load_tickets()

    def load_tickets(self):
        q = self.tickets_search.get().strip() if hasattr(self,'tickets_search') else ''
        status = self.tickets_status_combo.get() if hasattr(self,'tickets_status_combo') else 'All'
        division = self.tickets_division_combo.get() if hasattr(self,'tickets_division_combo') else 'All'
        rows = fetch_tickets(status=status, division=division, q=q)
        # clear tree
        for it in self.tree.get_children(): self.tree.delete(it)
        for r in rows:
            self.tree.insert('', 'end', values=(r['id'], r['title'], r['division'] or '-', r['priority'], r['status'], r['assigned_to'] or '-', (r['created_at'] or '')[:19]))

    def get_selected_ticket_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a ticket first")
            return None
        vals = self.tree.item(sel[0])['values']
        return int(vals[0])

    def action_view_ticket(self):
        tid = self.get_selected_ticket_id()
        if tid: self.open_ticket_dialog(tid)

    def action_assign_ticket(self):
        tid = self.get_selected_ticket_id()
        if not tid: return
        users = [u['username'] for u in fetch_users()]
        # simple prompt
        who = ctk.simpledialog.askstring("Assign", f"Assign ticket #{tid} to (username):", initialvalue=(users[0] if users else ""))
        if who:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("UPDATE tickets SET assigned_to=? WHERE id=?", (who, tid)); conn.commit(); conn.close()
            messagebox.showinfo("Assigned", f"Ticket #{tid} assigned to {who}")
            self.load_tickets(); self.update_overview()

    def action_update_status(self, status):
        tid = self.get_selected_ticket_id()
        if not tid: return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("UPDATE tickets SET status=? WHERE id=?", (status, tid)); conn.commit(); conn.close()
        messagebox.showinfo("Updated", f"Ticket #{tid} set to {status}")
        self.load_tickets(); self.update_overview()

    def action_delete_ticket(self):
        tid = self.get_selected_ticket_id()
        if not tid: return
        if not messagebox.askyesno("Delete", f"Delete ticket #{tid}?"): return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM tickets WHERE id=?", (tid,)); conn.commit(); conn.close()
        messagebox.showinfo("Deleted", f"Ticket #{tid} removed")
        self.load_tickets(); self.update_overview()

    def create_ticket_dialog(self):
        dlg = TicketDialog(self, title="Create Ticket")
        self.wait_window(dlg)
        if getattr(dlg, 'result', None):
            data = dlg.result
            conn = get_conn(); cur = conn.cursor()
            cur.execute("INSERT INTO tickets (title,description,priority,division,created_by,created_at) VALUES (?,?,?,?,?,?)",
                        (data['title'], data['description'], data['priority'], data['division'], self.user['username'], datetime.utcnow().isoformat()))
            conn.commit(); conn.close()
            messagebox.showinfo("Saved", "Ticket created")
            self.load_tickets(); self.update_overview()

    def open_ticket_dialog(self, tid):
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM tickets WHERE id=?", (tid,))
        r = cur.fetchone(); conn.close()
        if not r: messagebox.showerror("Not found", "Ticket not found"); return
        dlg = TicketDialog(self, title=f"Ticket #{tid}", data=dict(r))
        self.wait_window(dlg)
        if getattr(dlg, 'deleted', False):
            # deleted inside dialog
            self.load_tickets(); self.update_overview()
            return
        if getattr(dlg, 'updated', False):
            self.load_tickets(); self.update_overview()

    # -------------------------
    # Analytics frame
    # -------------------------
    def build_analytics(self, parent):
        p = parent
        p.pack_propagate(False)
        header = ctk.CTkLabel(p, text="Analytics", font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(anchor='w', padx=12, pady=(12,8))

        # large charts
        charts_area = ctk.CTkFrame(p)
        charts_area.pack(fill='both', expand=True, padx=12, pady=(6,12))

        left = ctk.CTkFrame(charts_area)
        left.pack(side='left', fill='both', expand=True, padx=(0,6))
        right = ctk.CTkFrame(charts_area, width=380)
        right.pack(side='left', fill='y', padx=(6,0))

        # reuse new figures for analytics
        self.figA_trend = Figure(figsize=(6,4), dpi=100)
        self.axA_trend = self.figA_trend.add_subplot(111)
        self.canvasA_trend = FigureCanvasTkAgg(self.figA_trend, master=left)
        self.canvasA_trend.get_tk_widget().pack(fill='both', expand=True, pady=6)

        self.figA_div = Figure(figsize=(4,4.5), dpi=100)
        self.axA_div = self.figA_div.add_subplot(111)
        self.canvasA_div = FigureCanvasTkAgg(self.figA_div, master=right)
        self.canvasA_div.get_tk_widget().pack(fill='both', expand=True, pady=6)
        self.canvasA_div.mpl_connect('button_press_event', self.on_div_click_analytics)

    def show_analytics(self):
        self.frames['analytics'].lift()
        self.update_analytics()

    def update_analytics(self):
        # trend
        self.axA_trend.clear()
        dates, counts = tickets_over_time(days=30)
        self.axA_trend.plot(dates, counts, marker='o')
        self.axA_trend.set_title("Tickets - Last 30 Days")
        self.axA_trend.tick_params(axis='x', rotation=45)
        self.canvasA_trend.draw()

        # div
        self.axA_div.clear()
        divs, counts = tickets_per_division()
        if not divs:
            self.axA_div.text(0.5,0.5,"No data",ha='center',va='center')
        else:
            bars = self.axA_div.barh(divs, counts)
            self.axA_div.invert_yaxis()
            self._analytics_bars = bars
        self.canvasA_div.draw()

    def on_div_click_analytics(self, event):
        if not hasattr(self, '_analytics_bars'): return
        for idx, bar in enumerate(self._analytics_bars):
            contains, _ = bar.contains(event)
            if contains:
                labels = [t.get_text() for t in self.axA_div.get_yticklabels()]
                if idx < len(labels):
                    div_label = labels[idx]
                    self.show_tickets()
                    self.tickets_division_combo.set(div_label)
                    self.load_tickets()
                break

    # -------------------------
    # Users frame (admin)
    # -------------------------
    def build_users(self, parent):
        self.users_parent = parent
        header = ctk.CTkLabel(parent, text="User Management", font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(anchor='w', padx=12, pady=(12,8))
        card = ctk.CTkFrame(parent)
        card.pack(fill='both', expand=True, padx=12, pady=(6,12))
        # table
        cols = ("id","username","role","division")
        self.user_tree = ttk.Treeview(card, columns=cols, show='headings')
        for c in cols:
            self.user_tree.heading(c, text=c.title())
            self.user_tree.column(c, width=120)
        self.user_tree.pack(fill='both', expand=True, side='left', padx=(6,0), pady=6)
        sb = ttk.Scrollbar(card, orient='vertical', command=self.user_tree.yview); self.user_tree.configure(yscroll=sb.set); sb.pack(side='left', fill='y')

        form = ctk.CTkFrame(parent)
        form.pack(fill='x', padx=12, pady=(0,12))
        self.new_user_ent = ctk.CTkEntry(form, placeholder_text="username"); self.new_user_ent.pack(side='left', padx=6)
        self.new_pass_ent = ctk.CTkEntry(form, placeholder_text="password"); self.new_pass_ent.pack(side='left', padx=6)
        self.new_role_opt = ctk.CTkOptionMenu(form, values=["user","admin"]); self.new_role_opt.set("user"); self.new_role_opt.pack(side='left', padx=6)
        self.new_div_ent = ctk.CTkEntry(form, placeholder_text="division"); self.new_div_ent.pack(side='left', padx=6)
        ctk.CTkButton(form, text="Create User", command=self.create_user).pack(side='left', padx=6)
        ctk.CTkButton(form, text="Refresh", command=self.load_users).pack(side='left', padx=6)
        ctk.CTkButton(form, text="Delete Selected", fg_color="red", command=self.delete_selected_user).pack(side='left', padx=6)

        self.load_users()

    def show_users(self):
        if self.user['role'] != 'admin':
            messagebox.showwarning("Access", "Admin only")
            return
        self.frames['users'].lift()
        self.load_users()

    def load_users(self):
        rows = fetch_users()
        for it in self.user_tree.get_children(): self.user_tree.delete(it)
        for r in rows:
            self.user_tree.insert('', 'end', values=(r['id'], r['username'], r['role'], r['division'] or '-'))

    def create_user(self):
        u = self.new_user_ent.get().strip(); p = self.new_pass_ent.get().strip(); role = self.new_role_opt.get(); div = self.new_div_ent.get().strip()
        if not u or not p:
            messagebox.showwarning("Validation","username & password required"); return
        pw = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("INSERT INTO users (username,password,role,division) VALUES (?,?,?,?)", (u,pw,role,div)); conn.commit(); conn.close()
            messagebox.showinfo("Created","User created"); self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create user: {e}")

    def delete_selected_user(self):
        sel = self.user_tree.selection()
        if not sel: messagebox.showwarning("Select","Select a user"); return
        vals = self.user_tree.item(sel[0])['values']
        uid, uname = vals[0], vals[1]
        if messagebox.askyesno("Confirm", f"Delete user {uname}?"):
            conn = get_conn(); cur = conn.cursor(); cur.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit(); conn.close()
            messagebox.showinfo("Deleted","User removed"); self.load_users()

    # -------------------------
    # Utilities
    # -------------------------
    def export_csv(self):
        rows = fetch_tickets()
        if not rows:
            messagebox.showwarning("No data","No tickets to export")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], title="Save tickets as CSV")
        if not filepath: return
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["id","title","description","priority","status","division","assigned_to","created_by","created_at"])
            for r in rows:
                w.writerow([r['id'], r['title'], r['description'], r['priority'], r['status'], r['division'], r['assigned_to'], r['created_by'], r['created_at']])
        messagebox.showinfo("Exported", f"Exported {len(rows)} tickets to {filepath}")

# -----------------------------
# Ticket Dialog (Create / View / Edit)
# -----------------------------
class TicketDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Ticket", data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("700x520")
        self.parent = parent
        self.data = data
        self.result = None
        self.deleted = False
        self.updated = False
        self.build_ui()

    def build_ui(self):
        frm = ctk.CTkFrame(self)
        frm.pack(fill='both', expand=True, padx=12, pady=12)

        ctk.CTkLabel(frm, text=self.title(), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(6,6))
        ctk.CTkLabel(frm, text="Title").pack(anchor='w')
        self.e_title = ctk.CTkEntry(frm, width=680)
        self.e_title.pack(pady=(4,8))
        ctk.CTkLabel(frm, text="Description").pack(anchor='w')
        self.t_desc = ctk.CTkTextbox(frm, width=680, height=200)
        self.t_desc.pack(pady=(4,8))
        bottom = ctk.CTkFrame(frm)
        bottom.pack(fill='x', pady=(8,6))
        ctk.CTkLabel(bottom, text="Priority").pack(side='left', padx=(6,4))
        self.pri_opt = ctk.CTkOptionMenu(bottom, values=["Low","Normal","High"])
        self.pri_opt.set("Normal"); self.pri_opt.pack(side='left', padx=6)
        ctk.CTkLabel(bottom, text="Division").pack(side='left', padx=(12,4))
        self.div_opt = ctk.CTkOptionMenu(bottom, values=["IT Support","Security","Finance","Marketing","HR"])
        self.div_opt.set("IT Support"); self.div_opt.pack(side='left', padx=6)
        ctk.CTkLabel(bottom, text="Assigned To").pack(side='left', padx=(12,4))
        users = [u['username'] for u in fetch_users()]; users.insert(0,"")
        self.assign_opt = ctk.CTkOptionMenu(bottom, values=users)
        self.assign_opt.set("")
        self.assign_opt.pack(side='left', padx=6)

        # action buttons
        btnf = ctk.CTkFrame(frm)
        btnf.pack(pady=(12,6))
        ctk.CTkButton(btnf, text="Save", command=self.save).pack(side='left', padx=6)
        ctk.CTkButton(btnf, text="Delete", fg_color="red", command=self.delete).pack(side='left', padx=6)
        ctk.CTkButton(btnf, text="Close", command=self.close).pack(side='left', padx=6)

        # populate if data
        if self.data:
            self.e_title.insert(0, self.data.get('title',''))
            self.t_desc.insert('1.0', self.data.get('description','') or '')
            self.pri_opt.set(self.data.get('priority','Normal'))
            if self.data.get('division'): self.div_opt.set(self.data.get('division'))
            if self.data.get('assigned_to'): self.assign_opt.set(self.data.get('assigned_to'))

    def save(self):
        title = self.e_title.get().strip()
        desc = self.t_desc.get('1.0','end').strip()
        pri = self.pri_opt.get()
        div = self.div_opt.get()
        who = self.assign_opt.get() or None
        if not title:
            messagebox.showwarning("Validation","Title required"); return
        if self.data:
            # update
            conn = get_conn(); cur = conn.cursor()
            cur.execute("UPDATE tickets SET title=?,description=?,priority=?,division=?,assigned_to=? WHERE id=?",
                        (title, desc, pri, div, who, self.data['id'])); conn.commit(); conn.close()
            messagebox.showinfo("Updated","Ticket updated")
            self.updated = True
            self.destroy()
        else:
            self.result = {'title':title,'description':desc,'priority':pri,'division':div}
            self.destroy()

    def delete(self):
        if not self.data: return
        if not messagebox.askyesno("Confirm","Delete this ticket?"): return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM tickets WHERE id=?", (self.data['id'],)); conn.commit(); conn.close()
        messagebox.showinfo("Deleted","Ticket removed")
        self.deleted = True
        self.destroy()

    def close(self):
        self.destroy()

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    init_db()
    app = HelpdeskApp()
    app.mainloop()
