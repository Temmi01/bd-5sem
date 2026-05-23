
use("lab4_shop");
db.dropDatabase();

// джсон вивід
function printDocs(cursor) {
  cursor.forEach((doc) => printjson(doc));
}

// створення товарів
printjson(
  db.items.insertMany([
    {
      _id: "item_phone_iphone13",
      category: "Phone",
      model: "iPhone 13",
      producer: "Apple",
      price: 32000,
      storage_gb: 128,
      ram_gb: 4,
      color: "Midnight",
      nfc: true,
    },
    {
      _id: "item_tv_lg_oled_c2",
      category: "TV",
      model: "LG OLED C2",
      producer: "LG",
      price: 54000,
      screen_size: 55,
      resolution: "4K",
      smart_tv: true,
      hdmi_ports: 4,
    },
    {
      _id: "item_watch_apple_series9",
      category: "SmartWatch",
      model: "Apple Watch Series 9",
      producer: "Apple",
      price: 18000,
      strap: "Sport Band",
      waterproof: true,
      eSIM: true,
    },
    {
      _id: "item_laptop_vivobook14",
      category: "Laptop",
      model: "VivoBook 14",
      producer: "ASUS",
      price: 25000,
      ram_gb: 16,
      storage_gb: 512,
      cpu: "Intel i7",
    },
    {
      _id: "item_console_ps5",
      category: "Console",
      model: "PlayStation 5",
      producer: "Sony",
      price: 29500,
      generation: "9th",
      storage_gb: 825,
    },
    {
      _id: "item_pool_inflatable_305",
      category: "Pool",
      model: "Inflatable Pool 305",
      producer: "Intex",
      price: 7900,
      diameter_cm: 305,
      volume_l: 3853,
      material: "PVC",
    },
    {
      _id: "item_led_bulb_e27_12w",
      category: "Lighting",
      model: "LED Bulb E27 12W",
      producer: "Philips",
      price: 450,
      socket: "E27",
      power_w: 12,
      color_temp_k: 4000,
    },
    {
      _id: "item_iron_ultraheat",
      category: "HomeAppliance",
      model: "Steam Iron UltraHeat",
      producer: "Tefal",
      price: 2300,
      power_w: 2400,
      steam_boost_gm: 180,
    },
    {
      _id: "item_broom_classic",
      category: "Cleaning",
      model: "Classic Broom",
      producer: "CleanHome",
      price: 300,
      material: "birch",
      handle_length_cm: 120,
    },
    {
      _id: "item_doc_spongebob_license",
      category: "Document",
      model: "SpongeBob Driver License",
      producer: "BikiniBottom DMV",
      price: 999999,
      owner: "SpongeBob SquarePants",
      valid_until: "2099-01-01",
    },
    {
      _id: "item_wooden_pillow_oak",
      category: "Furniture",
      model: "Wooden Pillow Oak Edition",
      producer: "CarpathianCraft",
      price: 1500,
      wood_type: "oak",
      length_cm: 55,
    },
  ])
);

// 2) вивід усіх товарів
printDocs(db.items.find());

// 3) кількість товарів у категорії
print("Кількість товарів у категорії Phone: " + db.items.countDocuments({ category: "Phone" }));

// 4) кількість категорій
print("Кількість категорій: " + db.items.distinct("category").length);

// 5) виробники товарів без повторів
printjson(db.items.distinct("producer"));

// 6a) товари за категорією та ціною
printDocs(
  db.items.find({
    $and: [{ category: "Phone" }, { price: { $gte: 30000, $lte: 37000 } }],
  })
);

// 6b) модель одна чи інша
printDocs(
  db.items.find({
    $or: [{ model: "iPhone 13" }, { model: "LG OLED C2" }],
  })
);

// 6c) виробники з переліку
printDocs(
  db.items.find({
    producer: { $in: ["Apple", "Sony"] },
  })
);

// 7) оновлення товарів
printjson(
  db.items.updateOne(
    { model: "iPhone 13" },
    { $set: { price: 31500, color: "Starlight" } }
  )
);
// за критерієм
printjson(
  db.items.updateMany(
    { category: "SmartWatch" },
    { $set: { warranty_months: 24 } }
  )
);

// 8) товари у яких присутнє поле нфс
printDocs(
  db.items.find(
    { nfc: { $exists: true } },
    { _id: 0, model: 1, price: 1 }
  )
);

// 9) підвищення ціни і перевірка
printjson(db.items.updateMany({ nfc: { $exists: true } }, { $inc: { price: 500 } }));

printDocs(
  db.items.find(
    { nfc: { $exists: true } },
    { _id: 0, model: 1, price: 1 }
  )
);

