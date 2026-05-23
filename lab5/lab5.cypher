

// Очищення БД і обмеження

MATCH (n) DETACH DELETE n;

CREATE CONSTRAINT item_id_unique IF NOT EXISTS
FOR (i:Item) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
FOR (c:Customer) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT order_id_unique IF NOT EXISTS
FOR (o:Order) REQUIRE o.id IS UNIQUE;


// заповнення Items(id, name, price), Customers(id, name), Orders(id, date) 

UNWIND [
  {id: 'I001', name: 'iPhone 13', price: 32000},
  {id: 'I002', name: 'Galaxy S23', price: 36000},
  {id: 'I003', name: 'LG OLED C2', price: 54000},
  {id: 'I004', name: 'PlayStation 5', price: 29500},
  {id: 'I005', name: 'Sony WH-CH520', price: 4000},
  {id: 'I006', name: 'Dyson V8 Vacuum', price: 17000}
] AS row
CREATE (:Item {id: row.id, name: row.name, price: row.price});

UNWIND [
  {id: 'C001', name: 'Andrii'},
  {id: 'C002', name: 'Iryna'},
  {id: 'C003', name: 'Oleksii'}
] AS row
CREATE (:Customer {id: row.id, name: row.name});

UNWIND [
  {id: 'O1001', date: date('2026-05-10')},
  {id: 'O1002', date: date('2026-05-11')},
  {id: 'O1003', date: date('2026-05-12')},
  {id: 'O1004', date: date('2026-05-13')}
] AS row
CREATE (:Order {id: row.id, date: row.date});


// Зв'язки: customer має багато orders, item може входити в декілька orders, customer може переглядати, але не купувати items 

UNWIND [
  {customerId: 'C001', orderId: 'O1001'},
  {customerId: 'C001', orderId: 'O1003'},
  {customerId: 'C002', orderId: 'O1002'},
  {customerId: 'C003', orderId: 'O1004'}
] AS row
MATCH (c:Customer {id: row.customerId})
MATCH (o:Order {id: row.orderId})
MERGE (c)-[:BOUGHT]->(o);

UNWIND [
  {orderId: 'O1001', itemId: 'I001', quantity: 1},
  {orderId: 'O1001', itemId: 'I003', quantity: 1},
  {orderId: 'O1002', itemId: 'I002', quantity: 1},
  {orderId: 'O1002', itemId: 'I005', quantity: 2},
  {orderId: 'O1003', itemId: 'I001', quantity: 1},
  {orderId: 'O1003', itemId: 'I004', quantity: 1},
  {orderId: 'O1003', itemId: 'I005', quantity: 1},
  {orderId: 'O1004', itemId: 'I003', quantity: 1},
  {orderId: 'O1004', itemId: 'I004', quantity: 2}
] AS row
MATCH (o:Order {id: row.orderId})
MATCH (i:Item {id: row.itemId})
MERGE (o)-[r:CONTAINS]->(i)
SET r.quantity = row.quantity;

UNWIND [
  {customerId: 'C001', itemId: 'I002'},
  {customerId: 'C001', itemId: 'I005'},
  {customerId: 'C001', itemId: 'I006'},
  {customerId: 'C002', itemId: 'I001'},
  {customerId: 'C002', itemId: 'I002'},
  {customerId: 'C002', itemId: 'I003'},
  {customerId: 'C003', itemId: 'I003'},
  {customerId: 'C003', itemId: 'I004'},
  {customerId: 'C003', itemId: 'I006'}
] AS row
MATCH (c:Customer {id: row.customerId})
MATCH (i:Item {id: row.itemId})
MERGE (c)-[:VIEWED]->(i);


// Запити 

// Знайти Items, які входять в конкретний Order (за Order id)
:param orderId => 'O1003';
MATCH (:Order {id: $orderId})-[r:CONTAINS]->(i:Item)
RETURN i.id AS item_id, i.name AS item_name, r.quantity AS qty, i.price AS price
ORDER BY i.name;

// Підрахувати вартість конкретного Order
:param orderId => 'O1004';
MATCH (:Order {id: $orderId})-[r:CONTAINS]->(i:Item)
RETURN $orderId AS order_id, sum(i.price * coalesce(r.quantity, 1)) AS total_amount;

// Знайти всі Orders конкретного Customer
:param customerId => 'C001';
MATCH (:Customer {id: $customerId})-[:BOUGHT]->(o:Order)
RETURN o.id AS order_id, o.date AS order_date
ORDER BY o.date;

// Знайти всі Items, куплені конкретним Customer (через його Orders)
:param customerId => 'C001';
MATCH (:Customer {id: $customerId})-[:BOUGHT]->(:Order)-[:CONTAINS]->(i:Item)
RETURN DISTINCT i.id AS item_id, i.name AS item_name, i.price AS price
ORDER BY i.name;

// Знайти загальну кількість Items, куплених конкретним Customer
:param customerId => 'C001';
MATCH (:Customer {id: $customerId})-[:BOUGHT]->(:Order)-[r:CONTAINS]->(:Item)
RETURN $customerId AS customer_id, sum(coalesce(r.quantity, 1)) AS total_items_qty;

// Знайти для Customer на яку загальну суму він придбав товари
:param customerId => 'C001';
MATCH (:Customer {id: $customerId})-[:BOUGHT]->(:Order)-[r:CONTAINS]->(i:Item)
RETURN $customerId AS customer_id, sum(i.price * coalesce(r.quantity, 1)) AS total_spent;

// Знайти скільки разів кожен товар був придбаний, відсортувати
MATCH (:Order)-[r:CONTAINS]->(i:Item)
RETURN i.id AS item_id, i.name AS item_name, sum(coalesce(r.quantity, 1)) AS purchased_times
ORDER BY purchased_times DESC, item_name ASC;

// Знайти всі Items переглянуті (view) конкретним Customer
:param customerId => 'C002';
MATCH (:Customer {id: $customerId})-[:VIEWED]->(i:Item)
RETURN i.id AS item_id, i.name AS item_name, i.price AS price
ORDER BY i.name;

// Знайти інші Items, що купувались разом з конкретним Item
:param itemId => 'I001';
MATCH (:Item {id: $itemId})<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(other:Item)
WHERE other.id <> $itemId
RETURN other.id AS item_id, other.name AS item_name, count(DISTINCT o) AS together_orders
ORDER BY together_orders DESC, item_name ASC;

// Знайти Customers, які купили конкретний Item
:param itemId => 'I003';
MATCH (c:Customer)-[:BOUGHT]->(:Order)-[:CONTAINS]->(:Item {id: $itemId})
RETURN DISTINCT c.id AS customer_id, c.name AS customer_name
ORDER BY customer_name;

// Знайти для Customer товари, які він переглядав, але не купив
:param customerId => 'C002';
MATCH (c:Customer {id: $customerId})-[:VIEWED]->(i:Item)
WHERE NOT EXISTS {
  MATCH (c)-[:BOUGHT]->(:Order)-[:CONTAINS]->(i)
}
RETURN i.id AS item_id, i.name AS item_name, i.price AS price
ORDER BY i.name;
