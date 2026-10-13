"""School Transport Route & Student Pickup Management - Review 3
Run: python transport_app.py   (needs only Python 3 with Tkinter; DB = transport.db)
Business rules are enforced INSIDE the database (CHECK, UNIQUE, partial index, triggers).
Delete transport.db to reset the demo data."""
import os, sqlite3, tkinter as tk
from datetime import date, datetime
from tkinter import ttk, messagebox

DB = "transport.db"
R_OF = "(SELECT route_id FROM route_stop WHERE route_stop_id=NEW.route_stop_id)"
SCHEMA = f"""
CREATE TABLE bus(bus_id INTEGER PRIMARY KEY, reg_no TEXT UNIQUE NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 80),
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN('Active','Maintenance','Retired')));
CREATE TABLE driver(driver_id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT,
 licence_no TEXT UNIQUE NOT NULL, licence_expiry DATE NOT NULL);
CREATE TABLE attendant(attendant_id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT);
CREATE TABLE route(route_id INTEGER PRIMARY KEY, route_name TEXT UNIQUE NOT NULL, start_point TEXT, end_point TEXT);
CREATE TABLE stop(stop_id INTEGER PRIMARY KEY, stop_name TEXT UNIQUE NOT NULL, landmark TEXT);
CREATE TABLE route_stop(route_stop_id INTEGER PRIMARY KEY,
 route_id INTEGER NOT NULL REFERENCES route ON DELETE CASCADE,
 stop_id INTEGER NOT NULL REFERENCES stop,
 stop_seq INTEGER NOT NULL CHECK(stop_seq>0), pickup_time TEXT,
 UNIQUE(route_id,stop_seq), UNIQUE(route_id,stop_id));
CREATE TABLE route_allocation(alloc_id INTEGER PRIMARY KEY, route_id INTEGER NOT NULL REFERENCES route,
 bus_id INTEGER NOT NULL REFERENCES bus, driver_id INTEGER NOT NULL REFERENCES driver,
 attendant_id INTEGER REFERENCES attendant, from_date DATE NOT NULL, to_date DATE);
CREATE TABLE student(student_id INTEGER PRIMARY KEY, name TEXT NOT NULL, class TEXT NOT NULL,
 guardian_name TEXT, guardian_phone TEXT);
CREATE TABLE fee_plan(plan_id INTEGER PRIMARY KEY, plan_name TEXT NOT NULL,
 amount REAL NOT NULL CHECK(amount>0), frequency TEXT);
CREATE TABLE transport_registration(reg_id INTEGER PRIMARY KEY,
 student_id INTEGER NOT NULL REFERENCES student, route_stop_id INTEGER NOT NULL REFERENCES route_stop,
 plan_id INTEGER NOT NULL REFERENCES fee_plan, start_date DATE NOT NULL DEFAULT CURRENT_DATE,
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN('Active','Cancelled')));
CREATE UNIQUE INDEX one_active_per_student ON transport_registration(student_id) WHERE status='Active';
CREATE TABLE pickup_log(log_id INTEGER PRIMARY KEY, reg_id INTEGER NOT NULL REFERENCES transport_registration ON DELETE CASCADE,
 log_date DATE NOT NULL DEFAULT CURRENT_DATE, trip_type TEXT NOT NULL CHECK(trip_type IN('Pickup','Drop')),
 status TEXT NOT NULL CHECK(status IN('Present','Absent','Late')), UNIQUE(reg_id,log_date,trip_type));
CREATE TABLE payment(payment_id INTEGER PRIMARY KEY, reg_id INTEGER NOT NULL REFERENCES transport_registration,
 pay_date DATE NOT NULL DEFAULT CURRENT_DATE, amount_paid REAL NOT NULL CHECK(amount_paid>0),
 mode TEXT NOT NULL DEFAULT 'Cash' CHECK(mode IN('Cash','UPI','Card')), receipt_no TEXT UNIQUE NOT NULL);
CREATE TABLE maintenance(maint_id INTEGER PRIMARY KEY, bus_id INTEGER NOT NULL REFERENCES bus,
 service_date DATE NOT NULL, type TEXT NOT NULL, cost REAL NOT NULL CHECK(cost>=0), next_due_date DATE,
 status TEXT NOT NULL DEFAULT 'Done' CHECK(status IN('Done','In Progress')));
CREATE INDEX idx_student_name ON student(name);
CREATE INDEX idx_pickup_date ON pickup_log(log_date);
CREATE INDEX idx_reg_stop ON transport_registration(route_stop_id);
CREATE INDEX idx_pay_reg ON payment(reg_id);

CREATE TRIGGER trg_licence BEFORE INSERT ON route_allocation BEGIN
 SELECT RAISE(ABORT,'Driver licence expired or expires before allocation start')
  WHERE (SELECT licence_expiry FROM driver WHERE driver_id=NEW.driver_id) <= NEW.from_date;
 SELECT RAISE(ABORT,'Bus is not Active') WHERE (SELECT status FROM bus WHERE bus_id=NEW.bus_id)<>'Active';
END;
CREATE TRIGGER trg_capacity BEFORE INSERT ON transport_registration WHEN NEW.status='Active' BEGIN
 SELECT RAISE(ABORT,'Bus capacity full (or no bus allocated to this route)')
  WHERE (SELECT COUNT(*) FROM transport_registration t JOIN route_stop x USING(route_stop_id)
         WHERE t.status='Active' AND x.route_id={R_OF})
     >= COALESCE((SELECT MIN(b.capacity) FROM route_allocation a JOIN bus b USING(bus_id)
         WHERE a.route_id={R_OF} AND a.to_date IS NULL),0);
END;
CREATE TRIGGER trg_payment BEFORE INSERT ON payment BEGIN
 SELECT RAISE(ABORT,'Payment exceeds fee due')
  WHERE NEW.amount_paid + COALESCE((SELECT SUM(amount_paid) FROM payment WHERE reg_id=NEW.reg_id),0)
      > (SELECT fp.amount FROM fee_plan fp JOIN transport_registration t USING(plan_id) WHERE t.reg_id=NEW.reg_id);
END;
CREATE VIEW v_capacity AS
 SELECT r.route_name, b.reg_no bus, b.capacity, COUNT(tr.reg_id) used,
  b.capacity-COUNT(tr.reg_id) free_seats, ROUND(100.0*COUNT(tr.reg_id)/b.capacity,1) util_pct
 FROM route r JOIN route_allocation a ON a.route_id=r.route_id AND a.to_date IS NULL
 JOIN bus b ON b.bus_id=a.bus_id LEFT JOIN route_stop rs ON rs.route_id=r.route_id
 LEFT JOIN transport_registration tr ON tr.route_stop_id=rs.route_stop_id AND tr.status='Active'
 GROUP BY r.route_id;
CREATE VIEW v_dues AS
 SELECT s.name student, s.guardian_phone, fp.amount fee, COALESCE(SUM(p.amount_paid),0) paid,
  fp.amount-COALESCE(SUM(p.amount_paid),0) due
 FROM transport_registration tr JOIN student s USING(student_id) JOIN fee_plan fp USING(plan_id)
 LEFT JOIN payment p ON p.reg_id=tr.reg_id WHERE tr.status='Active' GROUP BY tr.reg_id;
"""
SEED = """
INSERT INTO bus(reg_no,capacity,status) VALUES('KA01AB1001',4,'Active'),('KA01AB1002',40,'Active'),('KA01AB1003',30,'Maintenance');
INSERT INTO driver(name,phone,licence_no,licence_expiry) VALUES('Ravi Kumar','9800000001','DL-1001','2030-05-01'),
 ('Anil Das','9800000002','DL-1002','2029-01-15'),('Sunil Rao','9800000003','DL-1003','2025-01-01');
INSERT INTO attendant(name,phone) VALUES('Meena','9700000001'),('Latha','9700000002'),('Geeta','9700000003');
INSERT INTO route(route_name,start_point,end_point) VALUES('R1 North','School','Hill Park'),('R2 South','School','Lake View');
INSERT INTO stop(stop_name,landmark) VALUES('Hill Park','Temple'),('Green Ave','Bank'),('Mall Road','Mall'),
 ('Lake View','Lake'),('Station Rd','Railway Stn'),('Market','Bus Stand');
INSERT INTO route_stop(route_id,stop_id,stop_seq,pickup_time) VALUES(1,1,1,'07:00'),(1,2,2,'07:10'),(1,3,3,'07:20'),
 (2,4,1,'07:05'),(2,5,2,'07:15'),(2,6,3,'07:25');
INSERT INTO route_allocation(route_id,bus_id,driver_id,attendant_id,from_date) VALUES(1,1,1,1,'2026-06-01'),(2,2,2,2,'2026-06-01');
INSERT INTO student(name,class,guardian_name,guardian_phone) VALUES('Aarav S','5A','Suresh S','9000000001'),
 ('Diya M','6B','Mohan M','9000000002'),('Kabir R','7A','Rita R','9000000003'),('Isha P','4C','Prem P','9000000004'),
 ('Neel T','8B','Tara T','9000000005'),('Sara K','3A','Kiran K','9000000006'),('Vihaan D','9A','Dev D','9000000007'),
 ('Anya G','2B','Gita G','9000000008');
INSERT INTO fee_plan(plan_name,amount,frequency) VALUES('Monthly',1500,'Monthly'),('Term',6000,'Term');
INSERT INTO transport_registration(student_id,route_stop_id,plan_id,start_date) VALUES(1,1,1,'2026-06-01'),(2,2,1,'2026-06-01'),
 (3,3,2,'2026-06-01'),(4,3,1,'2026-06-01'),(5,4,2,'2026-06-01'),(6,5,1,'2026-06-01'),(7,6,2,'2026-06-01');
INSERT INTO payment(reg_id,amount_paid,mode,receipt_no) VALUES(1,1500,'Cash','RC001'),(2,500,'UPI','RC002'),(5,6000,'Card','RC003');
INSERT INTO pickup_log(reg_id,trip_type,status) VALUES(1,'Pickup','Present'),(2,'Pickup','Absent'),(3,'Pickup','Late'),(5,'Pickup','Absent');
INSERT INTO maintenance(bus_id,service_date,type,cost,next_due_date,status) VALUES(1,'2026-07-01','Oil change',3500,'2026-10-01','Done'),
 (2,'2026-09-01','Full service',9000,'2027-03-01','Done'),(3,'2026-09-20','Engine repair',25000,NULL,'In Progress');
"""
REPORTS = {
 "Route list": "SELECT r.route_name, rs.stop_seq, s.stop_name, rs.pickup_time FROM route_stop rs JOIN route r USING(route_id) JOIN stop s USING(stop_id) ORDER BY r.route_name, rs.stop_seq",
 "Capacity utilization": "SELECT * FROM v_capacity",
 "Absent students today": "SELECT s.name, s.class, r.route_name, st.stop_name, s.guardian_phone FROM pickup_log pl JOIN transport_registration tr USING(reg_id) JOIN student s USING(student_id) JOIN route_stop rs USING(route_stop_id) JOIN route r USING(route_id) JOIN stop st USING(stop_id) WHERE pl.status='Absent' AND pl.log_date=date('now')",
 "Fee dues": "SELECT * FROM v_dues WHERE due>0 ORDER BY due DESC",
 "Students with no payment (nested)": "SELECT name, class FROM student WHERE student_id IN (SELECT student_id FROM transport_registration WHERE status='Active' AND reg_id NOT IN (SELECT reg_id FROM payment))",
 "Driver assignments": "SELECT d.name driver, d.licence_expiry, b.reg_no bus, r.route_name, a.from_date, a.to_date FROM route_allocation a JOIN driver d USING(driver_id) JOIN bus b USING(bus_id) JOIN route r USING(route_id)",
 "Maintenance status": "SELECT b.reg_no, b.status, MAX(m.service_date) last_service, MAX(m.next_due_date) next_due, SUM(m.cost) total_cost, CASE WHEN MAX(m.next_due_date)<date('now') THEN 'OVERDUE' ELSE 'OK' END flag FROM bus b LEFT JOIN maintenance m USING(bus_id) GROUP BY b.bus_id",
}

