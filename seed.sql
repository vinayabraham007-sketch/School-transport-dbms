-- Sample data

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