// 1) створення замовлень
printjson(
  db.orders.insertMany([
    {
      _id: "order_1001",
      order_number: 1001,
      date: ISODate("2026-05-10T00:00:00Z"),
      total_sum: 86000,
      customer: {
        name: "Andrii",
        surname: "Rodionov",
        phones: [9876543, 1234567],
        address: "Kyiv, UA",
      },
      payment: {
        card_owner: "Andrii Rodionov",
        cardId: "5168-****-****-1122",
      },
      items_id: ["item_phone_iphone13", "item_tv_lg_oled_c2"],
    },
    {
      _id: "order_1002",
      order_number: 1002,
      date: ISODate("2026-05-11T00:00:00Z"),
      total_sum: 14950,
      customer: {
        name: "Iryna",
        surname: "Koval",
        phones: [501112233],
        address: "Lviv, UA",
      },
      payment: {
        card_owner: "Iryna Koval",
        cardId: "5375-****-****-7766",
      },
      items_id: ["item_led_bulb_e27_12w", "item_headphones_wh1000xm5"],
    },
    {
      _id: "order_1003",
      order_number: 1003,
      date: ISODate("2026-05-12T00:00:00Z"),
      total_sum: 114000,
      customer: {
        name: "Andrii",
        surname: "Rodionov",
        phones: [9876543],
        address: "Kyiv, UA",
      },
      payment: {
        card_owner: "Andrii Rodionov",
        cardId: "5168-****-****-1122",
      },
      items_id: ["item_phone_iphone13", "item_laptop_vivobook14"],
    },
    {
      _id: "order_1004",
      order_number: 1004,
      date: ISODate("2026-05-14T00:00:00Z"),
      total_sum: 8200,
      customer: {
        name: "Oleksii",
        surname: "Melnyk",
        phones: [661234567],
        address: "Dnipro, UA",
      },
      payment: {
        card_owner: "Oleksii Melnyk",
        cardId: "4149-****-****-3344",
      },
      items_id: ["item_pool_inflatable_305", "item_broom_classic"],
    },
  ])
);

// 2) вивід усіх замовлень
printDocs(db.orders.find());

// 3) замовлення з вартістю більше 50000
printDocs(db.orders.find({ total_sum: { $gt: 50000 } }));

// 4) замовлення одного замовника
printDocs(
  db.orders.find({
    "customer.name": "Andrii",
    "customer.surname": "Rodionov",
  })
);

// 5) замовлення з певним товаром
printDocs(db.orders.find({ items_id: "item_phone_iphone13" }));

// 6) додати товар у замовлення і збільшити суму
printjson(
  db.orders.updateMany(
    { items_id: "item_phone_iphone13" },
    { $addToSet: { items_id: "item_iron_ultraheat" }, $inc: { total_sum: 2300 } }
  )
);

// 7) кількість товарів у певному замовленні
const order1001 = db.orders.findOne(
  { order_number: 1001 },
  { _id: 0, items_id: 1 }
);
print("Кількість товарів у замовленні 1001: " + (order1001 ? order1001.items_id.length : 0));

// 8) інформація про кастомера та номер кредитної картки для замовлень з сумою більше 70000
printDocs(
  db.orders.find(
    { total_sum: { $gt: 70000 } },
    { _id: 0, customer: 1, "payment.cardId": 1 }
  )
);

// 9) видалити товар із замовлень за період
printjson(
  db.orders.updateMany(
    {
      date: {
        $gte: ISODate("2026-05-11T00:00:00Z"),
        $lte: ISODate("2026-05-13T23:59:59Z"),
      },
    },
    { $pull: { items_id: "item_headphones_wh1000xm5" } }
  )
);

// 10) змінити прізвище у всіх замовленнях
printjson(db.orders.updateMany({}, { $set: { "customer.surname": "Shevchenko" } }));

// 11) замовлення зроблені одним замовником
printDocs(
  db.orders.aggregate([
    {
      $match: {
        "customer.name": "Andrii",
        "customer.surname": "Shevchenko",
      },
    },
    {
      $lookup: {
        from: "items",
        localField: "items_id",
        foreignField: "_id",
        as: "items_info",
      },
    },
    {
      $project: {
        _id: 0,
        customer: 1,
        items: {
          $map: {
            input: "$items_info",
            as: "i",
            in: { model: "$$i.model", price: "$$i.price" },
          },
        },
      },
    },
  ])
);

// 1) capped колекція 
printjson(
  db.createCollection("reviews_capped", {
    capped: true,
    size: 16384,
    max: 5,
  })
);

// 2) додати 7 відгуків
printjson(
  db.reviews_capped.insertMany([
    {
      review_id: 1,
      author: "user1",
      rating: 4,
      text: "Review #1",
      created_at: ISODate("2026-05-20T10:01:00Z"),
    },
    {
      review_id: 2,
      author: "user2",
      rating: 5,
      text: "Review #2",
      created_at: ISODate("2026-05-20T10:02:00Z"),
    },
    {
      review_id: 3,
      author: "user3",
      rating: 3,
      text: "Review #3",
      created_at: ISODate("2026-05-20T10:03:00Z"),
    },
    {
      review_id: 4,
      author: "user4",
      rating: 4,
      text: "Review #4",
      created_at: ISODate("2026-05-20T10:04:00Z"),
    },
    {
      review_id: 5,
      author: "user5",
      rating: 5,
      text: "Review #5",
      created_at: ISODate("2026-05-20T10:05:00Z"),
    },
    {
      review_id: 6,
      author: "user6",
      rating: 4,
      text: "Review #6",
      created_at: ISODate("2026-05-20T10:06:00Z"),
    },
    {
      review_id: 7,
      author: "user7",
      rating: 5,
      text: "Review #7",
      created_at: ISODate("2026-05-20T10:07:00Z"),
    },
  ])
);

// 3) показати відгуки, що залишились
printDocs(
  db.reviews_capped
    .find({}, { _id: 0, review_id: 1, author: 1 })
    .sort({ review_id: 1 })
);
// 4) кількість відгуків у capped колекції
print("Кількість відгуків у capped колекції: " + db.reviews_capped.countDocuments());

