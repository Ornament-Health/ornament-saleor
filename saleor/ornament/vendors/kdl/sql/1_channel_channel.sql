-- channels (aka vendors/providers)
update channel_channel 
set name = 'Москва и МО',
slug = 'moscow',
currency_code = 'RUB',
default_country = 'RU',
allocation_strategy = 'prioritize-sorting-order'
where id = 1;

insert into channel_channel (id,"name",slug,is_active,currency_code,default_country,allocation_strategy,automatically_confirm_all_new_orders,automatically_fulfill_non_shippable_gift_card,order_mark_as_paid_strategy,default_transaction_flow_strategy,expire_orders_after,delete_expired_orders_after,metadata,private_metadata,allow_unpaid_orders) values
(2,	'Спб', 'spb',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(3,	'Саратов', 'saratov',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(4,	'Майкоп', 'maykop',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(5,	'Омск', 'omsk',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(6,	'Волгоград', 'volgograd',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(7,	'Новокузнецк', 'novokuzneck',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(8,	'Новосибирск', 'novosibirsk',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(9,	'Уфа (Стерлитамак, Салават, Уфа)', 'ufa',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(10, 'Екатеринбург', 'ekaterinburg',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(11, 'Астрахань', 'astrahan',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(12, 'Тюмень', 'tumen',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(13, 'Кемерово', 'kemerovo',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(14, 'Краснодар', 'krasnodar',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(15, 'Казань', 'kazan',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(16, 'Ростов (Таганрог, Ростов-на-Дону)', 'rostov',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(17, 'Побережье (Новороссийск)', 'pobereje',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(18, 'Ярославль', 'yaroslavl',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(19, 'Армавир', 'armavir',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(20, 'Барнаул', 'barnaul',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false),
(21, 'Пермь', 'perm',true,'RUB','RU','prioritize-sorting-order',true,true,'payment_flow','charge',null,'60 days','{}','{}',false);

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
countries = 'RU'
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
set name = 'KDL Default'
where id = 1;

update shipping_shippingmethodchannellisting
set currency = 'RUB'
where id = 1;

insert into shipping_shippingmethodchannellisting (id, minimum_order_price_amount, currency, maximum_order_price_amount, price_amount, channel_id, shipping_method_id) values
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

insert into shipping_shippingmethodchannellisting (id, minimum_order_price_amount, currency, maximum_order_price_amount, price_amount, channel_id, shipping_method_id) values
(2, 0.000, 'RUB', null, 0.000, 2, 1),
(3, 0.000, 'RUB', null, 0.000, 3, 1),
(4, 0.000, 'RUB', null, 0.000, 4, 1),
(5, 0.000, 'RUB', null, 0.000, 5, 1),
(6, 0.000, 'RUB', null, 0.000, 6, 1),
(7, 0.000, 'RUB', null, 0.000, 7, 1),
(8, 0.000, 'RUB', null, 0.000, 8, 1),
(9, 0.000, 'RUB', null, 0.000, 9, 1),
(10, 0.000, 'RUB', null, 0.000, 10, 1),
(11, 0.000, 'RUB', null, 0.000, 11, 1),
(12, 0.000, 'RUB', null, 0.000, 12, 1),
(13, 0.000, 'RUB', null, 0.000, 13, 1),
(14, 0.000, 'RUB', null, 0.000, 14, 1),
(15, 0.000, 'RUB', null, 0.000, 15, 1),
(16, 0.000, 'RUB', null, 0.000, 16, 1),
(17, 0.000, 'RUB', null, 0.000, 17, 1),
(18, 0.000, 'RUB', null, 0.000, 18, 1),
(19, 0.000, 'RUB', null, 0.000, 19, 1),
(20, 0.000, 'RUB', null, 0.000, 20, 1),
(21, 0.000, 'RUB', null, 0.000, 21, 1);