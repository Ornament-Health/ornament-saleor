-- channels (aka vendors/providers)
update channel_channel 
set name = 'Москва и МО',
slug = 'moscow',
currency_code = 'RUB',
default_country = 'RU',
allocation_strategy = 'prioritize-sorting-order',
allow_unpaid_orders = true
where id = 1;

insert into channel_channel (id,"name",slug,is_active,currency_code,default_country,allocation_strategy,automatically_confirm_all_new_orders,automatically_fulfill_non_shippable_gift_card,order_mark_as_paid_strategy,default_transaction_flow_strategy,expire_orders_after,delete_expired_orders_after,metadata,private_metadata,allow_unpaid_orders) values
(2,	'Спб', 'spb',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(3,	'Саратов', 'saratov',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(4,	'Майкоп', 'maykop',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(5,	'Омск', 'omsk',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(6,	'Волгоград', 'volgograd',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(7,	'Новокузнецк', 'novokuzneck',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(8,	'Новосибирск', 'novosibirsk',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(9,	'Уфа (Стерлитамак, Салават, Уфа)', 'ufa',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(10, 'Екатеринбург', 'ekaterinburg',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(11, 'Астрахань', 'astrahan',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(12, 'Тюмень', 'tumen',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(13, 'Кемерово', 'kemerovo',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(14, 'Краснодар', 'krasnodar',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(15, 'Казань', 'kazan',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(16, 'Ростов (Таганрог, Ростов-на-Дону)', 'rostov',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(17, 'Побережье (Новороссийск)', 'pobereje',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(18, 'Ярославль', 'yaroslavl',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(19, 'Армавир', 'armavir',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(20, 'Барнаул', 'barnaul',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true),
(21, 'Пермь', 'perm',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',true);

update account_address 
set company_name = 'KDL',
street_address_1 = 'Address',
city = 'MOSCOW',
postal_code = '101000',
country = 'RU',
country_area = 'Москва'
where id = 1;

delete from warehouse_warehouse_shipping_zones where id > 0;
delete from warehouse_channelwarehouse where id > 0;

update warehouse_warehouse 
set id = '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58',
name = 'KDL Warehouse',
slug = 'kdl-warehouse',
is_private = false
where address_id = 1;

insert into warehouse_channelwarehouse (id, warehouse_id, channel_id) values
(1, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 1),
(2, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 2),
(3, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 3),
(4, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 4),
(5, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 5),
(6, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 6),
(7, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 7),
(8, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 8),
(9, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 9),
(10, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 10),
(11, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 11),
(12, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 12),
(13, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 13),
(14, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 14),
(15, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 15),
(16, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 16),
(17, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 17),
(18, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 18),
(19, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 19),
(20, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 20),
(21, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 21);

update shipping_shippingzone
set name = 'KDL Russia',
countries = 'RU',
"default" = true
where id = 1;

insert into shipping_shippingzone_channels (id, shippingzone_id, channel_id) values
(2, 1, 2),
(3, 1, 3),
(4, 1, 4),
(5, 1, 5),
(6, 1, 6),
(7, 1, 7),
(8, 1, 8),
(9, 1, 9),
(10, 1, 10),
(11, 1, 11),
(12, 1, 12),
(13, 1, 13),
(14, 1, 14),
(15, 1, 15),
(16, 1, 16),
(17, 1, 17),
(18, 1, 18),
(19, 1, 19),
(20, 1, 20),
(21, 1, 21);

insert into warehouse_warehouse_shipping_zones (id, warehouse_id, shippingzone_id) values
(1, '2e83f67b-a080-4710-9ee8-4bf3bc0e0b58', 1);

update shipping_shippingmethod
set name = 'KDL Standart'
where id = 1;

insert into shipping_shippingmethod (id, "name", maximum_order_weight, minimum_order_weight, "type", shipping_zone_id, metadata, private_metadata, maximum_delivery_days, minimum_delivery_days, description, tax_class_id) values
(2, 'KDL Discounted', NULL, 0.0, 'price', 1, '{}'::jsonb, '{}'::jsonb, NULL, NULL, 'null'::jsonb, NULL);

delete from shipping_shippingmethodchannellisting
where id = 1;

insert into shipping_shippingmethodchannellisting (minimum_order_price_amount, currency, maximum_order_price_amount, price_amount, channel_id, shipping_method_id) values
(NULL, 'RUB', 1900.000, 690.000, 1, 1),
(NULL, 'RUB', 1500.000, 530.000, 12, 1),
(NULL, 'RUB', 1500.000, 655.000, 10, 1),
(NULL, 'RUB', 1500.000, 600.000, 2, 1),
(NULL, 'RUB', 1500.000, 600.000, 15, 1),
(NULL, 'RUB', 1500.000, 630.000, 19, 1),
(NULL, 'RUB', 1500.000, 510.000, 20, 1),
(NULL, 'RUB', 1500.000, 610.000, 9, 1),
(NULL, 'RUB', 1500.000, 940.000, 5, 1),
(NULL, 'RUB', 1500.000, 620.000, 3, 1),
(NULL, 'RUB', 1500.000, 720.000, 17, 1),
(NULL, 'RUB', 1900.000, 610.000, 18, 1),
(NULL, 'RUB', 1500.000, 606.000, 4, 1),
(NULL, 'RUB', 1500.000, 660.000, 11, 1),
(NULL, 'RUB', NULL, 640.000, 21, 1),
(NULL, 'RUB', 1000.000, 630.000, 13, 1),
(NULL, 'RUB', 1900.000, 820.000, 14, 1),
(NULL, 'RUB', 1500.000, 610.000, 6, 1),
(NULL, 'RUB', 1500.000, 650.000, 8, 1),
(NULL, 'RUB', 1500.000, 630.000, 7, 1),
(NULL, 'RUB', 1500.000, 820.000, 16, 1),
(1500.000, 'RUB', NULL, 130.000, 12, 2),
(1500.000, 'RUB', NULL, 165.000, 10, 2),
(1500.000, 'RUB', NULL, 100.000, 2, 2),
(1500.000, 'RUB', NULL, 110.000, 15, 2),
(1500.000, 'RUB', NULL, 180.000, 19, 2),
(1500.000, 'RUB', NULL, 120.000, 20, 2),
(1500.000, 'RUB', NULL, 110.000, 9, 2),
(1500.000, 'RUB', NULL, 140.000, 5, 2),
(1500.000, 'RUB', NULL, 120.000, 3, 2),
(1900.000, 'RUB', NULL, 200.000, 1, 2),
(1500.000, 'RUB', NULL, 120.000, 17, 2),
(1900.000, 'RUB', NULL, 110.000, 18, 2),
(1500.000, 'RUB', NULL, 126.000, 4, 2),
(1500.000, 'RUB', NULL, 60.000, 11, 2),
(1000.000, 'RUB', NULL, 130.000, 13, 2),
(1900.000, 'RUB', NULL, 120.000, 14, 2),
(1500.000, 'RUB', NULL, 160.000, 6, 2),
(1500.000, 'RUB', NULL, 150.000, 8, 2),
(1500.000, 'RUB', NULL, 175.000, 7, 2),
(1500.000, 'RUB', NULL, 120.000, 16, 2);