fresh = not os.path.exists(DB)
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")
if fresh:
    con.executescript(SCHEMA + SEED)
    con.commit()

root = tk.Tk(); root.title("School Transport Management"); root.geometry("900x560")
nb = ttk.Notebook(root); nb.pack(fill="both", expand=True)
refreshers = []

def show(tree, sql, flt=""):
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c); tree.column(c, width=110, anchor="w")
    tree.delete(*tree.get_children())
    for row in cur.fetchall():
        if flt.lower() in " ".join(map(str, row)).lower():
            tree.insert("", "end", values=row)

def tab(title, table, pk, fields, cols, view):
    f = ttk.Frame(nb); nb.add(f, text=title)
    box = ttk.Frame(f); box.pack(fill="x", padx=6, pady=4)
    ents = []
    for i, (lab, src) in enumerate(fields):
        ttk.Label(box, text=lab).grid(row=i, column=0, sticky="w", pady=1)
        if isinstance(src, tuple):
            w = ttk.Combobox(box, values=src[1:] if src[0] == "L" else [], state="readonly", width=40)
            if src[0] == "L": w.set(src[1])
        else:
            w = ttk.Entry(box, width=43); w.insert(0, src)
        w.grid(row=i, column=1, padx=6, pady=1); ents.append((lab, src, w))
    tree = ttk.Treeview(f, show="headings", height=10)
    sv = tk.StringVar()
    def refresh():
        for lab, src, w in ents:
            if isinstance(src, tuple) and src[0] == "Q":
                w["values"] = [f"{a} - {b}" for a, b in con.execute(src[1])]
        show(tree, view, sv.get())
    def add():
        vals = []
        for lab, src, w in ents:
            v = w.get().strip()
            if not v and "(opt)" not in lab:
                return messagebox.showwarning("Validation", f"'{lab}' is required")
            if "date" in lab.lower() and v:
                try: datetime.strptime(v, "%Y-%m-%d")
                except ValueError: return messagebox.showwarning("Validation", f"'{lab}' must be YYYY-MM-DD")
            if lab.startswith(("Seq", "Capacity", "Cost", "Amount")) and v:
                try: float(v)
                except ValueError: return messagebox.showwarning("Validation", f"'{lab}' must be a number")
            if isinstance(src, tuple) and src[0] == "Q": v = v.split(" - ")[0]
            vals.append(v or None)
        try:
            with con:
                con.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?'*len(cols))})", vals)
            messagebox.showinfo("Saved", "Record added")
            refresh_all()
        except sqlite3.Error as e:
            messagebox.showerror("Rejected by database", str(e))
    def delete():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Delete", "Select a row first")
        if not messagebox.askyesno("Confirm", "Delete selected record?"): return
        try:
            with con: con.execute(f"DELETE FROM {table} WHERE {pk}=?", (tree.item(sel[0])["values"][0],))
            refresh_all()
        except sqlite3.Error as e:
            messagebox.showerror("Cannot delete", str(e))
    bar = ttk.Frame(f); bar.pack(fill="x", padx=6)
    ttk.Button(bar, text="Add", command=add).pack(side="left")
    ttk.Button(bar, text="Delete selected", command=delete).pack(side="left", padx=6)
    ttk.Label(bar, text="Search:").pack(side="left", padx=(20, 2))
    e = ttk.Entry(bar, textvariable=sv, width=22); e.pack(side="left")
    e.bind("<KeyRelease>", lambda _: refresh())
    tree.pack(fill="both", expand=True, padx=6, pady=6)
    refreshers.append(refresh); refresh()

