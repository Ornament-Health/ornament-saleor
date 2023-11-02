-- product categories
insert into product_category (id,"name",slug,description,lft,rght,tree_id,"level",parent_id,background_image,seo_description,seo_title,background_image_alt,metadata,private_metadata,description_plaintext) values
(1000, 'Анализы', 'analizy', 'null', 0, 0, 1, 0, null, '', null, null, '', '{}', '{}', '{}'),
(2, 'Комплексные анализы', 'kompleksnye-analizy', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(3, 'Витамины', 'vitaminy', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(4, 'Клинический анализ крови', 'klinicheskii-analiz-krovi', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(5, 'Анализ мочи', 'analiz-mochi', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(6, 'Биохимия', 'biokhimiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(7, 'Гормоны', 'gormony', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(8, 'Комплексное обследование check-up', 'kompleksnoe-obsledovanie-check-up', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(9, 'Генетические обследования', 'geneticheskie-obsledovaniia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(10, 'Гематология', 'gematologiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(11, 'Коагулограмма', 'koagulogramma', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(12, 'Онкология', 'onkologiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(13, 'Вирусы/инфекции/паразиты', 'virusyinfektsiiparazity', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(14, 'Общеклинические', 'obshcheklinicheskie', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(15, 'Группа крови, резус', 'gruppa-krovi-rezus', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(16, 'Цито- и гистология', 'tsito-i-gistologiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(17, 'Иммунология', 'immunologiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(18, 'Витамины, микроэлементы', 'vitaminy-mikroelementy', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(19, 'Токсикология', 'toksikologiia', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}'),
(20, 'Генетические', 'geneticheskie', 'null', 0, 0, 1, 1, 1000, '', null, null, '', '{}', '{}', '{}');

update product_category 
set name = 'Популярное',
slug = 'populiarnoe',
tree_id = 1,
level = 1,
parent_id = 1000
where id = 1;