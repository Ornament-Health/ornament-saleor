-- product categories
insert into product_category (id,"name",slug,description,lft,rght,tree_id,"level",parent_id,background_image,seo_description,seo_title,background_image_alt,metadata,private_metadata,description_plaintext) values
(1000, 'Анализы', 'analizy', 'null', 1, 43, 1, 0, null, '', null, null, '', '{}', '{}', '{}'),
(2, 'Комплексные анализы', 'kompleksnye-analizy', 'null', 3, 4, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(3, 'Витамины', 'vitaminy', 'null', 5, 6, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(4, 'Клинический анализ крови', 'klinicheskii-analiz-krovi', 'null', 7, 8, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(5, 'Анализ мочи', 'analiz-mochi', 'null', 9, 10, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(6, 'Биохимия', 'biokhimiia', 'null', 11, 12, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(7, 'Гормоны', 'gormony', 'null', 13, 14, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(8, 'Комплексное обследование check-up', 'kompleksnoe-obsledovanie-check-up', 'null', 15, 16, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(9, 'Генетические обследования', 'geneticheskie-obsledovaniia', 'null', 17, 18, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(10, 'Гематология', 'gematologiia', 'null', 19, 20, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(11, 'Коагулограмма', 'koagulogramma', 'null', 21, 22, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(12, 'Онкология', 'onkologiia', 'null', 23, 24, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(13, 'Вирусы/инфекции/паразиты', 'virusyinfektsiiparazity', 'null', 25, 26, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(14, 'Общеклинические', 'obshcheklinicheskie', 'null', 27, 28, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(15, 'Группа крови, резус', 'gruppa-krovi-rezus', 'null', 29, 30, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(16, 'Цито- и гистология', 'tsito-i-gistologiia', 'null', 31, 32, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(17, 'Иммунология', 'immunologiia', 'null', 33, 34, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(18, 'Витамины, микроэлементы', 'vitaminy-mikroelementy', 'null', 35, 36, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(19, 'Токсикология', 'toksikologiia', 'null', 37, 38, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(20, 'Генетические', 'geneticheskie', 'null', 39, 40, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(21, 'Разное', 'raznoe', 'null', 41, 42, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}');

update product_category 
set name = 'Популярное',
slug = 'populiarnoe',
lft = 1,
rght = 2,
tree_id = 1,
level = 1,
parent_id = 1000
where id = 1;

update product_producttype 
set name = 'Анализ',
slug = 'analiz'
where id = 1;