def refresh_all():
    for r in refreshers: r()

T = date.today().isoformat()
Q = lambda s: ("Q", s)
tab("Routes", "route", "route_id", [("Route name", ""), ("Start point", ""), ("End point", "")],
    ["route_name", "start_point", "end_point"], "SELECT * FROM route")
tab("Stops", "stop", "stop_id", [("Stop name", ""), ("Landmark (opt)", "")],
    ["stop_name", "landmark"], "SELECT * FROM stop")
tab("Route Setup", "route_stop", "route_stop_id",
    [("Route", Q("SELECT route_id, route_name FROM route")), ("Stop", Q("SELECT stop_id, stop_name FROM stop")),
     ("Seq no.", ""), ("Pickup time (HH:MM)", "07:00")],
    ["route_id", "stop_id", "stop_seq", "pickup_time"],
    "SELECT rs.route_stop_id, r.route_name, rs.stop_seq, s.stop_name, rs.pickup_time FROM route_stop rs JOIN route r USING(route_id) JOIN stop s USING(stop_id) ORDER BY 2,3")
tab("Students", "student", "student_id", [("Name", ""), ("Class", ""), ("Guardian", ""), ("Guardian phone", "")],
    ["name", "class", "guardian_name", "guardian_phone"], "SELECT * FROM student")
tab("Student-Stop", "transport_registration", "reg_id",
    [("Student", Q("SELECT student_id, name FROM student")),
     ("Stop", Q("SELECT rs.route_stop_id, r.route_name||' / '||s.stop_name FROM route_stop rs JOIN route r USING(route_id) JOIN stop s USING(stop_id)")),
     ("Fee plan", Q("SELECT plan_id, plan_name||' '||amount FROM fee_plan")), ("Start date", T)],
    ["student_id", "route_stop_id", "plan_id", "start_date"],
    "SELECT tr.reg_id, s.name, r.route_name, st.stop_name, tr.status FROM transport_registration tr JOIN student s USING(student_id) JOIN route_stop rs USING(route_stop_id) JOIN route r USING(route_id) JOIN stop st USING(stop_id)")
tab("Bus Allocation", "route_allocation", "alloc_id",
    [("Route", Q("SELECT route_id, route_name FROM route")), ("Bus", Q("SELECT bus_id, reg_no||' cap '||capacity FROM bus")),
     ("Driver", Q("SELECT driver_id, name FROM driver")), ("Attendant", Q("SELECT attendant_id, name FROM attendant")),
     ("From date", T)],
    ["route_id", "bus_id", "driver_id", "attendant_id", "from_date"],
    "SELECT a.alloc_id, r.route_name, b.reg_no, d.name driver, at.name attendant, a.from_date, a.to_date FROM route_allocation a JOIN route r USING(route_id) JOIN bus b USING(bus_id) JOIN driver d USING(driver_id) JOIN attendant at USING(attendant_id)")
tab("Pickup", "pickup_log", "log_id",
    [("Student", Q("SELECT tr.reg_id, s.name FROM transport_registration tr JOIN student s USING(student_id) WHERE tr.status='Active'")),
     ("Log date", T), ("Trip", ("L", "Pickup", "Drop")), ("Status", ("L", "Present", "Absent", "Late"))],
    ["reg_id", "log_date", "trip_type", "status"],
    "SELECT pl.log_id, s.name, pl.log_date, pl.trip_type, pl.status FROM pickup_log pl JOIN transport_registration tr USING(reg_id) JOIN student s USING(student_id) ORDER BY pl.log_date DESC")
tab("Fees", "payment", "payment_id",
    [("Student", Q("SELECT tr.reg_id, s.name FROM transport_registration tr JOIN student s USING(student_id) WHERE tr.status='Active'")),
     ("Amount", ""), ("Mode", ("L", "Cash", "UPI", "Card")), ("Receipt no", ""), ("Pay date", T)],
    ["reg_id", "amount_paid", "mode", "receipt_no", "pay_date"],
    "SELECT p.payment_id, s.name, p.amount_paid, p.mode, p.receipt_no, p.pay_date FROM payment p JOIN transport_registration tr USING(reg_id) JOIN student s USING(student_id)")
tab("Maintenance", "maintenance", "maint_id",
    [("Bus", Q("SELECT bus_id, reg_no FROM bus")), ("Service date", T), ("Type", ""), ("Cost", ""),
     ("Next due date (opt)", ""), ("Status", ("L", "Done", "In Progress"))],
    ["bus_id", "service_date", "type", "cost", "next_due_date", "status"],
    "SELECT m.maint_id, b.reg_no, m.service_date, m.type, m.cost, m.next_due_date, m.status FROM maintenance m JOIN bus b USING(bus_id)")

rf = ttk.Frame(nb); nb.add(rf, text="Reports")
top = ttk.Frame(rf); top.pack(fill="x", padx=6, pady=6)
cb = ttk.Combobox(top, values=list(REPORTS), state="readonly", width=40); cb.set("Route list"); cb.pack(side="left")
rt = ttk.Treeview(rf, show="headings", height=14)
def run_report():
    try: show(rt, REPORTS[cb.get()])
    except sqlite3.Error as e: messagebox.showerror("Report error", str(e))
ttk.Button(top, text="Run", command=run_report).pack(side="left", padx=6)
rt.pack(fill="both", expand=True, padx=6, pady=6); run_report()
nb.bind("<<NotebookTabChanged>>", lambda _: (refresh_all(), run_report()))
root.mainloop()
